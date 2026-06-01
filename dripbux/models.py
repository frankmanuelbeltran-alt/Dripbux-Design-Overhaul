"""
DripBux Complete Overhaul - Database Models
=============================================
All SQLAlchemy models for the full e-commerce marketplace.
"""

from flask import url_for
from flask_login import UserMixin
from datetime import datetime, timedelta
from extensions import db
import random
import string
import json


# =============================================================================
# USER MODELS
# =============================================================================

class User(UserMixin, db.Model):
    """User model with Google OAuth + role-based access"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth-only users
    google_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    google_avatar = db.Column(db.String(500), nullable=True)
    avatar_url = db.Column(db.String(255), default='default-avatar.png')
    robux_balance = db.Column(db.Integer, default=10000)
    role = db.Column(db.String(20), default='customer')  # customer, seller, admin
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    auth_provider = db.Column(db.String(20), default='local')  # local, google

    # Relationships
    addresses = db.relationship('Address', backref='user', lazy=True, cascade='all, delete-orphan')
    cart = db.relationship('Cart', backref='user', uselist=False, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan', order_by='Order.created_at.desc()')
    wishlist_items = db.relationship('Wishlist', backref='user', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan', order_by='Transaction.created_at.desc()')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan', order_by='Notification.created_at.desc()')
    seller_profile = db.relationship('Seller', backref='user', uselist=False, cascade='all, delete-orphan')
    followers = db.relationship('Follower', backref='user', lazy=True, cascade='all, delete-orphan', foreign_keys='Follower.user_id')
    following = db.relationship('Follower', backref='followed_user', lazy=True, cascade='all, delete-orphan', foreign_keys='Follower.seller_user_id')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True, cascade='all, delete-orphan')
    messages_sent = db.relationship('Message', backref='sender', lazy=True, cascade='all, delete-orphan', foreign_keys='Message.sender_id')
    messages_received = db.relationship('Message', backref='receiver', lazy=True, cascade='all, delete-orphan', foreign_keys='Message.receiver_id')

    # Role constants
    ROLE_CUSTOMER = 'customer'
    ROLE_SELLER = 'seller'
    ROLE_ADMIN = 'admin'

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_seller(self):
        return self.role == self.ROLE_SELLER

    def has_role(self, role):
        return self.role == role

    def get_display_name(self):
        return self.username or self.email.split('@')[0]

    def get_avatar(self):
        if self.google_avatar:
            return self.google_avatar
        avatar = self.avatar_url or 'default-avatar.png'
        if avatar.startswith('http://') or avatar.startswith('https://'):
            return avatar
        if avatar.startswith('/'):
            return avatar
        return url_for('static', filename=f'images/avatars/{avatar}')

    def has_sufficient_robux(self, amount):
        return self.robux_balance >= amount

    def deduct_robux(self, amount, description="Purchase", order_id=None):
        if self.has_sufficient_robux(amount):
            self.robux_balance -= amount
            transaction = Transaction(
                user_id=self.id,
                amount=-amount,
                description=description,
                transaction_type='debit',
                order_id=order_id
            )
            db.session.add(transaction)
            return True
        return False

    def add_robux(self, amount, description="Added Robux"):
        self.robux_balance += amount
        transaction = Transaction(
            user_id=self.id,
            amount=amount,
            description=description,
            transaction_type='credit'
        )
        db.session.add(transaction)
        return True

    def get_cart_count(self):
        if self.cart:
            return self.cart.get_total_items()
        return 0

    def get_wishlist_count(self):
        return len(self.wishlist_items)

    def get_unread_notifications_count(self):
        return Notification.query.filter_by(user_id=self.id, is_read=False).count()


class Address(db.Model):
    """Shipping address model"""
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address_line1 = db.Column(db.String(255), nullable=False)
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), default='USA')
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_full_address(self):
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.append(f"{self.city}, {self.state} {self.postal_code}")
        parts.append(self.country)
        return ", ".join(parts)


# =============================================================================
# SELLER MODELS
# =============================================================================

class Seller(db.Model):
    """Seller profile/store model"""
    __tablename__ = 'sellers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    store_name = db.Column(db.String(100), nullable=False)
    store_slug = db.Column(db.String(100), unique=True, nullable=False)
    store_description = db.Column(db.Text)
    store_banner = db.Column(db.String(255))
    store_logo = db.Column(db.String(255))
    verification_status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    is_active = db.Column(db.Boolean, default=True)
    total_sales = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Integer, default=0)
    rating_average = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    follower_count = db.Column(db.Integer, default=0)
    response_time_hours = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', backref='seller', lazy=True, cascade='all, delete-orphan')
    followers_list = db.relationship('Follower', backref='seller', lazy=True, cascade='all, delete-orphan', foreign_keys='Follower.seller_id')
    vouchers = db.relationship('Voucher', backref='seller', lazy=True, cascade='all, delete-orphan')

    def get_display_name(self):
        return self.store_name or self.user.username

    def update_rating(self):
        reviews = SellerReview.query.filter_by(seller_id=self.id).all()
        if reviews:
            self.rating_average = round(sum(r.rating for r in reviews) / len(reviews), 1)
            self.rating_count = len(reviews)
        else:
            self.rating_average = 0.0
            self.rating_count = 0


class SellerReview(db.Model):
    """Reviews for sellers"""
    __tablename__ = 'seller_reviews'

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    seller = db.relationship('Seller', backref='reviews')
    user = db.relationship('User', backref='seller_reviews')


class SellerApplication(db.Model):
    """Seller application submitted by users for review"""
    __tablename__ = 'seller_applications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    store_name = db.Column(db.String(100), nullable=False)
    store_description = db.Column(db.Text)
    evidence = db.Column(db.JSON, default=list)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    user = db.relationship('User', foreign_keys=[user_id])


class SellerWarning(db.Model):
    """Warnings issued by admins to sellers (three-strike workflow)"""
    __tablename__ = 'seller_warnings'

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id'), nullable=False)
    issued_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(150))
    details = db.Column(db.Text)
    strike = db.Column(db.Integer, default=1)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    seller = db.relationship('Seller', backref='warnings')
    issuer = db.relationship('User', foreign_keys=[issued_by])


class SellerFlag(db.Model):
    """Flags raised against sellers by users"""
    __tablename__ = 'seller_flags'

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(150))
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    seller = db.relationship('Seller', backref='flags')
    user = db.relationship('User')


class Follower(db.Model):
    """User following sellers"""
    __tablename__ = 'followers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    seller_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'seller_id', name='unique_follow'),)


# =============================================================================
# PRODUCT MODELS
# =============================================================================

class Category(db.Model):
    """Product category model"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    icon = db.Column(db.String(50))
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy=True)

    def get_product_count(self):
        return Product.query.filter_by(category_id=self.id, is_active=True).count()


