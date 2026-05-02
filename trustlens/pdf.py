from io import BytesIO
from flask import Blueprint, send_file, redirect, url_for, flash
from flask_login import login_required, current_user
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from .models import Audit
from .plans import can_download_pdf

pdf_bp = Blueprint("pdf", __name__)

@pdf_bp.route("/reports/<int:audit_id>/pdf")
@login_required
def download_pdf(audit_id):
    audit = Audit.query.get_or_404(audit_id)
    if audit.user_id != current_user.id and current_user.role != "admin":
        flash("You do not have permission to download this report.", "error")
        return redirect(url_for("main.dashboard"))
    if current_user.role != "admin" and not can_download_pdf(current_user):
        flash("PDF export is available on paid plans.", "error")
        return redirect(url_for("main.report", audit_id=audit.id))
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="TrustLens AI Report")
    styles = getSampleStyleSheet()
    story = []
    report = audit.report_json or {}
    story.append(Paragraph("TrustLens AI Website Trust Report", styles["Title"]))
    story.append(Paragraph(f"URL: {audit.normalized_url}", styles["BodyText"]))
    story.append(Paragraph(f"Trust Score: {audit.trust_score}/100", styles["Heading2"]))
    story.append(Paragraph(f"Conversion Risk: {audit.conversion_risk}", styles["Heading2"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(report.get("summary", ""), styles["BodyText"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Top Problems", styles["Heading2"]))
    for p in report.get("top_problems", []):
        story.append(Paragraph("• " + str(p), styles["BodyText"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Recommendations", styles["Heading2"]))
    for r in report.get("recommendations", []):
        story.append(Paragraph(f"[{r.get('priority')}] {r.get('title')}: {r.get('detail')}", styles["BodyText"]))
    doc.build(story)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"trustlens-report-{audit.id}.pdf", mimetype="application/pdf")
