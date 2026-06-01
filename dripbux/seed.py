#!/usr/bin/env python3
"""
DripBux Database Seeder
Run: python seed.py
"""

from app import app, db
from models import User, Category, Product, Cart, SiteConfig
from werkzeug.security import generate_password_hash

def seed():
    with app.app_context():
        print(" Seeding database...")

        # Create admin if not exists
        admin = User.query.filter_by(email='admin@dripbux.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@dripbux.com',
                password_hash=generate_password_hash('admin123'),
                robux_balance=9999999,
                role='admin',
                is_active=True,
                email_verified=True
            )
            db.session.add(admin)
            print("   Created admin: admin@dripbux.com / admin123")

        # Create demo customer
        customer = User.query.filter_by(email='demo@dripbux.com').first()
        if not customer:
            customer = User(
                username='demouser',
                email='demo@dripbux.com',
                password_hash=generate_password_hash('demo123'),
                robux_balance=5000,
                role='customer',
                is_active=True,
                email_verified=True
            )
            db.session.add(customer)
            cart = Cart(user_id=customer.id)
            db.session.add(cart)
            print("   Created demo user: demo@dripbux.com / demo123")

        db.session.commit()
        print(" Done!")

if __name__ == '__main__':
    seed()
