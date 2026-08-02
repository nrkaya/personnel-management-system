import os
from flask import Flask, render_template, session
from werkzeug.security import generate_password_hash
from config import config_by_name
from database import db, csrf
from models import Kullanici, Personel, Izin, Log, LoginAttempt
from utils import has_permission


def create_app(config_name=None):
    """Application factory for KAYA PTS Enterprise."""
    app = Flask(__name__)

    if not config_name:
        config_name = os.environ.get("FLASK_ENV", "development")

    app.config.from_object(
        config_by_name.get(config_name, config_by_name["default"])
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

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

    @app.context_processor
    def inject_globals():
        user_role = session.get("rol", "")
        return {
            "user_role": user_role,
            "can_manage_users": has_permission(user_role, "users"),
            "can_view_logs": has_permission(user_role, "logs"),
            "can_view_trash": has_permission(user_role, "trash"),
            "can_add_personnel": has_permission(user_role, "add"),
            "can_view_salary": has_permission(user_role, "salary"),
            "_": _,
            "get_locale": get_locale,
        }

    @app.errorhandler(400)
    def bad_request(e):
        return render_template(
            "400.html",
            error_desc="Invalid request or CSRF token mismatch."
        ), 400

    @app.errorhandler(403)
    def access_forbidden(e):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("500.html"), 500

    with app.app_context():
        db.create_all()

        admin_user = Kullanici.query.filter_by(
            kullanici_adi="admin"
        ).first()

        if admin_user is None:
            try:
                admin_user = Kullanici(
                    kullanici_adi="admin",
                    sifre_hash=generate_password_hash("Admin123!"),
                    rol="Admin",
                    ad_soyad="System Administrator",
                    email="admin@kayapts.com",
                    aktif_mi=True,
                )

                db.session.add(admin_user)
                db.session.commit()

            except Exception:
                db.session.rollback()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
    )