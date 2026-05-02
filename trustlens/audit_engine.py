import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from .security import validate_public_url, safe_join
from .scoring import score_report

LEGAL_PATTERNS = {
    "about": ["about", "who we are", "من نحن"],
    "contact": ["contact", "support", "اتصل", "تواصل"],
    "privacy": ["privacy", "سياسة الخصوصية"],
    "terms": ["terms", "conditions", "الشروط"],
    "refund": ["refund", "return", "استرجاع", "استرداد"],
    "faq": ["faq", "questions", "الأسئلة"],
}
CTA_WORDS = ["buy", "start", "get started", "sign up", "register", "subscribe", "checkout", "order", "book", "اشترك", "ابدأ", "سجل", "شراء", "اطلب"]
SOCIAL_WORDS = ["testimonial", "review", "trusted", "customers", "clients", "stars", "case study", "تقييم", "عملاء", "موثوق"]
RED_FLAG_WORDS = ["guaranteed 100%", "get rich", "earn fast", "risk free profit", "مضمون 100%", "اربح بسرعة"]
ERROR_WORDS = ["traceback", "fatal error", "stack trace", "sql syntax", "warning:", "undefined index"]
PRICE_RE = re.compile(r"(\$|€|£|₪|USD|EUR|ILS|SAR|AED)\s?\d+|\d+\s?(USD|EUR|ILS|SAR|AED|دولار|شيكل)", re.I)
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)

class LimitedRedirectSession(requests.Session):
    def rebuild_auth(self, prepared_request, response):
        return

