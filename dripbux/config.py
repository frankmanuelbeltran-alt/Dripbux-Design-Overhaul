"""
DripBux Complete Overhaul Configuration
========================================
Full e-commerce marketplace configuration.
"""

import os


class ThemeConfig:
    """Dark futuristic + pink neon gaming theme"""

    # Primary Pink Palette
    PRIMARY = "#ff4d8d"
    PRIMARY_LIGHT = "#ff80ab"
    PRIMARY_DARK = "#e91e63"
    PINK_GLOW = "#ff6b9d"

    # Dark Base Colors
    DARK_BG = "#0a0a0f"
    DARK_CARD = "#14141f"
    DARK_ELEVATED = "#1e1e2d"
    DARK_BORDER = "#2a2a3d"

    # Gradient Definitions
    HERO_GRADIENT = "linear-gradient(135deg, #0a0a0f 0%, #150a15 50%, #1f0f1f 100%)"
    PINK_GRADIENT = "linear-gradient(135deg, #ff4d8d 0%, #ff80ab 50%, #ff6b9d 100%)"
    GLOW_GRADIENT = "radial-gradient(ellipse at center, rgba(255,77,141,0.15) 0%, transparent 70%)"
    CARD_GRADIENT = "linear-gradient(145deg, rgba(20,20,31,0.95) 0%, rgba(10,10,15,0.98) 100%)"

    # Accent Colors
    ACCENT_GOLD = "#ffd700"
    ACCENT_PURPLE = "#9d4edd"
    ACCENT_CYAN = "#00d9ff"
    ACCENT_GREEN = "#00e676"

    # Text Colors
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a0a0b8"
    TEXT_MUTED = "#6a6a80"
    TEXT_PINK = "#ff80ab"

    # Status Colors
    SUCCESS = "#00e676"
    ERROR = "#ff1744"
    WARNING = "#ffc400"
    INFO = "#00b0ff"

    # Glassmorphism
    GLASS_BG = "rgba(20,20,31,0.75)"
    GLASS_BORDER = "rgba(255,77,141,0.2)"
    GLASS_BLUR = "20px"

    # Typography
    FONT_FAMILY = "'Poppins','Inter',-apple-system,BlinkMacSystemFont,sans-serif"
    FONT_HEADING = "'Poppins',sans-serif"
    FONT_BODY = "'Inter',sans-serif"

    # Spacing & Radius
    RADIUS_SM = "8px"
    RADIUS_MD = "12px"
    RADIUS_LG = "20px"
    RADIUS_XL = "28px"
    RADIUS_FULL = "9999px"

    # Shadows
    SHADOW_PINK = "0 0 30px rgba(255,77,141,0.4)"
    SHADOW_PINK_HOVER = "0 0 50px rgba(255,77,141,0.6)"
    SHADOW_CARD = "0 8px 32px rgba(0,0,0,0.4)"
    SHADOW_ELEVATED = "0 20px 60px rgba(0,0,0,0.5)"

    # Rarity Colors
    RARITY_COMMON = "#a0a0b8"
    RARITY_UNCOMMON = "#00e676"
    RARITY_RARE = "#00b0ff"
    RARITY_EPIC = "#9d4edd"
    RARITY_LEGENDARY = "#ffd700"
    RARITY_MYTHIC = "#ff4d8d"


class IconConfig:
    """Lucide icon mapping"""
    CDN = "https://unpkg.com/lucide@latest"
    ICONS = {
        'home': 'home',
        'shop': 'shopping-bag',
        'search': 'search',
        'menu': 'menu',
        'close': 'x',
        'arrow_right': 'arrow-right',
        'arrow_left': 'arrow-left',
        'chevron_down': 'chevron-down',
        'chevron_up': 'chevron-up',
        'user': 'user',
        'profile': 'user-circle',
        'login': 'log-in',
        'logout': 'log-out',
        'register': 'user-plus',
        'settings': 'settings',
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
        'dashboard': 'layout-dashboard',
        'users': 'users',
        'analytics': 'bar-chart-3',
        'edit': 'pencil',
        'delete': 'trash-2',
        'add': 'plus-circle',
        'save': 'save',
        'view': 'eye',
        'image': 'image',
        'success': 'check-circle',
        'error': 'alert-circle',
        'warning': 'alert-triangle',
        'info': 'info',
        'pending': 'clock',
        'delivered': 'check-check',
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
        'bell': 'bell',
        'store': 'store',
        'message': 'message-circle',
        'share': 'share-2',
        'gift': 'gift',
        'ticket': 'ticket',
        'clock': 'clock',
        'eye': 'eye',
        'download': 'download',
        'upload': 'upload',
        'verified': 'badge-check',
    }


class DatabaseConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dripbux.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}


class SecurityConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dripbux-secret-key-2024-complete-overhaul')
    PASSWORD_HASH_METHOD = 'pbkdf2:sha256:600000'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600


class OAuthConfig:
    """Google OAuth configuration"""
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
    GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'


class UploadConfig:
    UPLOAD_FOLDER = 'static/images/products'
    AVATAR_FOLDER = 'static/images/avatars'
    SELLER_FOLDER = 'static/images/sellers'
    CATEGORY_FOLDER = 'static/images/categories'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    MAX_IMAGE_SIZE = (1200, 1200)
    THUMBNAIL_SIZE = (400, 400)


class FeatureConfig:
    STARTING_ROBUX_BALANCE = 10000
    USER_REGISTRATION_ENABLED = True
    WISHLIST_ENABLED = True
    REVIEWS_ENABLED = True
    LIVE_SEARCH_ENABLED = True
    STANDARD_SHIPPING_FEE = 0
    EXPRESS_SHIPPING_FEE = 199
    EXPRESS_SHIPPING_DAYS = 2
    STANDARD_SHIPPING_DAYS = 5
    LOW_STOCK_THRESHOLD = 5
    FLASH_SALE_DURATION_HOURS = 24
    TRENDING_VIEWS_WEIGHT = 1
    TRENDING_SALES_WEIGHT = 3


class AppConfig:
    APP_NAME = "DripBux"
    APP_VERSION = "4.0.0"
    APP_TAGLINE = "The Ultimate Roblox Marketplace"
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    SECRET_KEY = SecurityConfig.SECRET_KEY
    SQLALCHEMY_DATABASE_URI = DatabaseConfig.SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = DatabaseConfig.SQLALCHEMY_TRACK_MODIFICATIONS
    SQLALCHEMY_ENGINE_OPTIONS = DatabaseConfig.SQLALCHEMY_ENGINE_OPTIONS
    UPLOAD_FOLDER = UploadConfig.UPLOAD_FOLDER
    MAX_CONTENT_LENGTH = UploadConfig.MAX_CONTENT_LENGTH
    WTF_CSRF_ENABLED = SecurityConfig.WTF_CSRF_ENABLED


class AdminConfig:
    DEFAULT_ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@dripbux.com')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    DEFAULT_ADMIN_ROBUX = 9999999


class SellerConfig:
    SELLER_APPLICATION_FEE = 0
    SELLER_COMMISSION_PERCENT = 5
    MIN_PAYOUT_ROBUX = 1000