class Product(db.Model):
    """Product model - gaming/Roblox digital items"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text)
    short_description = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id'), nullable=True)
    price_robux = db.Column(db.Integer, nullable=False)
    original_price = db.Column(db.Integer)
    discount_percentage = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(255))
    additional_images = db.Column(db.JSON, default=list)
    stock_quantity = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(50), unique=True)
    tags = db.Column(db.String(500))
    rarity = db.Column(db.String(20), default='common')  # common, uncommon, rare, epic, legendary, mythic
    product_type = db.Column(db.String(30), default='physical')  # physical, digital, gamepass, bundle
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_new = db.Column(db.Boolean, default=True)
    is_trending = db.Column(db.Boolean, default=False)
    is_flash_sale = db.Column(db.Boolean, default=False)
    is_limited = db.Column(db.Boolean, default=False)
    flash_sale_ends = db.Column(db.DateTime)
    views_count = db.Column(db.Integer, default=0)
    sales_count = db.Column(db.Integer, default=0)
    favorites_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sizes = db.relationship('ProductSize', backref='product', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='product', lazy=True, cascade='all, delete-orphan', order_by='Review.created_at.desc()')
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    wishlist_entries = db.relationship('Wishlist', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name}>'

    def get_average_rating(self):
        visible_reviews = [r for r in self.reviews if not r.is_hidden]
        if not visible_reviews:
            return 0
        return round(sum(r.rating for r in visible_reviews) / len(visible_reviews), 1)

    def get_review_count(self):
        return len([r for r in self.reviews if not r.is_hidden])

    def is_in_stock(self):
        if self.product_type == 'digital':
            return True
        return self.stock_quantity > 0 or any(size.stock > 0 for size in self.sizes)

    def get_total_stock(self):
        if self.product_type == 'digital':
            return 999
        return self.stock_quantity or sum(size.stock for size in self.sizes)

    def get_display_price(self):
        if self.sizes:
            return self.price_robux + min(s.price_modifier for s in self.sizes)
        return self.price_robux

    def get_discount_percentage(self):
        if self.original_price and self.original_price > self.price_robux:
            return int(((self.original_price - self.price_robux) / self.original_price) * 100)
        return self.discount_percentage or 0

    def is_on_sale(self):
        return self.get_discount_percentage() > 0

    def increment_views(self):
        self.views_count += 1
        db.session.commit()

    def get_rarity_color(self):
        colors = {
            'common': '#a0a0b8',
            'uncommon': '#00e676',
            'rare': '#00b0ff',
            'epic': '#9d4edd',
            'legendary': '#ffd700',
            'mythic': '#ff4d8d'
        }
        return colors.get(self.rarity, '#a0a0b8')

    def get_related_products(self, limit=4):
        query = Product.query.filter(
            Product.id != self.id,
            Product.is_active == True
        )
        if self.category_id:
            query = query.filter(Product.category_id == self.category_id)
        return query.order_by(Product.sales_count.desc()).limit(limit).all()

    def get_trending_score(self):
        return (self.views_count * 1) + (self.sales_count * 3) + (self.favorites_count * 2)


class ProductSize(db.Model):
    """Product size/variant model"""
    __tablename__ = 'product_sizes'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    stock = db.Column(db.Integer, default=0)
    price_modifier = db.Column(db.Integer, default=0)

    def get_total_price(self):
        return self.product.price_robux + self.price_modifier

    def is_available(self, quantity=1):
        return self.stock >= quantity


# =============================================================================
# CART MODELS
# =============================================================================

class Cart(db.Model):
    """Shopping cart - one per user"""
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('CartItem', backref='cart', lazy=True, cascade='all, delete-orphan')

    def get_total_items(self):
        return sum(item.quantity for item in self.items)

    def get_subtotal(self):
        return sum(item.get_subtotal() for item in self.items)

    def get_total(self):
        return self.get_subtotal()

    def clear_cart(self):
        for item in self.items:
            db.session.delete(item)
        db.session.commit()


class CartItem(db.Model):
    """Individual cart item"""
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size_id = db.Column(db.Integer, db.ForeignKey('product_sizes.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    size = db.relationship('ProductSize')

    def get_subtotal(self):
        price = self.product.price_robux
        if self.size:
            price += self.size.price_modifier
        return price * self.quantity

    def get_unit_price(self):
        price = self.product.price_robux
        if self.size:
            price += self.size.price_modifier
        return price

    def is_valid(self):
        if not self.product or not self.product.is_active:
            return False
        if self.size and not self.size.is_available(self.quantity):
            return False
        return True


# =============================================================================
# ORDER MODELS
# =============================================================================

class Order(db.Model):
    """Order model with full tracking"""
    __tablename__ = 'orders'

    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_REFUNDED = 'refunded'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default=STATUS_PENDING)
    subtotal_robux = db.Column(db.Integer, nullable=False)
    shipping_fee = db.Column(db.Integer, default=0)
    discount_amount = db.Column(db.Integer, default=0)
    total_robux = db.Column(db.Integer, nullable=False)
    shipping_name = db.Column(db.String(100))
    shipping_phone = db.Column(db.String(20))
    shipping_address = db.Column(db.Text)
    shipping_method = db.Column(db.String(20), default='standard')
    tracking_number = db.Column(db.String(50))
    estimated_delivery = db.Column(db.DateTime)
    shipped_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    cancellation = db.relationship('OrderCancellation', backref='order', uselist=False, cascade='all, delete-orphan')

    def generate_order_number(self):
        prefix = 'DBX'
        timestamp = datetime.utcnow().strftime('%y%m%d')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"{prefix}-{timestamp}-{random_str}"

    def can_cancel(self):
        return self.status in [self.STATUS_PENDING, self.STATUS_PROCESSING]

    def get_status_color(self):
        colors = {
            self.STATUS_PENDING: '#ffc400',
            self.STATUS_PROCESSING: '#00b0ff',
            self.STATUS_SHIPPED: '#9d4edd',
            self.STATUS_DELIVERED: '#00e676',
            self.STATUS_CANCELLED: '#ff1744',
            self.STATUS_REFUNDED: '#6a6a80'
        }
        return colors.get(self.status, '#a0a0b8')

    def get_total_items(self):
        return sum(item.quantity for item in self.items)


class OrderItem(db.Model):
    """Individual order item"""
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(20))
    quantity = db.Column(db.Integer, nullable=False)
    price_robux = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(150))
    product_image = db.Column(db.String(255))

    def get_subtotal(self):
        return self.price_robux * self.quantity


# =============================================================================
# REVIEW MODELS
# =============================================================================

class Review(db.Model):
    """Product review model"""
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100))
    comment = db.Column(db.Text, nullable=False)
    is_verified_purchase = db.Column(db.Boolean, default=False)
    is_hidden = db.Column(db.Boolean, default=False)
    helpful_count = db.Column(db.Integer, default=0)
    seller_reply = db.Column(db.Text)
    seller_reply_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Images stored as JSON array of URLs
    images = db.Column(db.JSON, default=list)

    def __repr__(self):
        return f'<Review {self.rating} stars for Product {self.product_id}>'


class ReviewHelpful(db.Model):
    """Track helpful votes on reviews"""
    __tablename__ = 'review_helpful'

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('review_id', 'user_id', name='unique_helpful_vote'),)


class OrderCancellation(db.Model):
    """Order cancellation reason history"""
    __tablename__ = 'order_cancellations'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    custom_reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')


# =============================================================================
# WISHLIST MODEL
# =============================================================================

class Wishlist(db.Model):
    """User wishlist"""
    __tablename__ = 'wishlists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_wishlist'),)


# =============================================================================
# TRANSACTION MODEL
# =============================================================================

class Transaction(db.Model):
    """Robux transaction history"""
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))
    transaction_type = db.Column(db.String(20), nullable=False)  # credit, debit, refund
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =============================================================================
# NOTIFICATION MODEL
# =============================================================================

class Notification(db.Model):
    """User notifications"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(30), default='general')  # order, sale, promotion, system, message
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =============================================================================
# COUPON / VOUCHER MODELS
# =============================================================================

