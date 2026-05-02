from datetime import datetime, timedelta, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), default="")
    role = db.Column(db.String(30), default="user")
    is_active_flag = db.Column(db.Boolean, default=True)
    plan_name = db.Column(db.String(30), default="Free")
    monthly_scan_limit = db.Column(db.Integer, default=3)
    scans_used = db.Column(db.Integer, default=0)
    subscription_status = db.Column(db.String(30), default="active")
    reset_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc) + timedelta(days=30))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    audits = db.relationship("Audit", backref="user", lazy=True, cascade="all, delete-orphan")

    @property
    def is_active(self):
        return self.is_active_flag

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def reset_usage_if_needed(self):
        now = datetime.now(timezone.utc)
        reset = self.reset_date
        if reset and reset.tzinfo is None:
            reset = reset.replace(tzinfo=timezone.utc)
        if not reset or reset <= now:
            self.scans_used = 0
            self.reset_date = now + timedelta(days=30)

    @property
    def scans_remaining(self):
        return max(0, (self.monthly_scan_limit or 0) - (self.scans_used or 0))

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    url = db.Column(db.String(1200), nullable=False)
    normalized_url = db.Column(db.String(1200), nullable=False)
    title = db.Column(db.String(500), default="")
    status = db.Column(db.String(30), default="completed")
    trust_score = db.Column(db.Integer, default=0)
    conversion_risk = db.Column(db.String(30), default="High")
    report_json = db.Column(db.JSON, nullable=False)
    error_message = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target = db.Column(db.String(500), default="")
    detail = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
