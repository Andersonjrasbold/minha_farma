from flask import Blueprint, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..models import Order, OrderStatusLog, User, UserAddress
from ..utils.geolocation import CITY_COORDINATES

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/registro', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        city = request.form.get('city', '').strip()

        if not all([name, email, password, city]):
            flash('Preencha todos os campos.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'warning')
            return redirect(url_for('auth.register'))

        latitude, longitude = CITY_COORDINATES.get(city, CITY_COORDINATES['Cascavel'])
        user = User(name=name, email=email, city=city, latitude=latitude, longitude=longitude)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Conta criada com sucesso.', 'success')
        return redirect(url_for('main.home'))

    return render_template('auth/register.html', cities=sorted(CITY_COORDINATES.keys()))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login realizado com sucesso.', 'success')
            return redirect(url_for('main.home'))

        flash('E-mail ou senha inválidos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('main.home'))


@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def profile():
    cities = sorted(CITY_COORDINATES.keys())

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        city = request.form.get('city', '').strip()
        password = request.form.get('password', '').strip()

        if not name or not email or not city:
            flash('Nome, e-mail e cidade são obrigatórios.', 'danger')
            return redirect(url_for('auth.profile'))

        if city not in CITY_COORDINATES:
            flash('Selecione uma cidade válida.', 'danger')
            return redirect(url_for('auth.profile'))

        if email != current_user.email and User.query.filter_by(email=email).first():
            flash('Este e-mail já está em uso.', 'warning')
            return redirect(url_for('auth.profile'))

        current_user.name = name
        current_user.email = email
        current_user.city = city
        current_user.latitude, current_user.longitude = CITY_COORDINATES[city]

        if password:
            current_user.set_password(password)

        db.session.commit()
        flash('Dados atualizados com sucesso.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', cities=cities)


@auth_bp.route('/perfil/pedidos')
@login_required
def profile_orders():
    orders = (
        Order.query
        .filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .all()
    )
    for order in orders:
        available_items_count = 0
        unavailable_items_count = 0
        for item in order.items:
            if item.product and item.product.is_active:
                available_items_count += item.quantity
            else:
                unavailable_items_count += item.quantity

        order.can_repeat_order = available_items_count > 0
        order.available_items_count = available_items_count
        order.unavailable_items_count = unavailable_items_count

    return render_template(
        'auth/orders.html',
        orders=orders,
    )


@auth_bp.route('/perfil/pedido/<int:order_id>')
@login_required
def profile_order_detail(order_id):
    order = (
        Order.query
        .filter_by(id=order_id, user_id=current_user.id)
        .first_or_404()
    )
    status_logs = (
        OrderStatusLog.query
        .filter_by(order_id=order.id)
        .order_by(OrderStatusLog.changed_at.asc())
        .all()
    )
    available_items_count = 0
    unavailable_items_count = 0
    for item in order.items:
        if item.product and item.product.is_active:
            available_items_count += item.quantity
        else:
            unavailable_items_count += item.quantity

    can_repeat_order = available_items_count > 0

    return render_template(
        'auth/order_detail.html',
        order=order,
        status_logs=status_logs,
        can_repeat_order=can_repeat_order,
        unavailable_items_count=unavailable_items_count,
        available_items_count=available_items_count,
    )


@auth_bp.route('/perfil/pedido/<int:order_id>/comprovante')
@login_required
def profile_order_receipt(order_id):
    order = (
        Order.query
        .filter_by(id=order_id, user_id=current_user.id)
        .first_or_404()
    )
    lines = [
        f'Pedido: #{order.id}',
        f'Status: {order.status}',
        f'Loja: {order.store.name}',
        f'Cliente: {current_user.name} ({current_user.email})',
        f'Endereço: {order.delivery_address}',
        f'Data: {order.created_at.strftime("%d/%m/%Y %H:%M:%S")}',
        '',
        'Itens:',
    ]
    for item in order.items:
        lines.append(
            f'- {item.product.name}: {item.quantity}x R$ {"%.2f" % float(item.unit_price)} = R$ {"%.2f" % float(item.unit_price * item.quantity)}'
        )
    lines.extend([
        '',
        f'Total: R$ {"%.2f" % float(order.total)}',
    ])

    response = make_response('\n'.join(lines))
    response.headers['Content-Disposition'] = f'attachment; filename="pedido_{order.id}_comprovante.txt"'
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response


@auth_bp.route('/perfil/pedido/<int:order_id>/cancelar', methods=['POST'])
@login_required
def profile_order_cancel(order_id):
    order = (
        Order.query
        .filter_by(id=order_id, user_id=current_user.id)
        .first_or_404()
    )
    if order.status == 'cancelado':
        flash('Este pedido já foi cancelado.', 'info')
        return redirect(url_for('auth.profile_order_detail', order_id=order.id))

    if order.status == 'entregue':
        flash('Pedidos entregues não podem ser cancelados.', 'warning')
        return redirect(url_for('auth.profile_order_detail', order_id=order.id))

    if order.status != 'pendente' and order.status != 'preparando':
        flash('Este pedido não pode ser cancelado no status atual.', 'warning')
        return redirect(url_for('auth.profile_order_detail', order_id=order.id))

    previous_status = order.status
    order.status = 'cancelado'
    log = OrderStatusLog(
        order_id=order.id,
        previous_status=previous_status,
        new_status='cancelado',
        changed_by_user_id=current_user.id,
    )
    db.session.add(log)
    db.session.commit()
    flash('Pedido cancelado com sucesso.', 'success')
    return redirect(url_for('auth.profile_order_detail', order_id=order.id))


@auth_bp.route('/perfil/enderecos', methods=['GET', 'POST'])
@login_required
def profile_addresses():
    default_city = current_user.city

    if request.method == 'POST':
        street = request.form.get('street', '').strip()
        street_number = request.form.get('street_number', '').strip()
        neighborhood = request.form.get('neighborhood', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        apartment = request.form.get('apartment', '').strip()
        complement = request.form.get('complement', '').strip()

        digits_zip = ''.join(ch for ch in zip_code if ch.isdigit())
        if digits_zip:
            if len(digits_zip) > 8:
                digits_zip = digits_zip[:8]
            if len(digits_zip) != 8:
                flash('CEP inválido. Use o formato 00000-000.', 'warning')
                return redirect(url_for('auth.profile_addresses'))

            zip_code = f'{digits_zip[:5]}-{digits_zip[5:]}'

        if not street and not street_number and not zip_code and not neighborhood:
            flash('Informe ao menos rua, número, bairro ou CEP para preencher o endereço.', 'warning')
            return redirect(url_for('auth.profile_addresses'))

        new_address = UserAddress(
            user_id=current_user.id,
            street=street or None,
            street_number=street_number or None,
            neighborhood=neighborhood or None,
            zip_code=zip_code or None,
            apartment=apartment or None,
            complement=complement or None,
            city=default_city,
            label='Endereço',
        )
        db.session.add(new_address)
        db.session.flush()
        if not current_user.default_address_id:
            current_user.default_address_id = new_address.id

        db.session.commit()
        flash('Endereço salvo com sucesso.', 'success')
        return redirect(url_for('auth.profile_addresses'))

    user_addresses = []
    seen_addresses = set()
    stored_addresses = (
        UserAddress.query
        .filter_by(user_id=current_user.id)
        .order_by(UserAddress.created_at.desc(), UserAddress.id.desc())
        .all()
    )

    main_address = (current_user.full_address or '').strip()
    if main_address:
        normalized_main = main_address.lower().strip()
        user_addresses.append({
            'source': 'Perfil anterior',
            'label': 'Endereço anterior',
            'value': main_address,
            'id': None,
            'is_legacy': True,
            'is_primary': not current_user.default_address_id,
        })
        seen_addresses.add(normalized_main)

    for stored_address in stored_addresses:
        address_value = stored_address.full_address.strip()
        if not address_value:
            continue

        normalized = address_value.lower().strip()
        if normalized in seen_addresses:
            continue

        user_addresses.append({
            'source': 'Endereço cadastrado',
            'label': stored_address.label or 'Endereço',
            'value': address_value,
            'id': stored_address.id,
            'is_legacy': False,
            'is_primary': current_user.default_address_id == stored_address.id,
        })
        seen_addresses.add(normalized)

    return render_template(
        'auth/addresses.html',
        cities=sorted(CITY_COORDINATES.keys()),
        user_addresses=user_addresses,
    )


@auth_bp.route('/perfil/enderecos/principal', methods=['POST'])
@login_required
def profile_set_main_address():
    address_id = request.form.get('address_id', type=int)
    use_legacy = request.form.get('use_legacy') == '1'

    if not address_id and not use_legacy:
        flash('Selecione um endereço válido para definir como principal.', 'warning')
        return redirect(url_for('auth.profile_addresses'))

    if use_legacy:
        current_user.default_address_id = None
        db.session.commit()
        flash('Endereço principal atualizado para o endereço do perfil.', 'success')
        return redirect(url_for('auth.profile_addresses'))

    address = UserAddress.query.filter_by(id=address_id, user_id=current_user.id).first()
    if not address:
        flash('Endereço não encontrado.', 'danger')
        return redirect(url_for('auth.profile_addresses'))

    current_user.default_address_id = address.id
    db.session.commit()
    flash('Endereço principal atualizado.', 'success')
    return redirect(url_for('auth.profile_addresses'))
