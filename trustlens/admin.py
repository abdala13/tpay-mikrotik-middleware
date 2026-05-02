from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .extensions import db
from .models import User, Audit, AuditLog
from .forms import PlanForm
from .plans import apply_plan

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required():
    return current_user.is_authenticated and current_user.role == "admin"

@admin_bp.before_request
def require_admin():
    if not admin_required():
        flash("Admin access required.", "error")
        return redirect(url_for("main.dashboard"))

@admin_bp.route("/")
@login_required
def dashboard():
    total_users = User.query.count()
    total_audits = Audit.query.count()
    active_users = User.query.filter_by(is_active_flag=True).count()
    latest_audits = Audit.query.order_by(Audit.created_at.desc()).limit(10).all()
    return render_template("admin_dashboard.html", total_users=total_users, total_audits=total_audits, active_users=active_users, latest_audits=latest_audits)

@admin_bp.route("/users")
@login_required
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    form = PlanForm()
    return render_template("admin_users.html", users=users, form=form)

@admin_bp.route("/users/<int:user_id>/plan", methods=["POST"])
@login_required
def update_plan(user_id):
    user = User.query.get_or_404(user_id)
    form = PlanForm()
    if form.validate_on_submit():
        apply_plan(user, form.plan_name.data)
        db.session.add(AuditLog(actor_id=current_user.id, action="plan_updated", target=user.email, detail=form.plan_name.data))
        db.session.commit()
        flash("Plan updated.", "success")
    else:
        flash("Invalid plan form.", "error")
    return redirect(url_for("admin.users"))

@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot disable your own account.", "error")
    else:
        user.is_active_flag = not user.is_active_flag
        db.session.add(AuditLog(actor_id=current_user.id, action="user_toggled", target=user.email, detail=str(user.is_active_flag)))
        db.session.commit()
        flash("User status updated.", "success")
    return redirect(url_for("admin.users"))

@admin_bp.route("/audits")
@login_required
def audits():
    audits = Audit.query.order_by(Audit.created_at.desc()).limit(200).all()
    return render_template("admin_audits.html", audits=audits)

@admin_bp.route("/logs")
@login_required
def logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return render_template("admin_logs.html", logs=logs)
