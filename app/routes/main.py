from flask import Blueprint, current_app, render_template, request
from flask_login import current_user

from ..models import Category, Offer, Store
from ..utils.geolocation import haversine_km, resolve_user_location

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    city = request.args.get('cidade')
    location = resolve_user_location(current_user if current_user.is_authenticated else None, city or current_app.config['DEFAULT_CITY'])

    all_stores = Store.query.filter_by(is_active=True).all()
    stores = []
    for store in all_stores:
        if store.city != 'Todo o Brasil' and store.city != location['city']:
            continue

        if store.city == 'Todo o Brasil':
            stores.append({'store': store, 'distance': None})
            continue

        distance = haversine_km(location['latitude'], location['longitude'], store.latitude, store.longitude)
        if distance <= store.delivery_radius_km:
            stores.append({'store': store, 'distance': round(distance, 1)})

    offers = Offer.query.filter_by(is_active=True).all()
    filtered_offers = [offer for offer in offers if offer.store.city == location['city'] or offer.store.city == 'Todo o Brasil']
    categories = Category.query.order_by(Category.name).all()

    return render_template(
        'index.html',
        location=location,
        stores=stores,
        offers=filtered_offers,
        categories=categories,
    )
