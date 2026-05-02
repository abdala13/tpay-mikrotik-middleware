from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from .extensions import db
from .models import User, AuditLog
from .forms import RegisterForm, LoginForm
from .plans import apply_plan

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "error")
            return render_template("register.html", form=form)
        user = User(email=email, name=form.name.data.strip())
        user.set_password(form.password.data)
        apply_plan(user, "Free")
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome to TrustLens AI.", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("register.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if not user or not user.check_password(form.password.data) or not user.is_active:
            flash("Invalid login or disabled account.", "error")
            return render_template("login.html", form=form)
        login_user(user)
        db.session.add(AuditLog(actor_id=user.id, action="login", target=user.email))
        db.session.commit()
        next_url = request.args.get("next")
        return redirect(next_url or url_for("main.dashboard"))
    return render_template("login.html", form=form)

@auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("main.landing"))

@auth_bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    return render_template("forgot.html")
