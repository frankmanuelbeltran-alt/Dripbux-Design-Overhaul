"""
DripBux Premium - API Routes
============================
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
                Product.description.ilike(f'%{query}%')
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
            'image': product.image_url,
            'category': product.category.name if product.category else None
        })
    
    return jsonify({'products': result})


@api_bp.route('/products/<int:product_id>/sizes')
def get_product_sizes(product_id):
    """Get available sizes for a product"""
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
    """Get cart summary for navbar"""
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
