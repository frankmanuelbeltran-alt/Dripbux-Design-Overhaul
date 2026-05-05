"""
DripBux Premium - Orders Routes
===============================
Order history and tracking.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Order
from extensions import db

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/')
@login_required
def index():
    """User order history"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    
    query = Order.query.filter_by(user_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
    
    query = query.order_by(Order.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    orders = pagination.items
    
    return render_template('orders/index.html', 
        orders=orders, 
        pagination=pagination,
        current_status=status
    )


@orders_bp.route('/<order_number>')
@login_required
def detail(order_number):
    """Order detail page"""
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    
    # Ensure user owns this order
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('orders.index'))
    
    return render_template('orders/detail.html', order=order)


@orders_bp.route('/<order_number>/cancel', methods=['POST'])
@login_required
def cancel_order(order_number):
    """Cancel an order"""
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    
    # Ensure user owns this order
    if order.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('orders.index'))
    
    # Check if order can be cancelled
    if not order.can_cancel():
        flash('This order cannot be cancelled.', 'error')
        return redirect(url_for('orders.detail', order_number=order_number))
    
    try:
        # Refund Robux
        from models import ProductSize
        
        # Restore stock
        for item in order.items:
            size = ProductSize.query.filter_by(
                product_id=item.product_id,
                size=item.size
            ).first()
            if size:
                size.stock += item.quantity
        
        # Refund Robux
        current_user.add_robux(
            order.total_robux,
            description=f'Refund for cancelled order #{order.order_number}'
        )
        
        # Update order status
        order.status = Order.STATUS_CANCELLED
        db.session.commit()
        
        flash('Order cancelled successfully. Robux has been refunded.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while cancelling the order.', 'error')
    
    return redirect(url_for('orders.detail', order_number=order_number))


@orders_bp.route('/<order_number>/track')
@login_required
def track_order(order_number):
    """Track order shipping"""
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    
    # Ensure user owns this order
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('orders.index'))
    
    # Mock tracking events (in real app, this would come from shipping API)
    tracking_events = []
    
    if order.status == Order.STATUS_DELIVERED:
        tracking_events = [
            {'date': order.delivered_at, 'status': 'Delivered', 'location': 'Your address', 'completed': True},
            {'date': order.shipped_at, 'status': 'Out for Delivery', 'location': 'Local facility', 'completed': True},
            {'date': order.shipped_at, 'status': 'Shipped', 'location': 'Distribution center', 'completed': True},
            {'date': order.created_at, 'status': 'Order Placed', 'location': 'Warehouse', 'completed': True},
        ]
    elif order.status == Order.STATUS_SHIPPED:
        tracking_events = [
            {'date': None, 'status': 'Delivered', 'location': 'Your address', 'completed': False},
            {'date': None, 'status': 'Out for Delivery', 'location': 'Local facility', 'completed': False},
            {'date': order.shipped_at, 'status': 'Shipped', 'location': 'Distribution center', 'completed': True},
            {'date': order.created_at, 'status': 'Order Placed', 'location': 'Warehouse', 'completed': True},
        ]
    else:
        tracking_events = [
            {'date': None, 'status': 'Delivered', 'location': 'Your address', 'completed': False},
            {'date': None, 'status': 'Out for Delivery', 'location': 'Local facility', 'completed': False},
            {'date': None, 'status': 'Shipped', 'location': 'Distribution center', 'completed': False},
            {'date': order.created_at, 'status': 'Order Placed', 'location': 'Warehouse', 'completed': True},
        ]
    
    return render_template('orders/track.html', 
        order=order, 
        tracking_events=tracking_events
    )
