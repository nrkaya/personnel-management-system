import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base application configuration."""
    # Never keep production secrets in source control. Development gets an
    # ephemeral value if .env has not been configured; production fails fast.
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Database URI (supports SQLite and PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(basedir, 'database.db')}"
    )
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }

    # File upload settings. Personnel photos are personal data, so they live
    # outside the public static folder and are served only to logged-in users.
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    # Photos uploaded by older versions; moved to UPLOAD_FOLDER on first use.
    LEGACY_UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    ALLOWED_MIMETYPES = {'image/png', 'image/jpeg', 'image/pjpeg', 'image/webp'}
    MAX_IMAGE_PIXELS = int(os.environ.get('MAX_IMAGE_PIXELS', 20_000_000))

    # Session and cookie security
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'

    # CSRF protection. Tokens live as long as the session, so a page left open
    # for a while does not fail with a 400 on submit.
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = int(PERMANENT_SESSION_LIFETIME.total_seconds())

    # Rate limiting & brute force protection. MAX_LOGIN_ATTEMPTS locks one
    # account; MAX_IP_LOGIN_ATTEMPTS (failures across all accounts) locks an IP.
    MAX_LOGIN_ATTEMPTS = 5
    MAX_IP_LOGIN_ATTEMPTS = int(os.environ.get('MAX_IP_LOGIN_ATTEMPTS', '20'))
    LOCKOUT_DURATION_MINUTES = 10

    # Reverse proxies must be explicitly opted into before forwarded headers
    # are trusted. Set this to the exact number of trusted proxy hops.
    TRUSTED_PROXY_COUNT = int(os.environ.get('TRUSTED_PROXY_COUNT', '0'))

    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')

    # Retention for audit logs (they hold names and IP addresses) and for
    # brute-force counters; applied by `flask purge-logs`.
    LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', '365'))
    LOGIN_ATTEMPT_RETENTION_DAYS = int(os.environ.get('LOGIN_ATTEMPT_RETENTION_DAYS', '30'))

    # REST API key
    API_KEY = os.environ.get('API_KEY')
    API_KEY_SCOPES = os.environ.get(
        'API_KEY_SCOPES',
        'personnel:read,personnel:write,personnel:salary,personnel:personal,stats:read'
    )
    # Optional JSON map for rotating integration keys. Each value must have a
    # "key" and a "scopes" list, e.g. {"payroll": {"key": "...", "scopes": ["personnel:read"]}}.
    API_KEYS_JSON = os.environ.get('API_KEYS_JSON', '{}')
    MAX_API_PAGE_SIZE = int(os.environ.get('MAX_API_PAGE_SIZE', '100'))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SECRET_KEY = 'test-secret-key-not-for-production'
    API_KEY = 'test-api-key-not-for-production'
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
