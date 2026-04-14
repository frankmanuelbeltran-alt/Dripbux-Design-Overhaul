"""
DripBux Premium - Sample Data Seeder
====================================
Populate the database with sample products and data.
"""

from app import app
from extensions import db
from models import Category, Product, ProductSize, User
from werkzeug.security import generate_password_hash
import random

# Sample product data
SAMPLE_PRODUCTS = [
    {
        'name': 'Neon Pink Oversized Hoodie',
        'description': 'Make a statement with this vibrant neon pink oversized hoodie. Features premium cotton blend, kangaroo pocket, and ribbed cuffs. Perfect for standing out in the crowd.',
        'short_description': 'Vibrant oversized hoodie with premium comfort',
        'category': 'hoodies',
        'price_robux': 899,
        'original_price': 1199,
        'is_featured': True,
        'is_new': True,
        'sizes': {'XS': 5, 'S': 10, 'M': 15, 'L': 12, 'XL': 8, 'XXL': 5}
    },
    {
        'name': 'Cyber Street Cargo Pants',
        'description': 'Techwear-inspired cargo pants with multiple pockets, adjustable straps, and water-resistant fabric. The ultimate blend of style and functionality.',
        'short_description': 'Techwear cargo pants with multiple pockets',
        'category': 'pants',
        'price_robux': 749,
        'is_featured': True,
        'sizes': {'S': 8, 'M': 12, 'L': 15, 'XL': 10, 'XXL': 6}
    },
    {
        'name': 'DripBux Logo Tee',
        'description': 'Classic DripBux logo t-shirt in premium cotton. Features our signature pink glow print on the chest. A must-have for any fan.',
        'short_description': 'Classic logo tee with signature glow print',
        'category': 't-shirts',
        'price_robux': 399,
        'original_price': 499,
        'is_new': True,
        'sizes': {'XS': 10, 'S': 20, 'M': 25, 'L': 20, 'XL': 15, 'XXL': 10, '3XL': 5}
    },
    {
        'name': 'Midnight Reflective Jacket',
        'description': 'Stand out at night with this reflective streetwear jacket. Features 3M reflective strips, hidden hood, and premium zippers.',
        'short_description': 'Reflective jacket with 3M strips',
        'category': 'jackets',
        'price_robux': 1299,
        'is_featured': True,
        'sizes': {'S': 5, 'M': 8, 'L': 10, 'XL': 7, 'XXL': 4}
    },
    {
        'name': 'Robux Chain Necklace',
        'description': 'Premium stainless steel chain with Robux coin pendant. Water-resistant and tarnish-free. The perfect accessory for any outfit.',
        'short_description': 'Stainless steel chain with Robux pendant',
        'category': 'accessories',
        'price_robux': 599,
        'is_new': True,
        'sizes': {'One Size': 50}
    },
    {
        'name': 'Limited Edition Drip Cap',
        'description': 'Limited edition embroidered cap with adjustable strap. Only 100 pieces available worldwide.',
        'short_description': 'Limited edition embroidered cap',
        'category': 'accessories',
        'price_robux': 449,
        'original_price': 599,
        'sizes': {'One Size': 25}
    },
    {
        'name': 'Hype Beast Sneaker Socks',
        'description': 'Premium cotton socks with cushioned sole and arch support. Features bold designs that pop with your sneakers.',
        'short_description': 'Premium cushioned socks with bold designs',
        'category': 'accessories',
        'price_robux': 149,
        'sizes': {'One Size': 100}
    },
    {
        'name': 'Shadow Black Hoodie',
        'description': 'Minimalist black hoodie with subtle DripBux branding on the sleeve. Premium heavyweight cotton for maximum comfort.',
        'short_description': 'Minimalist black hoodie with subtle branding',
        'category': 'hoodies',
        'price_robux': 799,
        'sizes': {'XS': 8, 'S': 15, 'M': 20, 'L': 18, 'XL': 12, 'XXL': 8}
    },
    {
        'name': 'Pixel Art Graphic Tee',
        'description': 'Retro pixel art design on premium cotton. Features a unique 8-bit inspired graphic that gamers will love.',
        'short_description': 'Retro pixel art graphic tee',
        'category': 't-shirts',
        'price_robux': 449,
        'is_new': True,
        'sizes': {'XS': 5, 'S': 12, 'M': 18, 'L': 15, 'XL': 10, 'XXL': 6}
    },
    {
        'name': 'Street Legend Bomber Jacket',
        'description': 'Classic bomber jacket with modern streetwear twist. Features embroidered patches, ribbed trim, and quilted lining.',
        'short_description': 'Classic bomber with embroidered patches',
        'category': 'jackets',
        'price_robux': 1499,
        'original_price': 1799,
        'is_featured': True,
        'sizes': {'S': 6, 'M': 10, 'L': 12, 'XL': 8, 'XXL': 4}
    },
    {
        'name': 'Neon Nights Joggers',
        'description': 'Comfortable joggers with neon pink side stripes. Perfect for lounging or hitting the streets.',
        'short_description': 'Joggers with neon pink side stripes',
        'category': 'pants',
        'price_robux': 549,
        'is_new': True,
        'sizes': {'XS': 6, 'S': 10, 'M': 15, 'L': 12, 'XL': 8, 'XXL': 5}
    },
    {
        'name': 'DripBux Backpack',
        'description': 'Spacious backpack with laptop compartment, multiple pockets, and water-resistant material. Features our signature pink accents.',
        'short_description': 'Spacious backpack with laptop compartment',
        'category': 'accessories',
        'price_robux': 899,
        'sizes': {'One Size': 30}
    },
    {
        'name': 'Limited Drop: Pink Flame Tee',
        'description': 'Ultra limited edition tee with pink flame design. Only available for 48 hours.',
        'short_description': 'Ultra limited pink flame design',
        'category': 'limited-edition',
        'price_robux': 699,
        'is_featured': True,
        'is_new': True,
        'sizes': {'S': 5, 'M': 8, 'L': 5, 'XL': 3}
    },
    {
        'name': 'Urban Camo Cargo Shorts',
        'description': 'Urban camo cargo shorts with multiple pockets. Perfect for summer streetwear looks.',
        'short_description': 'Urban camo cargo shorts',
        'category': 'pants',
        'price_robux': 449,
        'sizes': {'S': 8, 'M': 12, 'L': 15, 'XL': 10, 'XXL': 6}
    },
    {
        'name': 'Signature Pink Beanie',
        'description': 'Warm knit beanie in signature DripBux pink. Features embroidered logo and fold-over cuff.',
        'short_description': 'Warm knit beanie in signature pink',
        'category': 'accessories',
        'price_robux': 299,
        'sizes': {'One Size': 40}
    }
]


