# DripBux Premium v3.0.0

> The ultimate streetwear marketplace powered by Robux. Pink luxury theme with glassmorphism design.

![Version](https://img.shields.io/badge/version-3.0.0-ff4d8d)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Flask](https://img.shields.io/badge/flask-3.0.0-orange)

## Features

### Core Features
- **User Authentication** - Register, login, logout with secure password hashing
- **Robux Currency System** - Complete balance management with transaction history
- **Product Catalog** - Browse products by category with advanced filtering
- **Shopping Cart** - Persistent cart with add, remove, update functionality
- **Multi-step Checkout** - Shipping → Review → Payment → Confirmation
- **Order Management** - Track orders with status updates
- **Wishlist** - Save products for later
- **Product Reviews** - Verified purchase reviews with ratings

### Admin Features
- **Dashboard** - Analytics and statistics overview
- **Product Management** - CRUD operations with size variants
- **Category Management** - Organize products by category
- **Order Management** - Update order status and tracking
- **User Management** - View and manage users, add Robux
- **Review Moderation** - Manage product reviews

### Design Features
- **Pink Luxury Theme** - Premium aesthetic with #ff4d8d primary color
- **Glassmorphism** - Modern translucent UI elements
- **Smooth Animations** - Hover effects, transitions, and micro-interactions
- **Responsive Design** - Mobile-first approach
- **Dark Mode** - Default dark luxury theme

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Templating**: Jinja2
- **Icons**: Lucide Icons
- **Fonts**: Poppins, Inter

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone or download the project:**
```bash
cd dripbux-premium
```

2. **Create a virtual environment:**
```bash
python -m venv venv
```

3. **Activate the virtual environment:**

Windows:
```bash
venv\Scripts\activate
```

macOS/Linux:
```bash
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Run the application:**
```bash
python app.py
```

6. **Open in browser:**
```
http://localhost:5000
```

## Default Credentials

### Admin Account
- **Username**: `admin`
- **Email**: `admin@dripbux.com`
- **Password**: `admin123`

### New Users
- Starting balance: **10,000 Robux**

## Project Structure

```
dripbux-premium/
├── app.py                 # Flask application factory
├── config.py              # Configuration settings
├── extensions.py          # Flask extensions
├── models.py              # Database models
├── forms.py               # WTForms
├── requirements.txt       # Python dependencies
├── README.md              # This file
│
├── routes/                # Blueprint routes
│   ├── __init__.py
│   ├── auth.py            # Authentication routes
│   ├── main.py            # Main pages
│   ├── shop.py            # Shop & products
│   ├── cart.py            # Shopping cart
│   ├── checkout.py        # Checkout flow
│   ├── orders.py          # Order management
│   ├── admin.py           # Admin panel
│   └── api.py             # AJAX endpoints
│
├── templates/             # Jinja2 templates
│   ├── base.html          # Base template
│   ├── index.html         # Homepage
│   ├── partials/          # Reusable components
│   ├── auth/              # Auth templates
│   ├── shop/              # Shop templates
│   ├── cart/              # Cart templates
│   ├── checkout/          # Checkout templates
│   ├── orders/            # Order templates
│   ├── admin/             # Admin templates
│   └── errors/            # Error pages
│
└── static/                # Static assets
    ├── css/
    │   └── main.css       # Main stylesheet
    ├── js/
    │   └── main.js        # Main JavaScript
    └── images/
        ├── products/      # Product images
        ├── avatars/       # User avatars
        └── categories/    # Category images
```

## Database Models

### User
- Authentication (username, email, password)
- Robux balance
- Avatar support
- Admin flag

### Product
- Name, description, pricing
- Category relationship
- Size variants
- Images
- Featured/New flags

### Cart/CartItem
- User-specific carts
- Product + size + quantity

### Order/OrderItem
- Order tracking
- Shipping information
- Status workflow

### Category
- Product organization
- Slug for URLs

### Review
- Product ratings
- Verified purchase flag

### Wishlist
- User's saved products

### Transaction
- Robux transaction history

## Customization

### Theme Colors
Edit `config.py` - `ThemeConfig` class:

```python
PRIMARY = "#ff4d8d"        # Main brand color
PRIMARY_LIGHT = "#ff80ab"  # Light accent
DARK_BG = "#0f0f14"        # Background color
```

### Starting Robux Balance
Edit `config.py` - `FeatureConfig` class:

```python
STARTING_ROBUX_BALANCE = 10000
```

### Admin Credentials
Edit `config.py` - `AdminConfig` class or set environment variables:

```bash
export ADMIN_USERNAME=your_username
export ADMIN_EMAIL=your_email
export ADMIN_PASSWORD=your_password
```

## API Endpoints

### Public
- `GET /api/search?q={query}` - Live product search
- `GET /api/products/{id}/sizes` - Get product sizes
- `GET /api/cart/summary` - Get cart count & total

### Authentication Required
- `POST /cart/add` - Add item to cart
- `POST /cart/update/{item_id}` - Update cart item
- `POST /cart/remove/{item_id}` - Remove cart item
- `POST /shop/wishlist/add/{product_id}` - Add to wishlist
- `POST /shop/wishlist/remove/{product_id}` - Remove from wishlist

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_DEBUG` | Enable debug mode | `True` |
| `FLASK_HOST` | Server host | `0.0.0.0` |
| `FLASK_PORT` | Server port | `5000` |
| `SECRET_KEY` | Flask secret key | (dev key) |
| `DATABASE_URL` | Database URI | `sqlite:///dripbux.db` |
| `ADMIN_USERNAME` | Default admin username | `admin` |
| `ADMIN_EMAIL` | Default admin email | `admin@dripbux.com` |
| `ADMIN_PASSWORD` | Default admin password | `admin123` |

## Security Features

- CSRF protection on all forms
- Password hashing with PBKDF2
- Secure session management
- File upload validation
- SQL injection protection (SQLAlchemy)

## Performance

- Lazy loading images
- Debounced search
- Optimized CSS/JS
- Database indexing
- Pagination on all lists

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

MIT License - feel free to use for personal or commercial projects.

## Credits

- Design inspired by Shein, StockX, and Nike
- Icons by [Lucide](https://lucide.dev)
- Fonts by Google Fonts

## Support

For issues or feature requests, please open an issue on GitHub.

---

**Made with by the DripBux Team**
