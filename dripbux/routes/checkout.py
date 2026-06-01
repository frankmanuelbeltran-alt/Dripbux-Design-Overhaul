"""
DripBux Checkout Routes
========================
Multi-step checkout with coupon/voucher support.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from models import Cart, CartItem, Order, OrderItem, Address, ProductSize, Transaction, Coupon, UserCoupon
from forms import CheckoutShippingForm
from extensions import db
from datetime import datetime, timedelta

checkout_bp = Blueprint('checkout', __name__)


def format_address(shipping):
    parts = [shipping['address_line1']]
    if shipping.get('address_line2'):
        parts.append(shipping['address_line2'])
    parts.append(f"{shipping['city']}, {shipping['state']} {shipping['postal_code']}")
    parts.append(shipping['country'])
    return ", ".join(parts)


@checkout_bp.route('/')
@login_required
def checkout():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or cart.get_total_items() == 0:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('cart.view_cart'))
    return redirect(url_for('checkout.shipping'))


@checkout_bp.route('/shipping', methods=['GET', 'POST'])
@login_required
def shipping():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or cart.get_total_items() == 0:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('cart.view_cart'))

    # Validate items
    for item in cart.items:
        if not item.is_valid():
            flash(f'{item.product.name} is no longer available.', 'error')
            return redirect(url_for('cart.view_cart'))

    form = CheckoutShippingForm()
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
        session['checkout_shipping'] = {
            'full_name': form.full_name.data,
            'phone': form.phone.data,
            'address_line1': form.address_line1.data,
            'address_line2': form.address_line2.data or '',
            'city': form.city.data,
            'state': form.state.data or '',
            'postal_code': form.postal_code.data,
            'country': form.country.data,
            'shipping_method': form.shipping_method.data,
            'save_address': form.save_address.data,
        }
        if form.save_address.data:
            addr = Address(
                user_id=current_user.id,
                full_name=form.full_name.data, phone=form.phone.data,
                address_line1=form.address_line1.data, address_line2=form.address_line2.data,
                city=form.city.data, state=form.state.data, postal_code=form.postal_code.data,
                country=form.country.data
            )
            db.session.add(addr)
            db.session.commit()
        return redirect(url_for('checkout.review'))

    return render_template('checkout/shipping.html', form=form, cart=cart)


@checkout_bp.route('/review', methods=['GET', 'POST'])
@login_required
def review():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or cart.get_total_items() == 0:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('cart.view_cart'))

    shipping_info = session.get('checkout_shipping')
    if not shipping_info:
        flash('Please enter shipping information.', 'info')
        return redirect(url_for('checkout.shipping'))

    subtotal = cart.get_subtotal()
    shipping_method = shipping_info.get('shipping_method', 'standard')
    shipping_fee = 199 if shipping_method == 'express' else 0
    if subtotal >= 1000:
        shipping_fee = 0

    # Handle coupon
    discount = 0
    coupon_code = None
    if request.method == 'POST':
        coupon_code_input = request.form.get('coupon_code', '').strip().upper()
        if coupon_code_input:
            coupon = Coupon.query.filter_by(code=coupon_code_input, is_active=True).first()
            if coupon and coupon.is_valid():
                # Check if user hasn't used it
                already_used = UserCoupon.query.filter_by(user_id=current_user.id, coupon_id=coupon.id).first()
                if already_used:
                    flash('You have already used this coupon.', 'error')
                else:
                    if subtotal >= coupon.min_order_amount:
                        discount = coupon.calculate_discount(subtotal)
                        session['checkout_coupon_id'] = coupon.id
                        coupon_code = coupon.code
                        flash(f'Coupon applied! Saved {discount:,} Robux', 'success')
                    else:
                        flash(f'Minimum order of {coupon.min_order_amount:,} Robux required.', 'error')
            else:
                flash('Invalid or expired coupon.', 'error')

    # Check existing coupon in session
    if not coupon_code and session.get('checkout_coupon_id'):
        coupon = Coupon.query.get(session['checkout_coupon_id'])
        if coupon and coupon.is_valid():
            discount = coupon.calculate_discount(subtotal)
            coupon_code = coupon.code

    total = max(0, subtotal + shipping_fee - discount)

    if request.method == 'POST' and request.form.get('place_order'):
        session['checkout_total'] = total
        session['checkout_discount'] = discount
        return redirect(url_for('checkout.payment'))

    return render_template('checkout/review.html',
        cart=cart, shipping_info=shipping_info, subtotal=subtotal,
        shipping_fee=shipping_fee, discount=discount, total=total,
        user_balance=current_user.robux_balance, coupon_code=coupon_code)


@checkout_bp.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or cart.get_total_items() == 0:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('cart.view_cart'))

    shipping_info = session.get('checkout_shipping')
    total = session.get('checkout_total', 0)
    discount = session.get('checkout_discount', 0)

    if not shipping_info or not total:
        flash('Please complete checkout steps.', 'info')
        return redirect(url_for('checkout.shipping'))

    if not current_user.has_sufficient_robux(total):
        flash(f'Insufficient Robux. Need {total:,} but have {current_user.robux_balance:,}.', 'error')
        return redirect(url_for('checkout.review'))

    if request.method == 'POST':
        try:
            shipping_method = shipping_info.get('shipping_method', 'standard')
            shipping_fee = 199 if shipping_method == 'express' else 0
            subtotal = cart.get_subtotal()
            if subtotal >= 1000:
                shipping_fee = 0

            order = Order(
                user_id=current_user.id,
                order_number='', status=Order.STATUS_PENDING,
                subtotal_robux=subtotal,
                shipping_fee=shipping_fee,
                discount_amount=discount,
                total_robux=total,
                shipping_name=shipping_info['full_name'],
                shipping_phone=shipping_info['phone'],
                shipping_address=format_address(shipping_info),
                shipping_method=shipping_method,
                estimated_delivery=datetime.utcnow() + timedelta(days=2 if shipping_method == 'express' else 5)
            )
            order.order_number = order.generate_order_number()
            db.session.add(order)
            db.session.flush()

            for cart_item in cart.items:
                order_item = OrderItem(
                    order_id=order.id, product_id=cart_item.product_id,
                    size=cart_item.size.size if cart_item.size else None,
                    quantity=cart_item.quantity,
                    price_robux=cart_item.get_unit_price(),
                    product_name=cart_item.product.name,
                    product_image=cart_item.product.image_url
                )
                db.session.add(order_item)

                # Update stock
                if cart_item.size:
                    cart_item.size.stock -= cart_item.quantity
                else:
                    cart_item.product.stock_quantity -= cart_item.quantity
                cart_item.product.sales_count = (cart_item.product.sales_count or 0) + cart_item.quantity

                # Seller revenue
                if cart_item.product.seller_id:
                    seller = cart_item.product.seller
                    if seller:
                        seller.total_sales = (seller.total_sales or 0) + cart_item.quantity
                        seller.total_revenue = (seller.total_revenue or 0) + (cart_item.get_unit_price() * cart_item.quantity)

            # Deduct Robux
            current_user.deduct_robux(total, description=f'Order #{order.order_number}', order_id=order.id)

            # Record coupon usage
            coupon_id = session.pop('checkout_coupon_id', None)
            if coupon_id:
                user_coupon = UserCoupon(user_id=current_user.id, coupon_id=coupon_id, order_id=order.id)
                db.session.add(user_coupon)
                coupon = Coupon.query.get(coupon_id)
                if coupon:
                    coupon.usage_count = (coupon.usage_count or 0) + 1

            cart.clear_cart()
            db.session.commit()

            session['last_order_id'] = order.id
            session.pop('checkout_shipping', None)
            session.pop('checkout_total', None)
            session.pop('checkout_discount', None)

            return redirect(url_for('checkout.confirmation'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('checkout.review'))

    return render_template('checkout/payment.html', cart=cart, total=total,
        user_balance=current_user.robux_balance, shipping_info=shipping_info)


@checkout_bp.route('/confirmation')
@login_required
def confirmation():
    order_id = session.pop('last_order_id', None)
    if not order_id:
        flash('No recent order found.', 'info')
        return redirect(url_for('main.index'))

    order = Order.query.get(order_id)
    if not order or order.user_id != current_user.id:
        flash('Order not found.', 'error')
        return redirect(url_for('main.index'))

    return render_template('checkout/confirmation.html', order=order)
