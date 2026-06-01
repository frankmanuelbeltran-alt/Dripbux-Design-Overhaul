"""
DripBux Complete Overhaul - Flask Application Factory
=======================================================
Full e-commerce marketplace with Google OAuth, seller system, and admin panel.
"""

from flask import Flask, render_template, request, g
from sqlalchemy import inspect, text
from extensions import db, login_manager, migrate, csrf
from config import AppConfig, AdminConfig, ThemeConfig, FeatureConfig, IconConfig
from dotenv import load_dotenv
import os

# Load environment variables from the local .env file in the app directory
base_dir = os.path.dirname(__file__)
load_dotenv(os.path.join(base_dir, '.env'))


def create_app():
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(AppConfig)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Login config
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to access this page.'
    login_manager.login_message_category = 'info'

    # User loader
    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.shop import shop_bp
    from routes.cart import cart_bp
    from routes.checkout import checkout_bp
    from routes.orders import orders_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    from routes.seller import seller_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(shop_bp, url_prefix='/shop')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(checkout_bp, url_prefix='/checkout')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(seller_bp, url_prefix='/seller')

    # Create upload directories
    upload_dirs = [
        os.path.join(app.root_path, 'static/images/products'),
        os.path.join(app.root_path, 'static/images/avatars'),
        os.path.join(app.root_path, 'static/images/categories'),
        os.path.join(app.root_path, 'static/images/sellers'),
    ]
    for d in upload_dirs:
        os.makedirs(d, exist_ok=True)

    # Initialize database
    with app.app_context():
        db.create_all()
        create_default_admin()
        create_mod_admin()
        create_default_categories()
        create_default_products()
        create_default_site_config()
        ensure_review_schema()
        print(" Database initialized!")

    # Context processor
    @app.context_processor
    def inject_globals():
        from models import Category, Cart, Notification, Announcement, Wishlist
        from flask_login import current_user

        cart_count = 0
        wishlist_count = 0
        unread_notifications = 0
        user_seller = None
        user_wishlist_ids = []

        if current_user.is_authenticated:
            cart_count = current_user.get_cart_count()
            wishlist_count = current_user.get_wishlist_count()
            unread_notifications = current_user.get_unread_notifications_count()
            user_wishlist_ids = [w.product_id for w in Wishlist.query.filter_by(user_id=current_user.id).all()]
            if current_user.is_seller and current_user.seller_profile:
                user_seller = current_user.seller_profile

        categories = Category.query.filter_by(is_active=True, parent_id=None).order_by(Category.display_order).all()
        active_announcements = Announcement.query.filter_by(is_active=True).filter(
            (Announcement.expires_at == None) | (Announcement.expires_at > db.func.now())
        ).order_by(Announcement.created_at.desc()).all()

        return {
            'theme': ThemeConfig,
            'icons': IconConfig,
            'features': FeatureConfig,
            'app_name': AppConfig.APP_NAME,
            'app_version': AppConfig.APP_VERSION,
            'app_tagline': AppConfig.APP_TAGLINE,
            'categories': categories,
            'cart_count': cart_count,
            'wishlist_count': wishlist_count,
            'unread_notifications': unread_notifications,
            'user_seller': user_seller,
            'user_wishlist_ids': user_wishlist_ids,
            'active_announcements': active_announcements,
        }

    @app.before_request
    def before_request():
        from flask_login import current_user
        g.user = current_user

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Template filters
    @app.template_filter('format_robux')
    def format_robux(value):
        if value is None:
            return '0'
        return f'{int(value):,}'

    @app.template_filter('format_price')
    def format_price(value):
        if value is None:
            return '<span class="robux-amount">0 <i data-lucide="coins" class="inline-icon"></i></span>'
        return f'<span class="robux-amount">{int(value):,} <i data-lucide="coins" class="inline-icon"></i></span>'

    @app.template_filter('truncate_words')
    def truncate_words(s, num=20):
        if not s:
            return ''
        words = s.split()
        if len(words) > num:
            return ' '.join(words[:num]) + '...'
        return s

    @app.template_filter('rating_stars')
    def rating_stars(rating):
        if not rating:
            return '<i data-lucide="star" class="text-muted"></i>' * 5
        full = int(rating)
        half = 1 if rating - full >= 0.5 else 0
        empty = 5 - full - half
        stars = '<i data-lucide="star" class="star-filled"></i>' * full
        if half:
            stars += '<i data-lucide="star-half" class="star-filled"></i>'
        stars += '<i data-lucide="star" class="star-empty"></i>' * empty
        return stars

    @app.template_filter('time_ago')
    def time_ago(dt):
        if not dt:
            return ''
        now = datetime.utcnow()
        diff = now - dt
        if diff.days > 365:
            return f'{diff.days // 365}y ago'
        if diff.days > 30:
            return f'{diff.days // 30}mo ago'
        if diff.days > 0:
            return f'{diff.days}d ago'
        if diff.seconds > 3600:
            return f'{diff.seconds // 3600}h ago'
        if diff.seconds > 60:
            return f'{diff.seconds // 60}m ago'
        return 'just now'

    return app


