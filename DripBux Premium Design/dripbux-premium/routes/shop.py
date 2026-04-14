"""
DripBux Premium - Shop Routes
=============================
Product browsing, categories, search, and filters.
"""

from flask import Blueprint, render_template, request, jsonify
from models import Product, Category, Review, Wishlist
from extensions import db
from flask_login import current_user

shop_bp = Blueprint('shop', __name__)


@shop_bp.route('/')
def index():
    """Shop main page with all products"""
    page = request.args.get('page', 1, type=int)
    per_page = 24
    
    # Get filter parameters
    category_slug = request.args.get('category')
    sort = request.args.get('sort', 'newest')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    search_query = request.args.get('q')
    
    # Base query
    query = Product.query.filter_by(is_active=True)
    
    # Apply category filter
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first()
        if category:
            query = query.filter_by(category_id=category.id)
    
    # Apply price filter
    if min_price is not None:
        query = query.filter(Product.price_robux >= min_price)
    if max_price is not None:
        query = query.filter(Product.price_robux <= max_price)
    
    # Apply search
    if search_query:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.description.ilike(f'%{search_query}%')
            )
        )
    
    # Apply sorting
    if sort == 'price_low':
        query = query.order_by(Product.price_robux.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price_robux.desc())
    elif sort == 'popular':
        query = query.order_by(Product.sales_count.desc())
    elif sort == 'name':
        query = query.order_by(Product.name.asc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items
    
    # Get all categories for filter sidebar
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
    
    # Get current category if filtering
    current_category = None
    if category_slug:
        current_category = Category.query.filter_by(slug=category_slug).first()
    
    return render_template('shop/index.html',
        products=products,
        pagination=pagination,
        categories=categories,
        current_category=current_category,
        sort=sort,
        min_price=min_price,
        max_price=max_price,
        search_query=search_query
    )


@shop_bp.route('/product/<slug>')
def product_detail(slug):
    """Product detail page"""
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Increment view count
    product.increment_views()
    
    # Get related products from same category
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    
    # Get reviews
    reviews = Review.query.filter_by(product_id=product.id).order_by(Review.created_at.desc()).all()
    
    # Check if user has this in wishlist
    in_wishlist = False
    if current_user.is_authenticated:
        wishlist_item = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product.id
        ).first()
        in_wishlist = wishlist_item is not None
    
    # Check if user can review (has purchased)
    can_review = False
    if current_user.is_authenticated:
        from models import OrderItem, Order
        order_item = OrderItem.query.join(Order).filter(
            Order.user_id == current_user.id,
            OrderItem.product_id == product.id,
            Order.status == Order.STATUS_DELIVERED
        ).first()
        can_review = order_item is not None
    
    return render_template('shop/product_detail.html',
        product=product,
        related_products=related_products,
        reviews=reviews,
        in_wishlist=in_wishlist,
        can_review=can_review
    )


@shop_bp.route('/category/<slug>')
def category(slug):
    """Category page"""
    category = Category.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')
    
    query = Product.query.filter_by(category_id=category.id, is_active=True)
    
    # Apply sorting
    if sort == 'price_low':
        query = query.order_by(Product.price_robux.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price_robux.desc())
    elif sort == 'popular':
        query = query.order_by(Product.sales_count.desc())
    elif sort == 'name':
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=24, error_out=False)
    products = pagination.items
    
    return render_template('shop/category.html',
        category=category,
        products=products,
        pagination=pagination,
        sort=sort
    )


