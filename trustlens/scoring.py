def score_report(signals):
    score = 0
    details = []

    def add(name, points, ok, reason_ok, reason_bad):
        nonlocal score
        if ok:
            score += points
            details.append({"name": name, "points": points, "earned": points, "status": "pass", "reason": reason_ok})
        else:
            details.append({"name": name, "points": points, "earned": 0, "status": "fail", "reason": reason_bad})

    add("HTTPS", 10, signals.get("https"), "Website uses HTTPS.", "Website does not use HTTPS.")
    add("Legal pages", 20, signals.get("legal_pages_count", 0) >= 2, "Important legal pages are visible.", "Privacy/terms/refund pages are missing or hard to find.")
    add("Contact information", 15, signals.get("has_contact"), "Contact path or contact information is visible.", "Contact information is missing or unclear.")
    add("Clear offer", 15, signals.get("clear_offer"), "The page appears to explain the offer clearly.", "The visitor may not understand the offer quickly.")
    add("Social proof", 10, signals.get("social_proof"), "The page contains social proof indicators.", "Testimonials/reviews/social proof are weak or missing.")
    add("UX clarity", 15, signals.get("ux_clear"), "Primary action and page structure look reasonably clear.", "CTA or page structure may create friction.")
    add("Security signals", 10, signals.get("security_headers_count", 0) >= 2, "Some security headers are present.", "Security headers are limited or absent.")
    add("Low red flags", 5, signals.get("red_flags_count", 0) == 0, "No major trust red flags detected.", "One or more trust red flags were detected.")

    score = max(0, min(100, score))
    if score >= 80:
        risk = "Low"
    elif score >= 60:
        risk = "Medium"
    elif score >= 40:
        risk = "High"
    else:
        risk = "Critical"
    return score, risk, details
