"""
DripBux API Routes
==================
AJAX endpoints for dynamic functionality.
"""

from flask import Blueprint, jsonify, request
from models import Product, Category
from extensions import db

api_bp = Blueprint('api', __name__)


@api_bp.route('/search')
def search_products():
    """Live search API"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 8, type=int)

    if not query or len(query) < 2:
        return jsonify({'products': []})

    products = Product.query.filter(
        db.and_(
            Product.is_active == True,
            db.or_(
                Product.name.ilike(f'%{query}%'),
                Product.description.ilike(f'%{query}%'),
                Product.tags.ilike(f'%{query}%')
            )
        )
    ).limit(limit).all()

    result = []
    for product in products:
        result.append({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': product.get_display_price(),
            'original_price': product.original_price,
            'image': product.image_url,
            'category': product.category.name if product.category else None,
            'discount': product.get_discount_percentage(),
            'rarity': product.rarity
        })

    return jsonify({'products': result, 'query': query})


@api_bp.route('/products/<int:product_id>/sizes')
def get_product_sizes(product_id):
    product = Product.query.get_or_404(product_id)
    sizes = []
    for size in product.sizes:
        sizes.append({
            'id': size.id,
            'size': size.size,
            'stock': size.stock,
            'price': size.get_total_price(),
            'available': size.stock > 0
        })
    return jsonify({'sizes': sizes})


@api_bp.route('/cart/summary')
def cart_summary():
    from flask_login import current_user
    from models import Cart

    if not current_user.is_authenticated:
        return jsonify({'count': 0, 'total': 0})

    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        return jsonify({'count': 0, 'total': 0})

    return jsonify({
        'count': cart.get_total_items(),
        'total': cart.get_subtotal()
    })


@api_bp.route('/notifications/unread-count')
def unread_notifications_count():
    from flask_login import current_user
    from models import Notification

    if not current_user.is_authenticated:
        return jsonify({'count': 0})

    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


@api_bp.route('/trending')
def trending_products():
    limit = request.args.get('limit', 8, type=int)
    products = Product.query.filter_by(is_active=True).order_by(Product.views_count.desc()).limit(limit).all()
    result = []
    for p in products:
        result.append({
            'id': p.id, 'name': p.name, 'slug': p.slug,
            'price': p.get_display_price(), 'original_price': p.original_price,
            'image': p.image_url, 'discount': p.get_discount_percentage(),
            'rarity': p.rarity, 'sales_count': p.sales_count
        })
    return jsonify({'products': result})
