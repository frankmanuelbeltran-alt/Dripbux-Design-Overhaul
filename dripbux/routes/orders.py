"""
DripBux Orders Routes
=====================
Order history, tracking, cancellations.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Order, ProductSize, Notification, OrderCancellation, Product, Seller
from forms import CancellationReasonForm
from extensions import db

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    query = Order.query.filter_by(user_id=current_user.id)
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('orders/index.html', orders=orders, current_status=status)


@orders_bp.route('/<order_number>')
@login_required
def detail(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('orders.index'))

    cancel_form = CancellationReasonForm()
    return render_template('orders/detail.html', order=order, cancel_form=cancel_form)


@orders_bp.route('/<order_number>/cancel', methods=['POST'])
@login_required
def cancel_order(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    if order.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('orders.index'))

    if not order.can_cancel():
        flash('This order cannot be cancelled.', 'error')
        return redirect(url_for('orders.detail', order_number=order_number))

    form = CancellationReasonForm()
    if not form.validate_on_submit():
        flash('Please select a valid cancellation reason.', 'error')
        return redirect(url_for('orders.detail', order_number=order_number))

    try:
        for item in order.items:
            size = ProductSize.query.filter_by(product_id=item.product_id, size=item.size).first()
            if size:
                size.stock += item.quantity
            product = Product.query.get(item.product_id)
            if product and product.seller_id:
                seller = Seller.query.get(product.seller_id)
                if seller:
                    seller.total_sales = max(0, (seller.total_sales or 0) - item.quantity)
                    seller.total_revenue = max(0, (seller.total_revenue or 0) - (item.price_robux * item.quantity))

        cancellation = OrderCancellation(
            order_id=order.id,
            user_id=current_user.id,
            reason=form.reason.data,
            custom_reason=form.custom_reason.data if form.reason.data == 'other' else None
        )
        db.session.add(cancellation)

        current_user.add_robux(order.total_robux, description=f'Refund for cancelled order #{order.order_number}')
        order.status = Order.STATUS_CANCELLED
        db.session.commit()
        flash('Order cancelled. Robux refunded.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error cancelling order.', 'error')

    return redirect(url_for('orders.detail', order_number=order_number))


@orders_bp.route('/<order_number>/track')
@login_required
def track_order(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('orders.index'))

    events = []
    if order.status == Order.STATUS_DELIVERED:
        events = [
            {'date': order.delivered_at, 'status': 'Delivered', 'location': 'Your address', 'completed': True},
            {'date': order.shipped_at, 'status': 'Out for Delivery', 'location': 'Local facility', 'completed': True},
            {'date': order.shipped_at, 'status': 'Shipped', 'location': 'Distribution center', 'completed': True},
            {'date': order.created_at, 'status': 'Order Placed', 'location': 'Warehouse', 'completed': True},
        ]
    elif order.status == Order.STATUS_SHIPPED:
        events = [
            {'date': None, 'status': 'Delivered', 'location': 'Your address', 'completed': False},
            {'date': None, 'status': 'Out for Delivery', 'location': 'Local facility', 'completed': False},
            {'date': order.shipped_at, 'status': 'Shipped', 'location': 'Distribution center', 'completed': True},
            {'date': order.created_at, 'status': 'Order Placed', 'location': 'Warehouse', 'completed': True},
        ]
    elif order.status == Order.STATUS_CANCELLED:
        events = [
            {'date': order.created_at, 'status': 'Order Cancelled', 'location': 'N/A', 'completed': True, 'is_cancelled': True},
        ]
    else:
        events = [
            {'date': None, 'status': 'Delivered', 'location': 'Your address', 'completed': False},
            {'date': None, 'status': 'Out for Delivery', 'location': 'Local facility', 'completed': False},
            {'date': None, 'status': 'Shipped', 'location': 'Distribution center', 'completed': False},
            {'date': order.created_at, 'status': 'Order Placed', 'location': 'Warehouse', 'completed': True},
        ]

    return render_template('orders/track.html', order=order, tracking_events=events)


from datetime import datetime
