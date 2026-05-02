PLANS = {
    "Free": {"limit": 3, "pdf": False, "white_label": False, "price": 0},
    "Starter": {"limit": 25, "pdf": True, "white_label": False, "price": 19},
    "Pro": {"limit": 150, "pdf": True, "white_label": True, "price": 49},
    "Agency": {"limit": 1000, "pdf": True, "white_label": True, "price": 149},
}

def apply_plan(user, plan_name):
    plan = PLANS.get(plan_name, PLANS["Free"])
    user.plan_name = plan_name if plan_name in PLANS else "Free"
    user.monthly_scan_limit = plan["limit"]
    user.subscription_status = "active"
    return user

def can_download_pdf(user):
    return PLANS.get(user.plan_name, PLANS["Free"]).get("pdf", False)
