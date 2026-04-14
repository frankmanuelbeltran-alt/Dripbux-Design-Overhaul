"""
DripBux Premium Forms
=====================
All WTForms for the application.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, EmailField, TextAreaField, 
    IntegerField, FloatField, BooleanField, SelectField,
    FileField, HiddenField, SubmitField, FieldList, FormField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, NumberRange,
    Optional, ValidationError
)
from flask_wtf.file import FileAllowed, FileRequired


# =============================================================================
# AUTHENTICATION FORMS
# =============================================================================

class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be 3-80 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be 3-80 characters')
    ])
    email = EmailField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Create Account')


class ProfileForm(FlaskForm):
    """User profile edit form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80)
    ])
    email = EmailField('Email', validators=[
        DataRequired(),
        Email()
    ])
    avatar = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!'),
        Optional()
    ])
    submit = SubmitField('Save Changes')


class ChangePasswordForm(FlaskForm):
    """Change password form"""
    current_password = PasswordField('Current Password', validators=[
        DataRequired()
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6)
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')


# =============================================================================
# ADDRESS FORMS
# =============================================================================

class AddressForm(FlaskForm):
    """Shipping address form"""
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required'),
        Length(max=100)
    ])
    phone = StringField('Phone Number', validators=[
        DataRequired(message='Phone number is required'),
        Length(max=20)
    ])
    address_line1 = StringField('Address Line 1', validators=[
        DataRequired(message='Address is required'),
        Length(max=255)
    ])
    address_line2 = StringField('Address Line 2 (Optional)', validators=[
        Optional(),
        Length(max=255)
    ])
    city = StringField('City', validators=[
        DataRequired(message='City is required'),
        Length(max=100)
    ])
    state = StringField('State/Province', validators=[
        Optional(),
        Length(max=100)
    ])
    postal_code = StringField('Postal Code', validators=[
        DataRequired(message='Postal code is required'),
        Length(max=20)
    ])
    country = SelectField('Country', choices=[
        ('USA', 'United States'),
        ('CAN', 'Canada'),
        ('UK', 'United Kingdom'),
        ('AUS', 'Australia'),
        ('OTHER', 'Other')
    ], default='USA')
    is_default = BooleanField('Set as default address')
    submit = SubmitField('Save Address')


# =============================================================================
# PRODUCT FORMS (Admin)
# =============================================================================

