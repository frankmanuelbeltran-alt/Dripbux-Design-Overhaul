"""
DripBux Premium Database Models
===============================
All SQLAlchemy models for the premium streetwear marketplace.
"""

from flask_login import UserMixin
from datetime import datetime, timedelta
from extensions import db
import random
import string


# =============================================================================
# USER MODELS
# =============================================================================

class User(UserMixin, db.Model):
    """User model with authentication and Robux balance"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    robux_balance = db.Column(db.Integer, default=10000)
    avatar_url = db.Column(db.String(255), default='default-avatar.png')
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    addresses = db.relationship('Address', backref='user', lazy=True, cascade='all, delete-orphan')
    cart = db.relationship('Cart', backref='user', uselist=False, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan', order_by='Order.created_at.desc()')
    wishlist_items = db.relationship('Wishlist', backref='user', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan', order_by='Transaction.created_at.desc()')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def has_sufficient_robux(self, amount):
        """Check if user has enough Robux balance"""
        return self.robux_balance >= amount
    
    def deduct_robux(self, amount, description="Purchase", order_id=None):
        """Deduct Robux from user balance and log transaction"""
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
        """Add Robux to user balance and log transaction"""
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
        """Get total items in cart"""
        if self.cart:
            return self.cart.get_total_items()
        return 0
    
    def get_wishlist_count(self):
        """Get total items in wishlist"""
        return len(self.wishlist_items)


class Address(db.Model):
    """Shipping address model for users"""
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
    
    def __repr__(self):
        return f'<Address {self.full_name}>'
    
    def get_full_address(self):
        """Get formatted full address"""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.append(f"{self.city}, {self.state} {self.postal_code}")
        parts.append(self.country)
        return ", ".join(parts)


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
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def get_product_count(self):
        """Get number of active products in category"""
        return Product.query.filter_by(category_id=self.id, is_active=True).count()


class Product(db.Model):
    """Product model for clothing items"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text)
    short_description = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    price_robux = db.Column(db.Integer, nullable=False)
    original_price = db.Column(db.Integer)  # For sale items
    image_url = db.Column(db.String(255))
    additional_images = db.Column(db.JSON, default=list)  # List of additional image URLs
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_new = db.Column(db.Boolean, default=True)
    views_count = db.Column(db.Integer, default=0)
    sales_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sizes = db.relationship('ProductSize', backref='product', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='product', lazy=True, cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    wishlist_entries = db.relationship('Wishlist', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def get_average_rating(self):
        """Calculate average rating from reviews"""
        if not self.reviews:
            return 0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)
    
    def get_review_count(self):
        """Get number of reviews"""
        return len(self.reviews)
    
    def is_in_stock(self):
        """Check if any size is in stock"""
        return any(size.stock > 0 for size in self.sizes)
    
    def get_total_stock(self):
        """Get total stock across all sizes"""
        return sum(size.stock for size in self.sizes)
    
    def get_price_range(self):
        """Get price range across all sizes"""
        if not self.sizes:
            return (self.price_robux, self.price_robux)
        modifiers = [s.price_modifier for s in self.sizes]
        return (self.price_robux + min(modifiers), self.price_robux + max(modifiers))
    
    def get_display_price(self):
        """Get price to display (lowest)"""
        if not self.sizes:
            return self.price_robux
        return self.price_robux + min(s.price_modifier for s in self.sizes)
    
    def get_discount_percentage(self):
        """Get discount percentage if on sale"""
        if self.original_price and self.original_price > self.price_robux:
            return int(((self.original_price - self.price_robux) / self.original_price) * 100)
        return 0
    
    def increment_views(self):
        """Increment view counter"""
        self.views_count += 1
        db.session.commit()


class ProductSize(db.Model):
    """Product size variant with stock tracking"""
    __tablename__ = 'product_sizes'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(10), nullable=False)  # XS, S, M, L, XL, XXL, 3XL
    stock = db.Column(db.Integer, default=0)
    price_modifier = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<ProductSize {self.size}>'
    
    def get_total_price(self):
        """Calculate total price including size modifier"""
        return self.product.price_robux + self.price_modifier
    
    def is_available(self, quantity=1):
        """Check if size is available in requested quantity"""
        return self.stock >= quantity


# =============================================================================
# CART MODELS
# =============================================================================

