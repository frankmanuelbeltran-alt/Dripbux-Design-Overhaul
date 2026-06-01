# DRIPBUX - The Ultimate Roblox Marketplace

A fully functional, production-style e-commerce platform built with Flask, featuring a dark futuristic gaming aesthetic with pink neon accents. All transactions use **ROBUX** currency.

![DripBux](https://img.shields.io/badge/DripBux-v4.0.0-ff4d8d)
![Flask](https://img.shields.io/badge/Flask-3.0.0-000000)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB)

## Features

### Authentication
- Google OAuth 2.0 login (Gmail)
- Username/password registration & login
- Role-based access control (Customer, Seller, Admin)
- Secure session management with CSRF protection
- Profile management with avatar upload

### E-Commerce
- Product catalog with 14 categories
- Product browsing, searching, filtering, sorting
- Shopping cart with quantity management
- Multi-step checkout (Shipping, Review, Payment)
- Coupon/voucher discount system
- Order tracking with status updates
- Wishlist functionality
- Product reviews with verified purchase badges

### Seller Dashboard
- Seller application & verification system
- Product management (CRUD)
- Order management
- Sales analytics
- Voucher creation
- Store customization

### Admin Panel
- Dashboard with statistics
- User management (with Robux addition)
- Seller verification, application review, and a three-strike warning workflow (admin warnings create `SellerWarning` records; strike 2 suspends, strike 3 bans)
- Product moderation
- Order management with status updates
- Category management
- Coupon management
- Announcement system
- Site settings
- Activity logs

### Design
- Dark futuristic theme with pink neon accents
- Animated particle background
- Glassmorphism effects
- Responsive design (Mobile, Tablet, Desktop)
- Smooth animations and hover effects
- Toast notifications
- Loading skeletons

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.10+, Flask 3.0 |
| Database | SQLite (SQLAlchemy ORM) |
| Auth | Flask-Login + Google OAuth 2.0 |
| Forms | Flask-WTF + WTForms |
| Templates | Jinja2 |
| Styling | Custom CSS (dark/pink theme) |
| Icons | Lucide Icons |
| Fonts | Poppins + Inter |

## Installation

### 1. Clone & Navigate

```bash
cd dripbux
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True
DATABASE_URL=sqlite:///dripbux.db
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### 5. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Navigate to **APIs & Services > Credentials**
4. Click **Create Credentials > OAuth client ID**
5. Configure the OAuth consent screen
6. Set Application type to **Web application**
7. Add Authorized redirect URI: `http://localhost:5000/auth/google/callback`
8. Copy the **Client ID** and **Client Secret** to your `.env` file

## Demo Accounts

| Role | Username | Email | Password |
|------|----------|-------|----------|
| Admin | admin | admin@dripbux.com | admin123 |
| Admin (Moderator) | mod | adminmod@dripbux.com | adminmod |
| Customer | demouser | demo@dripbux.com | demo123 |

New users start with **10,000 ROBUX**.

## Database Models

- **users** - Accounts with role-based access
- **sellers** - Store profiles
- **products** - Catalog items with rarity & type
- **categories** - Product categories
- **carts & cart_items** - Shopping cart
- **orders & order_items** - Order management
- **reviews** - Product reviews & ratings
- **wishlists** - User wishlists
- **coupons & vouchers** - Discount system
- **notifications** - User notifications
- **transactions** - Robux transaction history
- **activity_logs** - Admin audit trail

## Project Structure

```
dripbux/
├── app.py              # Flask application factory
├── config.py           # Configuration classes
├── extensions.py       # Flask extensions
├── models.py           # Database models
├── forms.py            # WTForms
├── requirements.txt    # Dependencies
├── .env.example        # Environment template
├── seed.py             # Database seeder
├── static/
│   ├── css/
│   │   ├── main.css    # Main styles
│   │   └── particles.css
│   └── js/
│       ├── main.js     # Main scripts
│       └── particles.js
├── routes/
│   ├── auth.py         # Authentication
│   ├── main.py         # Homepage & static
│   ├── shop.py         # Product browsing
│   ├── cart.py         # Shopping cart
│   ├── checkout.py     # Checkout flow
│   ├── orders.py       # Order management
│   ├── seller.py       # Seller dashboard
│   ├── admin.py        # Admin panel
│   └── api.py          # AJAX endpoints
└── templates/
    ├── base.html       # Base layout
    ├── index.html      # Homepage
    ├── auth/           # Login, register, profile
    ├── shop/           # Products, search
    ├── cart/           # Cart page
    ├── checkout/       # Checkout steps
    ├── orders/         # Order history
    ├── seller/         # Seller dashboard
    ├── admin/          # Admin pages
    └── errors/         # Error pages
```

## Security Features

- CSRF protection on all forms
- Password hashing with PBKDF2
- Secure session management
- Role-based access control
- Input validation
- XSS protection via template escaping

## License

This project is for educational purposes.
