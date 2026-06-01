"""
DripBux Cart Routes
===================
Shopping cart management.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Cart, CartItem, Product, ProductSize
from extensions import db

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/')
@login_required
def view_cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    invalid_items = [item for item in cart.items if not item.is_valid()]
    return render_template('cart/index.html', cart=cart, invalid_items=invalid_items)


@cart_bp.route('/add', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    size_id = request.form.get('size_id', type=int) or None
    quantity = request.form.get('quantity', 1, type=int)

    if not product_id:
        return jsonify({'success': False, 'message': 'Product required'})

    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return jsonify({'success': False, 'message': 'Product not found'})

    if size_id:
        size = ProductSize.query.get(size_id)
        if not size or size.product_id != product_id:
            return jsonify({'success': False, 'message': 'Invalid variant'})
        if size.stock < quantity:
            return jsonify({'success': False, 'message': f'Only {size.stock} available'})
    else:
        if product.stock_quantity < quantity:
            return jsonify({'success': False, 'message': f'Only {product.stock_quantity} available'})

    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    existing = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id, size_id=size_id).first()
    if existing:
        new_qty = existing.quantity + quantity
        if size_id and size:
            if new_qty > size.stock:
                return jsonify({'success': False, 'message': f'Cannot add more. Only {size.stock} available.'})
        else:
            if new_qty > product.stock_quantity:
                return jsonify({'success': False, 'message': f'Cannot add more. Only {product.stock_quantity} available.'})
        existing.quantity = new_qty
    else:
        item = CartItem(cart_id=cart.id, product_id=product_id, size_id=size_id, quantity=quantity)
        db.session.add(item)

    db.session.commit()
    cart = Cart.query.get(cart.id)
    response = {
        'success': True,
        'message': f'Added {product.name} to cart',
        'cart_count': cart.get_total_items(),
        'cart_total': cart.get_subtotal()
    }
    if request.args.get('checkout') == '1' or request.form.get('checkout') == '1':
        response['redirect'] = url_for('checkout.shipping')
    return jsonify(response)


@cart_bp.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart_item(item_id):
    quantity = request.form.get('quantity', type=int)
    if quantity is None or quantity < 0:
        return jsonify({'success': False, 'message': 'Invalid quantity'})

    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        return jsonify({'success': False, 'message': 'Cart not found'})

    item = CartItem.query.get(item_id)
    if not item or item.cart_id != cart.id:
        return jsonify({'success': False, 'message': 'Item not found'})

    if quantity == 0:
        db.session.delete(item)
    else:
        if item.size_id and item.size:
            if quantity > item.size.stock:
                return jsonify({'success': False, 'message': f'Only {item.size.stock} available'})
        elif item.product:
            if quantity > item.product.stock_quantity:
                return jsonify({'success': False, 'message': f'Only {item.product.stock_quantity} available'})
        item.quantity = quantity

    db.session.commit()
    cart = Cart.query.get(cart.id)
    return jsonify({'success': True, 'message': 'Cart updated', 'cart_count': cart.get_total_items(), 'cart_subtotal': cart.get_subtotal(), 'cart_total': cart.get_total()})


@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        return jsonify({'success': False, 'message': 'Cart not found'})

    item = CartItem.query.get(item_id)
    if not item or item.cart_id != cart.id:
        return jsonify({'success': False, 'message': 'Item not found'})

    db.session.delete(item)
    db.session.commit()
    cart = Cart.query.get(cart.id)
    return jsonify({'success': True, 'message': 'Item removed', 'cart_count': cart.get_total_items(), 'cart_subtotal': cart.get_subtotal(), 'cart_total': cart.get_total()})


@cart_bp.route('/clear', methods=['POST'])
@login_required
def clear_cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if cart:
        cart.clear_cart()
        flash('Cart cleared.', 'success')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/count')
@login_required
def get_cart_count():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    count = cart.get_total_items() if cart else 0
    return jsonify({'count': count})
