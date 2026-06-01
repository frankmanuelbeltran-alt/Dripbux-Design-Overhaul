"""
DripBux Complete Overhaul - All WTForms
========================================
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, EmailField, TextAreaField,
    IntegerField, FloatField, BooleanField, SelectField,
    FileField, HiddenField, SubmitField, DateField, SelectMultipleField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, NumberRange,
    Optional, ValidationError, URL
)
from flask_wtf.file import FileAllowed


# =============================================================================
# AUTHENTICATION FORMS
# =============================================================================

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')


class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    avatar = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif']), Optional()])
    submit = SubmitField('Save Changes')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')


# =============================================================================
# ADDRESS FORMS
# =============================================================================

class AddressForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=255)])
    address_line2 = StringField('Address Line 2 (Optional)', validators=[Optional(), Length(max=255)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State/Province', validators=[Optional(), Length(max=100)])
    postal_code = StringField('Postal Code', validators=[DataRequired(), Length(max=20)])
    country = SelectField('Country', choices=[('USA', 'United States'), ('CAN', 'Canada'), ('UK', 'United Kingdom'), ('AUS', 'Australia'), ('OTHER', 'Other')], default='USA')
    is_default = BooleanField('Set as default address')
    submit = SubmitField('Save Address')


# =============================================================================
# PRODUCT FORMS
# =============================================================================

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[DataRequired()])
    short_description = StringField('Short Description', validators=[Optional(), Length(max=255)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    price_robux = IntegerField('Price (Robux)', validators=[DataRequired(), NumberRange(min=1)])
    original_price = IntegerField('Original Price (Optional)', validators=[Optional(), NumberRange(min=0)])
    stock_quantity = IntegerField('Stock Quantity', validators=[NumberRange(min=0)], default=10)
    rarity = SelectField('Rarity', choices=[('common', 'Common'), ('uncommon', 'Uncommon'), ('rare', 'Rare'), ('epic', 'Epic'), ('legendary', 'Legendary'), ('mythic', 'Mythic')], default='common')
    product_type = SelectField('Product Type', choices=[('physical', 'Physical Item'), ('digital', 'Digital Item'), ('gamepass', 'Gamepass'), ('bundle', 'Bundle')], default='physical')
    tags = StringField('Tags (comma separated)', validators=[Optional(), Length(max=500)])
    image = FileField('Main Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp']), Optional()])
    additional_images = FileField('Additional Images', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp']), Optional()], render_kw={'multiple': True})
    is_active = BooleanField('Active', default=True)
    is_featured = BooleanField('Featured', default=False)
    is_new = BooleanField('Mark as New', default=True)
    is_trending = BooleanField('Trending', default=False)
    is_flash_sale = BooleanField('Flash Sale', default=False)
    is_limited = BooleanField('Limited Edition', default=False)
    submit = SubmitField('Save Product')


class ProductSizeForm(FlaskForm):
    size = StringField('Variant Name', validators=[DataRequired(), Length(max=20)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)], default=10)
    price_modifier = IntegerField('Price Modifier', validators=[NumberRange(min=0)], default=0)
    submit = SubmitField('Add Variant')


# =============================================================================
# CATEGORY FORMS
# =============================================================================

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=50)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional()])
    image = FileField('Category Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif']), Optional()])
    icon = StringField('Icon Name', validators=[Optional(), Length(max=50)])
    display_order = IntegerField('Display Order', default=0)
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Category')


# =============================================================================
# CHECKOUT FORMS
# =============================================================================

class CheckoutShippingForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address_line1 = StringField('Address', validators=[DataRequired()])
    address_line2 = StringField('Apartment, Suite, etc. (Optional)', validators=[Optional()])
    city = StringField('City', validators=[DataRequired()])
    state = StringField('State', validators=[Optional()])
    postal_code = StringField('Postal Code', validators=[DataRequired()])
    country = SelectField('Country', choices=[('USA', 'United States'), ('CAN', 'Canada'), ('UK', 'United Kingdom'), ('AUS', 'Australia')], default='USA')
    shipping_method = SelectField('Shipping Method', choices=[('standard', 'Standard Shipping (5-7 days) - FREE'), ('express', 'Express Shipping (2-3 days) - 199 Robux')], default='standard')
    save_address = BooleanField('Save this address for future orders')
    submit = SubmitField('Continue')


# =============================================================================
# REVIEW FORM
# =============================================================================

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[('5', '5 Stars'), ('4', '4 Stars'), ('3', '3 Stars'), ('2', '2 Stars'), ('1', '1 Star')], default='5', validators=[DataRequired()])
    title = StringField('Review Title', validators=[Optional(), Length(max=100)])
    comment = TextAreaField('Your Review', validators=[DataRequired(), Length(min=10, max=1000)])
    images = FileField('Review Images', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp']), Optional()], render_kw={'multiple': True})
    submit = SubmitField('Submit Review')


# =============================================================================
# SELLER FORMS
# =============================================================================

class SellerApplicationForm(FlaskForm):
    store_name = StringField('Store Name', validators=[DataRequired(), Length(min=3, max=100)])
    store_description = TextAreaField('Store Description', validators=[DataRequired(), Length(min=20, max=1000)])
    store_logo = FileField('Store Logo', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif']), Optional()])
    store_banner = FileField('Store Banner', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif']), Optional()])
    submit = SubmitField('Apply to Become a Seller')


class SellerSettingsForm(FlaskForm):
    store_name = StringField('Store Name', validators=[DataRequired(), Length(max=100)])
    store_description = TextAreaField('Store Description', validators=[DataRequired()])
    store_logo = FileField('Store Logo', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif']), Optional()])
    store_banner = FileField('Store Banner', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif']), Optional()])
    is_active = BooleanField('Store Active')
    submit = SubmitField('Save Settings')


class VoucherForm(FlaskForm):
    code = StringField('Voucher Code', validators=[DataRequired(), Length(max=30)])
    description = StringField('Description', validators=[Optional(), Length(max=255)])
    discount_type = SelectField('Discount Type', choices=[('percent', 'Percentage'), ('fixed', 'Fixed Amount')], default='percent')
    discount_value = IntegerField('Discount Value', validators=[DataRequired(), NumberRange(min=1)])
    min_order_amount = IntegerField('Min Order Amount', validators=[NumberRange(min=0)], default=0)
    usage_limit = IntegerField('Usage Limit (-1 for unlimited)', default=-1)
    expires_at = DateField('Expires At (Optional)', validators=[Optional()], format='%Y-%m-%d')
    submit = SubmitField('Create Voucher')


# =============================================================================
# ADMIN FORMS
# =============================================================================

class AdminUserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    robux_balance = IntegerField('Robux Balance', validators=[DataRequired(), NumberRange(min=0)])
    role = SelectField('Role', choices=[('customer', 'Customer'), ('seller', 'Seller'), ('admin', 'Admin')], default='customer')
    is_active = BooleanField('Active')
    submit = SubmitField('Save Changes')


class AdminUserCreateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('customer', 'Customer'), ('seller', 'Seller'), ('admin', 'Admin')], default='admin')
    robux_balance = IntegerField('Robux Balance', validators=[DataRequired(), NumberRange(min=0)], default=10000)
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Create User')


class SellerActionForm(FlaskForm):
    action = HiddenField('Action')
    reason = StringField('Reason', validators=[Optional(), Length(max=150)])
    message = TextAreaField('Message', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Submit')


class AddRobuxForm(FlaskForm):
    amount = IntegerField('Amount', validators=[DataRequired(), NumberRange(min=1)])
    reason = StringField('Reason', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Add Robux')


class OrderStatusForm(FlaskForm):
    status = SelectField('Status', choices=[('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded')], validators=[DataRequired()])
    tracking_number = StringField('Tracking Number', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Update Status')


class CancellationReasonForm(FlaskForm):
    reason = SelectField('Why are you cancelling?', choices=[
        ('ordered_by_mistake', 'Ordered by mistake'),
        ('found_cheaper_elsewhere', 'Found cheaper elsewhere'),
        ('changed_my_mind', 'Changed my mind'),
        ('wrong_product_selected', 'Wrong product selected'),
        ('delivery_takes_too_long', 'Delivery takes too long'),
        ('payment_issue', 'Payment issue'),
        ('duplicate_order', 'Duplicate order'),
        ('other', 'Other')
    ], validators=[DataRequired(message='Please select a cancellation reason.')])
    custom_reason = StringField('Other reason (optional)', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Confirm Cancellation')


class CouponForm(FlaskForm):
    code = StringField('Coupon Code', validators=[DataRequired(), Length(max=30)])
    description = StringField('Description', validators=[Optional(), Length(max=255)])
    discount_type = SelectField('Discount Type', choices=[('percent', 'Percentage'), ('fixed', 'Fixed Amount')], default='percent')
    discount_value = IntegerField('Discount Value', validators=[DataRequired(), NumberRange(min=1)])
    min_order_amount = IntegerField('Min Order Amount', default=0)
    max_discount = IntegerField('Max Discount', validators=[Optional()])
    usage_limit = IntegerField('Usage Limit (-1 for unlimited)', default=-1)
    starts_at = DateField('Starts At', validators=[Optional()], format='%Y-%m-%d')
    expires_at = DateField('Expires At', validators=[Optional()], format='%Y-%m-%d')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Coupon')


class AnnouncementForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    announcement_type = SelectField('Type', choices=[('info', 'Info'), ('warning', 'Warning'), ('success', 'Success'), ('promo', 'Promotion')], default='info')
    is_active = BooleanField('Active', default=True)
    expires_at = DateField('Expires At (Optional)', validators=[Optional()], format='%Y-%m-%d')
    submit = SubmitField('Post Announcement')


class SiteSettingsForm(FlaskForm):
    site_name = StringField('Site Name', validators=[DataRequired()])
    tagline = StringField('Tagline', validators=[Optional()])
    maintenance_mode = BooleanField('Maintenance Mode')
    registration_enabled = BooleanField('Registration Enabled', default=True)
    submit = SubmitField('Save Settings')


# =============================================================================
# CONTACT FORM
# =============================================================================

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10, max=2000)])
    submit = SubmitField('Send Message')