def audit_website(url, timeout=10):
    normalized = validate_public_url(url)
    session = LimitedRedirectSession()
    headers = {"User-Agent": "TrustLensAI/1.0 (+defensive trust audit)"}
    response = session.get(normalized, headers=headers, timeout=timeout, allow_redirects=True)
    final_url = validate_public_url(response.url)
    if len(response.history) > 5:
        raise ValueError("Too many redirects.")
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type.lower():
        raise ValueError("The URL did not return an HTML page.")
    html = response.text[:1_500_000]
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = (soup.title.string.strip() if soup.title and soup.title.string else "Untitled website")[:500]
    meta_desc = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        meta_desc = meta.get("content", "").strip()
    text = " ".join(soup.get_text(" ").split())
    lower = text.lower()
    links = []
    same_domain_links = []
    external_links = []
    base_host = urlparse(final_url).netloc.lower()
    for a in soup.find_all("a", href=True):
        joined = safe_join(final_url, a.get("href"))
        if not joined:
            continue
        label = " ".join(a.get_text(" ").split())[:160]
        links.append({"url": joined, "text": label})
        if urlparse(joined).netloc.lower() == base_host:
            same_domain_links.append(joined)
        else:
            external_links.append(joined)

    forms = soup.find_all("form")
    buttons_text = " ".join([b.get_text(" ") for b in soup.find_all(["button", "a"])])
    buttons_lower = buttons_text.lower()

    found_pages = {}
    for key, words in LEGAL_PATTERNS.items():
        found_pages[key] = any(any(w in (l["url"] + " " + l["text"]).lower() for w in words) for l in links)

    security_headers = [h for h in ["Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy", "Strict-Transport-Security"] if response.headers.get(h)]
    has_mixed = "http://" in html and final_url.startswith("https://")
    has_cta = any(w in buttons_lower or w in lower[:3000] for w in CTA_WORDS)
    has_price = bool(PRICE_RE.search(text)) or any(word in lower for word in ["pricing", "plans", "price", "الأسعار", "السعر"])
    has_email = bool(EMAIL_RE.search(text))
    has_contact = found_pages.get("contact") or has_email
    social_proof = any(w in lower for w in SOCIAL_WORDS)
    clear_offer = bool(title and len(title) > 8) and (bool(meta_desc) or len(text) > 350)
    ux_clear = has_cta and len(forms) <= 3 and len(text) >= 250
    red_flags = []
    for word in RED_FLAG_WORDS:
        if word in lower:
            red_flags.append(f"Suspicious or exaggerated claim detected: {word}")
    for word in ERROR_WORDS:
        if word in lower:
            red_flags.append(f"Technical error text appears publicly visible: {word}")
    if has_mixed:
        red_flags.append("Possible mixed-content references detected on an HTTPS page.")

    legal_count = sum(1 for k in ["privacy", "terms", "refund", "faq", "about"] if found_pages.get(k))
    signals = {
        "https": final_url.startswith("https://"),
        "legal_pages_count": legal_count,
        "has_contact": has_contact,
        "clear_offer": clear_offer,
        "social_proof": social_proof,
        "ux_clear": ux_clear,
        "security_headers_count": len(security_headers),
        "red_flags_count": len(red_flags),
    }
    trust_score, conversion_risk, score_details = score_report(signals)

    missing = []
    for key in ["about", "contact", "privacy", "terms", "refund", "faq"]:
        if not found_pages.get(key):
            missing.append(key.title().replace("Faq", "FAQ") + " page or link")
    if not has_price:
        missing.append("Clear pricing or plan information")
    if not social_proof:
        missing.append("Testimonials, reviews, case studies, or trust badges")
    if len(security_headers) < 2:
        missing.append("Basic security headers")

    problems = []
    if not signals["https"]: problems.append("The site is not using HTTPS as the final loaded URL.")
    if legal_count < 2: problems.append("Legal/trust pages are missing or not easy to find.")
    if not has_contact: problems.append("Visitors may struggle to find a reliable contact path.")
    if not has_cta: problems.append("The main call-to-action is weak or unclear.")
    if not social_proof: problems.append("Social proof is weak or missing.")
    if not has_price: problems.append("Pricing or purchase clarity appears limited.")
    problems.extend(red_flags)
    if not problems:
        problems = ["No critical trust blocker detected in the first-page scan."]

    recommendations = []
    def rec(priority, title, detail):
        recommendations.append({"priority": priority, "title": title, "detail": detail})
    if legal_count < 2: rec("Critical", "Add visible legal pages", "Add Privacy Policy, Terms, Refund/Return Policy and link them from the footer.")
    if not has_contact: rec("High", "Make contact information obvious", "Add a contact page, support email, business identity, and expected response time.")
    if not has_cta: rec("High", "Clarify the primary action", "Use one clear CTA above the fold, such as Start Free Audit, Buy Now, or Book a Demo.")
    if not has_price: rec("Medium", "Improve pricing clarity", "Show plan prices, what is included, and what happens after purchase.")
    if not social_proof: rec("Medium", "Add proof that real users trust you", "Add testimonials, client logos, reviews, screenshots, or case-study snippets.")
    if len(security_headers) < 2: rec("Medium", "Improve visible security posture", "Add common security headers through your hosting or reverse proxy configuration.")
    if red_flags: rec("Critical", "Remove public red flags", "Remove technical errors, exaggerated claims, and mixed-content references.")
    if not recommendations: rec("Low", "Keep improving clarity", "Run this audit again after major landing-page or checkout changes.")

    report = {
        "url": url,
        "final_url": final_url,
        "title": title,
        "meta_description": meta_desc,
        "trust_score": trust_score,
        "conversion_risk": conversion_risk,
        "score_details": score_details,
        "summary": f"TrustLens reviewed the public first page and found a trust score of {trust_score}/100 with {conversion_risk} conversion risk.",
        "top_problems": problems[:5],
        "quick_wins": recommendations[:5],
        "recommendations": recommendations,
        "missing_elements": missing[:12],
        "red_flags": red_flags,
        "signals": {
            "pages_found": found_pages,
            "https": final_url.startswith("https://"),
            "security_headers": security_headers,
            "forms_count": len(forms),
            "internal_links_count": len(set(same_domain_links)),
            "external_links_count": len(set(external_links)),
            "has_cta": has_cta,
            "has_price": has_price,
            "has_email": has_email,
            "has_mixed_content_indicator": has_mixed,
        },
    }
    return report
