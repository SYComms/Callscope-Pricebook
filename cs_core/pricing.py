"""All the Call Scope pricing maths. No Streamlit in here, so it can be tested on its own."""
import math


def r2(x):
    return round(float(x) + 1e-9, 2)


def money(x, dp=2):
    x = float(x or 0)
    sign = "-" if x < 0 else ""
    return f"{sign}£{abs(x):,.{dp}f}"


def mod_by_id(cfg):
    return {m["id"]: m for m in cfg["modules"]}


def setup_by_id(cfg):
    return {s["id"]: s for s in cfg["setup"]}


def max_discount_for(cfg, months):
    for t in cfg["customer_terms"]:
        if int(t["months"]) == int(months):
            return float(t["max_discount"])
    return 0.0


# ─────────────────────────── CUSTOMER (direct) ───────────────────────────
def discount_steps(discount, years, style="stepped"):
    """Discount % for each contract year.
    stepped: full discount in year 1, then equal steps down so the final year is the standard price.
    fixed:   the same discount every year of the term."""
    d = float(discount)
    if years <= 1 or style == "fixed":
        return [d] * max(1, years)
    return [r2(d * (years - 1 - i) / (years - 1)) for i in range(years)]


def customer_quote(cfg, qty, minutes=0, agent_setups=0, term=60, discount=0.0, style="stepped",
                   review_pct=None, setup_mode="invoice"):
    mods = cfg["modules"]
    review = cfg["annual_review_pct"] if review_pct is None else float(review_pct)
    years = max(1, math.ceil(int(term) / 12))
    steps = discount_steps(discount, years, style)

    lines = []
    for m in mods:
        q = int(qty.get(m["id"], 0) or 0)
        if q <= 0:
            continue
        d = steps[0] if m.get("discountable", True) else 0.0
        unit = r2(m["rrp"] * (1 - d / 100))
        lines.append({"id": m["id"], "name": m["name"], "unit_label": m.get("unit", ""), "qty": q,
                      "rrp": r2(m["rrp"]), "price": unit, "total": r2(unit * q), "buy": r2(m["buy"]),
                      "discountable": m.get("discountable", True)})
    mins = int(minutes or 0)
    if mins:
        mc = cfg["minutes"]
        p = r2(mins * mc["rrp_per_min"])
        lines.append({"id": "minutes", "name": f"AI minutes bundle - {mins:,} mins", "unit_label": "per month",
                      "qty": 1, "rrp": p, "price": p, "total": p, "buy": r2(mins * mc["buy_per_min"]),
                      "discountable": False})

    # yearly schedule (unit prices rounded to the penny each year so every document agrees)
    sched = []
    standard = r2(sum(l["rrp"] * l["qty"] for l in lines))
    prev = None
    for y in range(years):
        d = steps[y]
        mo = r2(sum((r2(l["rrp"] * (1 - d / 100)) if l["discountable"] else l["rrp"]) * l["qty"] for l in lines))
        mo_rev = r2(mo * (1 + review / 100) ** y)
        m_from = y * 12 + 1
        m_to = min(int(term), (y + 1) * 12)
        sched.append({"year": y + 1, "months": f"{m_from} - {m_to}", "n_months": m_to - m_from + 1,
                      "discount": d, "monthly": mo, "monthly_with_review": mo_rev,
                      "change": None if prev is None else r2(mo - prev)})
        prev = mo

    # one-off set-up
    sid = setup_by_id(cfg)
    setup = []
    if lines:
        s = sid.get("platform")
        if s:
            setup.append({"name": s["name"], "qty": 1, "price": r2(s["rrp"]), "buy": r2(s["buy"])})
        n_rec = int(qty.get("receptionist", 0) or 0)
        s = sid.get("rec_setup")
        if s and n_rec:
            setup.append({"name": s["name"], "qty": n_rec, "price": r2(s["rrp"]), "buy": r2(s["buy"])})
        s = sid.get("agent_setup")
        if s and agent_setups:
            setup.append({"name": s["name"], "qty": int(agent_setups), "price": r2(s["rrp"]), "buy": r2(s["buy"])})
    for s in setup:
        s["total"] = r2(s["price"] * s["qty"])
    setup_total = r2(sum(s["total"] for s in setup)) if setup_mode != "waived" else 0.0
    setup_list_total = r2(sum(s["total"] for s in setup))

    monthly_total = sched[0]["monthly"] if lines else 0.0
    services_value = r2(sum(s["monthly"] * s["n_months"] for s in sched))
    services_value_rev = r2(sum(s["monthly_with_review"] * s["n_months"] for s in sched))
    buy_mo = r2(sum(l["buy"] * l["qty"] for l in lines))
    setup_buy = r2(sum(s["buy"] * s["qty"] for s in setup))
    profit = r2(services_value - buy_mo * int(term) + setup_total - setup_buy)
    return {
        "lines": lines, "schedule": sched, "setup": setup, "setup_total": setup_total,
        "setup_list_total": setup_list_total, "setup_mode": setup_mode,
        "standard_monthly": standard, "monthly_total": monthly_total, "term": int(term), "years": years,
        "discount": float(discount), "style": style, "review_pct": review,
        "services_value": services_value, "services_value_with_review": services_value_rev,
        "contract_value": r2(services_value + setup_total),
        "buy_monthly": buy_mo, "setup_buy": setup_buy, "profit": profit,
        "saving_vs_standard": r2(standard * int(term) - services_value),
    }