def slugify(name):
    """Convert name to slug"""
    return name.lower().replace(' ', '-').replace(':', '').replace('(', '').replace(')', '')


def seed_database():
    """Seed the database with sample data"""
    with app.app_context():
        print("🌱 Seeding database...")
        
        # Get categories
        categories = {cat.slug: cat for cat in Category.query.all()}
        
        if not categories:
            print("❌ No categories found. Please run the app first to create default categories.")
            return
        
        products_created = 0
        
        for product_data in SAMPLE_PRODUCTS:
            # Check if product already exists
            slug = slugify(product_data['name'])
            existing = Product.query.filter_by(slug=slug).first()
            if existing:
                print(f"  ⚠️  Product '{product_data['name']}' already exists, skipping...")
                continue
            
            # Get category
            category_slug = product_data['category']
            category = categories.get(category_slug)
            if not category:
                print(f"  ⚠️  Category '{category_slug}' not found, skipping...")
                continue
            
            # Create product
            product = Product(
                name=product_data['name'],
                slug=slug,
                description=product_data['description'],
                short_description=product_data.get('short_description', ''),
                category_id=category.id,
                price_robux=product_data['price_robux'],
                original_price=product_data.get('original_price'),
                is_active=True,
                is_featured=product_data.get('is_featured', False),
                is_new=product_data.get('is_new', False)
            )
            db.session.add(product)
            db.session.flush()  # Get product ID
            
            # Create size variants
            for size, stock in product_data['sizes'].items():
                product_size = ProductSize(
                    product_id=product.id,
                    size=size,
                    stock=stock,
                    price_modifier=0
                )
                db.session.add(product_size)
            
            products_created += 1
            print(f"  ✅ Created: {product_data['name']}")
        
        db.session.commit()
        print(f"\n✅ Successfully created {products_created} products!")
        
        # Create sample user
        sample_user = User.query.filter_by(username='demo').first()
        if not sample_user:
            demo_user = User(
                username='demo',
                email='demo@dripbux.com',
                password_hash=generate_password_hash('demo123'),
                robux_balance=50000,
                is_admin=False
            )
            db.session.add(demo_user)
            db.session.commit()
            print("\n✅ Created demo user:")
            print("   Username: demo")
            print("   Password: demo123")
            print("   Balance: 50,000 Robux")


if __name__ == '__main__':
    seed_database()
