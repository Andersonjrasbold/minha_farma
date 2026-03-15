import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    _default_sqlite_url = f"sqlite:///{os.path.join(BASE_DIR, 'minha_farma.db')}"
    _env_database_url = (
        os.getenv('SQLALCHEMY_DATABASE_URI')
        or os.getenv('DATABASE_URL')
        or _default_sqlite_url
    )
    _normalized_db_url = _env_database_url.replace('postgres://', 'postgresql+psycopg2://')
    SQLALCHEMY_DATABASE_URI = (
        f"{_normalized_db_url}{'&' if '?' in _normalized_db_url else '?'}sslmode=require"
        if _normalized_db_url.startswith('postgresql+psycopg2://')
        and 'supabase.co' in _normalized_db_url
        and 'sslmode=' not in _normalized_db_url
        else _normalized_db_url
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLITE_FALLBACK_ENABLED = (
        os.getenv('SQLITE_FALLBACK_ENABLED', 'false').lower() in ('1', 'true', 'yes', 'on')
    )
    DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'Cascavel')
    PARTNER_EMAILS = os.getenv('PARTNER_EMAILS', '')