class ProductForm(FlaskForm):
    """Product creation/edit form"""
    name = StringField('Product Name', validators=[
        DataRequired(),
        Length(max=150)
    ])
    description = TextAreaField('Description', validators=[
        DataRequired()
    ])
    short_description = StringField('Short Description', validators=[
        Optional(),
        Length(max=255)
    ])
    category_id = SelectField('Category', coerce=int, validators=[
        DataRequired()
    ])
    price_robux = IntegerField('Price (Robux)', validators=[
        DataRequired(),
        NumberRange(min=1, message='Price must be at least 1 Robux')
    ])
    original_price = IntegerField('Original Price (Optional)', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    image = FileField('Main Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    is_active = BooleanField('Active', default=True)
    is_featured = BooleanField('Featured', default=False)
    is_new = BooleanField('Mark as New', default=True)
    submit = SubmitField('Save Product')


class ProductSizeForm(FlaskForm):
    """Product size variant form"""
    size = SelectField('Size', choices=[
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
        ('3XL', '3XL')
    ], validators=[DataRequired()])
    stock = IntegerField('Stock', validators=[
        DataRequired(),
        NumberRange(min=0)
    ], default=10)
    price_modifier = IntegerField('Price Modifier', validators=[
        NumberRange(min=0)
    ], default=0)


class CategoryForm(FlaskForm):
    """Category creation/edit form"""
    name = StringField('Category Name', validators=[
        DataRequired(),
        Length(max=50)
    ])
    slug = StringField('Slug', validators=[
        DataRequired(),
        Length(max=50)
    ])
    description = TextAreaField('Description', validators=[Optional()])
    image = FileField('Category Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    display_order = IntegerField('Display Order', default=0)
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Category')


# =============================================================================
# CHECKOUT FORMS
# =============================================================================

class CheckoutShippingForm(FlaskForm):
    """Checkout shipping information form"""
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address_line1 = StringField('Address', validators=[DataRequired()])
    address_line2 = StringField('Apartment, Suite, etc. (Optional)', validators=[Optional()])
    city = StringField('City', validators=[DataRequired()])
    state = StringField('State', validators=[Optional()])
    postal_code = StringField('Postal Code', validators=[DataRequired()])
    country = SelectField('Country', choices=[
        ('USA', 'United States'),
        ('CAN', 'Canada'),
        ('UK', 'United Kingdom'),
        ('AUS', 'Australia')
    ], default='USA')
    save_address = BooleanField('Save this address for future orders')
    submit = SubmitField('Continue to Review')


class CheckoutReviewForm(FlaskForm):
    """Checkout review form"""
    shipping_method = SelectField('Shipping Method', choices=[
        ('standard', 'Standard Shipping (5-7 days) - FREE'),
        ('express', 'Express Shipping (2-3 days) - 199 Robux')
    ], default='standard')
    promo_code = StringField('Promo Code (Optional)', validators=[Optional()])
    submit = SubmitField('Place Order')


# =============================================================================
# REVIEW FORM
# =============================================================================

class ReviewForm(FlaskForm):
    """Product review form"""
    rating = SelectField('Rating', choices=[
        ('5', '5 Stars - Excellent'),
        ('4', '4 Stars - Very Good'),
        ('3', '3 Stars - Good'),
        ('2', '2 Stars - Fair'),
        ('1', '1 Star - Poor')
    ], default='5', validators=[DataRequired()])
    title = StringField('Review Title', validators=[
        Optional(),
        Length(max=100)
    ])
    comment = TextAreaField('Your Review', validators=[
        DataRequired(),
        Length(min=10, max=1000, message='Review must be 10-1000 characters')
    ])
    submit = SubmitField('Submit Review')


# =============================================================================
# ADMIN FORMS
# =============================================================================

class AdminUserEditForm(FlaskForm):
    """Admin user edit form"""
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    robux_balance = IntegerField('Robux Balance', validators=[
        DataRequired(),
        NumberRange(min=0)
    ])
    is_admin = BooleanField('Admin')
    is_active = BooleanField('Active')
    submit = SubmitField('Save Changes')


class AddRobuxForm(FlaskForm):
    """Add Robux to user form"""
    amount = IntegerField('Amount', validators=[
        DataRequired(),
        NumberRange(min=1, message='Amount must be at least 1')
    ])
    reason = StringField('Reason', validators=[
        Optional(),
        Length(max=255)
    ])
    submit = SubmitField('Add Robux')


class OrderStatusForm(FlaskForm):
    """Update order status form"""
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], validators=[DataRequired()])
    tracking_number = StringField('Tracking Number', validators=[Optional()])
    submit = SubmitField('Update Status')


# =============================================================================
# SEARCH FORM
# =============================================================================

class SearchForm(FlaskForm):
    """Product search form"""
    q = StringField('Search', validators=[
        DataRequired(),
        Length(min=1, max=100)
    ])
    category = SelectField('Category', coerce=int, validators=[Optional()])
    sort = SelectField('Sort By', choices=[
        ('newest', 'Newest First'),
        ('price_low', 'Price: Low to High'),
        ('price_high', 'Price: High to Low'),
        ('popular', 'Most Popular'),
        ('name', 'Name: A-Z')
    ], default='newest')
    min_price = IntegerField('Min Price', validators=[Optional()])
    max_price = IntegerField('Max Price', validators=[Optional()])
    submit = SubmitField('Search')