# ─────────────────────────── RESELLER (partner) ───────────────────────────
def tier_by_name(cfg, name):
    for t in cfg["reseller"]["tiers"]:
        if t["name"] == name:
            return t
    return cfg["reseller"]["tiers"][0]


def term_bonus(cfg, months):
    for t in cfg["reseller"]["terms"]:
        if int(t["months"]) == int(months):
            return float(t["bonus"])
    return 0.0


def wholesale_list(cfg, tier_name, term):
    """Per-module wholesale prices for a tier + partner term. Never below our cost + the floor margin."""
    R = cfg["reseller"]
    tier = tier_by_name(cfg, tier_name)
    disc = float(tier["discount"]) + term_bonus(cfg, term)
    out = []
    for m in cfg["modules"]:
        raw = r2(m["rrp"] * (1 - disc / 100))
        floor = r2(m["buy"] * (1 + R["floor_margin_pct"] / 100))
        w = max(raw, floor)
        out.append({"id": m["id"], "name": m["name"], "unit": m.get("unit", ""), "rrp": r2(m["rrp"]),
                    "wholesale": w, "floored": raw < floor, "buy": r2(m["buy"]),
                    "partner_margin": r2(m["rrp"] - w), "partner_margin_pct": (m["rrp"] - w) / m["rrp"] * 100 if m["rrp"] else 0,
                    "effective_discount": (1 - w / m["rrp"]) * 100 if m["rrp"] else 0,
                    "counts_to_commit": m.get("counts_to_commit", True)})
    return out, disc


def shortfall_rate(wl):
    rates = [w["wholesale"] for w in wl if w["counts_to_commit"]]
    return min(rates) if rates else 0.0


