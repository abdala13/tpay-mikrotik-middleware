import os
import logging
from datetime import timedelta
from flask import Flask
from dotenv import load_dotenv
from .extensions import db, login_manager, csrf
from .models import User
from .plans import apply_plan

load_dotenv()

class Config:
    APP_NAME = os.getenv("APP_NAME", "TrustLens AI")
    SECRET_KEY = os.getenv("SECRET_KEY") or "dev-change-me-render-safe-fallback"
    raw_db = os.getenv("DATABASE_URL", "").strip()
    if raw_db.startswith("postgres://"):
        raw_db = raw_db.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = raw_db or "sqlite:///trustlens.sqlite3"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None
    ALLOWED_SCAN_TIMEOUT = int(os.getenv("ALLOWED_SCAN_TIMEOUT", "10"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_DURATION = timedelta(days=14)

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None

def seed_admin(app):
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com").lower().strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "StrongPassword123!")
    user = User.query.filter_by(email=admin_email).first()
    if not user:
        user = User(email=admin_email, name="Admin", role="admin")
        user.set_password(admin_password)
        apply_plan(user, "Agency")
        db.session.add(user)
        db.session.commit()
        app.logger.info("Admin user created: %s", admin_email)
    elif user.role != "admin":
        user.role = "admin"
        db.session.commit()

def create_app():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "error"

    from .auth import auth_bp
    from .main import main_bp
    from .admin import admin_bp
    from .pdf import pdf_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(pdf_bp)

    @app.context_processor
    def inject_globals():
        return {"APP_NAME": app.config.get("APP_NAME", "TrustLens AI")}

    with app.app_context():
        db.create_all()
        seed_admin(app)

    return app
