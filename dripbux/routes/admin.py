"""
DripBux Admin Routes
====================
Admin dashboard, user management, product moderation, analytics.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from extensions import db
from models import (
    User, Product, Category, ProductSize, Order, Review, Transaction,
    Seller, Coupon, Announcement, ActivityLog, SiteConfig, Message, Notification,
    SellerApplication, SellerWarning, SellerFlag
)
from forms import (
    ProductForm, CategoryForm, AdminUserEditForm, AdminUserCreateForm, SellerActionForm, AddRobuxForm,
    OrderStatusForm, CouponForm, AnnouncementForm, SiteSettingsForm
)
from config import AdminConfig, AppConfig
import os
import uuid
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


def log_action(action, entity_type, entity_id=None, details=None):
    log = ActivityLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action, entity_type=entity_type, entity_id=entity_id, details=details
    )
    db.session.add(log)
    db.session.commit()


# =============================================================================
# DASHBOARD
# =============================================================================

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    stats = {
        'total_users': User.query.count(),
        'total_products': Product.query.count(),
        'total_orders': Order.query.count(),
        'total_revenue': db.session.query(db.func.sum(Order.total_robux)).filter(Order.status != Order.STATUS_CANCELLED).scalar() or 0,
        'pending_orders': Order.query.filter_by(status=Order.STATUS_PENDING).count(),
        'pending_sellers': Seller.query.filter_by(verification_status='pending').count(),
        'low_stock': Product.query.join(ProductSize).filter(ProductSize.stock < 5).distinct().count(),
    }

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    top_products = Product.query.order_by(Product.sales_count.desc()).limit(10).all()
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(20).all()

    # Revenue chart data (last 7 days)
    revenue_data = []
    for i in range(6, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        revenue = db.session.query(db.func.coalesce(db.func.sum(Order.total_robux), 0)).filter(
            Order.created_at >= day_start,
            Order.created_at < day_end,
            Order.status != Order.STATUS_CANCELLED
        ).scalar()
        revenue_data.append({'date': day_start.strftime('%m/%d'), 'revenue': int(revenue)})

    return render_template('admin/dashboard.html', stats=stats,
        recent_orders=recent_orders, recent_users=recent_users,
        top_products=top_products, revenue_data=revenue_data, recent_logs=recent_logs)


# =============================================================================
# USER MANAGEMENT
# =============================================================================

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')
    role = request.args.get('role')
    query = User.query
    if search:
        query = query.filter(db.or_(User.username.ilike(f'%{search}%'), User.email.ilike(f'%{search}%')))
    if role:
        query = query.filter_by(role=role)
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=25, error_out=False)
    return render_template('admin/users.html', users=users, search=search, role=role)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = AdminUserEditForm(obj=user)
    robux_form = AddRobuxForm()

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.robux_balance = form.robux_balance.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        db.session.commit()
        log_action('edit', 'user', user.id, f'Edited user {user.username}')
        flash('User updated.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/edit_user.html', user=user, form=form, robux_form=robux_form)


@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = AdminUserCreateForm()
    if form.validate_on_submit():
        existing = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        if existing:
            flash('A user with that username or email already exists.', 'error')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                robux_balance=form.robux_balance.data,
                role=form.role.data,
                is_active=form.is_active.data,
                email_verified=True,
                auth_provider='local'
            )
            db.session.add(user)
            db.session.commit()
            log_action('create', 'user', user.id, f'Created {user.username} as {user.role}')
            flash('User account created successfully.', 'success')
            return redirect(url_for('admin.users'))

    return render_template('admin/add_user.html', form=form)


@admin_bp.route('/users/<int:user_id>/add-robux', methods=['POST'])
@login_required
@admin_required
def add_robux(user_id):
    user = User.query.get_or_404(user_id)
    form = AddRobuxForm()
    if form.validate_on_submit():
        user.add_robux(form.amount.data, description=f'Admin: {form.reason.data or "Added by admin"}')
        db.session.commit()
        log_action('add_robux', 'user', user.id, f'Added {form.amount.data} Robux')
        flash(f'Added {form.amount.data:,} Robux to {user.username}', 'success')
    return redirect(url_for('admin.edit_user', user_id=user_id))


# =============================================================================
# SELLER MANAGEMENT
# =============================================================================

@admin_bp.route('/sellers')
@login_required
@admin_required
def sellers():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    query = Seller.query
    if status == 'pending':
        query = query.filter_by(verification_status='pending')
    elif status == 'verified':
        query = query.filter_by(verification_status='verified')
    elif status == 'rejected':
        query = query.filter_by(verification_status='rejected')
    sellers = query.order_by(Seller.created_at.desc()).paginate(page=page, per_page=25, error_out=False)
    warning_counts = {
        seller.user_id: Notification.query.filter_by(user_id=seller.user_id, notification_type='warning').count()
        for seller in sellers.items
    }
    return render_template('admin/sellers.html', sellers=sellers, status=status, warning_counts=warning_counts)


@admin_bp.route('/sellers/<int:seller_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_seller(seller_id):
    seller = Seller.query.get_or_404(seller_id)
    action = request.form.get('action')
    if action == 'verify':
        seller.verification_status = 'verified'
        seller.user.role = User.ROLE_SELLER
        flash(f'Seller {seller.store_name} verified!', 'success')
    elif action == 'reject':
        seller.verification_status = 'rejected'
        flash(f'Seller {seller.store_name} rejected.', 'warning')
    db.session.commit()
    return redirect(url_for('admin.sellers'))


@admin_bp.route('/sellers/<int:seller_id>/manage', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_seller(seller_id):
    seller = Seller.query.get_or_404(seller_id)
    form = SellerActionForm()
    if form.validate_on_submit():
        action = request.form.get('action')
        if action == 'warn':
            message = form.message.data or 'Please review marketplace rules and keep your store compliant.'
            # create SellerWarning record
            existing_strikes = SellerWarning.query.filter_by(seller_id=seller.id, is_resolved=False).count()
            strike_no = existing_strikes + 1
            warn = SellerWarning(
                seller_id=seller.id,
                issued_by=current_user.id,
                reason=form.reason.data or 'Policy violation',
                details=message,
                strike=strike_no
            )
            db.session.add(warn)

            # send notification
            notification = Notification(
                user_id=seller.user_id,
                title=f'Seller warning (Strike {strike_no})',
                message=message,
                notification_type='warning',
                link=url_for('seller.dashboard') if seller.user.is_seller else None
            )
            db.session.add(notification)

            # If strike 2 / 3 take actions
            if strike_no == 2:
                # optional temporary suspension
                seller.is_active = False
                seller.verification_status = 'suspended'
                flash('Seller temporarily suspended (strike 2).', 'warning')
                log_action('suspend', 'seller', seller.id, f'Suspended seller {seller.store_name} on strike 2')
            elif strike_no >= 3:
                # escalate to ban/review
                seller.is_active = False
                seller.verification_status = 'banned'
                seller.user.role = User.ROLE_CUSTOMER
                flash('Seller banned (strike 3).', 'error')
                log_action('ban', 'seller', seller.id, f'Banned seller {seller.store_name} on strike 3')

            log_action('warn', 'seller', seller.id, f'Warned seller {seller.store_name}: {message} (strike {strike_no})')
            flash('Warning issued to seller.', 'success')
        elif action == 'revoke':
            seller.is_active = False
            seller.verification_status = 'revoked'
            seller.user.role = User.ROLE_CUSTOMER
            db.session.commit()
            log_action('revoke', 'seller', seller.id, f'Revoked seller access for {seller.store_name}')
            flash('Seller access revoked.', 'warning')
        elif action == 'reinstate':
            seller.is_active = True
            seller.verification_status = 'verified'
            seller.user.role = User.ROLE_SELLER
            db.session.commit()
            log_action('reinstate', 'seller', seller.id, f'Reinstated seller {seller.store_name}')
            flash('Seller access reinstated.', 'success')
        return redirect(url_for('admin.manage_seller', seller_id=seller.id))

    warning_count = Notification.query.filter_by(user_id=seller.user_id, notification_type='warning').count()
    # fetch warnings
    warnings = SellerWarning.query.filter_by(seller_id=seller.id).order_by(SellerWarning.created_at.desc()).all()
    return render_template('admin/manage_seller.html', seller=seller, form=form, warning_count=warning_count, warnings=warnings)


@admin_bp.route('/seller-applications')
@login_required
@admin_required
def seller_applications():
    page = request.args.get('page', 1, type=int)
    apps = SellerApplication.query.order_by(SellerApplication.submitted_at.desc()).paginate(page=page, per_page=25, error_out=False)
    return render_template('admin/seller_applications.html', applications=apps)


@admin_bp.route('/seller-applications/<int:app_id>/review', methods=['POST'])
@login_required
@admin_required
def review_seller_application(app_id):
    app_rec = SellerApplication.query.get_or_404(app_id)
    action = request.form.get('action')
    message = request.form.get('message')
    if action == 'approve':
        # create seller profile if not exists
        if not Seller.query.filter_by(user_id=app_rec.user_id).first():
            user = User.query.get(app_rec.user_id)
            slug = (user.username or f'seller-{user.id}').lower()
            base = slug
            counter = 1
            while Seller.query.filter_by(store_slug=slug).first():
                slug = f'{base}-{counter}'; counter += 1
            seller = Seller(user_id=user.id, store_name=f"{user.get_display_name()}'s Store", store_slug=slug, verification_status='verified', is_active=True)
            db.session.add(seller)
        app_rec.status = 'approved'
        app_rec.reviewed_at = datetime.utcnow()
        app_rec.reviewed_by = current_user.id
        # promote user to seller
        user = User.query.get(app_rec.user_id)
        user.role = User.ROLE_SELLER
        db.session.commit()
        log_action('approve', 'seller_application', app_rec.id, f'Approved application for user {user.id}')
        flash('Application approved and seller created.', 'success')
    elif action == 'reject':
        app_rec.status = 'rejected'
        app_rec.reviewed_at = datetime.utcnow()
        app_rec.reviewed_by = current_user.id
        db.session.commit()
        log_action('reject', 'seller_application', app_rec.id, f'Rejected application {app_rec.id}')
        flash('Application rejected.', 'warning')
    return redirect(url_for('admin.seller_applications'))


# =============================================================================
# PRODUCT MANAGEMENT
# =============================================================================

@admin_bp.route('/products')
@login_required
@admin_required
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')
    category_id = request.args.get('category', type=int)
    status = request.args.get('status')
    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    elif status == 'featured':
        query = query.filter_by(is_featured=True)
    elif status == 'low_stock':
        query = query.join(ProductSize).filter(ProductSize.stock < 5).distinct()
    products = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=25, error_out=False)
    categories = Category.query.filter_by(is_active=True).all()
    return render_template('admin/products.html', products=products, categories=categories, search=search, status=status)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]
    if form.validate_on_submit():
        slug = form.name.data.lower().replace(' ', '-')[:100]
        base = slug
        counter = 1
        while Product.query.filter_by(slug=slug).first():
            slug = f'{base}-{counter}'
            counter += 1

        image_url = None
        if form.image.data:
            f = form.image.data
            fn = secure_filename(f.filename)
            unique = f"{uuid.uuid4().hex}_{fn}"
            f.save(os.path.join(current_app.root_path, 'static/images/products', unique))
            image_url = unique

        product = Product(
            name=form.name.data, slug=slug, description=form.description.data,
            short_description=form.short_description.data, category_id=form.category_id.data,
            price_robux=form.price_robux.data, original_price=form.original_price.data,
            stock_quantity=form.stock_quantity.data, rarity=form.rarity.data,
            product_type=form.product_type.data, tags=form.tags.data,
            image_url=image_url, is_active=form.is_active.data,
            is_featured=form.is_featured.data, is_new=form.is_new.data,
            is_trending=form.is_trending.data, is_flash_sale=form.is_flash_sale.data,
            is_limited=form.is_limited.data
        )
        db.session.add(product)
        db.session.commit()
        log_action('create', 'product', product.id, f'Created {product.name}')
        flash('Product added!', 'success')
        return redirect(url_for('admin.edit_product', product_id=product.id))

    return render_template('admin/add_product.html', form=form)


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]

    if form.validate_on_submit():
        if form.image.data:
            f = form.image.data
            fn = secure_filename(f.filename)
            unique = f"{uuid.uuid4().hex}_{fn}"
            f.save(os.path.join(current_app.root_path, 'static/images/products', unique))
            product.image_url = unique

        product.name = form.name.data
        product.description = form.description.data
        product.short_description = form.short_description.data
        product.category_id = form.category_id.data
        product.price_robux = form.price_robux.data
        product.original_price = form.original_price.data
        product.stock_quantity = form.stock_quantity.data
        product.rarity = form.rarity.data
        product.product_type = form.product_type.data
        product.tags = form.tags.data
        product.is_active = form.is_active.data
        product.is_featured = form.is_featured.data
        product.is_new = form.is_new.data
        product.is_trending = form.is_trending.data
        product.is_flash_sale = form.is_flash_sale.data
        product.is_limited = form.is_limited.data
        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('admin.edit_product', product_id=product.id))

    return render_template('admin/edit_product.html', form=form, product=product)


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    log_action('delete', 'product', product_id, f'Deleted {product.name}')
    flash('Product deleted.', 'success')
    return redirect(url_for('admin.products'))


# =============================================================================
# CATEGORY MANAGEMENT
# =============================================================================

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.order_by(Category.display_order).all()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        cat = Category(name=form.name.data, slug=form.slug.data, description=form.description.data,
                       icon=form.icon.data, display_order=form.display_order.data, is_active=form.is_active.data)
        if form.image.data:
            f = form.image.data
            fn = secure_filename(f.filename)
            unique = f"{uuid.uuid4().hex}_{fn}"
            f.save(os.path.join(current_app.root_path, 'static/images/categories', unique))
            cat.image_url = unique
        db.session.add(cat)
        db.session.commit()
        flash('Category added!', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/add_category.html', form=form)


@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.get_product_count() > 0 or category.subcategories:
        flash('Cannot remove a category with linked products or subcategories. Deactivate it instead.', 'error')
        return redirect(url_for('admin.categories'))

    db.session.delete(category)
    db.session.commit()
    log_action('delete', 'category', category.id, f'Deleted category {category.name}')
    flash('Category removed successfully.', 'success')
    return redirect(url_for('admin.categories'))


# =============================================================================
# ORDER MANAGEMENT
# =============================================================================

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=25, error_out=False)
    return render_template('admin/orders.html', orders=orders, status=status)


@admin_bp.route('/orders/<order_number>')
@login_required
@admin_required
def order_detail(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    form = OrderStatusForm(obj=order)
    return render_template('admin/order_detail.html', order=order, form=form)


@admin_bp.route('/orders/<order_number>/update-status', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    form = OrderStatusForm()
    if form.validate_on_submit():
        old_status = order.status
        order.status = form.status.data
        if form.tracking_number.data:
            order.tracking_number = form.tracking_number.data
        if order.status == Order.STATUS_SHIPPED and old_status != Order.STATUS_SHIPPED:
            order.shipped_at = datetime.utcnow()
        if order.status == Order.STATUS_DELIVERED and old_status != Order.STATUS_DELIVERED:
            order.delivered_at = datetime.utcnow()
        db.session.commit()

        # Notify user
        notif = Notification(
            user_id=order.user_id,
            title=f'Order #{order.order_number} Updated',
            message=f'Your order status changed from {old_status} to {order.status}',
            notification_type='order',
            link=f'/orders/{order.order_number}'
        )
        db.session.add(notif)
        db.session.commit()

        log_action('update_status', 'order', order.id, f'{old_status} -> {order.status}')
        flash('Order status updated.', 'success')
    return redirect(url_for('admin.order_detail', order_number=order_number))


# =============================================================================
# COUPON MANAGEMENT
# =============================================================================

@admin_bp.route('/coupons')
@login_required
@admin_required
def coupons():
    page = request.args.get('page', 1, type=int)
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).paginate(page=page, per_page=25, error_out=False)
    return render_template('admin/coupons.html', coupons=coupons)


@admin_bp.route('/coupons/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_coupon():
    form = CouponForm()
    if form.validate_on_submit():
        coupon = Coupon(
            code=form.code.data.upper(),
            description=form.description.data,
            discount_type=form.discount_type.data,
            discount_value=form.discount_value.data,
            min_order_amount=form.min_order_amount.data or 0,
            max_discount=form.max_discount.data,
            usage_limit=form.usage_limit.data,
            starts_at=form.starts_at.data,
            expires_at=form.expires_at.data,
            is_active=form.is_active.data
        )
        db.session.add(coupon)
        db.session.commit()
        flash('Coupon created!', 'success')
        return redirect(url_for('admin.coupons'))
    return render_template('admin/add_coupon.html', form=form)


# =============================================================================
# ANNOUNCEMENTS
# =============================================================================

@admin_bp.route('/announcements')
@login_required
@admin_required
def announcements():
    anns = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin/announcements.html', announcements=anns)


@admin_bp.route('/announcements/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_announcement():
    form = AnnouncementForm()
    if form.validate_on_submit():
        ann = Announcement(
            title=form.title.data, content=form.content.data,
            announcement_type=form.announcement_type.data,
            is_active=form.is_active.data, expires_at=form.expires_at.data,
            created_by=current_user.id
        )
        db.session.add(ann)
        db.session.commit()
        flash('Announcement posted!', 'success')
        return redirect(url_for('admin.announcements'))
    return render_template('admin/add_announcement.html', form=form)


@admin_bp.route('/announcements/<int:announcement_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_announcement(announcement_id):
    ann = Announcement.query.get_or_404(announcement_id)
    db.session.delete(ann)
    db.session.commit()
    log_action('delete', 'announcement', announcement_id, f'Deleted announcement: {ann.title}')
    flash('Announcement deleted.', 'success')
    return redirect(url_for('admin.announcements'))


# =============================================================================
# ANALYTICS
# =============================================================================

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    # Top level stats
    total_revenue = db.session.query(db.func.coalesce(db.func.sum(Order.total_robux), 0)).filter(
        Order.status != Order.STATUS_CANCELLED
    ).scalar()

    # Product stats
    product_stats = {
        'total': Product.query.count(),
        'active': Product.query.filter_by(is_active=True).count(),
        'featured': Product.query.filter_by(is_featured=True).count(),
        'out_of_stock': Product.query.filter_by(stock_quantity=0).count(),
    }

    # User stats
    user_stats = {
        'total': User.query.count(),
        'active_today': User.query.filter(User.last_login >= datetime.utcnow() - timedelta(days=1)).count(),
        'new_this_week': User.query.filter(User.created_at >= datetime.utcnow() - timedelta(days=7)).count(),
        'sellers': User.query.filter_by(role='seller').count(),
    }

    # Monthly revenue
    monthly_revenue = []
    for i in range(5, -1, -1):
        month_start = (datetime.utcnow() - timedelta(days=i*30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = month_start + timedelta(days=32)
        rev = db.session.query(db.func.coalesce(db.func.sum(Order.total_robux), 0)).filter(
            Order.created_at >= month_start, Order.created_at < month_end,
            Order.status != Order.STATUS_CANCELLED
        ).scalar()
        monthly_revenue.append({'month': month_start.strftime('%b'), 'revenue': int(rev)})

    return render_template('admin/analytics.html',
        total_revenue=total_revenue,
        product_stats=product_stats,
        user_stats=user_stats,
        monthly_revenue=monthly_revenue)


# =============================================================================
# SITE SETTINGS
# =============================================================================

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    site_name = SiteConfig.query.filter_by(key='site_name').first()
    maintenance = SiteConfig.query.filter_by(key='maintenance_mode').first()
    reg_enabled = SiteConfig.query.filter_by(key='registration_enabled').first()

    form = SiteSettingsForm(
        site_name=site_name.value if site_name else 'DripBux',
        maintenance_mode=maintenance.value == 'true' if maintenance else False,
        registration_enabled=reg_enabled.value != 'false' if reg_enabled else True,
    )

    if form.validate_on_submit():
        if site_name:
            site_name.value = form.site_name.data
        if maintenance:
            maintenance.value = 'true' if form.maintenance_mode.data else 'false'
        if reg_enabled:
            reg_enabled.value = 'false' if not form.registration_enabled.data else 'true'
        db.session.commit()
        flash('Settings saved!', 'success')
        return redirect(url_for('admin.settings'))

    return render_template('admin/settings.html', form=form)


# Need current_app for file uploads
from flask import current_app
