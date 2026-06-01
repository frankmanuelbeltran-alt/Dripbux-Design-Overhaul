"""
DripBux Seller Routes
=====================
Seller dashboard, product management, orders, analytics.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Product, ProductSize, Order, OrderItem, Seller, SellerReview, Voucher, Category, Notification, Message, Follower, Announcement, ActivityLog
from forms import ProductForm, ProductSizeForm, SellerApplicationForm, SellerSettingsForm, VoucherForm
import os
import uuid
from datetime import datetime

seller_bp = Blueprint('seller', __name__)


def seller_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please sign in.', 'error')
            return redirect(url_for('auth.login'))
        if not current_user.is_seller or not current_user.seller_profile:
            flash('Seller access required.', 'error')
            return redirect(url_for('auth.profile'))
        if current_user.seller_profile.verification_status != 'verified':
            flash('Your seller account is pending verification.', 'warning')
            return redirect(url_for('auth.profile'))
        return f(*args, **kwargs)
    return decorated


# =============================================================================
# SELLER APPLICATION
# =============================================================================

@seller_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    if current_user.seller_profile:
        if current_user.seller_profile.verification_status == 'verified':
            flash('You are already a seller!', 'info')
            return redirect(url_for('seller.dashboard'))
        if current_user.seller_profile.verification_status == 'pending':
            flash('Your seller application is pending review.', 'info')
            return redirect(url_for('auth.profile'))
        if current_user.seller_profile.verification_status == 'rejected':
            flash('Your seller application was rejected. Please contact support to reapply.', 'warning')
            return redirect(url_for('auth.profile'))

    form = SellerApplicationForm()
    if form.validate_on_submit():
        slug = form.store_name.data.lower().replace(' ', '-')[:100]
        base = slug
        counter = 1
        while Seller.query.filter_by(store_slug=slug).first():
            slug = f'{base}-{counter}'
            counter += 1

        logo_url = None
        banner_url = None

        if form.store_logo.data:
            f = form.store_logo.data
            fn = secure_filename(f.filename)
            unique = f"{uuid.uuid4().hex}_{fn}"
            f.save(os.path.join('static/images/sellers', unique))
            logo_url = unique

        if form.store_banner.data:
            f = form.store_banner.data
            fn = secure_filename(f.filename)
            unique = f"{uuid.uuid4().hex}_{fn}"
            f.save(os.path.join('static/images/sellers', unique))
            banner_url = unique

        seller = Seller(
            user_id=current_user.id,
            store_name=form.store_name.data,
            store_slug=slug,
            store_description=form.store_description.data,
            store_logo=logo_url,
            store_banner=banner_url,
            verification_status='pending'
        )
        db.session.add(seller)
        db.session.commit()
        flash('Application submitted! We will review it soon.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('seller/apply.html', form=form)


# =============================================================================
# DASHBOARD
# =============================================================================

@seller_bp.route('/dashboard')
@login_required
@seller_required
def dashboard():
    seller = current_user.seller_profile

    # Stats
    total_products = Product.query.filter_by(seller_id=seller.id).count()
    active_products = Product.query.filter_by(seller_id=seller.id, is_active=True).count()
    coupon_count = Voucher.query.filter_by(seller_id=seller.id).count()
    category_count = Category.query.filter_by(is_active=True).count()
    announcement_count = Announcement.query.filter_by(is_active=True).count()

    # Orders containing seller's products
    order_items = OrderItem.query.join(Product).filter(Product.seller_id == seller.id).all()
    total_orders = len(set(oi.order_id for oi in order_items))

    # Recent orders grouped by order
    recent_orders = []
    seen_order_ids = set()
    for oi in OrderItem.query.join(Product).filter(
        Product.seller_id == seller.id
    ).join(Order).order_by(Order.created_at.desc()).all():
        if oi.order_id not in seen_order_ids:
            seen_order_ids.add(oi.order_id)
            recent_orders.append(oi.order)
            if len(recent_orders) >= 10:
                break

    # Recent activity log entries for this seller
    recent_logs = ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.created_at.desc()).limit(10).all()

    # Low stock products
    low_stock = Product.query.filter_by(seller_id=seller.id).filter(
        db.or_(Product.stock_quantity <= 5, Product.stock_quantity == 0)
    ).all()

    return render_template('seller/dashboard.html',
        seller=seller, total_products=total_products,
        active_products=active_products, coupon_count=coupon_count,
        category_count=category_count, announcement_count=announcement_count,
        total_orders=total_orders, recent_orders=recent_orders,
        recent_order_items=order_items, low_stock=low_stock,
        recent_logs=recent_logs)


@seller_bp.route('/announcements')
@login_required
@seller_required
def announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('seller/announcements.html', announcements=announcements)


# =============================================================================
# PRODUCTS
# =============================================================================

@seller_bp.route('/products')
@login_required
@seller_required
def products():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    search = request.args.get('q', '')

    query = Product.query.filter_by(seller_id=current_user.seller_profile.id)
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    elif status == 'low_stock':
        query = query.filter(Product.stock_quantity <= 5)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    products = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('seller/products.html', products=products, status=status, search=search)


@seller_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@seller_required
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
            f.save(os.path.join('static/images/products', unique))
            image_url = unique

        product = Product(
            name=form.name.data, slug=slug, description=form.description.data,
            short_description=form.short_description.data,
            category_id=form.category_id.data,
            seller_id=current_user.seller_profile.id,
            price_robux=form.price_robux.data, original_price=form.original_price.data,
            stock_quantity=form.stock_quantity.data, rarity=form.rarity.data,
            product_type=form.product_type.data, tags=form.tags.data,
            image_url=image_url, is_active=form.is_active.data,
            is_featured=False, is_new=True
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added!', 'success')
        return redirect(url_for('seller.edit_product', product_id=product.id))

    return render_template('seller/add_product.html', form=form)


@seller_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@seller_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.seller_profile.id and not current_user.is_admin:
        abort(403)

    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]
    size_form = ProductSizeForm()

    if form.validate_on_submit():
        if form.image.data:
            f = form.image.data
            fn = secure_filename(f.filename)
            unique = f"{uuid.uuid4().hex}_{fn}"
            f.save(os.path.join('static/images/products', unique))
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
        return redirect(url_for('seller.edit_product', product_id=product.id))

    return render_template('seller/edit_product.html', form=form, product=product, size_form=size_form)


@seller_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@seller_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.seller_profile.id and not current_user.is_admin:
        abort(403)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'success')
    return redirect(url_for('seller.products'))


# =============================================================================
# SELLER ORDERS
# =============================================================================

@seller_bp.route('/orders')
@login_required
@seller_required
def orders():
    status = request.args.get('status')
    seller_id = current_user.seller_profile.id

    query = OrderItem.query.join(Product).filter(Product.seller_id == seller_id).join(Order)
    if status:
        query = query.filter(Order.status == status)

    order_items = query.order_by(OrderItem.id.desc()).all()
    return render_template('seller/orders.html', order_items=order_items, status=status)


# =============================================================================
# ANALYTICS
# =============================================================================

@seller_bp.route('/analytics')
@login_required
@seller_required
def analytics():
    seller = current_user.seller_profile

    # Sales by product
    top_products = Product.query.filter_by(seller_id=seller.id).order_by(Product.sales_count.desc()).limit(10).all()

    # Monthly sales
    from sqlalchemy import func
    monthly_sales = db.session.query(
        func.strftime('%Y-%m', Order.created_at).label('month'),
        func.sum(OrderItem.price_robux * OrderItem.quantity).label('revenue'),
        func.sum(OrderItem.quantity).label('units')
    ).join(OrderItem).join(Product).filter(
        Product.seller_id == seller.id,
        Order.status != Order.STATUS_CANCELLED
    ).group_by('month').order_by('month').limit(12).all()

    return render_template('seller/analytics.html',
        seller=seller, top_products=top_products, monthly_sales=monthly_sales)


# =============================================================================
# SETTINGS
# =============================================================================

@seller_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@seller_required
def settings():
    seller = current_user.seller_profile
    form = SellerSettingsForm(obj=seller)

    if form.validate_on_submit():
        seller.store_name = form.store_name.data
        seller.store_description = form.store_description.data
        seller.is_active = form.is_active.data

        if form.store_logo.data:
            f = form.store_logo.data
            fn = secure_filename(f.filename)
            unique = f"{uuid.uuid4().hex}_{fn}"
            f.save(os.path.join('static/images/sellers', unique))
            seller.store_logo = unique

        if form.store_banner.data:
            f = form.store_banner.data
            fn = secure_filename(f.filename)
            unique = f"{uuid.uuid4().hex}_{fn}"
            f.save(os.path.join('static/images/sellers', unique))
            seller.store_banner = unique

        db.session.commit()
        flash('Store settings saved!', 'success')
        return redirect(url_for('seller.settings'))

    return render_template('seller/settings.html', form=form, seller=seller)


# =============================================================================
# VOUCHERS
# =============================================================================

@seller_bp.route('/vouchers')
@login_required
@seller_required
def vouchers():
    seller = current_user.seller_profile
    vouchers = Voucher.query.filter_by(seller_id=seller.id).order_by(Voucher.created_at.desc()).all()
    return render_template('seller/vouchers.html', vouchers=vouchers)


@seller_bp.route('/vouchers/create', methods=['GET', 'POST'])
@login_required
@seller_required
def create_voucher():
    form = VoucherForm()
    if form.validate_on_submit():
        voucher = Voucher(
            seller_id=current_user.seller_profile.id,
            code=form.code.data.upper(),
            description=form.description.data,
            discount_type=form.discount_type.data,
            discount_value=form.discount_value.data,
            min_order_amount=form.min_order_amount.data or 0,
            usage_limit=form.usage_limit.data,
            expires_at=form.expires_at.data
        )
        db.session.add(voucher)
        db.session.commit()
        flash('Voucher created!', 'success')
        return redirect(url_for('seller.vouchers'))
    return render_template('seller/create_voucher.html', form=form)


from flask import current_app
try:
    from sqlalchemy import func
except:
    pass
