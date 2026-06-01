"""
One-shot helper to create an admin user `ADMIN` with password `Manage123`.

Run this from the project root (or this package) to add the user.
"""
import os
import sys

# Ensure project root (package dir) is on sys.path when running the script directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app
from werkzeug.security import generate_password_hash
from extensions import db
from models import User

USERNAME = 'ADMIN'
PASSWORD = 'Manage123'
DEFAULT_EMAIL = 'admin_manage@dripbux.com'

def main():
    with app.app_context():
        # Ensure unique username/email
        existing = User.query.filter((User.username == USERNAME) | (User.email == DEFAULT_EMAIL)).first()
        if existing:
            if existing.username == USERNAME:
                print(f'User with username "{USERNAME}" already exists: {existing.email}')
                return
            # if email taken, generate alternative
            import time
            email = f'admin_manage+{int(time.time())}@dripbux.com'
        else:
            email = DEFAULT_EMAIL

        user = User(
            username=USERNAME,
            email=email,
            password_hash=generate_password_hash(PASSWORD),
            role=User.ROLE_ADMIN,
            is_active=True,
            email_verified=True,
            auth_provider='local'
        )
        db.session.add(user)
        db.session.commit()
        print(f'Created admin user: {USERNAME} with email {email}')

if __name__ == '__main__':
    main()