class Coupon(db.Model):
    """Global platform coupons"""
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.String(255))
    discount_type = db.Column(db.String(10), default='percent')  # percent, fixed
    discount_value = db.Column(db.Integer, nullable=False)
    min_order_amount = db.Column(db.Integer, default=0)
    max_discount = db.Column(db.Integer)
    usage_limit = db.Column(db.Integer, default=-1)  # -1 = unlimited
    usage_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    starts_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self):
        if not self.is_active:
            return False
        if self.usage_limit > 0 and self.usage_count >= self.usage_limit:
            return False
        now = datetime.utcnow()
        if self.starts_at and now < self.starts_at:
            return False
        if self.expires_at and now > self.expires_at:
            return False
        return True

    def calculate_discount(self, order_total):
        if self.discount_type == 'percent':
            discount = int(order_total * (self.discount_value / 100))
            if self.max_discount:
                discount = min(discount, self.max_discount)
            return discount
        return min(self.discount_value, order_total)


class Voucher(db.Model):
    """Seller-specific vouchers"""
    __tablename__ = 'vouchers'

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id'), nullable=False)
    code = db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(255))
    discount_type = db.Column(db.String(10), default='percent')
    discount_value = db.Column(db.Integer, nullable=False)
    min_order_amount = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    usage_limit = db.Column(db.Integer, default=-1)
    usage_count = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('seller_id', 'code', name='unique_seller_voucher'),)

    def is_valid(self):
        if not self.is_active:
            return False
        if self.usage_limit > 0 and self.usage_count >= self.usage_limit:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True


