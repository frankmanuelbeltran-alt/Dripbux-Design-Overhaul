"""
DripBux Main Routes
===================
Homepage, static pages, contact, FAQ, etc.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from models import Product, Category, Order, User, Seller, Announcement, Review
from extensions import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage with hero, featured products, and sections"""
    # Featured products
    featured = Product.query.filter_by(is_active=True, is_featured=True).limit(8).all()
    # New arrivals
    new_arrivals = Product.query.filter_by(is_active=True, is_new=True).order_by(Product.created_at.desc()).limit(8).all()
    # Trending
    trending = Product.query.filter_by(is_active=True, is_trending=True).order_by(Product.sales_count.desc()).limit(8).all()
    # Flash sales
    flash_sales = Product.query.filter_by(is_active=True, is_flash_sale=True).limit(4).all()
    # Best sellers
    best_sellers = Product.query.filter_by(is_active=True).order_by(Product.sales_count.desc()).limit(8).all()
    # Categories
    categories = Category.query.filter_by(is_active=True, parent_id=None).order_by(Category.display_order).limit(10).all()
    # Top sellers
    top_sellers = Seller.query.filter_by(is_active=True, verification_status='verified').order_by(Seller.total_sales.desc()).limit(6).all()
    # Stats for hero
    stats = {
        'total_products': Product.query.filter_by(is_active=True).count(),
        'total_users': User.query.count(),
        'total_orders': Order.query.count(),
    }

    return render_template('index.html',
        featured_products=featured,
        new_arrivals=new_arrivals,
        trending_products=trending,
        flash_sales=flash_sales,
        best_sellers=best_sellers,
        categories=categories,
        top_sellers=top_sellers,
        stats=stats
    )


@main_bp.route('/about')
def about():
    stats = {
        'products': Product.query.filter_by(is_active=True).count(),
        'users': User.query.count(),
        'orders': Order.query.count(),
        'sellers': Seller.query.filter_by(verification_status='verified').count(),
    }
    return render_template('about.html', stats=stats)


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    from forms import ContactForm
    form = ContactForm()
    if form.validate_on_submit():
        flash('Message sent! We will get back to you soon.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html', form=form)


@main_bp.route('/faq')
def faq():
    faqs = [
        {'q': 'What is DripBux?', 'a': 'DripBux is the ultimate Roblox-inspired marketplace where you can buy, sell, and trade virtual items using Robux currency.'},
        {'q': 'How do I get Robux?', 'a': 'New accounts start with 10,000 Robux. Admins can add more Robux to your account.'},
        {'q': 'How do I become a seller?', 'a': 'Go to your profile and click "Become a Seller" to apply. Your application will be reviewed by our team.'},
        {'q': 'Can I cancel my order?', 'a': 'Yes, orders can be cancelled while they are in Pending or Processing status. Robux will be refunded.'},
        {'q': 'What are Mystery Boxes?', 'a': 'Mystery Boxes contain random items of varying rarity. Each box guarantees at least one item!'},
        {'q': 'How do flash sales work?', 'a': 'Flash sales are limited-time deals with deep discounts. They last 24 hours or until stock runs out.'},
    ]
    return render_template('faq.html', faqs=faqs)


@main_bp.route('/terms')
def terms():
    return render_template('terms.html')


@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')


@main_bp.route('/seller-guide')
def seller_guide():
    return render_template('seller_guide.html')
