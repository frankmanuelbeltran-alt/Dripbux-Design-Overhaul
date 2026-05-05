"""
DripBux Premium - Admin Routes
==============================
Admin dashboard, product management, user management, and order management.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Product, Category, ProductSize, Order, Review, Transaction
from forms import ProductForm, CategoryForm, AdminUserEditForm, AddRobuxForm, OrderStatusForm
import os
import uuid

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Statistics
    stats = {
        'total_users': User.query.count(),
        'total_products': Product.query.count(),
        'total_orders': Order.query.count(),
        'pending_orders': Order.query.filter_by(status=Order.STATUS_PENDING).count(),
        'total_revenue': db.session.query(db.func.sum(Order.total_robux)).filter(
            Order.status != Order.STATUS_CANCELLED
        ).scalar() or 0,
        'low_stock_products': Product.query.join(ProductSize).filter(
            ProductSize.stock < 5
        ).distinct().count()
    }
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Top selling products
    top_products = Product.query.order_by(Product.sales_count.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
        stats=stats,
        recent_orders=recent_orders,
        recent_users=recent_users,
        top_products=top_products
    )


# =============================================================================
# PRODUCT MANAGEMENT
# =============================================================================

@admin_bp.route('/products')
@login_required
@admin_required
def products():
    """Product list"""
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
    
    query = query.order_by(Product.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    products = pagination.items
    
    categories = Category.query.filter_by(is_active=True).all()
    
    return render_template('admin/products.html',
        products=products,
        pagination=pagination,
        categories=categories,
        search=search,
        category_id=category_id,
        status=status
    )


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    """Add new product"""
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        # Generate slug
        base_slug = form.name.data.lower().replace(' ', '-')
        slug = base_slug
        counter = 1
        while Product.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{counter}'
            counter += 1
        
        # Handle image upload
        image_url = None
        if form.image.data:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            image_path = os.path.join(current_app.root_path, 'static/images/products', unique_filename)
            image_file.save(image_path)
            image_url = unique_filename
        
        product = Product(
            name=form.name.data,
            slug=slug,
            description=form.description.data,
            short_description=form.short_description.data,
            category_id=form.category_id.data,
            price_robux=form.price_robux.data,
            original_price=form.original_price.data,
            image_url=image_url,
            is_active=form.is_active.data,
            is_featured=form.is_featured.data,
            is_new=form.is_new.data
        )
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin.edit_product', id=product.id))
    
    return render_template('admin/add_product.html', form=form)


@admin_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    """Edit product"""
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        # Handle image upload
        if form.image.data:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            image_path = os.path.join(current_app.root_path, 'static/images/products', unique_filename)
            image_file.save(image_path)
            product.image_url = unique_filename
        
        product.name = form.name.data
        product.description = form.description.data
        product.short_description = form.short_description.data
        product.category_id = form.category_id.data
        product.price_robux = form.price_robux.data
        product.original_price = form.original_price.data
        product.is_active = form.is_active.data
        product.is_featured = form.is_featured.data
        product.is_new = form.is_new.data
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.edit_product', id=product.id))
    
    return render_template('admin/edit_product.html', form=form, product=product)


@admin_bp.route('/products/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    """Delete product"""
    product = Product.query.get_or_404(id)
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/<int:product_id>/sizes/add', methods=['POST'])
@login_required
@admin_required
def add_product_size(product_id):
    """Add size variant to product"""
    product = Product.query.get_or_404(product_id)
    
    size = request.form.get('size')
    stock = request.form.get('stock', type=int, default=0)
    price_modifier = request.form.get('price_modifier', type=int, default=0)
    
    if not size:
        flash('Size is required.', 'error')
        return redirect(url_for('admin.edit_product', id=product_id))
    
    # Check if size already exists
    existing = ProductSize.query.filter_by(product_id=product_id, size=size).first()
    if existing:
        flash('This size already exists for this product.', 'error')
        return redirect(url_for('admin.edit_product', id=product_id))
    
    product_size = ProductSize(
        product_id=product_id,
        size=size,
        stock=stock,
        price_modifier=price_modifier
    )
    db.session.add(product_size)
    db.session.commit()
    
    flash('Size added successfully!', 'success')
    return redirect(url_for('admin.edit_product', id=product_id))


@admin_bp.route('/products/sizes/<int:size_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_product_size(size_id):
    """Edit product size"""
    size = ProductSize.query.get_or_404(size_id)
    
    size.stock = request.form.get('stock', type=int, default=size.stock)
    size.price_modifier = request.form.get('price_modifier', type=int, default=size.price_modifier)
    
    db.session.commit()
    
    flash('Size updated successfully!', 'success')
    return redirect(url_for('admin.edit_product', id=size.product_id))


@admin_bp.route('/products/sizes/<int:size_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product_size(size_id):
    """Delete product size"""
    size = ProductSize.query.get_or_404(size_id)
    product_id = size.product_id
    
    db.session.delete(size)
    db.session.commit()
    
    flash('Size deleted successfully!', 'success')
    return redirect(url_for('admin.edit_product', id=product_id))


# =============================================================================
# CATEGORY MANAGEMENT
# =============================================================================

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    """Category list"""
    categories = Category.query.order_by(Category.display_order).all()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    """Add new category"""
    form = CategoryForm()
    
    if form.validate_on_submit():
        # Check if slug exists
        if Category.query.filter_by(slug=form.slug.data).first():
            flash('Slug already exists.', 'error')
            return render_template('admin/add_category.html', form=form)
        
        # Handle image upload
        image_url = None
        if form.image.data:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            image_path = os.path.join(current_app.root_path, 'static/images/categories', unique_filename)
            image_file.save(image_path)
            image_url = unique_filename
        
        category = Category(
            name=form.name.data,
            slug=form.slug.data,
            description=form.description.data,
            image_url=image_url,
            display_order=form.display_order.data,
            is_active=form.is_active.data
        )
        db.session.add(category)
        db.session.commit()
        
        flash('Category added successfully!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/add_category.html', form=form)


@admin_bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    """Edit category"""
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        # Check if slug is taken by another category
        existing = Category.query.filter_by(slug=form.slug.data).first()
        if existing and existing.id != id:
            flash('Slug already exists.', 'error')
            return render_template('admin/edit_category.html', form=form, category=category)
        
        # Handle image upload
        if form.image.data:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            image_path = os.path.join(current_app.root_path, 'static/images/categories', unique_filename)
            image_file.save(image_path)
            category.image_url = unique_filename
        
        category.name = form.name.data
        category.slug = form.slug.data
        category.description = form.description.data
        category.display_order = form.display_order.data
        category.is_active = form.is_active.data
        
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/edit_category.html', form=form, category=category)


@admin_bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    """Delete category"""
    category = Category.query.get_or_404(id)
    
    # Check if category has products
    if category.products:
        flash('Cannot delete category with products. Please move or delete products first.', 'error')
        return redirect(url_for('admin.categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin.categories'))


# =============================================================================
# USER MANAGEMENT
# =============================================================================

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User list"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    query = query.order_by(User.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    users = pagination.items
    
    return render_template('admin/users.html', users=users, pagination=pagination, search=search)


@admin_bp.route('/users/<int:id>')
@login_required
@admin_required
def view_user(id):
    """View user details"""
    user = User.query.get_or_404(id)
    add_robux_form = AddRobuxForm()
    return render_template('admin/view_user.html', user=user, add_robux_form=add_robux_form)


@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    """Edit user"""
    user = User.query.get_or_404(id)
    form = AdminUserEditForm(obj=user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.robux_balance = form.robux_balance.data
        user.is_admin = form.is_admin.data
        user.is_active = form.is_active.data
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.view_user', id=user.id))
    
    return render_template('admin/edit_user.html', form=form, user=user)


@admin_bp.route('/users/<int:id>/add-robux', methods=['POST'])
@login_required
@admin_required
def admin_add_robux(id):
    """Add Robux to user"""
    user = User.query.get_or_404(id)
    form = AddRobuxForm()
    
    if form.validate_on_submit():
        amount = form.amount.data
        reason = form.reason.data or 'Added by admin'
        
        user.add_robux(amount, description=reason)
        db.session.commit()
        
        flash(f'Added {amount:,} Robux to {user.username}\'s account.', 'success')
    
    return redirect(url_for('admin.view_user', id=user.id))


@admin_bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    """Delete user"""
    user = User.query.get_or_404(id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.users'))


# =============================================================================
# ORDER MANAGEMENT
# =============================================================================

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    """Order list"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    search = request.args.get('q', '')
    
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
    
    if search:
        query = query.filter(
            db.or_(
                Order.order_number.ilike(f'%{search}%'),
                Order.shipping_name.ilike(f'%{search}%')
            )
        )
    
    query = query.order_by(Order.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    orders = pagination.items
    
    return render_template('admin/orders.html', 
        orders=orders, 
        pagination=pagination,
        current_status=status,
        search=search
    )


@admin_bp.route('/orders/<order_number>')
@login_required
@admin_required
def view_order(order_number):
    """View order details"""
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    form = OrderStatusForm(obj=order)
    form.status.data = order.status
    return render_template('admin/view_order.html', order=order, form=form)


@admin_bp.route('/orders/<order_number>/update-status', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_number):
    """Update order status"""
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    form = OrderStatusForm()
    
    if form.validate_on_submit():
        old_status = order.status
        order.status = form.status.data
        
        if form.status.data == Order.STATUS_SHIPPED:
            order.shipped_at = db.func.now()
            order.tracking_number = form.tracking_number.data
        elif form.status.data == Order.STATUS_DELIVERED:
            order.delivered_at = db.func.now()
        
        db.session.commit()
        
        flash(f'Order status updated from {old_status} to {order.status}.', 'success')
    
    return redirect(url_for('admin.view_order', order_number=order_number))


# =============================================================================
# REVIEWS MANAGEMENT
# =============================================================================

@admin_bp.route('/reviews')
@login_required
@admin_required
def reviews():
    """Reviews list"""
    page = request.args.get('page', 1, type=int)
    
    reviews = Review.query.order_by(Review.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/reviews.html', reviews=reviews)


@admin_bp.route('/reviews/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_review(id):
    """Delete review"""
    review = Review.query.get_or_404(id)
    
    db.session.delete(review)
    db.session.commit()
    
    flash('Review deleted successfully!', 'success')
    return redirect(url_for('admin.reviews'))
