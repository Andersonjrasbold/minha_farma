from functools import wraps

from flask import current_app
from flask import flash, redirect, url_for
from flask_login import current_user


def _partner_email_list():
    raw = current_app.config.get('PARTNER_EMAILS', '')
    if isinstance(raw, (list, tuple, set)):
        values = raw
    else:
        values = [item.strip().lower() for item in str(raw).split(',') if item.strip()]
    return {value for value in values}


def is_partner_email(user_email):
    if not user_email:
        return False
    return user_email.strip().lower() in _partner_email_list()


def is_partner_user(user=None):
    from .models import Store

    if user is None:
        user = current_user

    if not user or not getattr(user, 'is_authenticated', False):
        return False

    email = (getattr(user, 'email', '') or '').strip().lower()
    if not email:
        return False

    if is_partner_email(email):
        return True

    # Allow users who já possuem alguma loja vinculada pelo e-mail de contato
    # a gerenciar suas próprias lojas.
    return Store.query.filter(Store.contact_email == email).first() is not None


def can_manage_store(user, store):
    if not user or not store:
        return False

    email = (getattr(user, 'email', '') or '').strip().lower()
    if not email:
        return False

    if is_partner_email(email):
        return True

    return (store.contact_email or '').strip().lower() == email


def partner_required(view):
    @wraps(view)
    def _wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        if not is_partner_user(current_user):
            flash('Acesso restrito: esta área é exclusiva para parceiros.', 'warning')
            return redirect(url_for('main.home'))

        return view(*args, **kwargs)

    return _wrapped


def partner_store_required(view):
    from .models import Store

    @wraps(view)
    def _wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        store_id = kwargs.get('store_id')
        store = Store.query.get_or_404(store_id) if store_id else None
        if not store or not can_manage_store(current_user, store):
            flash('Você não tem permissão para gerenciar esta loja.', 'warning')
            return redirect(url_for('main.home'))

        return view(*args, **kwargs)

    return _wrapped
