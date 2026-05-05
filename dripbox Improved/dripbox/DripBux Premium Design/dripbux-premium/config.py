"""
DripBux Premium Configuration
=============================
Pink luxury theme configuration for the ultimate streetwear marketplace.
"""

import os

# =============================================================================
# PINK LUXURY THEME CONFIGURATION
# =============================================================================

class ThemeConfig:
    """Premium pink luxury theme colors and styling"""
    
    # Primary Pink Palette
    PRIMARY = "#ff4d8d"           # Hot pink - main brand color
    PRIMARY_LIGHT = "#ff80ab"     # Light pink - accents
    PRIMARY_DARK = "#e91e63"      # Dark pink - hover states
    PINK_GLOW = "#ff6b9d"         # Neon pink glow
    
    # Dark Base Colors
    DARK_BG = "#0f0f14"           # Deep dark background
    DARK_CARD = "#1a1a24"         # Card background
    DARK_ELEVATED = "#252532"     # Elevated surfaces
    DARK_BORDER = "#2a2a3a"       # Subtle borders
    
    # Gradient Definitions
    HERO_GRADIENT = "linear-gradient(135deg, #0f0f14 0%, #1a0a1a 50%, #2d1a2d 100%)"
    PINK_GRADIENT = "linear-gradient(135deg, #ff4d8d 0%, #ff80ab 50%, #ff6b9d 100%)"
    GLOW_GRADIENT = "radial-gradient(ellipse at center, rgba(255, 77, 141, 0.15) 0%, transparent 70%)"
    CARD_GRADIENT = "linear-gradient(145deg, rgba(26, 26, 36, 0.9) 0%, rgba(15, 15, 20, 0.95) 100%)"
    
    # Accent Colors
    ACCENT_GOLD = "#ffd700"       # Gold accents
    ACCENT_PURPLE = "#9d4edd"     # Purple accent
    ACCENT_CYAN = "#00d9ff"       # Cyan accent for contrast
    
    # Text Colors
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a0a0b0"
    TEXT_MUTED = "#6a6a7a"
    TEXT_PINK = "#ff80ab"
    
    # Status Colors
    SUCCESS = "#00e676"
    ERROR = "#ff1744"
    WARNING = "#ffc400"
    INFO = "#00b0ff"
    
    # Glassmorphism
    GLASS_BG = "rgba(26, 26, 36, 0.7)"
    GLASS_BORDER = "rgba(255, 77, 141, 0.2)"
    GLASS_BLUR = "20px"
    
    # Typography
    FONT_FAMILY = "'Poppins', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
    FONT_HEADING = "'Poppins', sans-serif"
    FONT_BODY = "'Inter', sans-serif"
    
    # Spacing & Radius
    RADIUS_SM = "8px"
    RADIUS_MD = "12px"
    RADIUS_LG = "20px"
    RADIUS_XL = "28px"
    RADIUS_FULL = "9999px"
    
    # Shadows
    SHADOW_PINK = "0 0 30px rgba(255, 77, 141, 0.4)"
    SHADOW_PINK_HOVER = "0 0 50px rgba(255, 77, 141, 0.6)"
    SHADOW_CARD = "0 8px 32px rgba(0, 0, 0, 0.4)"
    SHADOW_ELEVATED = "0 20px 60px rgba(0, 0, 0, 0.5)"


