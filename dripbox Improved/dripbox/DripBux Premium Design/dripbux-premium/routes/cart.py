"""
DripBux Premium - Cart Routes
=============================
Shopping cart management.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Cart, CartItem, Product, ProductSize
from extensions import db

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/')
def view_cart():
    """View shopping cart"""
    if not current_user.is_authenticated:
        # For guest users, we could use session-based cart
        # For now, redirect to login
        flash('Please sign in to view your cart.', 'info')
        return redirect(url_for('auth.login', next=request.path))
    
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    # Check for invalid items (out of stock)
    invalid_items = []
    for item in cart.items:
        if not item.is_valid():
            invalid_items.append(item)
    
    return render_template('cart/index.html', 
        cart=cart, 
        invalid_items=invalid_items
    )


@cart_bp.route('/add', methods=['POST'])
def add_to_cart():
    """Add item to cart"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please sign in to add items to cart'})
    
    product_id = request.form.get('product_id', type=int)
    size_id = request.form.get('size_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)
    
    if not product_id or not size_id:
        return jsonify({'success': False, 'message': 'Product and size are required'})
    
    # Validate product and size
    product = Product.query.get(product_id)
    size = ProductSize.query.get(size_id)
    
    if not product or not product.is_active:
        return jsonify({'success': False, 'message': 'Product not found'})
    
    if not size or size.product_id != product.id:
        return jsonify({'success': False, 'message': 'Invalid size selected'})
    
    if size.stock < quantity:
        return jsonify({'success': False, 'message': f'Only {size.stock} items available'})
    
    # Get or create cart
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    # Check if item already in cart
    existing_item = CartItem.query.filter_by(
        cart_id=cart.id,
        product_id=product_id,
        size_id=size_id
    ).first()
    
    if existing_item:
        # Update quantity
        new_quantity = existing_item.quantity + quantity
        if new_quantity > size.stock:
            return jsonify({'success': False, 'message': f'Cannot add more. Only {size.stock} available.'})
        existing_item.quantity = new_quantity
    else:
        # Add new item
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            size_id=size_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Added {product.name} to cart',
        'cart_count': cart.get_total_items(),
        'cart_total': cart.get_subtotal()
    })


@cart_bp.route('/update/<int:item_id>', methods=['POST'])
def update_cart_item(item_id):
    """Update cart item quantity"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please sign in'})
    
    quantity = request.form.get('quantity', type=int)
    
    if quantity is None or quantity < 0:
        return jsonify({'success': False, 'message': 'Invalid quantity'})
    
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        return jsonify({'success': False, 'message': 'Cart not found'})
    
    item = CartItem.query.get(item_id)
    if not item or item.cart_id != cart.id:
        return jsonify({'success': False, 'message': 'Item not found in cart'})
    
    if quantity == 0:
        db.session.delete(item)
    else:
        # Check stock
        if quantity > item.size.stock:
            return jsonify({'success': False, 'message': f'Only {item.size.stock} available'})
        item.quantity = quantity
    
    db.session.commit()
    
    # Recalculate cart totals
    cart = Cart.query.get(cart.id)
    
    return jsonify({
        'success': True,
        'message': 'Cart updated',
        'cart_count': cart.get_total_items(),
        'cart_subtotal': cart.get_subtotal(),
        'cart_total': cart.get_total(),
        'item_subtotal': item.get_subtotal() if quantity > 0 else 0
    })


@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    """Remove item from cart"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please sign in'})
    
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        return jsonify({'success': False, 'message': 'Cart not found'})
    
    item = CartItem.query.get(item_id)
    if not item or item.cart_id != cart.id:
        return jsonify({'success': False, 'message': 'Item not found in cart'})
    
    db.session.delete(item)
    db.session.commit()
    
    # Recalculate cart totals
    cart = Cart.query.get(cart.id)
    
    return jsonify({
        'success': True,
        'message': 'Item removed from cart',
        'cart_count': cart.get_total_items(),
        'cart_subtotal': cart.get_subtotal(),
        'cart_total': cart.get_total()
    })


@cart_bp.route('/clear', methods=['POST'])
@login_required
def clear_cart():
    """Clear entire cart"""
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if cart:
        cart.clear_cart()
        flash('Cart cleared successfully.', 'success')
    
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/count')
def get_cart_count():
    """Get cart item count (for AJAX updates)"""
    if not current_user.is_authenticated:
        return jsonify({'count': 0})
    
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    count = cart.get_total_items() if cart else 0
    
    return jsonify({'count': count})


@cart_bp.route('/mini')
def mini_cart():
    """Get mini cart data for dropdown"""
    if not current_user.is_authenticated:
        return jsonify({'items': [], 'total': 0, 'count': 0})
    
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        return jsonify({'items': [], 'total': 0, 'count': 0})
    
    items = []
    for item in cart.items:
        items.append({
            'id': item.id,
            'name': item.product.name,
            'image': item.product.image_url,
            'size': item.size.size,
            'quantity': item.quantity,
            'price': item.product.price_robux + item.size.price_modifier,
            'subtotal': item.get_subtotal()
        })
    
    return jsonify({
        'items': items,
        'total': cart.get_subtotal(),
        'count': cart.get_total_items()
    })