class Cart(db.Model):
    """Shopping cart model - one per user"""
    __tablename__ = 'carts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Cart {self.user_id}>'
    
    def get_total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items)
    
    def get_subtotal(self):
        """Calculate subtotal of all items"""
        return sum(item.get_subtotal() for item in self.items)
    
    def get_shipping_estimate(self):
        """Get estimated shipping cost"""
        subtotal = self.get_subtotal()
        if subtotal >= 1000:
            return 0
        return 0  # Free shipping for now
    
    def get_total(self):
        """Calculate total with shipping"""
        return self.get_subtotal() + self.get_shipping_estimate()
    
    def clear_cart(self):
        """Remove all items from cart"""
        for item in self.items:
            db.session.delete(item)
        db.session.commit()
    
    def add_item(self, product_id, size_id, quantity=1):
        """Add item to cart or update quantity if exists"""
        existing_item = CartItem.query.filter_by(
            cart_id=self.id, 
            product_id=product_id, 
            size_id=size_id
        ).first()
        
        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = CartItem(
                cart_id=self.id,
                product_id=product_id,
                size_id=size_id,
                quantity=quantity
            )
            db.session.add(new_item)
        
        db.session.commit()
    
    def remove_item(self, item_id):
        """Remove item from cart"""
        item = CartItem.query.get(item_id)
        if item and item.cart_id == self.id:
            db.session.delete(item)
            db.session.commit()
            return True
        return False
    
    def update_item_quantity(self, item_id, quantity):
        """Update item quantity"""
        item = CartItem.query.get(item_id)
        if item and item.cart_id == self.id:
            if quantity <= 0:
                db.session.delete(item)
            else:
                item.quantity = quantity
            db.session.commit()
            return True
        return False


class CartItem(db.Model):
    """Individual item in shopping cart"""
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size_id = db.Column(db.Integer, db.ForeignKey('product_sizes.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product')
    size = db.relationship('ProductSize')
    
    def __repr__(self):
        return f'<CartItem {self.product.name} x{self.quantity}>'
    
    def get_subtotal(self):
        """Calculate subtotal for this item"""
        return (self.product.price_robux + self.size.price_modifier) * self.quantity
    
    def is_valid(self):
        """Check if item is still valid (in stock)"""
        return self.size.stock >= self.quantity


# =============================================================================
# ORDER MODELS
# =============================================================================

class Order(db.Model):
    """Order model for completed purchases"""
    __tablename__ = 'orders'
    
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), default=STATUS_PENDING)
    
    # Pricing
    subtotal_robux = db.Column(db.Integer, nullable=False)
    shipping_fee = db.Column(db.Integer, default=0)
    discount_amount = db.Column(db.Integer, default=0)
    total_robux = db.Column(db.Integer, nullable=False)
    
    # Shipping Address
    shipping_name = db.Column(db.String(100), nullable=False)
    shipping_phone = db.Column(db.String(20), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    
    # Tracking
    tracking_number = db.Column(db.String(100))
    shipped_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    estimated_delivery = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.order_number}>'
    
    def generate_order_number(self):
        """Generate unique order number"""
        prefix = 'DBX'
        timestamp = datetime.utcnow().strftime('%y%m%d')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f'{prefix}-{timestamp}-{random_suffix}'
    
    def get_status_color(self):
        """Get status color for UI"""
        colors = {
            self.STATUS_PENDING: 'warning',
            self.STATUS_PROCESSING: 'info',
            self.STATUS_SHIPPED: 'primary',
            self.STATUS_DELIVERED: 'success',
            self.STATUS_CANCELLED: 'error'
        }
        return colors.get(self.status, 'default')
    
    def get_status_display(self):
        """Get display name for status"""
        displays = {
            self.STATUS_PENDING: 'Pending',
            self.STATUS_PROCESSING: 'Processing',
            self.STATUS_SHIPPED: 'Shipped',
            self.STATUS_DELIVERED: 'Delivered',
            self.STATUS_CANCELLED: 'Cancelled'
        }
        return displays.get(self.status, self.status.title())
    
    def get_total_items(self):
        """Get total items in order"""
        return sum(item.quantity for item in self.items)
    
    def can_cancel(self):
        """Check if order can be cancelled"""
        return self.status in [self.STATUS_PENDING, self.STATUS_PROCESSING]


class OrderItem(db.Model):
    """Individual item in an order"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_robux = db.Column(db.Integer, nullable=False)  # Price at time of purchase
    
    def __repr__(self):
        return f'<OrderItem {self.product.name} x{self.quantity}>'
    
    def get_subtotal(self):
        """Calculate subtotal for this item"""
        return self.price_robux * self.quantity


# =============================================================================
# WISHLIST MODEL
# =============================================================================

class Wishlist(db.Model):
    """User wishlist model"""
    __tablename__ = 'wishlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure unique wishlist items per user
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_wishlist_item'),)
    
    def __repr__(self):
        return f'<Wishlist {self.user_id}:{self.product_id}>'


# =============================================================================
# REVIEW MODEL
# =============================================================================

class Review(db.Model):
    """Product review model"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(100))
    comment = db.Column(db.Text)
    is_verified_purchase = db.Column(db.Boolean, default=False)
    helpful_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure one review per user per product
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_review'),)
    
    def __repr__(self):
        return f'<Review {self.rating} stars>'


# =============================================================================
# TRANSACTION MODEL
# =============================================================================

class Transaction(db.Model):
    """Robux transaction history model"""
    __tablename__ = 'transactions'
    
    TYPE_CREDIT = 'credit'
    TYPE_DEBIT = 'debit'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Positive for credit, negative for debit
    description = db.Column(db.String(255), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # credit/debit
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.amount}>'
    
    def is_credit(self):
        return self.amount > 0
    
    def get_display_amount(self):
        """Get formatted amount with sign"""
        if self.amount > 0:
            return f'+{self.amount:,}'
        return f'{self.amount:,}'
