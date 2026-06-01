"""
DripBux Shop Routes
===================
Product browsing, categories, search, filters, wishlist, reviews.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from models import Product, Category, Review, Wishlist, RecentlyViewed, Seller, Follower, OrderItem, Order, ReviewHelpful
from forms import ReviewForm
from extensions import db
from flask_login import current_user, login_required
import os
import uuid

shop_bp = Blueprint('shop', __name__)


@shop_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 24
    category_slug = request.args.get('category')
    sort = request.args.get('sort', 'newest')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    rarity = request.args.get('rarity')
    product_type = request.args.get('type')
    search_query = request.args.get('q')
    on_sale = request.args.get('sale')

    query = Product.query.filter_by(is_active=True)

    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first()
        if category:
            query = query.filter_by(category_id=category.id)

    if min_price is not None:
        query = query.filter(Product.price_robux >= min_price)
    if max_price is not None:
        query = query.filter(Product.price_robux <= max_price)
    if rarity:
        query = query.filter_by(rarity=rarity)
    if product_type:
        query = query.filter_by(product_type=product_type)
    if on_sale:
        query = query.filter(Product.original_price != None).filter(Product.original_price > Product.price_robux)
    if search_query:
        query = query.filter(db.or_(Product.name.ilike(f'%{search_query}%'), Product.description.ilike(f'%{search_query}%')))

    # Sorting
    sort_options = {
        'price_low': Product.price_robux.asc(),
        'price_high': Product.price_robux.desc(),
        'popular': Product.sales_count.desc(),
        'name': Product.name.asc(),
        'newest': Product.created_at.desc(),
        'trending': Product.views_count.desc(),
    }
    query = query.order_by(sort_options.get(sort, Product.created_at.desc()))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
    current_category = Category.query.filter_by(slug=category_slug).first() if category_slug else None

    return render_template('shop/index.html',
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        current_category=current_category,
        sort=sort,
        min_price=min_price,
        max_price=max_price,
        rarity=rarity,
        search_query=search_query
    )


@shop_bp.route('/product/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    product.increment_views()

    # Related products
    related = product.get_related_products(4)

    # Reviews - show only visible reviews
    reviews = Review.query.filter_by(product_id=product.id, is_hidden=False).order_by(Review.created_at.desc()).all()

    # Check wishlist
    in_wishlist = False
    if current_user.is_authenticated:
        in_wishlist = Wishlist.query.filter_by(user_id=current_user.id, product_id=product.id).first() is not None
        # Track recently viewed
        existing = RecentlyViewed.query.filter_by(user_id=current_user.id, product_id=product.id).first()
        if existing:
            existing.viewed_at = db.func.now()
        else:
            rv = RecentlyViewed(user_id=current_user.id, product_id=product.id)
            db.session.add(rv)
            # Keep only last 50
            old = RecentlyViewed.query.filter_by(user_id=current_user.id).order_by(RecentlyViewed.viewed_at.desc()).offset(50).all()
            for o in old:
                db.session.delete(o)
        db.session.commit()

    # Can review
    can_review = False
    eligible_order_id = None
    review_form = None
    if current_user.is_authenticated:
        review_form = ReviewForm()
        delivered_items = OrderItem.query.join(Order).filter(
            Order.user_id == current_user.id,
            OrderItem.product_id == product.id,
            Order.status == Order.STATUS_DELIVERED
        ).order_by(Order.delivered_at.desc()).all()

        for item in delivered_items:
            existing_review = Review.query.filter_by(
                user_id=current_user.id,
                product_id=product.id,
                order_id=item.order_id
            ).first()
            if not existing_review:
                eligible_order_id = item.order_id
                can_review = True
                break

    # Seller info
    seller = None
    if product.seller_id:
        seller = Seller.query.get(product.seller_id)
    is_following = False
    if current_user.is_authenticated and seller:
        is_following = Follower.query.filter_by(user_id=current_user.id, seller_id=seller.id).first() is not None

    return render_template('shop/product_detail.html',
        product=product,
        related_products=related,
        reviews=reviews,
        in_wishlist=in_wishlist,
        can_review=can_review,
        eligible_order_id=eligible_order_id,
        form=review_form,
        seller=seller,
        is_following=is_following
    )


@shop_bp.route('/category/<slug>')
def category(slug):
    category = Category.query.filter_by(slug=slug, is_active=True).first_or_404()
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')

    query = Product.query.filter_by(category_id=category.id, is_active=True)

    sort_map = {
        'price_low': Product.price_robux.asc(),
        'price_high': Product.price_robux.desc(),
        'popular': Product.sales_count.desc(),
        'newest': Product.created_at.desc(),
    }
    query = query.order_by(sort_map.get(sort, Product.created_at.desc()))

    pagination = query.paginate(page=page, per_page=24, error_out=False)
    return render_template('shop/category.html', category=category, products=pagination.items, pagination=pagination, sort=sort)


@shop_bp.route('/search')
def search():
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')

    if not query:
        return render_template('shop/search.html', products=[], query='', pagination=None)

    search_query = Product.query.filter(
        db.and_(Product.is_active == True,
                db.or_(Product.name.ilike(f'%{query}%'),
                       Product.description.ilike(f'%{query}%'),
                       Product.tags.ilike(f'%{query}%')))
    )

    sort_map = {
        'price_low': Product.price_robux.asc(),
        'price_high': Product.price_robux.desc(),
        'popular': Product.sales_count.desc(),
        'newest': Product.created_at.desc(),
    }
    search_query = search_query.order_by(sort_map.get(sort, Product.created_at.desc()))

    pagination = search_query.paginate(page=page, per_page=24, error_out=False)
    return render_template('shop/search.html', products=pagination.items, query=query, pagination=pagination, sort=sort)


@shop_bp.route('/flash-sales')
def flash_sales():
    page = request.args.get('page', 1, type=int)
    query = Product.query.filter_by(is_active=True, is_flash_sale=True).order_by(Product.created_at.desc())
    pagination = query.paginate(page=page, per_page=24, error_out=False)
    return render_template('shop/flash_sales.html', products=pagination.items, pagination=pagination)


@shop_bp.route('/new-arrivals')
def new_arrivals():
    page = request.args.get('page', 1, type=int)
    query = Product.query.filter_by(is_active=True, is_new=True).order_by(Product.created_at.desc())
    pagination = query.paginate(page=page, per_page=24, error_out=False)
    return render_template('shop/new_arrivals.html', products=pagination.items, pagination=pagination)


@shop_bp.route('/trending')
def trending():
    page = request.args.get('page', 1, type=int)
    query = Product.query.filter_by(is_active=True).order_by(Product.views_count.desc())
    pagination = query.paginate(page=page, per_page=24, error_out=False)
    return render_template('shop/trending.html', products=pagination.items, pagination=pagination)


@shop_bp.route('/best-sellers')
def best_sellers():
    page = request.args.get('page', 1, type=int)
    query = Product.query.filter_by(is_active=True).order_by(Product.sales_count.desc())
    pagination = query.paginate(page=page, per_page=24, error_out=False)
    return render_template('shop/best_sellers.html', products=pagination.items, pagination=pagination)


@shop_bp.route('/store/<slug>')
def store(slug):
    seller = Seller.query.filter_by(store_slug=slug, is_active=True).first_or_404()
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')

    query = Product.query.filter_by(seller_id=seller.id, is_active=True)
    sort_map = {'price_low': Product.price_robux.asc(), 'price_high': Product.price_robux.desc(),
                'popular': Product.sales_count.desc(), 'newest': Product.created_at.desc()}
    query = query.order_by(sort_map.get(sort, Product.created_at.desc()))

    pagination = query.paginate(page=page, per_page=24, error_out=False)
    is_following = False
    if current_user.is_authenticated:
        is_following = Follower.query.filter_by(user_id=current_user.id, seller_id=seller.id).first() is not None

    return render_template('shop/store.html', seller=seller, products=pagination.items, pagination=pagination, is_following=is_following, sort=sort)


# =============================================================================
# WISHLIST ROUTES
# =============================================================================

@shop_bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    product = Product.query.get_or_404(product_id)
    existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        return jsonify({'success': False, 'message': 'Already in wishlist'})

    item = Wishlist(user_id=current_user.id, product_id=product_id)
    db.session.add(item)
    product.favorites_count = product.favorites_count + 1 if product.favorites_count else 1
    db.session.commit()

    return jsonify({'success': True, 'message': 'Added to wishlist', 'wishlist_count': current_user.get_wishlist_count()})


@shop_bp.route('/wishlist/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Removed from wishlist', 'wishlist_count': current_user.get_wishlist_count()})
    return jsonify({'success': False, 'message': 'Item not found'})


# =============================================================================
# REVIEW ROUTES
# =============================================================================

@shop_bp.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    product = Product.query.get_or_404(product_id)
    form = ReviewForm()
    order_id = request.form.get('order_id', type=int)

    order_item = None
    if order_id:
        order_item = OrderItem.query.filter_by(order_id=order_id, product_id=product_id).join(Order).filter(
            Order.user_id == current_user.id,
            Order.status == Order.STATUS_DELIVERED
        ).first()

    if not order_item:
        flash('Review eligibility could not be confirmed. Please make sure this item is delivered.', 'error')
        return redirect(url_for('shop.product_detail', slug=product.slug))

    if form.validate_on_submit():
        existing = Review.query.filter_by(
            user_id=current_user.id,
            product_id=product_id,
            order_id=order_id
        ).first()
        if existing:
            flash('You have already reviewed this order item.', 'error')
            return redirect(url_for('shop.product_detail', slug=product.slug))

        images = []
        review_images = request.files.getlist('images')
        for image_file in review_images:
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                unique = f"{uuid.uuid4().hex}_{filename}"
                save_path = os.path.join(current_app.root_path, 'static/images/reviews')
                os.makedirs(save_path, exist_ok=True)
                image_file.save(os.path.join(save_path, unique))
                images.append(url_for('static', filename=f'images/reviews/{unique}'))

        review = Review(
            product_id=product_id,
            user_id=current_user.id,
            order_id=order_id,
            rating=int(form.rating.data),
            title=form.title.data,
            comment=form.comment.data,
            is_verified_purchase=True,
            images=images
        )
        db.session.add(review)
        db.session.commit()
        flash('Review submitted!', 'success')
    else:
        flash('Please complete the review form correctly.', 'error')

    return redirect(url_for('shop.product_detail', slug=product.slug))


@shop_bp.route('/review/<int:review_id>/helpful', methods=['POST'])
@login_required
def mark_review_helpful(review_id):
    review = Review.query.get_or_404(review_id)
    existing = ReviewHelpful.query.filter_by(review_id=review.id, user_id=current_user.id).first()
    if existing:
        return jsonify({'success': False, 'message': 'You already marked this review as helpful.'})

    vote = ReviewHelpful(review_id=review.id, user_id=current_user.id)
    review.helpful_count = (review.helpful_count or 0) + 1
    db.session.add(vote)
    db.session.commit()
    return jsonify({'success': True, 'helpful_count': review.helpful_count, 'message': 'Marked helpful!'})


# =============================================================================
# FOLLOW SELLER
# =============================================================================

@shop_bp.route('/seller/<int:seller_id>/follow', methods=['POST'])
@login_required
def follow_seller(seller_id):
    seller = Seller.query.get_or_404(seller_id)
    existing = Follower.query.filter_by(user_id=current_user.id, seller_id=seller_id).first()
    if existing:
        db.session.delete(existing)
        seller.follower_count = max(0, seller.follower_count - 1)
        db.session.commit()
        return jsonify({'success': True, 'following': False, 'follower_count': seller.follower_count})

    follow = Follower(user_id=current_user.id, seller_id=seller_id, seller_user_id=seller.user_id)
    db.session.add(follow)
    seller.follower_count = (seller.follower_count or 0) + 1
    db.session.commit()
    return jsonify({'success': True, 'following': True, 'follower_count': seller.follower_count})
