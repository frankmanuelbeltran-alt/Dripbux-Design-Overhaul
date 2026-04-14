"""
DripBux Premium - Main Routes
=============================
Homepage and main pages.
"""

from flask import Blueprint, render_template
from models import Product, Category

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage with hero, featured products, and trending"""
    # Featured products
    featured_products = Product.query.filter_by(
        is_active=True, 
        is_featured=True
    ).limit(8).all()
    
    # New arrivals
    new_arrivals = Product.query.filter_by(
        is_active=True,
        is_new=True
    ).order_by(Product.created_at.desc()).limit(8).all()
    
    # Trending products (by sales)
    trending_products = Product.query.filter_by(
        is_active=True
    ).order_by(Product.sales_count.desc()).limit(8).all()
    
    # All categories for category section
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
    
    return render_template('index.html',
        featured_products=featured_products,
        new_arrivals=new_arrivals,
        trending_products=trending_products,
        categories=categories
    )


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')


@main_bp.route('/faq')
def faq():
    """FAQ page"""
    return render_template('faq.html')


@main_bp.route('/shipping')
def shipping():
    """Shipping information page"""
    return render_template('shipping.html')


@main_bp.route('/returns')
def returns():
    """Returns policy page"""
    return render_template('returns.html')
