"""
DripBux Premium - Authentication Routes
=======================================
User registration, login, logout, and profile management.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Cart, Address
from forms import LoginForm, RegisterForm, ProfileForm, ChangePasswordForm, AddressForm
import os
import uuid

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html', form=form)
            
            login_user(user, remember=form.remember_me.data)
            user.last_login = db.func.now()
            db.session.commit()
            
            # Create cart if user doesn't have one
            if not user.cart:
                cart = Cart(user_id=user.id)
                db.session.add(cart)
                db.session.commit()
            
            flash(f'Welcome back, {user.username}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'error')
            return render_template('auth/register.html', form=form)
        
        # Check if email exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        
        # Create cart for new user
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.commit()
        
        flash('Account created successfully! Please sign in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    return render_template('auth/profile.html', addresses=addresses)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Check if username is taken by another user
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Username already taken.', 'error')
            return render_template('auth/edit_profile.html', form=form)
        
        # Check if email is taken by another user
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email and existing_email.id != current_user.id:
            flash('Email already registered.', 'error')
            return render_template('auth/edit_profile.html', form=form)
        
        # Handle avatar upload
        if form.avatar.data:
            avatar_file = form.avatar.data
            filename = secure_filename(avatar_file.filename)
            # Generate unique filename
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            avatar_path = os.path.join(current_app.root_path, 'static/images/avatars', unique_filename)
            avatar_file.save(avatar_path)
            current_user.avatar_url = unique_filename
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', form=form)


@auth_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not check_password_hash(current_user.password_hash, form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html', form=form)
        
        # Update password
        current_user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/profile/addresses')
@login_required
def addresses():
    """User addresses page"""
    addresses = Address.query.filter_by(user_id=current_user.id).order_by(Address.is_default.desc()).all()
    return render_template('auth/addresses.html', addresses=addresses)


@auth_bp.route('/profile/addresses/add', methods=['GET', 'POST'])
@login_required
def add_address():
    """Add new address"""
    form = AddressForm()
    
    if form.validate_on_submit():
        # If setting as default, unset other defaults
        if form.is_default.data:
            Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
        
        address = Address(
            user_id=current_user.id,
            full_name=form.full_name.data,
            phone=form.phone.data,
            address_line1=form.address_line1.data,
            address_line2=form.address_line2.data,
            city=form.city.data,
            state=form.state.data,
            postal_code=form.postal_code.data,
            country=form.country.data,
            is_default=form.is_default.data
        )
        db.session.add(address)
        db.session.commit()
        
        flash('Address added successfully!', 'success')
        return redirect(url_for('auth.addresses'))
    
    return render_template('auth/add_address.html', form=form)


@auth_bp.route('/profile/addresses/<int:address_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_address(address_id):
    """Edit existing address"""
    address = Address.query.get_or_404(address_id)
    
    # Ensure user owns this address
    if address.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('auth.addresses'))
    
    form = AddressForm(obj=address)
    
    if form.validate_on_submit():
        # If setting as default, unset other defaults
        if form.is_default.data and not address.is_default:
            Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
        
        address.full_name = form.full_name.data
        address.phone = form.phone.data
        address.address_line1 = form.address_line1.data
        address.address_line2 = form.address_line2.data
        address.city = form.city.data
        address.state = form.state.data
        address.postal_code = form.postal_code.data
        address.country = form.country.data
        address.is_default = form.is_default.data
        db.session.commit()
        
        flash('Address updated successfully!', 'success')
        return redirect(url_for('auth.addresses'))
    
    return render_template('auth/edit_address.html', form=form, address=address)


@auth_bp.route('/profile/addresses/<int:address_id>/delete', methods=['POST'])
@login_required
def delete_address(address_id):
    """Delete address"""
    address = Address.query.get_or_404(address_id)
    
    # Ensure user owns this address
    if address.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('auth.addresses'))
    
    db.session.delete(address)
    db.session.commit()
    
    flash('Address deleted successfully!', 'success')
    return redirect(url_for('auth.addresses'))


@auth_bp.route('/profile/orders')
@login_required
def order_history():
    """User order history"""
    from models import Order
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('auth/orders.html', orders=orders)


@auth_bp.route('/profile/wishlist')
@login_required
def wishlist():
    """User wishlist"""
    from models import Wishlist, Product
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    products = [item.product for item in wishlist_items]
    return render_template('auth/wishlist.html', products=products)
