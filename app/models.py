from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    street = db.Column(db.String(255), nullable=True)
    street_number = db.Column(db.String(20), nullable=True)
    neighborhood = db.Column(db.String(120), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    apartment = db.Column(db.String(80), nullable=True)
    complement = db.Column(db.String(120), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship('Order', backref='user', lazy=True)
    status_logs = db.relationship('OrderStatusLog', backref='changed_by', lazy=True)
    addresses = db.relationship(
        'UserAddress',
        foreign_keys='UserAddress.user_id',
        backref=db.backref('user', lazy=True),
        lazy=True,
        cascade='all, delete-orphan',
    )
    default_address_id = db.Column(db.Integer, db.ForeignKey('user_addresses.id'), nullable=True)
    default_address = db.relationship(
        'UserAddress',
        foreign_keys=[default_address_id],
        uselist=False,
        post_update=True,
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_address(self):
        def _clean(value):
            return (value or '').strip().strip(',')

        address_lines = [
            _clean(self.street),
            _clean(f"N° {self.street_number}" if self.street_number else ''),
            _clean(f"Apto: {self.apartment}" if self.apartment else ''),
        ]
        complement = _clean(self.complement)
        if complement:
            address_lines.append(f"Compl.: {complement}")

        parts = [item for item in address_lines if item]
        if _clean(self.neighborhood):
            parts.append(_clean(self.neighborhood))
        if _clean(self.city):
            parts.append(_clean(self.city))
        if _clean(self.zip_code):
            parts.append(_clean(self.zip_code))

        return ', '.join(parts)


class UserAddress(db.Model):
    __tablename__ = 'user_addresses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    label = db.Column(db.String(120), nullable=True)
    street = db.Column(db.String(255), nullable=True)
    street_number = db.Column(db.String(20), nullable=True)
    neighborhood = db.Column(db.String(120), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    apartment = db.Column(db.String(80), nullable=True)
    complement = db.Column(db.String(120), nullable=True)
    city = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def full_address(self):
        def _clean(value):
            return (value or '').strip().strip(',')

        address_lines = [
            _clean(self.street),
            _clean(f"N° {self.street_number}" if self.street_number else ''),
            _clean(f"Apto: {self.apartment}" if self.apartment else ''),
        ]
        complement = _clean(self.complement)
        if complement:
            address_lines.append(f"Compl.: {complement}")

        parts = [item for item in address_lines if item]
        if _clean(self.neighborhood):
            parts.append(_clean(self.neighborhood))
        if _clean(self.city):
            parts.append(_clean(self.city))
        if _clean(self.zip_code):
            parts.append(_clean(self.zip_code))

        return ', '.join(parts)


class Store(db.Model):
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    cnpj = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    contact_email = db.Column(db.String(180), nullable=True)
    city = db.Column(db.String(120), nullable=False)
    neighborhood = db.Column(db.String(120), nullable=True)
    delivery_radius_km = db.Column(db.Float, default=5)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    banner_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='store', lazy=True)
    offers = db.relationship('Offer', backref='store', lazy=True)


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)

    products = db.relationship('Product', backref='category', lazy=True)


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    promotional_price = db.Column(db.Numeric(10, 2), nullable=True)
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('store_id', 'slug', name='uq_store_product_slug'),
    )

    def current_price(self):
        return float(self.promotional_price or self.price)


class Offer(db.Model):
    __tablename__ = 'offers'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    starts_at = db.Column(db.DateTime, default=datetime.utcnow)
    ends_at = db.Column(db.DateTime, nullable=True)


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default='pendente')
    delivery_address = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    store = db.relationship('Store', lazy=True)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    status_logs = db.relationship('OrderStatusLog', backref='order', lazy=True, cascade='all, delete-orphan')


class OrderStatusLog(db.Model):
    __tablename__ = 'order_status_logs'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    previous_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    product = db.relationship('Product')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
