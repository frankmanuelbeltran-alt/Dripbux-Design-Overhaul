"""
DripBux Premium - Checkout Routes
==================================
Multi-step checkout flow:
Step 1: Shipping Info
Step 2: Order Review
Step 3: Payment (Robux deduction)
Step 4: Confirmation
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from models import Cart, CartItem, Order, OrderItem, Address, ProductSize, Transaction
from forms import CheckoutShippingForm, CheckoutReviewForm
from extensions import db
from datetime import datetime, timedelta

checkout_bp = Blueprint('checkout', __name__)


@checkout_bp.route('/')
@login_required
def checkout():
    """Redirect to first step of checkout"""
    return redirect(url_for('checkout.shipping'))


@checkout_bp.route('/shipping', methods=['GET', 'POST'])
@login_required
def shipping():
    """Step 1: Shipping Information"""
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart or cart.get_total_items() == 0:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('cart.view_cart'))
    
    # Check for invalid items
    for item in cart.items:
        if not item.is_valid():
            flash(f'{item.product.name} ({item.size.size}) is no longer available in the requested quantity.', 'error')
            return redirect(url_for('cart.view_cart'))
    
    form = CheckoutShippingForm()
    
    # Pre-fill with default address if available
    default_address = Address.query.filter_by(user_id=current_user.id, is_default=True).first()
    if default_address and request.method == 'GET':
        form.full_name.data = default_address.full_name
        form.phone.data = default_address.phone
        form.address_line1.data = default_address.address_line1
        form.address_line2.data = default_address.address_line2
        form.city.data = default_address.city
        form.state.data = default_address.state
        form.postal_code.data = default_address.postal_code
        form.country.data = default_address.country
    
    if form.validate_on_submit():
        # Store shipping info in session
        session['checkout_shipping'] = {
            'full_name': form.full_name.data,
            'phone': form.phone.data,
            'address_line1': form.address_line1.data,
            'address_line2': form.address_line2.data or '',
            'city': form.city.data,
            'state': form.state.data or '',
            'postal_code': form.postal_code.data,
            'country': form.country.data,
            'save_address': form.save_address.data
        }
        
        # Save address if requested
        if form.save_address.data:
            address = Address(
                user_id=current_user.id,
                full_name=form.full_name.data,
                phone=form.phone.data,
                address_line1=form.address_line1.data,
                address_line2=form.address_line2.data,
                city=form.city.data,
                state=form.state.data,
                postal_code=form.postal_code.data,
                country=form.country.data
            )
            db.session.add(address)
            db.session.commit()
        
        return redirect(url_for('checkout.review'))
    
    return render_template('checkout/shipping.html', form=form, cart=cart)


@checkout_bp.route('/review', methods=['GET', 'POST'])
@login_required
def review():
    """Step 2: Order Review"""
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart or cart.get_total_items() == 0:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('cart.view_cart'))
    
    # Check if shipping info exists
    shipping_info = session.get('checkout_shipping')
    if not shipping_info:
        flash('Please enter shipping information first.', 'info')
        return redirect(url_for('checkout.shipping'))
    
    # Check for invalid items
    for item in cart.items:
        if not item.is_valid():
            flash(f'{item.product.name} ({item.size.size}) is no longer available.', 'error')
            return redirect(url_for('cart.view_cart'))
    
    form = CheckoutReviewForm()
    
    if form.validate_on_submit():
        # Store shipping method in session
        session['checkout_shipping_method'] = form.shipping_method.data
        
        # Handle promo code (simplified - just store for now)
        if form.promo_code.data:
            session['checkout_promo_code'] = form.promo_code.data.upper()
        
        return redirect(url_for('checkout.payment'))
    
    # Calculate totals
    subtotal = cart.get_subtotal()
    shipping_method = session.get('checkout_shipping_method', 'standard')
    
    if shipping_method == 'express':
        shipping_fee = 199
        shipping_days = 2
    else:
        shipping_fee = 0
        shipping_days = 5
    
    # Free shipping for orders over 1000 Robux
    if subtotal >= 1000:
        shipping_fee = 0
    
    total = subtotal + shipping_fee
    
    return render_template('checkout/review.html',
        form=form,
        cart=cart,
        shipping_info=shipping_info,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        shipping_days=shipping_days,
        total=total,
        user_balance=current_user.robux_balance
    )


@checkout_bp.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    """Step 3: Payment (Robux deduction)"""
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart or cart.get_total_items() == 0:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('cart.view_cart'))
    
    # Check prerequisites
    shipping_info = session.get('checkout_shipping')
    shipping_method = session.get('checkout_shipping_method', 'standard')
    
    if not shipping_info:
        flash('Please enter shipping information first.', 'info')
        return redirect(url_for('checkout.shipping'))
    
    # Calculate totals
    subtotal = cart.get_subtotal()
    
    if shipping_method == 'express':
        shipping_fee = 199
    else:
        shipping_fee = 0
    
    # Free shipping for orders over 1000 Robux
    if subtotal >= 1000:
        shipping_fee = 0
    
    total = subtotal + shipping_fee
    
    # Check if user has sufficient balance
    if not current_user.has_sufficient_robux(total):
        flash(f'Insufficient Robux balance. You need {total:,} Robux but only have {current_user.robux_balance:,}.', 'error')
        return redirect(url_for('checkout.review'))
    
    if request.method == 'POST':
        # Process the order
        try:
            # Create order
            order = Order(
                user_id=current_user.id,
                order_number='',  # Will be generated
                status=Order.STATUS_PENDING,
                subtotal_robux=subtotal,
                shipping_fee=shipping_fee,
                total_robux=total,
                shipping_name=shipping_info['full_name'],
                shipping_phone=shipping_info['phone'],
                shipping_address=format_address(shipping_info),
                estimated_delivery=datetime.utcnow() + timedelta(days=5 if shipping_method == 'standard' else 2)
            )
            
            # Generate order number
            order.order_number = order.generate_order_number()
            
            db.session.add(order)
            db.session.flush()  # Get order ID
            
            # Create order items and update stock
            for cart_item in cart.items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=cart_item.product_id,
                    size=cart_item.size.size,
                    quantity=cart_item.quantity,
                    price_robux=cart_item.product.price_robux + cart_item.size.price_modifier
                )
                db.session.add(order_item)
                
                # Update stock
                cart_item.size.stock -= cart_item.quantity
                
                # Update product sales count
                cart_item.product.sales_count += cart_item.quantity
            
            # Deduct Robux
            current_user.deduct_robux(
                total, 
                description=f'Order #{order.order_number}',
                order_id=order.id
            )
            
            # Clear cart
            cart.clear_cart()
            
            # Commit all changes
            db.session.commit()
            
            # Store order ID in session for confirmation page
            session['last_order_id'] = order.id
            
            # Clear checkout session data
            session.pop('checkout_shipping', None)
            session.pop('checkout_shipping_method', None)
            session.pop('checkout_promo_code', None)
            
            return redirect(url_for('checkout.confirmation'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while processing your order. Please try again.', 'error')
            return redirect(url_for('checkout.review'))
    
    return render_template('checkout/payment.html',
        cart=cart,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        total=total,
        user_balance=current_user.robux_balance,
        shipping_info=shipping_info
    )


@checkout_bp.route('/confirmation')
@login_required
def confirmation():
    """Step 4: Order Confirmation"""
    order_id = session.get('last_order_id')
    
    if not order_id:
        flash('No recent order found.', 'info')
        return redirect(url_for('main.index'))
    
    order = Order.query.get(order_id)
    
    if not order or order.user_id != current_user.id:
        flash('Order not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Clear last order ID from session
    session.pop('last_order_id', None)
    
    return render_template('checkout/confirmation.html', order=order)


def format_address(shipping_info):
    """Format shipping address for storage"""
    parts = [
        shipping_info['address_line1']
    ]
    
    if shipping_info.get('address_line2'):
        parts.append(shipping_info['address_line2'])
    
    parts.append(f"{shipping_info['city']}, {shipping_info.get('state', '')} {shipping_info['postal_code']}")
    parts.append(shipping_info['country'])
    
    return '\n'.join(parts)
