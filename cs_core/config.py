"""Default prices, terms and branding for the Call Scope pricebook.

Everything here can be changed in the app's Admin area. Admin changes are saved to
config.json (and, if GitHub details are in Streamlit Secrets, committed back to the repo
so they survive Streamlit Cloud restarts). Anything missing from config.json falls back
to the defaults below.
"""
import base64
import copy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config.json")

DEFAULTS = {
    "version": 1,
    "brand": {
        "trading": "Call Scope",
        "byline": "by SY Comms",
        "tag": "Every conversation. More intelligence.",
        "legal": "SY Comms Ltd",
        "address": "Suite C Jupiter House, Sitka Drive, Shrewsbury Business Park, Shrewsbury SY2 6LG",
        "email": "hello@sycomms.co.uk",
        "phone": "",
        "website": "callscope.sycomms.cloud",
        "accent": "#7870E8",
        "navy": "#101938",
    },
    # Monthly modules. buy = our cost, rrp = standard customer price (per unit, per month).
    # discountable: whether the customer introductory discount applies.
    # counts_to_commit: whether it counts as a "licence" towards a reseller's commitment.
    "modules": [
        {"id": "portal", "name": "AI Integration - Portal", "unit": "per user", "buy": 5.00, "rrp": 32.00,
         "discountable": True, "counts_to_commit": True,
         "blurb": "Every call transcribed, summarised and searchable in the Call Scope portal."},
        {"id": "crm", "name": "AI Integration - CRM", "unit": "per user", "buy": 5.00, "rrp": 35.00,
         "discountable": True, "counts_to_commit": True,
         "blurb": "Call summaries and actions written straight into your CRM."},
        {"id": "dashboard", "name": "Manager Dashboard", "unit": "per manager", "buy": 5.00, "rrp": 59.00,
         "discountable": True, "counts_to_commit": True,
         "blurb": "Live team performance, missed-call recovery and trends for managers."},
        {"id": "callscore", "name": "Call Score", "unit": "per user", "buy": 20.00, "rrp": 45.00,
         "discountable": True, "counts_to_commit": True,
         "blurb": "Every call scored against your own standards, with coaching notes."},
        {"id": "receptionist", "name": "AI Receptionist", "unit": "per receptionist", "buy": 69.00, "rrp": 89.00,
         "discountable": True, "counts_to_commit": True,
         "blurb": "Answers, qualifies and routes calls 24/7 in your business's voice."},
        {"id": "widget", "name": "Website Widget", "unit": "per website", "buy": 30.00, "rrp": 50.00,
         "discountable": True, "counts_to_commit": False,
         "blurb": "Let website visitors talk to your AI receptionist from any page."},
    ],
    # AI minutes bundles - priced per minute, never discounted.
    "minutes": {"buy_per_min": 0.10, "rrp_per_min": 0.25, "wholesale_per_min": 0.16,
                "bundles": [500, 1000, 1500, 2000]},
    # One-off set-up items. auto: "always" (once per order), "per_receptionist", or "optional".
    "setup": [
        {"id": "platform", "name": "Call Scope Platform Setup", "buy": 300.00, "rrp": 500.00, "wholesale": 375.00,
         "auto": "always"},
        {"id": "rec_setup", "name": "AI Receptionist Setup", "buy": 69.00, "rrp": 100.00, "wholesale": 85.00,
         "auto": "per_receptionist"},
        {"id": "agent_setup", "name": "Bespoke AI Agent Build", "buy": 1000.00, "rrp": 2500.00, "wholesale": 1750.00,
         "auto": "optional"},
    ],
    # ---- CUSTOMER (direct) pricing ----
    # For each term: the biggest introductory discount a consultant can give.
    "customer_terms": [
        {"months": 12, "max_discount": 10},
        {"months": 24, "max_discount": 20},
        {"months": 36, "max_discount": 30},
        {"months": 48, "max_discount": 35},
        {"months": 60, "max_discount": 40},
        {"months": 72, "max_discount": 40},
        {"months": 84, "max_discount": 40},
    ],
    "annual_review_pct": 5.0,          # annual price review on monthly charges
    "late_payment_fee": 25.0,
    "renewal_months": 12,
    "notice_days": 90,
    # ---- RESELLER (partner) pricing ----
    "reseller": {
        # Each tier: committed licences (counted monthly modules) and discount off RRP.
        "tiers": [
            {"name": "Bronze", "commit": 0, "discount": 30, "onboarding": 495.0, "white_label": False,
             "note": "No commitment - pay as you go"},
            {"name": "Silver", "commit": 25, "discount": 40, "onboarding": 295.0, "white_label": False,
             "note": "Commit to 25 licences"},
            {"name": "Gold", "commit": 50, "discount": 45, "onboarding": 0.0, "white_label": False,
             "note": "Commit to 50 licences - onboarding free"},
            {"name": "Platinum", "commit": 100, "discount": 50, "onboarding": 0.0, "white_label": True,
             "note": "Commit to 100 licences - white label included"},
        ],
        # Extra discount for agreeing a longer partner term.
        "terms": [
            {"months": 12, "bonus": 0.0},
            {"months": 24, "bonus": 2.5},
            {"months": 36, "bonus": 5.0},
            {"months": 48, "bonus": 6.0},
            {"months": 60, "bonus": 7.5},
            {"months": 72, "bonus": 8.5},
            {"months": 84, "bonus": 10.0},
        ],
        "default_term": 36,
        "floor_margin_pct": 25.0,      # wholesale never goes below our cost + this %
        "ramp_months": 6,              # months to reach the commitment before shortfall applies
        "white_label_fee": 149.0,      # monthly, unless the tier includes it
        "annual_review_pct": 5.0,
        "payment_days": 14,
    },
    "terms_customer": "",   # blank = use the default text in cs_core/terms.py
    "terms_reseller": "",
}


def deep_merge(base, extra):
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_config():
    cfg = copy.deepcopy(DEFAULTS)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = deep_merge(cfg, json.load(f))
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return cfg


def config_json(cfg):
    return json.dumps(cfg, indent=2, ensure_ascii=False)


def save_local(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(config_json(cfg))
        return True, "Saved to config.json on this server."
    except Exception as e:
        return False, f"Could not save locally: {e}"


def save_github(cfg, token, repo, branch="main", path="config.json"):
    """Commit config.json to the GitHub repo so changes survive a Streamlit restart."""
    import requests
    if not (token and repo):
        return False, "GitHub not set up - add GITHUB_TOKEN and GITHUB_REPO to Streamlit Secrets."
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    try:
        r = requests.get(url, headers=h, params={"ref": branch}, timeout=15)
        sha = r.json().get("sha") if r.status_code == 200 else None
        body = {"message": "Update Call Scope pricebook settings (from the app)",
                "content": base64.b64encode(config_json(cfg).encode("utf-8")).decode(),
                "branch": branch}
        if sha:
            body["sha"] = sha
        r = requests.put(url, headers=h, json=body, timeout=20)
        if r.status_code in (200, 201):
            return True, "Saved to GitHub - the settings will survive restarts."
        return False, f"GitHub said {r.status_code}: {r.text[:160]}"
    except Exception as e:
        return False, f"Could not reach GitHub: {e}"
