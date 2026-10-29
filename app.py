import os
import secrets
from datetime import datetime, timedelta
import click
from flask import Flask, render_template, session, request, redirect, url_for, jsonify, flash
from werkzeug.security import generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import text
from config import config_by_name
from database import db, csrf, migrate, limiter
from models import Kullanici, Log, LoginAttempt
from utils import (
    avatar_url, end_user_session, get_active_session_user, has_permission,
    manager_department_missing, utcnow, validate_password,
)


# Example values and keys that were once committed to the public repository.
# They are rejected so a deployment can never run with a known secret.
PLACEHOLDER_SECRETS = {
    '',
    'enter_your_super_secret_random_key_here_32_bytes_min',
    'replace_with_a_64_character_random_secret',
    'replace_with_a_separate_random_api_key',
    'change-me',
    'changeme',
    'nexus_enterprise_super_secret_key_2026_x89f7!@#',
    'kaya_pts_ultra_secure_enterprise_secret_key_2026',
    'kaya-pts-ultra-secure-key-2026-v4',
    'kaya-pts-enterprise-api-key-2026',
}
MIN_SECRET_LENGTH = 32

CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "img-src 'self' data:; "
    "style-src 'self'; "
    "font-src 'self'; "
    "script-src 'self'; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)


def create_app(config_name=None):
    """Application factory for KAYA PTS Enterprise."""
    app = Flask(__name__)

    if not config_name:
        config_name = os.environ.get("FLASK_ENV", "development")

    app.config.from_object(
        config_by_name.get(config_name, config_by_name["default"])
    )

    for key in ('SECRET_KEY', 'API_KEY'):
        value = (app.config.get(key) or '').strip()
        if value.lower() not in PLACEHOLDER_SECRETS and len(value) >= MIN_SECRET_LENGTH:
            continue
        if config_name == 'production':
            raise RuntimeError(
                f'{key} üretim ortamında zorunludur; en az {MIN_SECRET_LENGTH} karakterlik, '
                'daha önce kullanılmamış rastgele bir değer tanımlayın.'
            )
        if config_name != 'testing':
            app.config[key] = secrets.token_urlsafe(48)
            app.logger.warning('%s yapılandırılmadı; yalnızca bu geliştirme sürecinde geçerli rastgele değer kullanılıyor.', key)

    if config_name == 'production' and app.config['RATELIMIT_STORAGE_URI'].startswith('memory://'):
        app.logger.warning(
            'RATELIMIT_STORAGE_URI memory:// kullanıyor; birden fazla gunicorn worker '
            'arasında hız sınırları paylaşılmaz. Redis gibi ortak bir depo tanımlayın.'
        )

    proxy_count = app.config.get('TRUSTED_PROXY_COUNT', 0)
    if proxy_count:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxy_count, x_proto=proxy_count)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # Initialize i18n translations
    from i18n import load_translations, _, get_locale
    load_translations()

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.personel import personel_bp
    from routes.izin import izin_bp
    from routes.kullanici import kullanici_bp
    from routes.logs import logs_bp
    from routes.api import api_bp
    from routes.lang import lang_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(personel_bp)
    app.register_blueprint(izin_bp)
    app.register_blueprint(kullanici_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(lang_bp)

    @app.before_request
    def refresh_session_user():
        """Invalidate revoked, disabled or deleted accounts and refresh role changes immediately."""
        exempt_endpoints = {'static', 'auth.login', 'auth.logout', 'lang.set_language', 'healthz'}
        if request.blueprint == 'api' or request.endpoint in exempt_endpoints:
            return None
        if (session.get('user_id') or session.get('kullanici_adi')) and get_active_session_user() is None:
            end_user_session()
            flash(_('msg_session_invalid'), 'error')
            return redirect(url_for('auth.login'))
        return None

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
        response.headers.setdefault('Content-Security-Policy', CONTENT_SECURITY_POLICY)
        if app.config.get('SESSION_COOKIE_SECURE'):
            response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        return response

    @app.get('/healthz')
    def healthz():
        try:
            db.session.execute(text('SELECT 1'))
        except Exception:
            db.session.rollback()
            return jsonify({'status': 'unhealthy'}), 503
        return jsonify({'status': 'ok', 'time': datetime.now().astimezone().isoformat()}), 200

    @app.context_processor
    def inject_globals():
        user = get_active_session_user() if session.get('user_id') else None
        user_role = user.rol if user else ""
        return {
            "current_user": user,
            "user_role": user_role,
            "can_manage_users": has_permission(user_role, "users"),
            "can_view_logs": has_permission(user_role, "logs"),
            "can_view_trash": has_permission(user_role, "trash"),
            "can_hard_delete": has_permission(user_role, "hard_delete"),
            "can_add_personnel": has_permission(user_role, "add"),
            "can_view_salary": has_permission(user_role, "salary"),
            "can_view_personal": has_permission(user_role, "personal"),
            "can_manage_leaves": has_permission(user_role, "leaves"),
            "can_delete_leaves": has_permission(user_role, "leave_delete"),
            "can_view_leave_reason": has_permission(user_role, "leave_reason"),
            "can_export": has_permission(user_role, "export"),
            "department_missing": manager_department_missing(user),
            "avatar_url": avatar_url,
            "_": _,
            "get_locale": get_locale,
        }

    def _api_error(status, message):
        return jsonify({'success': False, 'error': message}), status

    def _error_page(code, title_key, desc_key):
        return render_template('error.html', code=code, title=_(title_key), description=_(desc_key)), code

    @app.errorhandler(400)
    def bad_request(e):
        if request.blueprint == 'api':
            return _api_error(400, 'Geçersiz istek.')
        return render_template("400.html"), 400

    @app.errorhandler(403)
    def access_forbidden(e):
        if request.blueprint == 'api':
            return _api_error(403, 'Erişim reddedildi.')
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def page_not_found(e):
        if request.blueprint == 'api':
            return _api_error(404, 'Kaynak bulunamadı.')
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def payload_too_large(e):
        if request.blueprint == 'api':
            return _api_error(413, 'İstek boyutu sınırı aşıldı.')
        return _error_page(413, 'err_413_title', 'err_413_desc')

    @app.errorhandler(429)
    def too_many_requests(e):
        if request.blueprint == 'api':
            return _api_error(429, 'Çok fazla istek. Lütfen daha sonra tekrar deneyin.')
        return _error_page(429, 'err_429_title', 'err_429_desc')

    @app.errorhandler(500)
    def internal_server_error(e):
        db.session.rollback()
        if request.blueprint == 'api':
            return _api_error(500, 'Sunucu hatası.')
        return render_template("500.html"), 500

    @app.cli.command('create-admin')
    @click.option('--username', prompt='Yönetici kullanıcı adı')
    @click.option('--full-name', prompt='Ad soyad', default='System Administrator')
    @click.option('--email', prompt='E-posta (opsiyonel)', default='', show_default=False)
    def create_admin(username, full_name, email):
        """Create the first administrator without embedding credentials in code."""
        username = username.strip()
        if not username:
            raise click.UsageError('Kullanıcı adı boş olamaz.')
        if Kullanici.query.filter_by(kullanici_adi=username).first():
            raise click.UsageError('Bu kullanıcı adı zaten var.')
        password = click.prompt('Güçlü parola', hide_input=True, confirmation_prompt=True)
        valid, message = validate_password(password)
        if not valid:
            raise click.UsageError(message)
        admin = Kullanici(
            kullanici_adi=username,
            ad_soyad=full_name.strip() or None,
            email=email.strip() or None,
            sifre_hash=generate_password_hash(password),
            rol='Admin',
            aktif_mi=True,
        )
        db.session.add(admin)
        db.session.commit()
        click.echo(f'Yönetici kullanıcı oluşturuldu: {username}')

    @app.cli.command('purge-logs')
    @click.option('--days', type=click.IntRange(min=1), default=None,
                  help='Bu günden eski denetim kayıtlarını sil (varsayılan: LOG_RETENTION_DAYS).')
    @click.option('--attempt-days', type=click.IntRange(min=1), default=None,
                  help='Bu günden eski giriş denemesi sayaçlarını sil (varsayılan: LOGIN_ATTEMPT_RETENTION_DAYS).')
    def purge_logs(days, attempt_days):
        """Apply the retention policy to audit logs and login-attempt counters."""
        days = days or app.config['LOG_RETENTION_DAYS']
        attempt_days = attempt_days or app.config['LOGIN_ATTEMPT_RETENTION_DAYS']
        now = utcnow()
        log_count = Log.query.filter(Log.tarih_saat < now - timedelta(days=days)).delete(synchronize_session=False)
        attempt_count = LoginAttempt.query.filter(
            LoginAttempt.son_deneme < now - timedelta(days=attempt_days),
            (LoginAttempt.kilit_bitis.is_(None)) | (LoginAttempt.kilit_bitis < now),
        ).delete(synchronize_session=False)
        db.session.add(Log(
            kullanici_adi='Sistem',
            islem_tipi='Log Temizliği',
            detay=f'{days} günden eski {log_count} denetim kaydı ve {attempt_days} günden eski '
                  f'{attempt_count} giriş denemesi kaydı silindi.',
            tarih_saat=now,
        ))
        db.session.commit()
        click.echo(f'{log_count} denetim kaydı ve {attempt_count} giriş denemesi kaydı silindi.')

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
    )
