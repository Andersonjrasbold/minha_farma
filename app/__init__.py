from decimal import Decimal
import os

from flask import Flask, session, url_for
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from werkzeug.routing import BuildError

from .config import BASE_DIR, Config
from .extensions import db, login_manager, migrate
from .models import Category, Offer, Product, Store


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config.setdefault("ENV", os.getenv("FLASK_ENV", "production"))
    configured_db_url = app.config["SQLALCHEMY_DATABASE_URI"]
    fallback_sqlite_url = f"sqlite:///{os.path.join(BASE_DIR, 'minha_farma.db')}"
    allow_sqlite_fallback = app.config.get("SQLITE_FALLBACK_ENABLED", False)

    if configured_db_url.startswith("postgresql"):
        try:
            with create_engine(configured_db_url).connect():
                pass
        except OperationalError:
            if allow_sqlite_fallback:
                print(
                    "AVISO: Não foi possível conectar no PostgreSQL em SQLALCHEMY_DATABASE_URI. "
                    f"Usando fallback SQLite ({fallback_sqlite_url})."
                )
                app.config["SQLALCHEMY_DATABASE_URI"] = fallback_sqlite_url
            else:
                raise RuntimeError(
                    "Falha ao conectar no PostgreSQL e SQLITE_FALLBACK_ENABLED está desativado. "
                    "Verifique a conectividade/credenciais do Supabase antes de continuar."
                )

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    from .routes.store import store_bp
    from .routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/gestao')
    app.register_blueprint(store_bp, url_prefix='/lojas')
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.context_processor
    def inject_globals():
        try:
            store_panel_url = url_for('store.store_register')
        except BuildError:
            store_panel_url = None
        cart_data = session.get('cart', {})
        cart_count = sum(int(quantity) for quantity in cart_data.values())
        return {
            'app_name': 'Minha Farma',
            'store_panel_url': store_panel_url,
            'cart_count': cart_count,
        }

    @app.cli.command('seed')
    def seed():
        if Store.query.first():
            print('Banco já possui dados.')
            return

        categorias = [
            Category(name='Medicamentos', slug='medicamentos'),
            Category(name='Higiene', slug='higiene'),
            Category(name='Vitaminas', slug='vitaminas'),
        ]
        db.session.add_all(categorias)
        db.session.flush()

        store1 = Store(
            name='Farmácia Central Cascavel',
            slug='farmacia-central-cascavel',
            city='Cascavel',
            neighborhood='Centro',
            delivery_radius_km=8,
            latitude=-24.9555,
            longitude=-53.4552,
            banner_url='https://images.unsplash.com/photo-1587854692152-cbe660dbde88?q=80&w=1200&auto=format&fit=crop'
        )
        store2 = Store(
            name='Drogaria Vida Curitiba',
            slug='drogaria-vida-curitiba',
            city='Curitiba',
            neighborhood='Batel',
            delivery_radius_km=10,
            latitude=-25.4372,
            longitude=-49.2806,
            banner_url='https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?q=80&w=1200&auto=format&fit=crop'
        )
        db.session.add_all([store1, store2])
        db.session.flush()

        produtos = [
            Product(store_id=store1.id, category_id=categorias[0].id, name='Dipirona 1g com 10 comprimidos', slug='dipirona-1g-10', description='Analgésico e antitérmico.', price=Decimal('14.90'), promotional_price=Decimal('11.90'), stock=100, image_url='https://images.unsplash.com/photo-1584017911766-d451b3d0e843?q=80&w=800&auto=format&fit=crop'),
            Product(store_id=store1.id, category_id=categorias[1].id, name='Álcool em Gel 500ml', slug='alcool-em-gel-500ml', description='Higienização das mãos.', price=Decimal('12.50'), promotional_price=Decimal('9.99'), stock=80, image_url='https://images.unsplash.com/photo-1584744982491-665216d95f8b?q=80&w=800&auto=format&fit=crop'),
            Product(store_id=store1.id, category_id=categorias[2].id, name='Vitamina C 1g com 30 comprimidos', slug='vitamina-c-1g-30', description='Suplemento vitamínico.', price=Decimal('28.90'), promotional_price=None, stock=55, image_url='https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?q=80&w=800&auto=format&fit=crop'),
            Product(store_id=store2.id, category_id=categorias[0].id, name='Ibuprofeno 600mg com 20 cápsulas', slug='ibuprofeno-600mg-20', description='Anti-inflamatório.', price=Decimal('21.90'), promotional_price=Decimal('18.90'), stock=70, image_url='https://images.unsplash.com/photo-1471864190281-a93a3070b6de?q=80&w=800&auto=format&fit=crop'),
        ]
        db.session.add_all(produtos)

        ofertas = [
            Offer(store_id=store1.id, title='Ofertas da semana em Cascavel', description='Medicamentos e higiene com entrega rápida.', image_url=store1.banner_url),
            Offer(store_id=store2.id, title='Promoções em Curitiba', description='Descontos em produtos selecionados.', image_url=store2.banner_url),
        ]
        db.session.add_all(ofertas)
        db.session.commit()
        print('Dados iniciais criados com sucesso.')

    return app
