"""
DripBux Auth Routes
===================
Google OAuth + Local authentication with role-based access.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Cart, Seller
from forms import LoginForm, RegisterForm, ProfileForm, ChangePasswordForm
from config import OAuthConfig
import os
import uuid
import requests

auth_bp = Blueprint('auth', __name__)


# =============================================================================
# GOOGLE OAUTH
# =============================================================================

@auth_bp.route('/google/login')
def google_login():
    """Initiate Google OAuth login"""
    if not OAuthConfig.GOOGLE_CLIENT_ID:
        flash('Google login is not configured.', 'error')
        return redirect(url_for('auth.login'))

    redirect_uri = url_for('auth.google_callback', _external=True)
    scope = 'openid email profile'
    state = str(uuid.uuid4())
    session['oauth_state'] = state

    auth_url = (
        f"{OAuthConfig.GOOGLE_AUTH_URL}"
        f"?client_id={OAuthConfig.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={requests.utils.quote(scope)}"
        f"&state={state}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return redirect(auth_url)


@auth_bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    if 'error' in request.args:
        flash('Google login was cancelled or failed.', 'error')
        return redirect(url_for('auth.login'))

    state = request.args.get('state')
    stored_state = session.pop('oauth_state', None)
    if not state or state != stored_state:
        flash('Invalid state parameter. Please try again.', 'error')
        return redirect(url_for('auth.login'))

    code = request.args.get('code')
    if not code:
        flash('Authorization code not received.', 'error')
        return redirect(url_for('auth.login'))

    # Exchange code for tokens
    redirect_uri = url_for('auth.google_callback', _external=True)
    token_data = {
        'code': code,
        'client_id': OAuthConfig.GOOGLE_CLIENT_ID,
        'client_secret': OAuthConfig.GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    try:
        token_resp = requests.post(OAuthConfig.GOOGLE_TOKEN_URL, data=token_data, timeout=10)
        token_resp.raise_for_status()
        tokens = token_resp.json()
        access_token = tokens.get('access_token')

        # Get user info
        userinfo_resp = requests.get(
            OAuthConfig.GOOGLE_USERINFO_URL,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        userinfo_resp.raise_for_status()
        userinfo = userinfo_resp.json()

        google_id = userinfo.get('sub')
        email = userinfo.get('email')
        name = userinfo.get('name') or email.split('@')[0]
        picture = userinfo.get('picture')

        if not google_id or not email:
            flash('Could not retrieve account information from Google.', 'error')
            return redirect(url_for('auth.login'))

        # Check if user exists
        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            user = User.query.filter_by(email=email).first()

        if user:
            # Update existing user
            user.google_id = google_id
            if picture:
                user.google_avatar = picture
            user.last_login = datetime.utcnow()
            if user.auth_provider == 'local':
                user.auth_provider = 'google'
            db.session.commit()
        else:
            # Create new user
            base_username = name.replace(' ', '_').lower()[:30]
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
                google_id=google_id,
                google_avatar=picture,
                avatar_url='default-avatar.png',
                auth_provider='google',
                email_verified=True,
                role='customer',
                is_active=True,
                robux_balance=10000
            )
            db.session.add(user)
            db.session.commit()

            # Create cart
            cart = Cart(user_id=user.id)
            db.session.add(cart)
            db.session.commit()

            flash(f'Welcome to DripBux, {user.username}!', 'success')

        login_user(user, remember=True)
        user.last_login = datetime.utcnow()
        db.session.commit()

        next_page = request.args.get('next') or url_for('main.index')
        return redirect(next_page)

    except requests.RequestException as e:
        flash('Failed to connect to Google. Please try again.', 'error')
        return redirect(url_for('auth.login'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred during login. Please try again.', 'error')
        return redirect(url_for('auth.login'))


# =============================================================================
# LOCAL AUTH
# =============================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.password_hash and check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated.', 'error')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()

            if not user.cart:
                cart = Cart(user_id=user.id)
                db.session.add(cart)
            db.session.commit()

            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next') or url_for('main.index')
            return redirect(next_page)
        else:
            flash('Invalid username or password.', 'error')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'error')
            return render_template('auth/register.html', form=form)

        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'error')
            return render_template('auth/register.html', form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            auth_provider='local',
            email_verified=False,
            role='customer',
            robux_balance=10000
        )
        db.session.add(user)
        db.session.commit()

        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.commit()

        flash('Account created! Please sign in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('main.index'))


# =============================================================================
# PROFILE
# =============================================================================

@auth_bp.route('/profile')
@login_required
def profile():
    from models import Order, Address, Wishlist, RecentlyViewed
    addresses = Address.query.filter_by(user_id=current_user.id).order_by(Address.is_default.desc()).all()
    recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).order_by(Wishlist.created_at.desc()).limit(6).all()
    recently_viewed = RecentlyViewed.query.filter_by(user_id=current_user.id).order_by(RecentlyViewed.viewed_at.desc()).limit(8).all()
    return render_template('auth/profile.html', addresses=addresses, recent_orders=recent_orders, wishlist_items=wishlist_items, recently_viewed=recently_viewed)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Username already taken.', 'error')
            return render_template('auth/edit_profile.html', form=form)

        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email and existing_email.id != current_user.id:
            flash('Email already registered.', 'error')
            return render_template('auth/edit_profile.html', form=form)

        if form.avatar.data:
            avatar_file = form.avatar.data
            filename = secure_filename(avatar_file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            avatar_path = os.path.join(current_app.root_path, 'static/images/avatars', unique_filename)
            avatar_file.save(avatar_path)
            current_user.avatar_url = unique_filename

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/edit_profile.html', form=form)


@auth_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if current_user.auth_provider == 'google' and not current_user.password_hash:
        flash('Google accounts cannot change password here. Use Google account settings.', 'info')
        return redirect(url_for('auth.profile'))

    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not check_password_hash(current_user.password_hash, form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html', form=form)

        current_user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash('Password changed!', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/profile/addresses')
@login_required
def addresses():
    from models import Address
    addresses = Address.query.filter_by(user_id=current_user.id).order_by(Address.is_default.desc()).all()
    return render_template('auth/addresses.html', addresses=addresses)


@auth_bp.route('/profile/addresses/add', methods=['GET', 'POST'])
@login_required
def add_address():
    from models import Address
    from forms import AddressForm
    form = AddressForm()
    if form.validate_on_submit():
        if form.is_default.data:
            Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
        address = Address(user_id=current_user.id, **{k: v for k, v in form.data.items() if k not in ('submit', 'csrf_token')})
        db.session.add(address)
        db.session.commit()
        flash('Address added!', 'success')
        return redirect(url_for('auth.addresses'))
    return render_template('auth/add_address.html', form=form)


@auth_bp.route('/profile/addresses/<int:address_id>/delete', methods=['POST'])
@login_required
def delete_address(address_id):
    from models import Address
    address = Address.query.get_or_404(address_id)
    if address.user_id != current_user.id:
        abort(403)
    db.session.delete(address)
    db.session.commit()
    flash('Address deleted.', 'success')
    return redirect(url_for('auth.addresses'))


@auth_bp.route('/profile/orders')
@login_required
def order_history():
    from models import Order
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    query = Order.query.filter_by(user_id=current_user.id)
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('auth/orders.html', orders=orders, current_status=status)


@auth_bp.route('/profile/wishlist')
@login_required
def wishlist():
    from models import Wishlist
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).order_by(Wishlist.created_at.desc()).all()
    return render_template('auth/wishlist.html', wishlist_items=wishlist_items)


@auth_bp.route('/profile/notifications')
@login_required
def notifications():
    from models import Notification
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    # Mark as read
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for n in unread:
        n.is_read = True
    db.session.commit()
    return render_template('auth/notifications.html', notifications=notifications)


from datetime import datetime