@shop_bp.route('/search')
def search():
    """Search products"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')
    
    if not query:
        return render_template('shop/search.html', 
            products=[], 
            query='', 
            pagination=None
        )
    
    # Search in name and description
    search_query = Product.query.filter(
        db.and_(
            Product.is_active == True,
            db.or_(
                Product.name.ilike(f'%{query}%'),
                Product.description.ilike(f'%{query}%')
            )
        )
    )
    
    # Apply sorting
    if sort == 'price_low':
        search_query = search_query.order_by(Product.price_robux.asc())
    elif sort == 'price_high':
        search_query = search_query.order_by(Product.price_robux.desc())
    elif sort == 'popular':
        search_query = search_query.order_by(Product.sales_count.desc())
    else:
        search_query = search_query.order_by(Product.created_at.desc())
    
    pagination = search_query.paginate(page=page, per_page=24, error_out=False)
    products = pagination.items
    
    return render_template('shop/search.html',
        products=products,
        query=query,
        pagination=pagination,
        sort=sort
    )


@shop_bp.route('/new-arrivals')
def new_arrivals():
    """New arrivals page"""
    page = request.args.get('page', 1, type=int)
    
    query = Product.query.filter_by(is_active=True, is_new=True).order_by(Product.created_at.desc())
    pagination = query.paginate(page=page, per_page=24, error_out=False)
    products = pagination.items
    
    return render_template('shop/new_arrivals.html',
        products=products,
        pagination=pagination
    )


@shop_bp.route('/trending')
def trending():
    """Trending products page"""
    page = request.args.get('page', 1, type=int)
    
    query = Product.query.filter_by(is_active=True).order_by(Product.sales_count.desc())
    pagination = query.paginate(page=page, per_page=24, error_out=False)
    products = pagination.items
    
    return render_template('shop/trending.html',
        products=products,
        pagination=pagination
    )


@shop_bp.route('/sale')
def sale():
    """Sale items page"""
    page = request.args.get('page', 1, type=int)
    
    query = Product.query.filter(
        Product.is_active == True,
        Product.original_price != None,
        Product.original_price > Product.price_robux
    ).order_by((Product.original_price - Product.price_robux).desc())
    
    pagination = query.paginate(page=page, per_page=24, error_out=False)
    products = pagination.items
    
    return render_template('shop/sale.html',
        products=products,
        pagination=pagination
    )


# =============================================================================
# WISHLIST ROUTES
# =============================================================================

@shop_bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
def add_to_wishlist(product_id):
    """Add product to wishlist"""
    from flask_login import login_required
    login_required()
    
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please sign in to add to wishlist'})
    
    product = Product.query.get_or_404(product_id)
    
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': 'Already in wishlist'})
    
    wishlist_item = Wishlist(user_id=current_user.id, product_id=product_id)
    db.session.add(wishlist_item)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Added to wishlist',
        'wishlist_count': current_user.get_wishlist_count()
    })


@shop_bp.route('/wishlist/remove/<int:product_id>', methods=['POST'])
def remove_from_wishlist(product_id):
    """Remove product from wishlist"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please sign in'})
    
    wishlist_item = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'Removed from wishlist',
            'wishlist_count': current_user.get_wishlist_count()
        })
    
    return jsonify({'success': False, 'message': 'Item not found in wishlist'})


# =============================================================================
# REVIEW ROUTES
# =============================================================================

@shop_bp.route('/product/<slug>/review', methods=['POST'])
def add_review(slug):
    """Add product review"""
    from flask_login import login_required
    from forms import ReviewForm
    
    login_required()
    
    product = Product.query.filter_by(slug=slug).first_or_404()
    form = ReviewForm()
    
    if form.validate_on_submit():
        # Check if user already reviewed
        existing = Review.query.filter_by(
            user_id=current_user.id,
            product_id=product.id
        ).first()
        
        if existing:
            flash('You have already reviewed this product.', 'error')
            return redirect(url_for('shop.product_detail', slug=slug))
        
        # Check if user has purchased
        from models import OrderItem, Order
        order_item = OrderItem.query.join(Order).filter(
            Order.user_id == current_user.id,
            OrderItem.product_id == product.id,
            Order.status == Order.STATUS_DELIVERED
        ).first()
        
        review = Review(
            user_id=current_user.id,
            product_id=product.id,
            rating=int(form.rating.data),
            title=form.title.data,
            comment=form.comment.data,
            is_verified_purchase=order_item is not None
        )
        db.session.add(review)
        db.session.commit()
        
        flash('Review submitted successfully!', 'success')
    else:
        for error in form.errors.values():
            flash(error[0], 'error')
    
    return redirect(url_for('shop.product_detail', slug=slug))