class IconConfig:
    """Lucide icon configuration"""
    
    CDN = "https://unpkg.com/lucide@latest"
    
    ICONS = {
        # Navigation
        'home': 'home',
        'shop': 'shopping-bag',
        'search': 'search',
        'menu': 'menu',
        'close': 'x',
        'arrow_right': 'arrow-right',
        'arrow_left': 'arrow-left',
        'chevron_down': 'chevron-down',
        'chevron_up': 'chevron-up',
        
        # User
        'user': 'user',
        'profile': 'user-circle',
        'login': 'log-in',
        'logout': 'log-out',
        'register': 'user-plus',
        'settings': 'settings',
        
        # Shopping
        'cart': 'shopping-cart',
        'wishlist': 'heart',
        'orders': 'package',
        'checkout': 'credit-card',
        'payment': 'wallet',
        'shipping': 'truck',
        'delivery': 'map-pin',
        'trash': 'trash-2',
        'plus': 'plus',
        'minus': 'minus',
        
        # Products
        'product': 'box',
        'category': 'tags',
        'price': 'tag',
        'stock': 'layers',
        'size': 'ruler',
        'color': 'palette',
        'star': 'star',
        'star_half': 'star-half',
        'filter': 'sliders-horizontal',
        'sort': 'arrow-up-down',
        
        # Admin
        'dashboard': 'layout-dashboard',
        'users': 'users',
        'analytics': 'bar-chart-3',
        'edit': 'pencil',
        'delete': 'trash-2',
        'add': 'plus-circle',
        'save': 'save',
        'view': 'eye',
        'image': 'image',
        
        # Status
        'success': 'check-circle',
        'error': 'alert-circle',
        'warning': 'alert-triangle',
        'info': 'info',
        'pending': 'clock',
        'delivered': 'check-check',
        
        # Misc
        'robux': 'coins',
        'phone': 'phone',
        'email': 'mail',
        'location': 'map-pin',
        'calendar': 'calendar',
        'grid': 'layout-grid',
        'list': 'list',
        'moon': 'moon',
        'sun': 'sun',
        'sparkles': 'sparkles',
        'zap': 'zap',
        'trending': 'trending-up',
        'fire': 'flame',
    }


# =============================================================================
# BACKEND CONFIGURATION
# =============================================================================

class DatabaseConfig:
    """Database settings"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dripbux.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class SecurityConfig:
    """Security settings"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dripbux-premium-secret-key-2024-pink-luxury')
    PASSWORD_HASH_METHOD = 'pbkdf2:sha256:600000'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600


class UploadConfig:
    """File upload settings"""
    UPLOAD_FOLDER = 'static/images/products'
    AVATAR_FOLDER = 'static/images/avatars'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    MAX_IMAGE_SIZE = (1200, 1200)
    THUMBNAIL_SIZE = (400, 400)


# =============================================================================
# FEATURE CONFIGURATION
# =============================================================================

class FeatureConfig:
    """Feature toggles"""
    
    # User Features
    STARTING_ROBUX_BALANCE = 10000
    USER_REGISTRATION_ENABLED = True
    
    # Shop Features
    WISHLIST_ENABLED = True
    REVIEWS_ENABLED = True
    LIVE_SEARCH_ENABLED = True
    
    # Checkout
    STANDARD_SHIPPING_FEE = 0
    EXPRESS_SHIPPING_FEE = 199
    EXPRESS_SHIPPING_DAYS = 2
    STANDARD_SHIPPING_DAYS = 5
    
    # Admin
    LOW_STOCK_THRESHOLD = 5


# =============================================================================
# APP CONFIGURATION
# =============================================================================

class AppConfig:
    """Main Flask configuration"""
    
    APP_NAME = "DripBux"
    APP_VERSION = "3.0.0"
    APP_TAGLINE = "Premium Streetwear. Robux Powered."
    
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    SECRET_KEY = SecurityConfig.SECRET_KEY
    SQLALCHEMY_DATABASE_URI = DatabaseConfig.SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = DatabaseConfig.SQLALCHEMY_TRACK_MODIFICATIONS
    UPLOAD_FOLDER = UploadConfig.UPLOAD_FOLDER
    MAX_CONTENT_LENGTH = UploadConfig.MAX_CONTENT_LENGTH
    WTF_CSRF_ENABLED = SecurityConfig.WTF_CSRF_ENABLED


class AdminConfig:
    """Default admin credentials"""
    DEFAULT_ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    DEFAULT_ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@dripbux.com')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    DEFAULT_ADMIN_ROBUX = 9999999