def create_default_admin():
    from models import User
    from werkzeug.security import generate_password_hash

    admin = User.query.filter_by(email=AdminConfig.DEFAULT_ADMIN_EMAIL).first()
    if not admin:
        admin = User(
            username='admin',
            email=AdminConfig.DEFAULT_ADMIN_EMAIL,
            password_hash=generate_password_hash(AdminConfig.DEFAULT_ADMIN_PASSWORD),
            robux_balance=AdminConfig.DEFAULT_ADMIN_ROBUX,
            role=User.ROLE_ADMIN,
            is_active=True,
            email_verified=True,
            auth_provider='local'
        )
        db.session.add(admin)
        db.session.commit()
        print(f"   Admin: {AdminConfig.DEFAULT_ADMIN_EMAIL} / {AdminConfig.DEFAULT_ADMIN_PASSWORD}")


def create_mod_admin():
    from models import User
    from werkzeug.security import generate_password_hash

    email = 'adminmod@dripbux.com'
    password = 'adminmod'

    mod = User.query.filter_by(email=email).first()
    if not mod:
        mod = User(
            username='mod',
            email=email,
            password_hash=generate_password_hash(password),
            robux_balance=AdminConfig.DEFAULT_ADMIN_ROBUX,
            role=User.ROLE_ADMIN,
            is_active=True,
            email_verified=True,
            auth_provider='local'
        )
        db.session.add(mod)
        db.session.commit()
        print(f"   Admin mod: {email} / {password}")


def create_default_categories():
    from models import Category

    cats = [
        {'name': 'Trending', 'slug': 'trending', 'description': 'Hot items right now', 'display_order': 1, 'icon': 'trending-up'},
        {'name': 'Limiteds', 'slug': 'limiteds', 'description': 'Exclusive limited items', 'display_order': 2, 'icon': 'zap'},
        {'name': 'Accessories', 'slug': 'accessories', 'description': 'Hats, glasses, gear', 'display_order': 3, 'icon': 'box'},
        {'name': 'Outfits', 'slug': 'outfits', 'description': 'Complete character outfits', 'display_order': 4, 'icon': 'sparkles'},
        {'name': 'Hoodies', 'slug': 'hoodies', 'description': 'Streetwear hoodies', 'display_order': 5, 'icon': 'shirt'},
        {'name': 'Shirts', 'slug': 'shirts', 'description': 'Graphic tees and shirts', 'display_order': 6, 'icon': 'shirt'},
        {'name': 'Pants', 'slug': 'pants', 'description': 'Bottoms and jeans', 'display_order': 7, 'icon': 'shirt'},
        {'name': 'Bundles', 'slug': 'bundles', 'description': 'Value item bundles', 'display_order': 8, 'icon': 'package'},
        {'name': 'Gamepasses', 'slug': 'gamepasses', 'description': 'Game access passes', 'display_order': 9, 'icon': 'ticket'},
        {'name': 'Cosmetics', 'slug': 'cosmetics', 'description': 'Skins and effects', 'display_order': 10, 'icon': 'palette'},
        {'name': 'Avatar Items', 'slug': 'avatar-items', 'description': 'Full avatar sets', 'display_order': 11, 'icon': 'user'},
        {'name': 'Mystery Boxes', 'slug': 'mystery-boxes', 'description': 'Random item drops', 'display_order': 12, 'icon': 'gift'},
        {'name': 'Featured Drops', 'slug': 'featured-drops', 'description': 'Curated selections', 'display_order': 13, 'icon': 'star'},
        {'name': 'Flash Sales', 'slug': 'flash-sales', 'description': 'Limited time deals', 'display_order': 14, 'icon': 'flame'},
    ]

    for c in cats:
        if not Category.query.filter_by(slug=c['slug']).first():
            db.session.add(Category(**c))
    db.session.commit()


