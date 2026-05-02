from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from .extensions import db
from .models import Audit, AuditLog
from .forms import AuditForm
from .audit_engine import audit_website

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("landing.html")

@main_bp.route("/healthz")
def healthz():
    return {"ok": True, "service": "TrustLens AI"}, 200

@main_bp.route("/dashboard")
@login_required
def dashboard():
    current_user.reset_usage_if_needed()
    db.session.commit()
    audits = Audit.query.filter_by(user_id=current_user.id).order_by(Audit.created_at.desc()).limit(8).all()
    return render_template("dashboard.html", audits=audits)

@main_bp.route("/audit/new", methods=["GET", "POST"])
@login_required
def new_audit():
    current_user.reset_usage_if_needed()
    form = AuditForm()
    if form.validate_on_submit():
        if current_user.scans_remaining <= 0:
            flash("You reached your monthly scan limit. Upgrade your plan or ask admin to change it.", "error")
            return redirect(url_for("main.dashboard"))
        url = form.url.data.strip()
        timeout = int(current_app.config.get("ALLOWED_SCAN_TIMEOUT", 10))
        try:
            report = audit_website(url, timeout=timeout)
            audit = Audit(user_id=current_user.id, url=url, normalized_url=report["final_url"], title=report["title"], trust_score=report["trust_score"], conversion_risk=report["conversion_risk"], report_json=report, status="completed")
            current_user.scans_used += 1
            db.session.add(audit)
            db.session.add(AuditLog(actor_id=current_user.id, action="audit_completed", target=url, detail=f"score={report['trust_score']}"))
            db.session.commit()
            flash("Audit completed.", "success")
            return redirect(url_for("main.report", audit_id=audit.id))
        except Exception as exc:
            report = {"summary": "Audit failed safely.", "top_problems": [str(exc)], "recommendations": [], "missing_elements": [], "red_flags": [str(exc)], "score_details": [], "signals": {}}
            audit = Audit(user_id=current_user.id, url=url, normalized_url=url, title="Failed audit", trust_score=0, conversion_risk="Critical", report_json=report, status="failed", error_message=str(exc))
            current_user.scans_used += 1
            db.session.add(audit)
            db.session.add(AuditLog(actor_id=current_user.id, action="audit_failed", target=url, detail=str(exc)))
            db.session.commit()
            flash("Audit failed safely: " + str(exc), "error")
            return redirect(url_for("main.report", audit_id=audit.id))
    return render_template("new_audit.html", form=form)

@main_bp.route("/reports")
@login_required
def reports():
    audits = Audit.query.filter_by(user_id=current_user.id).order_by(Audit.created_at.desc()).all()
    return render_template("reports.html", audits=audits)

@main_bp.route("/reports/<int:audit_id>")
@login_required
def report(audit_id):
    audit = Audit.query.get_or_404(audit_id)
    if audit.user_id != current_user.id and current_user.role != "admin":
        flash("You do not have permission to view this report.", "error")
        return redirect(url_for("main.dashboard"))
    return render_template("report.html", audit=audit, report=audit.report_json)