def simulate_partner(cfg, tier_name, term, mix, minutes_per_cust=0, start_customers=1, new_per_month=1.0,
                     churn_pct=1.0, resale_discount=0.0, setup_resale_pct=100.0, white_label=False,
                     setups_per_cust=None):
    """Month-by-month projection of a partner's revenue, wholesale cost and profit."""
    R = cfg["reseller"]
    tier = tier_by_name(cfg, tier_name)
    wl, disc = wholesale_list(cfg, tier_name, term)
    wmap = {w["id"]: w for w in wl}
    mc = cfg["minutes"]

    cust_whsl = sum(wmap[k]["wholesale"] * float(q or 0) for k, q in mix.items() if k in wmap)
    cust_rrp = sum(wmap[k]["rrp"] * float(q or 0) for k, q in mix.items() if k in wmap)
    cust_resale = r2(cust_rrp * (1 - float(resale_discount) / 100))
    mins = float(minutes_per_cust or 0)
    cust_whsl += mins * mc["wholesale_per_min"]
    cust_resale += mins * mc["rrp_per_min"]
    cust_buy = sum(wmap[k]["buy"] * float(q or 0) for k, q in mix.items() if k in wmap) + mins * mc["buy_per_min"]
    lic_per_cust = sum(float(q or 0) for k, q in mix.items() if k in wmap and wmap[k]["counts_to_commit"])

    sid = setup_by_id(cfg)
    rec = float(mix.get("receptionist", 0) or 0)
    setup_w = sid["platform"]["wholesale"] + rec * sid["rec_setup"]["wholesale"]
    setup_rrp = sid["platform"]["rrp"] + rec * sid["rec_setup"]["rrp"]
    setup_resale = setup_rrp * float(setup_resale_pct) / 100
    setup_buy = sid["platform"]["buy"] + rec * sid["rec_setup"]["buy"]

    commit = float(tier["commit"])
    sf_rate = shortfall_rate(wl)
    wl_fee = 0.0 if (not white_label or tier.get("white_label")) else float(R["white_label_fee"])
    onboarding = float(tier["onboarding"])

    rows, cum, c = [], -0.0, 0.0
    tot = {"revenue": 0.0, "wholesale": 0.0, "shortfall": 0.0, "fees": onboarding, "profit": 0.0, "ours": 0.0}
    payback = None
    for t in range(1, int(term) + 1):
        new = float(start_customers) + float(new_per_month) if t == 1 else float(new_per_month)
        c = c * (1 - float(churn_pct) / 100) + new
        lic = c * lic_per_cust
        rev = c * cust_resale + new * setup_resale
        cost = c * cust_whsl + new * setup_w
        short = (commit - lic) * sf_rate if (t > R["ramp_months"] and lic < commit) else 0.0
        fee = wl_fee + (onboarding if t == 1 else 0.0)
        p = rev - cost - short - fee
        cum += p
        if payback is None and cum >= 0:
            payback = t
        rows.append({"month": t, "customers": c, "licences": lic, "revenue": rev, "wholesale": cost,
                     "shortfall": short, "fees": fee, "profit": p, "cumulative": cum})
        tot["revenue"] += rev
        tot["wholesale"] += cost
        tot["shortfall"] += short
        tot["fees"] += wl_fee
        tot["profit"] += p
        tot["ours"] += cost - (c * cust_buy + new * setup_buy) + short + fee
    spend = tot["wholesale"] + tot["shortfall"] + tot["fees"]
    last = rows[-1] if rows else {}
    hit = next((r["month"] for r in rows if r["licences"] >= commit), None) if commit else 0
    return {
        "tier": tier, "term": int(term), "discount": disc, "wholesale": wl, "rows": rows, "totals": tot,
        "spend": spend, "roi_pct": (tot["profit"] / spend * 100) if spend else 0.0,
        "margin_pct": (tot["profit"] / tot["revenue"] * 100) if tot["revenue"] else 0.0,
        "payback_month": payback, "commit": commit, "commit_hit_month": hit, "ramp": R["ramp_months"],
        "per_customer": {"resale": cust_resale, "wholesale": cust_whsl, "profit": cust_resale - cust_whsl,
                         "licences": lic_per_cust, "setup_resale": setup_resale, "setup_wholesale": setup_w},
        "end_mrr_profit": (last.get("revenue", 0) - last.get("wholesale", 0) - last.get("shortfall", 0)) if rows else 0.0,
        "end_customers": last.get("customers", 0), "end_licences": last.get("licences", 0),
        "shortfall_rate": sf_rate, "white_label_fee": wl_fee, "onboarding": onboarding,
    }


def compare_tiers(cfg, term, **kw):
    out = []
    for t in cfg["reseller"]["tiers"]:
        s = simulate_partner(cfg, t["name"], term, **kw)
        out.append(s)
    return out
