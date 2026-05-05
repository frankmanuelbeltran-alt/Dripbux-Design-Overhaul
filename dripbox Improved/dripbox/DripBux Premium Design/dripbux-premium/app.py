"""
DripBux Premium - Flask Application Factory
============================================
The ultimate streetwear marketplace powered by Robux.
Pink luxury theme with glassmorphism design.
"""

from flask import Flask, render_template, request
from extensions import db, login_manager, migrate, csrf
from config import AppConfig, AdminConfig, ThemeConfig, FeatureConfig, IconConfig
import os


def create_app():
    """Application factory pattern for creating Flask app instance"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(AppConfig)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Import models for user loader
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
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(shop_bp, url_prefix='/shop')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(checkout_bp, url_prefix='/checkout')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create upload directories
    upload_folders = [
        os.path.join(app.root_path, 'static/images/products'),
        os.path.join(app.root_path, 'static/images/avatars'),
        os.path.join(app.root_path, 'static/images/categories'),
    ]
    for folder in upload_folders:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            print(f" Created directory: {folder}")
    
    # Create database tables and default data
    with app.app_context():
        db.create_all()
        create_default_admin()
        create_default_categories()
        print(" Database initialized successfully!")
    
    # Global template context processor
    @app.context_processor
    def inject_globals():
        """Make config available in all templates"""
        from models import Category, Cart
        
        # Get cart count for navbar
        cart_count = 0
        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            cart_count = request.user.get_cart_count()
        
        # Get all categories for navbar
        categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
        
        return {
            'theme': ThemeConfig,
            'icons': IconConfig,
            'features': FeatureConfig,
            'app_name': AppConfig.APP_NAME,
            'app_version': AppConfig.APP_VERSION,
            'app_tagline': AppConfig.APP_TAGLINE,
            'categories': categories,
            'cart_count': cart_count,
        }
    
    # Before request - set user for context processor
    @app.before_request
    def before_request():
        from flask_login import current_user
        request.user = current_user
    
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
        """Format Robux amount with commas"""
        if value is None:
            return '0'
        return f'{int(value):,}'
    
    @app.template_filter('format_price')
    def format_price(value):
        """Format price with Robux symbol"""
        if value is None:
            return '<span class="robux-amount">0 <i data-lucide="coins" class="inline-icon"></i></span>'
        return f'<span class="robux-amount">{int(value):,} <i data-lucide="coins" class="inline-icon"></i></span>'
    
    @app.template_filter('truncate_words')
    def truncate_words(s, num=20):
        """Truncate text to specified number of words"""
        words = s.split()
        if len(words) > num:
            return ' '.join(words[:num]) + '...'
        return s
    
    return app


def create_default_admin():
    """Create default admin user if it doesn't exist"""
    from models import User
    from werkzeug.security import generate_password_hash
    
    admin = User.query.filter_by(username=AdminConfig.DEFAULT_ADMIN_USERNAME).first()
    if not admin:
        admin = User(
            username=AdminConfig.DEFAULT_ADMIN_USERNAME,
            email=AdminConfig.DEFAULT_ADMIN_EMAIL,
            password_hash=generate_password_hash(AdminConfig.DEFAULT_ADMIN_PASSWORD),
            robux_balance=AdminConfig.DEFAULT_ADMIN_ROBUX,
            is_admin=True,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"   Admin user created: {AdminConfig.DEFAULT_ADMIN_USERNAME}")
        print(f"   Email: {AdminConfig.DEFAULT_ADMIN_EMAIL}")
        print(f"   Password: {AdminConfig.DEFAULT_ADMIN_PASSWORD}")


def create_default_categories():
    """Create default product categories"""
    from models import Category
    
    default_categories = [
        {'name': 'T-Shirts', 'slug': 't-shirts', 'description': 'Premium streetwear tees', 'display_order': 1},
        {'name': 'Hoodies', 'slug': 'hoodies', 'description': 'Cozy and stylish hoodies', 'display_order': 2},
        {'name': 'Jackets', 'slug': 'jackets', 'description': 'Outerwear for any season', 'display_order': 3},
        {'name': 'Pants', 'slug': 'pants', 'description': 'Streetwear bottoms', 'display_order': 4},
        {'name': 'Accessories', 'slug': 'accessories', 'description': 'Complete your look', 'display_order': 5},
        {'name': 'Limited Edition', 'slug': 'limited-edition', 'description': 'Exclusive drops', 'display_order': 6},
    ]
    
    for cat_data in default_categories:
        existing = Category.query.filter_by(slug=cat_data['slug']).first()
        if not existing:
            category = Category(**cat_data)
            db.session.add(category)
    
    db.session.commit()


# Create the application instance
app = create_app()

if __name__ == '__main__':
    print(f"   Starting {AppConfig.APP_NAME} v{AppConfig.APP_VERSION}...")
    print(f"   Debug mode: {AppConfig.DEBUG}")
    print(f"   Database: {AppConfig.SQLALCHEMY_DATABASE_URI}")
    print(f"   Theme: Pink Luxury")
    app.run(
        host=AppConfig.HOST,
        port=AppConfig.PORT,
        debug=AppConfig.DEBUG
    )