def create_default_products():
    from models import Product, Category

    if Product.query.first():
        return

    products_data = [
        {'name': 'Neon Valkyrie Wings', 'slug': 'neon-valkyrie-wings', 'description': 'Legendary glowing wings with particle trails. Exclusive limited drop.', 'short_description': 'Legendary wings with neon glow', 'category_slug': 'limiteds', 'price_robux': 4999, 'original_price': 9999, 'stock_quantity': 50, 'rarity': 'legendary', 'is_featured': True, 'is_limited': True, 'is_trending': True, 'image_url': 'https://images.unsplash.com/photo-1614732414444-096e6f3d2d96?w=400&h=400&fit=crop', 'tags': 'wings,legendary,neon,limited'},
        {'name': 'Shadow Assassin Hoodie', 'slug': 'shadow-assassin-hoodie', 'description': 'Dark streetwear hoodie with hidden details. Perfect for any avatar.', 'short_description': 'Premium dark streetwear hoodie', 'category_slug': 'hoodies', 'price_robux': 899, 'original_price': 1299, 'stock_quantity': 200, 'rarity': 'rare', 'is_featured': True, 'is_new': True, 'image_url': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=400&h=400&fit=crop', 'tags': 'hoodie,streetwear,dark'},
        {'name': 'Crystal Crown of Legends', 'slug': 'crystal-crown-legends', 'description': 'Shimmering crystal crown that grants prestige. Mythic rarity item.', 'short_description': 'Mythic crystal crown', 'category_slug': 'accessories', 'price_robux': 2999, 'original_price': 4999, 'stock_quantity': 25, 'rarity': 'mythic', 'is_featured': True, 'is_limited': True, 'image_url': 'https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=400&h=400&fit=crop', 'tags': 'crown,crystal,mythic,accessory'},
        {'name': 'Cyber Ninja Bundle', 'slug': 'cyber-ninja-bundle', 'description': 'Complete cyber ninja outfit with mask, armor, and katana back accessory.', 'short_description': 'Full cyber ninja set', 'category_slug': 'bundles', 'price_robux': 2499, 'original_price': 3999, 'stock_quantity': 100, 'rarity': 'epic', 'is_featured': True, 'is_new': True, 'image_url': 'https://images.unsplash.com/photo-1563089145-599997674d42?w=400&h=400&fit=crop', 'tags': 'ninja,bundle,cyber,outfit'},
        {'name': 'Premium VIP Gamepass', 'slug': 'premium-vip-gamepass', 'description': 'Lifetime VIP access with exclusive areas, 2x rewards, and special badge.', 'short_description': 'Lifetime VIP gamepass', 'category_slug': 'gamepasses', 'price_robux': 1499, 'original_price': 2999, 'stock_quantity': 999, 'rarity': 'epic', 'product_type': 'gamepass', 'image_url': 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=400&h=400&fit=crop', 'tags': 'vip,gamepass,premium'},
        {'name': 'Retro Pixel Shades', 'slug': 'retro-pixel-shades', 'description': '8-bit pixel sunglasses with animated frames. Nostalgic and cool.', 'short_description': 'Animated pixel sunglasses', 'category_slug': 'accessories', 'price_robux': 399, 'original_price': 599, 'stock_quantity': 500, 'rarity': 'uncommon', 'is_new': True, 'image_url': 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&h=400&fit=crop', 'tags': 'glasses,pixel,retro'},
        {'name': 'Dragon Slayer Outfit', 'slug': 'dragon-slayer-outfit', 'description': 'Epic armor set forged for dragon slayers. Includes chest plate, helm, and boots.', 'short_description': 'Epic dragon slayer armor', 'category_slug': 'outfits', 'price_robux': 1899, 'original_price': 2499, 'stock_quantity': 75, 'rarity': 'epic', 'is_trending': True, 'image_url': 'https://images.unsplash.com/photo-1519074069444-1ba4fff66d16?w=400&h=400&fit=crop', 'tags': 'armor,outfit,dragon,epic'},
        {'name': 'Mystery Legend Box', 'slug': 'mystery-legend-box', 'description': 'Contains a random legendary item. Could be wings, crown, or exclusive gear!', 'short_description': 'Random legendary item drop', 'category_slug': 'mystery-boxes', 'price_robux': 999, 'original_price': 1999, 'stock_quantity': 500, 'rarity': 'legendary', 'product_type': 'bundle', 'is_featured': True, 'image_url': 'https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=400&h=400&fit=crop', 'tags': 'mystery,box,legendary,surprise'},
        {'name': 'Galaxy Aura Effect', 'slug': 'galaxy-aura-effect', 'description': 'Surround your avatar with a swirling galaxy aura. Cosmetic effect.', 'short_description': 'Swirling galaxy aura', 'category_slug': 'cosmetics', 'price_robux': 799, 'original_price': 1199, 'stock_quantity': 300, 'rarity': 'rare', 'product_type': 'digital', 'image_url': 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=400&h=400&fit=crop', 'tags': 'aura,cosmetic,galaxy,effect'},
        {'name': 'Streetwear Starter Pack', 'slug': 'streetwear-starter-pack', 'description': 'Everything you need to start drippin: hoodie, cargo pants, sneakers, and cap.', 'short_description': 'Complete streetwear set', 'category_slug': 'bundles', 'price_robux': 1299, 'original_price': 1999, 'stock_quantity': 150, 'rarity': 'uncommon', 'is_new': True, 'image_url': 'https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=400&h=400&fit=crop', 'tags': 'streetwear,bundle,starter'},
        {'name': 'Phantom Mask', 'slug': 'phantom-mask', 'description': 'Mysterious phantom mask with glowing eye slits. Perfect for stealthy avatars.', 'short_description': 'Glowing phantom mask', 'category_slug': 'accessories', 'price_robux': 599, 'stock_quantity': 200, 'rarity': 'rare', 'is_trending': True, 'image_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop', 'tags': 'mask,phantom,glow'},
        {'name': 'Drip Kicks Pro', 'slug': 'drip-kicks-pro', 'description': 'Limited edition sneakers with custom colors and particle effects when walking.', 'short_description': 'LE sneakers with effects', 'category_slug': 'avatar-items', 'price_robux': 1599, 'original_price': 2299, 'stock_quantity': 60, 'rarity': 'epic', 'is_limited': True, 'image_url': 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=400&fit=crop', 'tags': 'shoes,sneakers,limited,effects'},
    ]

    for pd in products_data:
        cat = Category.query.filter_by(slug=pd.pop('category_slug')).first()
        if cat:
            p = Product(category_id=cat.id, **pd)
            db.session.add(p)

    db.session.commit()
    print(f"   Created {len(products_data)} default products")


def create_default_site_config():
    from models import SiteConfig

    defaults = [
        ('site_name', 'DripBux', 'Website name'),
        ('maintenance_mode', 'false', 'Maintenance mode on/off'),
        ('flash_sale_enabled', 'true', 'Enable flash sales'),
        ('max_cart_items', '50', 'Maximum items in cart'),
        ('featured_seller_id', '', 'Currently featured seller'),
    ]
    for key, value, desc in defaults:
        if not SiteConfig.query.filter_by(key=key).first():
            db.session.add(SiteConfig(key=key, value=value, description=desc))
    db.session.commit()


def ensure_review_schema():
    """Adds missing review columns to an existing SQLite reviews table."""
    inspector = inspect(db.engine)
    if 'reviews' not in inspector.get_table_names():
        return

    existing_columns = {col['name'] for col in inspector.get_columns('reviews')}
    alter_statements = []

    if 'is_verified_purchase' not in existing_columns:
        alter_statements.append("ALTER TABLE reviews ADD COLUMN is_verified_purchase BOOLEAN DEFAULT 0")
    if 'is_hidden' not in existing_columns:
        alter_statements.append("ALTER TABLE reviews ADD COLUMN is_hidden BOOLEAN DEFAULT 0")
    if 'helpful_count' not in existing_columns:
        alter_statements.append("ALTER TABLE reviews ADD COLUMN helpful_count INTEGER DEFAULT 0")
    if 'seller_reply' not in existing_columns:
        alter_statements.append("ALTER TABLE reviews ADD COLUMN seller_reply TEXT")
    if 'seller_reply_at' not in existing_columns:
        alter_statements.append("ALTER TABLE reviews ADD COLUMN seller_reply_at DATETIME")
    if 'images' not in existing_columns:
        alter_statements.append("ALTER TABLE reviews ADD COLUMN images JSON DEFAULT '[]'")

    for stmt in alter_statements:
        db.session.execute(text(stmt))

    if alter_statements:
        db.session.commit()


from datetime import datetime
app = create_app()

if __name__ == '__main__':
    print(f"   Starting {AppConfig.APP_NAME} v{AppConfig.APP_VERSION}...")
    app.run(host=AppConfig.HOST, port=AppConfig.PORT, debug=AppConfig.DEBUG)
