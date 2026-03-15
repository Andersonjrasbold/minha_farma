from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func

from ..extensions import db
from ..models import Offer, Order, Product, Store
from ..security import is_partner_email, is_partner_user
from ..utils.geolocation import CITY_COORDINATES


admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not is_partner_user():
        return render_template(
            'admin/dashboard.html',
            stores=[],
            city='',
            city_options=[],
            total_stores=0,
            active_stores=0,
            inactive_stores=0,
            total_products=0,
            active_products=0,
            total_offers=0,
            active_offers=0,
            total_orders=0,
            total_order_value=0,
            products_by_store={},
            offers_by_store={},
            orders_by_store={},
            access_denied=True,
        )

    city = request.args.get('cidade', '').strip()
    email = (current_user.email or '').strip().lower()

    stores_query = Store.query
    if not is_partner_email(email):
        stores_query = stores_query.filter(Store.contact_email == email)

    if city:
        stores_query = stores_query.filter(Store.city == city)

    stores = stores_query.order_by(Store.is_active.desc(), Store.name.asc()).all()
    all_store_cities = sorted({store.city for store in stores_query.all()})
    city_options = sorted(set(CITY_COORDINATES.keys()).union(all_store_cities))

    total_stores = stores_query.count()
    active_stores = stores_query.filter(Store.is_active.is_(True)).count()
    inactive_stores = max(total_stores - active_stores, 0)
    store_ids = [store.id for store in stores]

    if store_ids:
        total_products = Product.query.filter(Product.store_id.in_(store_ids)).count()
        active_products = Product.query.filter(
            Product.store_id.in_(store_ids),
            Product.is_active.is_(True),
        ).count()
        total_offers = Offer.query.filter(Offer.store_id.in_(store_ids)).count()
        active_offers = Offer.query.filter(
            Offer.store_id.in_(store_ids),
            Offer.is_active.is_(True),
        ).count()
        total_orders = Order.query.filter(Order.store_id.in_(store_ids)).count()
        total_order_value = db.session.query(func.coalesce(func.sum(Order.total), 0)).filter(
            Order.store_id.in_(store_ids),
        ).scalar() or 0
    else:
        total_products = 0
        active_products = 0
        total_offers = 0
        active_offers = 0
        total_orders = 0
        total_order_value = 0

    offer_stats = (
        db.session.query(Product.store_id, func.count(Product.id).label('count'))
        .filter(Product.store_id.in_(store_ids))
        .group_by(Product.store_id)
        .all()
    )
    products_by_store = {store_id: count for store_id, count in offer_stats}

    offer_stats = (
        db.session.query(Offer.store_id, func.count(Offer.id).label('count'))
        .filter(Offer.store_id.in_(store_ids))
        .group_by(Offer.store_id)
        .all()
    )
    offers_by_store = {store_id: count for store_id, count in offer_stats}

    order_stats = (
        db.session.query(Order.store_id, func.count(Order.id).label('count'))
        .filter(Order.store_id.in_(store_ids))
        .group_by(Order.store_id)
        .all()
    )
    orders_by_store = {store_id: count for store_id, count in order_stats}

    return render_template(
        'admin/dashboard.html',
        stores=stores,
        city=city,
        city_options=city_options,
        total_stores=total_stores,
        active_stores=active_stores,
        inactive_stores=inactive_stores,
        total_products=total_products,
        active_products=active_products,
        total_offers=total_offers,
        active_offers=active_offers,
        total_orders=total_orders,
        total_order_value=total_order_value,
        products_by_store=products_by_store,
        offers_by_store=offers_by_store,
        orders_by_store=orders_by_store,
        access_denied=False,
    )
