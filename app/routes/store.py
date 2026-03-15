from datetime import datetime
import csv
import io
from decimal import Decimal
import re
import unicodedata

from flask import Blueprint, flash, jsonify, make_response, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Offer, Order, OrderItem, OrderStatusLog, Product, Store
from ..security import can_manage_store, is_partner_user, partner_required, partner_store_required
from ..utils.geolocation import CITY_COORDINATES

store_bp = Blueprint('store', __name__)


def _slugify(value):
    normalized = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower()).strip('-')
    return slug or 'loja'


def _next_slug(base_slug):
    slug = _slugify(base_slug)
    candidate = slug
    counter = 1
    while Store.query.filter_by(slug=candidate).first():
        counter += 1
        candidate = f'{slug}-{counter}'
    return candidate


@store_bp.route('/')
def store_list():
    stores = Store.query.filter_by(is_active=True).order_by(Store.name).all()
    return render_template('store/store_list.html', stores=stores)


@store_bp.route('/<slug>')
def store_detail(slug):
    store = Store.query.filter_by(slug=slug, is_active=True).first_or_404()
    products = Product.query.filter_by(store_id=store.id, is_active=True).all()
    return render_template('store/store_detail.html', store=store, products=products)


@store_bp.route('/painel/loja', methods=['GET', 'POST'])
@login_required
@partner_required
def store_register():
    if not is_partner_user(current_user):
        flash('Acesso restrito: apenas parceiros podem cadastrar lojas.', 'warning')
        return redirect(url_for('main.home'))

    cities = sorted(CITY_COORDINATES.keys())

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip().lower()
        cnpj = request.form.get('cnpj', '').strip()
        contact_email = request.form.get('contact_email', '').strip().lower()
        if not contact_email:
            contact_email = current_user.email
        phone = request.form.get('phone', '').strip()
        city = request.form.get('city', '').strip()
        neighborhood = request.form.get('neighborhood', '').strip()
        street = request.form.get('street', '').strip()
        street_number = request.form.get('street_number', '').strip()
        complement = request.form.get('complement', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        delivery_radius = request.form.get('delivery_radius_km', default=5, type=float)
        banner_url = request.form.get('banner_url', '').strip()
        is_national = request.form.get('is_national') == '1'

        display_city = 'Todo o Brasil' if is_national else city

        if not name or (not display_city):
            flash('Nome da loja e cidade são obrigatórios.', 'danger')
            return redirect(url_for('store.store_register'))

        if is_national:
            latitude, longitude = -14.235004, -51.92528
        elif display_city not in CITY_COORDINATES:
            flash('Selecione uma cidade válida.', 'danger')
            return redirect(url_for('store.store_register'))
        else:
            latitude, longitude = CITY_COORDINATES[display_city]

        address_lines = []
        if street:
            address_lines.append(street)
        if street_number:
            address_lines.append(f'N° {street_number}')
        if complement:
            address_lines.append(f'Compl.: {complement}')
        if zip_code:
            address_lines.append(zip_code)
        address = ', '.join([value for value in address_lines if value]) if address_lines else None

        if not slug:
            slug = _next_slug(name)
        elif Store.query.filter_by(slug=slug).first():
            flash('Slug já está em uso. Ajuste e tente novamente.', 'warning')
            return redirect(url_for('store.store_register'))

        store = Store(
            name=name,
            slug=slug,
            cnpj=cnpj or None,
            phone=phone or None,
            contact_email=contact_email or None,
            city=display_city,
            neighborhood=neighborhood,
            address=address,
            zip_code=zip_code or None,
            delivery_radius_km=delivery_radius,
            latitude=latitude,
            longitude=longitude,
            banner_url=banner_url or None,
        )
        db.session.add(store)
        db.session.commit()
        flash('Loja cadastrada com sucesso.', 'success')
        return redirect(url_for('store.store_dashboard', store_id=store.id))

    return render_template('store/store_register.html', cities=cities)


@store_bp.route('/painel/loja/<int:store_id>', methods=['GET', 'POST'])
@store_bp.route('/painel/loja/<int:store_id>/dashboard', methods=['GET', 'POST'])
@login_required
@partner_store_required
def store_dashboard(store_id):
    store = Store.query.get_or_404(store_id)
    cities = sorted(CITY_COORDINATES.keys())

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip().lower()
        city = request.form.get('city', '').strip()
        neighborhood = request.form.get('neighborhood', '').strip()
        address = request.form.get('address', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        phone = request.form.get('phone', '').strip()
        contact_email = request.form.get('contact_email', '').strip().lower()
        cnpj = request.form.get('cnpj', '').strip()
        delivery_radius = request.form.get('delivery_radius_km', default=store.delivery_radius_km, type=float)
        banner_url = request.form.get('banner_url', '').strip()
        is_active = request.form.get('is_active') == '1'
        is_national = request.form.get('is_national') == '1'

        target_city = 'Todo o Brasil' if is_national else city

        if not name or not target_city:
            flash('Nome da loja e cidade são obrigatórios.', 'danger')
            return redirect(url_for('store.store_dashboard', store_id=store.id))

        if target_city == 'Todo o Brasil':
            latitude, longitude = -14.235004, -51.92528
        elif target_city not in CITY_COORDINATES:
            flash('Selecione uma cidade válida.', 'danger')
            return redirect(url_for('store.store_dashboard', store_id=store.id))
        else:
            latitude, longitude = CITY_COORDINATES[target_city]

        if not slug:
            slug = _next_slug(name)
        elif slug != store.slug and Store.query.filter_by(slug=slug).first():
            flash('Slug já está em uso. Ajuste e tente novamente.', 'warning')
            return redirect(url_for('store.store_dashboard', store_id=store.id))

        store.name = name
        store.slug = slug
        store.city = target_city
        store.neighborhood = neighborhood
        store.address = address or None
        store.zip_code = zip_code or None
        store.phone = phone or None
        store.contact_email = contact_email or None
        store.cnpj = cnpj or None
        store.delivery_radius_km = delivery_radius
        store.banner_url = banner_url or None
        store.is_active = is_active
        store.latitude, store.longitude = latitude, longitude

        db.session.commit()
        flash('Dados da loja atualizados com sucesso.', 'success')
        return redirect(url_for('store.store_dashboard', store_id=store.id))

    offers = Offer.query.filter_by(store_id=store.id).order_by(Offer.id.desc()).all()
    total_orders = Order.query.filter_by(store_id=store.id).count()
    total_offers = len(offers)
    total_products = Product.query.filter_by(store_id=store.id).count()
    recent_orders = Order.query.filter_by(store_id=store.id).order_by(Order.id.desc()).limit(5).all()

    return render_template(
        'store/dashboard.html',
        store=store,
        cities=cities,
        offers=offers,
        total_products=total_products,
        total_offers=total_offers,
        total_orders=total_orders,
        recent_orders=recent_orders,
    )


@store_bp.route('/painel/loja/<int:store_id>/pedidos', methods=['GET', 'POST'])
@login_required
@partner_store_required
def store_orders(store_id):
    store = Store.query.get_or_404(store_id)
    valid_status = {'pendente', 'preparando', 'enviado', 'entregue', 'cancelado'}
    status_filter = request.form.get('status', '').strip() if request.method == 'POST' else request.args.get('status', '').strip()

    if request.method == 'POST':
        bulk_action = request.form.get('bulk_action')
        if bulk_action in valid_status:
            selected_order_ids = request.form.getlist('order_ids')
            if not selected_order_ids:
                flash('Selecione ao menos um pedido para atualizar.', 'warning')
                return redirect(url_for('store.store_orders', store_id=store.id))

            selected_order_ids = [int(order_id) for order_id in selected_order_ids]
            selected_orders = Order.query.filter(
                Order.store_id == store.id,
                Order.id.in_(selected_order_ids),
            ).all()
            updated_count = 0

            for order in selected_orders:
                previous_status = order.status
                if previous_status == bulk_action:
                    continue

                order.status = bulk_action
                log = OrderStatusLog(
                    order_id=order.id,
                    previous_status=previous_status,
                    new_status=bulk_action,
                    changed_by_user_id=current_user.id,
                )
                db.session.add(log)
                updated_count += 1
            if updated_count:
                db.session.commit()
                flash(f'{updated_count} pedido(s) atualizado(s) para "{bulk_action}".', 'success')
            else:
                flash('Nenhum pedido foi alterado porque já estão com esse status.', 'info')

            return redirect(
                url_for(
                    'store.store_orders',
                    store_id=store.id,
                    status=(status_filter if status_filter in valid_status else ''),
                )
            )

    query = Order.query.filter_by(store_id=store.id)
    if status_filter and status_filter in valid_status:
        query = query.filter_by(status=status_filter)

    orders = query.order_by(Order.created_at.desc(), Order.id.desc()).all()
    order_ids = [order.id for order in orders]
    latest_status_logs = {}
    if order_ids:
        logs = (
            OrderStatusLog.query.filter(OrderStatusLog.order_id.in_(order_ids))
            .order_by(OrderStatusLog.order_id, OrderStatusLog.changed_at.desc())
            .all()
        )
        for log in logs:
            if log.order_id not in latest_status_logs:
                latest_status_logs[log.order_id] = log

    return render_template(
        'store/orders.html',
        store=store,
        orders=orders,
        status_filter=status_filter,
        status_options=sorted(valid_status),
        latest_status_logs=latest_status_logs,
    )


@store_bp.route('/painel/loja/<int:store_id>/pedidos/export')
@login_required
@partner_store_required
def store_orders_export(store_id):
    store = Store.query.get_or_404(store_id)
    valid_status = {'pendente', 'preparando', 'enviado', 'entregue', 'cancelado'}
    status_filter = request.args.get('status', '').strip()

    query = Order.query.filter_by(store_id=store.id)
    if status_filter and status_filter in valid_status:
        query = query.filter_by(status=status_filter)

    orders = query.order_by(Order.created_at.desc(), Order.id.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'id',
        'status',
        'cliente',
        'valor_total',
        'endereco_entrega',
        'itens',
        'criado_em',
    ])

    for order in orders:
        itens = ', '.join([f'{item.product.name} ({item.quantity}x)' for item in order.items])
        writer.writerow([
            order.id,
            order.status,
            order.user.name,
            order.total,
            order.delivery_address,
            itens,
            order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = (
        f'attachment; filename="pedidos_loja_{store.id}.csv"'
    )
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return response


@store_bp.route('/painel/loja/<int:store_id>/ofertas', methods=['GET', 'POST'])
@login_required
@partner_store_required
def store_offers(store_id):
    store = Store.query.get_or_404(store_id)
    offers = Offer.query.filter_by(store_id=store.id).order_by(Offer.id.desc()).all()

    if request.method == 'POST':
        bulk_action = request.form.get('bulk_action')
        if bulk_action in {'ativar', 'desativar'}:
            selected_offer_ids = request.form.getlist('offer_ids')
            if not selected_offer_ids:
                flash('Selecione ao menos uma oferta para aplicar a ação.', 'warning')
                return redirect(url_for('store.store_offers', store_id=store.id))

            selected_ids = [int(item_id) for item_id in selected_offer_ids]
            selected_offers = Offer.query.filter(
                Offer.store_id == store.id,
                Offer.id.in_(selected_ids),
            ).all()
            is_active = bulk_action == 'ativar'
            for offer in selected_offers:
                offer.is_active = is_active
            db.session.commit()

            flash(
                f"{'Ativadas' if is_active else 'Desativadas'} {len(selected_offers)} ofertas com sucesso.",
                'success',
            )
            return redirect(url_for('store.store_offers', store_id=store.id))

        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        is_active = request.form.get('is_active') == '1'

        ends_at_raw = request.form.get('ends_at', '').strip()
        ends_at = None

        if ends_at_raw:
            try:
                ends_at = datetime.strptime(ends_at_raw, '%Y-%m-%d')
            except ValueError:
                flash('Data final inválida. Use o formato AAAA-MM-DD.', 'danger')
                return redirect(url_for('store.store_offers', store_id=store.id))

        if not title:
            flash('Informe o título da oferta.', 'danger')
            return redirect(url_for('store.store_offers', store_id=store.id))

        offer = Offer(
            store_id=store.id,
            title=title,
            description=description or None,
            image_url=image_url or None,
            is_active=is_active,
            ends_at=ends_at,
        )
        db.session.add(offer)
        db.session.commit()
        flash('Oferta cadastrada com sucesso.', 'success')
        return redirect(url_for('store.store_offers', store_id=store.id))

    return render_template('store/offer_register.html', store=store, offers=offers)


@store_bp.route('/<slug>/produto/<int:product_id>')
def product_detail(slug, product_id):
    store = Store.query.filter_by(slug=slug, is_active=True).first_or_404()
    product = Product.query.filter_by(id=product_id, store_id=store.id).first_or_404()
    return render_template('store/product_detail.html', store=store, product=product)


@store_bp.route('/carrinho')
def cart():
    cart_data = session.get('cart', {})
    items = []
    total = 0

    for product_id, quantity in cart_data.items():
        product = Product.query.get(int(product_id))
        if not product:
            continue
        subtotal = product.current_price() * quantity
        items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
        total += subtotal

    return render_template('store/cart.html', items=items, total=total)


@store_bp.route('/carrinho/adicionar', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', default=1, type=int)

    product = Product.query.get_or_404(product_id)
    cart_data = session.get('cart', {})
    cart_data[str(product.id)] = cart_data.get(str(product.id), 0) + max(quantity, 1)
    session['cart'] = cart_data
    flash(f'{product.name} foi adicionado ao carrinho.', 'success')
    return redirect(request.referrer or url_for('store.cart'))


@store_bp.route('/carrinho/repetir-pedido/<int:order_id>', methods=['GET', 'POST'])
@login_required
def repeat_order(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    cart_data = session.get('cart', {})
    added_count = 0
    unavailable_count = 0
    for item in order.items:
        product = Product.query.get(item.product_id)
        if not product or not product.is_active:
            unavailable_count += item.quantity
            continue
        cart_data[str(item.product_id)] = cart_data.get(str(item.product_id), 0) + item.quantity
        added_count += item.quantity
    session['cart'] = cart_data
    if unavailable_count:
        flash('Alguns itens não estavam mais disponíveis e não foram adicionados.', 'warning')
    if added_count:
        flash('Itens disponíveis foram adicionados ao carrinho.', 'success')
    else:
        flash('Nenhum item pôde ser repetido no momento.', 'warning')

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes['application/json']
        if is_ajax:
            return jsonify({
                'success': added_count > 0,
                'added_count': added_count,
                'unavailable_count': unavailable_count,
                'cart_count': sum(int(quantity) for quantity in cart_data.values()),
                'message': 'Itens disponíveis foram adicionados ao carrinho.' if added_count else 'Nenhum item pôde ser repetido no momento.',
                'message_type': 'success' if added_count else 'warning',
            })

    return redirect(url_for('store.cart'))


@store_bp.route('/carrinho/remover/<int:product_id>')
def remove_from_cart(product_id):
    cart_data = session.get('cart', {})
    cart_data.pop(str(product_id), None)
    session['cart'] = cart_data
    flash('Item removido do carrinho.', 'info')
    return redirect(url_for('store.cart'))


@store_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_data = session.get('cart', {})
    if not cart_data:
        flash('Seu carrinho está vazio.', 'warning')
        return redirect(url_for('store.cart'))

    items = []
    total = 0
    store_id = None

    for product_id, quantity in cart_data.items():
        product = Product.query.get(int(product_id))
        if not product:
            continue
        if store_id is None:
            store_id = product.store_id
        elif product.store_id != store_id:
            flash('Neste MVP o checkout aceita apenas itens da mesma loja.', 'danger')
            return redirect(url_for('store.cart'))
        subtotal = product.current_price() * quantity
        items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
        total += subtotal

    if request.method == 'POST':
        address = request.form.get('delivery_address', '').strip()
        if not address:
            flash('Informe o endereço de entrega.', 'danger')
            return redirect(url_for('store.checkout'))

        order = Order(
            user_id=current_user.id,
            store_id=store_id,
            total=Decimal(str(total)),
            delivery_address=address,
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product'].id,
                quantity=item['quantity'],
                unit_price=Decimal(str(item['product'].current_price())),
            )
            db.session.add(order_item)

        db.session.commit()
        session['cart'] = {}
        flash(f'Pedido #{order.id} criado com sucesso.', 'success')
        return redirect(url_for('store.store_detail', slug=items[0]['product'].store.slug))

    default_delivery_address = ''
    if current_user.default_address and current_user.default_address.full_address:
        default_delivery_address = current_user.default_address.full_address
    elif current_user.full_address:
        default_delivery_address = current_user.full_address
    elif current_user.addresses:
        default_delivery_address = current_user.addresses[0].full_address or ''

    return render_template(
        'store/checkout.html',
        items=items,
        total=total,
        default_delivery_address=default_delivery_address,
    )