class UserCoupon(db.Model):
    """Track user coupon usage"""
    __tablename__ = 'user_coupons'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'coupon_id', name='unique_user_coupon'),)


# =============================================================================
# MESSAGE MODEL
# =============================================================================

class Message(db.Model):
    """User-to-seller messaging"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    subject = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    replies = db.relationship('Message', backref=db.backref('parent', remote_side=[id]), lazy=True)
    product = db.relationship('Product')


# =============================================================================
# ACTIVITY LOG MODEL
# =============================================================================

class ActivityLog(db.Model):
    """System activity logs"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(30), nullable=False)  # user, product, order, seller, etc.
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =============================================================================
# RECENTLY VIEWED MODEL
# =============================================================================

class RecentlyViewed(db.Model):
    """Track recently viewed products per user"""
    __tablename__ = 'recently_viewed'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')

    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_recent_view'),)


# =============================================================================
# SITE CONFIGURATION MODEL
# =============================================================================

class SiteConfig(db.Model):
    """Dynamic site configuration"""
    __tablename__ = 'site_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# ANNOUNCEMENT MODEL
# =============================================================================

class Announcement(db.Model):
    """Admin announcements"""
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    announcement_type = db.Column(db.String(20), default='info')  # info, warning, success, promo
    is_active = db.Column(db.Boolean, default=True)
    starts_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
