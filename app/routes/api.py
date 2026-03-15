from flask import Blueprint, jsonify, request

from ..models import Product, Store

api_bp = Blueprint('api', __name__)


@api_bp.route('/stores')
def api_stores():
    city = request.args.get('city')
    query = Store.query.filter_by(is_active=True)
    if city:
        query = query.filter_by(city=city)

    stores = query.all()
    return jsonify([
        {
            'id': store.id,
            'name': store.name,
            'slug': store.slug,
            'city': store.city,
            'delivery_radius_km': store.delivery_radius_km,
        }
        for store in stores
    ])


@api_bp.route('/products/search')
def search_products():
    term = request.args.get('q', '')
    products = Product.query.filter(Product.name.ilike(f'%{term}%')).limit(20).all()
    return jsonify([
        {
            'id': product.id,
            'name': product.name,
            'price': product.current_price(),
            'store': product.store.name,
        }
        for product in products
    ])
