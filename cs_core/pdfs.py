"""PDF paperwork: the customer Service Order pack, the Partner Agreement pack and the partner ROI projection."""
import io
import os
from datetime import date

from fpdf import FPDF

from .pricing import money
from .terms import CUSTOMER_TERMS, RESELLER_TERMS, parse_terms, customer_subs, reseller_subs
from .config import ROOT

LOGO = os.path.join(ROOT, "assets", "callscope_logo.png")
INK, MUTE, LINE = (30, 32, 44), (110, 116, 135), (222, 224, 236)

_MAP = {"–": "-", "—": "-", "‘": "'", "’": "'", "“": '"', "”": '"', "•": "-",
        "…": "...", " ": " ", "→": "->", "≥": ">=", "≤": "<="}


def s(x):
    t = str(x if x is not None else "")
    for k, v in _MAP.items():
        t = t.replace(k, v)
    return t.encode("latin-1", "replace").decode("latin-1")


def hx(h, dflt):
    try:
        h = str(h).lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return dflt


def tint(rgb, f):
    return tuple(int(255 - (255 - c) * f) for c in rgb)


class Doc(FPDF):
    def __init__(self, brand, label):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.B = brand
        self.label = label
        self.VIO = hx(brand.get("accent"), (120, 112, 232))
        self.NAVY = hx(brand.get("navy"), (16, 25, 56))
        self.TINT = tint(self.VIO, 0.09)
        self.alias_nb_pages()
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(True, margin=20)

    def header(self):
        B = self.B
        if os.path.exists(LOGO):
            try:
                self.image(LOGO, x=15, y=8, h=17)
            except Exception:
                pass
        self.set_xy(45, 10.5)
        self.set_font("Helvetica", "B", 13); self.set_text_color(*self.NAVY)
        self.cell(90, 6, s(B["trading"]), new_x="LMARGIN", new_y="NEXT")
        self.set_x(45)
        self.set_font("Helvetica", "", 8); self.set_text_color(*MUTE)
        self.cell(100, 4.5, s(f"{B['byline']}  |  {B['tag']}" if B.get("byline") else B.get("tag", "")))
        self.set_xy(120, 11)
        self.set_font("Helvetica", "B", 8); self.set_text_color(*self.VIO)
        self.cell(75, 5, s(self.label), align="R")
        self.set_fill_color(*self.VIO); self.rect(15, 28, 180, 0.9, "F")
        self.set_y(34)

    def footer(self):
        B = self.B
        self.set_y(-14)
        self.set_font("Helvetica", "", 7); self.set_text_color(*MUTE)
        bits = [f"{B['trading']} {B.get('byline', '')}".strip(), B.get("legal", ""), "All figures exclude VAT", "Confidential"]
        self.cell(0, 4, s("  |  ".join(b for b in bits if b)), align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 4, f"Page {self.page_no()} of {{nb}}", align="C")

    # ── building blocks ──
    def doc_title(self, text, sub=""):
        self.set_font("Helvetica", "B", 17); self.set_text_color(*self.NAVY)
        self.cell(0, 9, s(text), new_x="LMARGIN", new_y="NEXT")
        if sub:
            self.set_font("Helvetica", "", 8); self.set_text_color(*MUTE)
            self.cell(0, 5, s(sub), new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def section(self, text):
        self.ln(3)
        y = self.get_y()
        self.set_fill_color(*self.VIO); self.rect(15, y + 0.6, 1.4, 5.2, "F")
        self.set_x(19.5)
        self.set_font("Helvetica", "B", 10.5); self.set_text_color(*self.NAVY)
        self.cell(0, 6.5, s(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(1.5)

    def para(self, text, size=8.5, color=INK, h=4.3):
        self.set_font("Helvetica", "", size); self.set_text_color(*color)
        self.multi_cell(180, h, s(text), new_x="LMARGIN", new_y="NEXT")

    def details_box(self, pairs_left, pairs_right):
        y0 = self.get_y()
        rows = max(len(pairs_left), len(pairs_right))
        h = rows * 6 + 4
        self.set_fill_color(*self.TINT); self.set_draw_color(*tint(self.VIO, 0.3))
        self.rect(15, y0, 180, h, "DF")
        for col, pairs in ((0, pairs_left), (1, pairs_right)):
            for i, (k, v) in enumerate(pairs):
                x = 18 + col * 90
                self.set_xy(x, y0 + 2 + i * 6)
                self.set_font("Helvetica", "B", 7.5); self.set_text_color(*MUTE)
                self.cell(24, 6, s(k))
                self.set_font("Helvetica", "", 8.5); self.set_text_color(*INK)
                self.cell(64, 6, s(v)[:52])
        self.set_y(y0 + h + 2)

    def table(self, cols, rows, bold_cols=(), mute_cols=(), zebra=True, size=8.5):
        """cols: [(header, width, align)]. rows: list of lists of strings."""
        self.set_fill_color(*self.NAVY); self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 8)
        for h, w, a in cols:
            self.cell(w, 7, s(" " + h + " ") if a == "L" else s(h + " "), align=a, fill=True)
        self.ln(7)
        for i, r in enumerate(rows):
            if self.get_y() > 265:
                self.add_page()
            fill = zebra and i % 2 == 1
            self.set_fill_color(*tint(self.VIO, 0.05))
            for j, (v, (h, w, a)) in enumerate(zip(r, cols)):
                self.set_font("Helvetica", "B" if j in bold_cols else "", size)
                self.set_text_color(*(MUTE if j in mute_cols else INK))
                self.cell(w, 6.6, s(" " + str(v) + " ") if a == "L" else s(str(v) + " "), align=a, fill=fill)
            self.ln(6.6)

    def total_bar(self, label, value):
        self.set_fill_color(*self.NAVY); self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 9.5)
        self.cell(140, 8.5, s("  " + label), fill=True)
        self.cell(40, 8.5, s(value + " "), align="R", fill=True, new_x="LMARGIN", new_y="NEXT")

    def callout(self, head, body):
        y0 = self.get_y() + 2
        self.set_xy(18, y0 + 2)
        self.set_font("Helvetica", "B", 8.5); self.set_text_color(*self.VIO)
        self.multi_cell(174, 4.5, s(head), new_x="LMARGIN", new_y="NEXT")
        self.set_x(18)
        self.set_font("Helvetica", "", 7.8); self.set_text_color(*INK)
        self.multi_cell(174, 4, s(body), new_x="LMARGIN", new_y="NEXT")
        y1 = self.get_y() + 2
        self.set_draw_color(*self.VIO); self.set_line_width(0.35)
        self.rect(15, y0, 180, y1 - y0, "D")
        self.set_line_width(0.2)
        self.set_y(y1 + 1)

    def tiles(self, items, per_row=4):
        w = (180 - (per_row - 1) * 3) / per_row
        for start in range(0, len(items), per_row):
            y0 = self.get_y()
            for i, (k, v) in enumerate(items[start:start + per_row]):
                x = 15 + i * (w + 3)
                self.set_fill_color(*self.TINT); self.set_draw_color(*tint(self.VIO, 0.3))
                self.rect(x, y0, w, 15, "DF")
                self.set_xy(x + 3, y0 + 2)
                self.set_font("Helvetica", "B", 6.5); self.set_text_color(*MUTE)
                self.cell(w - 6, 4, s(k.upper()))
                self.set_xy(x + 3, y0 + 7.5)
                self.set_font("Helvetica", "B", 9); self.set_text_color(*self.NAVY)
                self.cell(w - 6, 5, s(v))
            self.set_y(y0 + 18)

    def bars(self, values, labels, sub=None, h=26):
        if not values:
            return
        n = len(values)
        top = max(values) or 1
        gap = 4
        w = min(32, (180 - gap * (n - 1)) / n)
        y0 = self.get_y() + 2
        base = y0 + h
        for i, v in enumerate(values):
            x = 15 + i * (w + gap)
            bh = max(1.5, h * v / top)
            f = 0.45 + 0.55 * (i / max(1, n - 1))
            self.set_fill_color(*tint(self.VIO, f))
            self.rect(x, base - bh, w, bh, "F")
            self.set_xy(x, base + 1)
            self.set_font("Helvetica", "B", 7.5); self.set_text_color(*INK)
            self.cell(w, 4, s(labels[i]), align="C")
            if sub:
                self.set_xy(x, base + 4.6)
                self.set_font("Helvetica", "", 6.8); self.set_text_color(*MUTE)
                self.cell(w, 3.5, s(sub[i]), align="C")
        self.set_y(base + 10)

    def bullets(self, items, size=8.3):
        for it in items:
            self.set_x(17)
            self.set_font("Helvetica", "", size); self.set_text_color(*MUTE)
            self.cell(4, 4.4, "-")
            self.set_text_color(*INK)
            self.multi_cell(174, 4.4, s(it), new_x="LMARGIN", new_y="NEXT")

    def terms_pages(self, title, terms, provider_line):
        self.add_page()
        self.doc_title(title, provider_line)
        for head, paras in terms:
            if self.get_y() > 258:
                self.add_page()
            self.ln(1.6)
            self.set_fill_color(*self.TINT); self.set_text_color(*self.VIO); self.set_font("Helvetica", "B", 8)
            self.cell(180, 5.2, s("  " + head), fill=True, new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(*INK); self.set_font("Helvetica", "", 7.1)
            for p in paras:
                self.multi_cell(180, 3.5, s(p), align="J", new_x="LMARGIN", new_y="NEXT")
                self.ln(0.6)

    def sign_block(self, heading, left_title, left_lines, right_title, right_lines):
        if self.get_y() > 225:
            self.add_page()
        self.ln(3)
        self.set_fill_color(*self.NAVY); self.set_text_color(255, 255, 255); self.set_font("Helvetica", "B", 8.5)
        self.cell(180, 7, s("  " + heading), fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        y0 = self.get_y()
        for col, (t, lines) in enumerate(((left_title, left_lines), (right_title, right_lines))):
            self.set_xy(15 + col * 92, y0)
            self.set_font("Helvetica", "B", 8.3); self.set_text_color(*INK)
            self.cell(88, 5.5, s(t))
            for i, ln in enumerate(lines):
                self.set_xy(15 + col * 92, y0 + 6 + i * 6.2)
                self.set_font("Helvetica", "", 8.3)
                self.cell(88, 6, s(ln))
        self.set_y(y0 + 6 + max(len(left_lines), len(right_lines)) * 6.2 + 2)


def _blank(v, n=24):
    return v if v else "_" * n


# ─────────────────────────── CUSTOMER PACK ───────────────────────────
def customer_pack(cfg, q, cust, prepared_by="", show_review=False, terms_text=None):
    B = cfg["brand"]
    q = dict(q, show_review=show_review)
    pdf = Doc(B, "SERVICE ORDER")
    pdf.add_page()
    today = date.today().strftime("%d %B %Y")
    pdf.doc_title(f"{B['trading']} Service Order", f"Prepared {today}" + (f"  |  by {prepared_by}" if prepared_by else ""))
    contact = cust.get("contact", "") + (f" - {cust['position']}" if cust.get("position") else "")
    pdf.details_box([("Customer", cust.get("company", "")), ("Contact", contact), ("Email", cust.get("email", ""))],
                    [("Company no.", cust.get("company_no", "")), ("Address", cust.get("address", "")),
                     ("Telephone", cust.get("phone", ""))])

    pdf.section(f"Your {B['trading']} services")
    disc = q["discount"] > 0
    cols = [("Service", 95, "L"), ("Qty", 15, "C"), ("Standard /mo", 24, "R"), ("Your price /mo", 23, "R"), ("Monthly total", 23, "R")]
    rows = [[l["name"], l["qty"], money(l["rrp"]), money(l["price"]), money(l["total"])] for l in q["lines"]]
    pdf.table(cols, rows, bold_cols=(3, 4), mute_cols=(2,), zebra=False)
    pdf.total_bar("Monthly total at the start of the agreement (excl. VAT)", money(q["monthly_total"]))
    if disc:
        if q["years"] <= 1 or q["style"] == "fixed":
            body = "Applies for the whole of your minimum term - see the Price Schedule on the next page."
            head = f"Your discount: {q['discount']:g}% off the standard price"
        else:
            body = ("Applies for the first 12 months, then reduces in steps to the standard price - "
                    "see the Price Schedule on the next page.")
            head = f"Introductory discount: {q['discount']:g}% off the standard price"
        pdf.callout(head, body)

    if q["setup"]:
        pdf.section("One-off set-up")
        cols = [("Item", 130, "L"), ("Qty", 20, "C"), ("Price (excl. VAT)", 30, "R")]
        rows = [[x["name"], x["qty"], money(x["total"])] for x in q["setup"]]
        pdf.table(cols, rows, zebra=False)
        note = {"invoice": "Set-up is invoiced when your Order is accepted.",
                "spread": f"Set-up is spread over your first 12 months: {money(q['setup_list_total'] / 12)} per month on top of the charges above.",
                "waived": "Set-up has been waived for this Order.",
                "included": "Set-up is included in your separate equipment or telephony agreement and spread over its term."}[q["setup_mode"]]
        pdf.set_font("Helvetica", "I", 7.5); pdf.set_text_color(*MUTE)
        pdf.cell(0, 5, s(note), new_x="LMARGIN", new_y="NEXT")

    pdf.section("Your agreement at a glance")
    pdf.tiles([("Minimum term", f"{q['term']} months"), ("Billing", "Monthly in advance"),
               ("Start date", "On go-live"), ("Renewal", f"Rolling {int(cfg['renewal_months'])} months")])
    pdf.set_font("Helvetica", "", 7.5); pdf.set_text_color(*MUTE)
    pdf.multi_cell(180, 4, s(f"This Order is a stand-alone agreement for {B['trading']} services. The {B['trading']} Terms & Conditions "
                             "are on the last pages of this document."), new_x="LMARGIN", new_y="NEXT")

    # ── Price schedule ──
    pdf.label = "PRICE SCHEDULE"
    pdf.add_page()
    pdf.doc_title("Your Price Schedule", f"How your monthly {B['trading']} charges move over your {q['term']}-month agreement")
    sched = q["schedule"]
    std = q["standard_monthly"]
    if q["years"] <= 1 or q["style"] == "fixed" or not disc:
        intro = (f"Your monthly charge is {money(q['monthly_total'])}"
                 + (f", which includes a {q['discount']:g}% discount on your modules (standard price {money(std)} per month)" if disc else "")
                 + f" and applies for your whole {q['term']}-month minimum term.")
    else:
        intro = (f"You are receiving an introductory discount of {q['discount']:g}% on the standard {B['trading']} price. "
                 f"It applies in full for your first 12 months. After that it reduces in equal steps each year, so that in year "
                 f"{q['years']} - the final year of your agreement - you pay the full standard price of {money(std)} per month. "
                 "It does not jump straight to the full price after the first year.")
    if q["review_pct"] > 0:
        intro += (f" The annual price review of {q['review_pct']:g}% is " +
                  ("included in the figures below." if show_review else "applied on top of the figures below."))
    pdf.para(intro)
    pdf.ln(3)
    col_m = "Monthly charge" + (" (incl. review)" if show_review else "")
    cols = [("Year", 25, "L"), ("Months", 40, "L"), (col_m, 40, "R"), ("Change on last year", 40, "R"), ("Discount remaining", 35, "R")]
    rows, prev = [], None
    for r in sched:
        mo = r["monthly_with_review"] if show_review else r["monthly"]
        ch = "-" if prev is None else ("+ " + money(mo - prev) if mo >= prev else "- " + money(prev - mo))
        dl = "Standard price" if r["discount"] <= 0 else f"{r['discount']:g}% off"
        rows.append([f"Year {r['year']}", f"Months {r['months']}", money(mo), ch, dl])
        prev = mo
    pdf.table(cols, rows, bold_cols=(2,))
    pdf.set_font("Helvetica", "I", 7.5); pdf.set_text_color(*MUTE)
    pdf.cell(0, 5, s(f"All figures are per month, exclude VAT, and apply to the {B['trading']} services listed on your Order."),
             new_x="LMARGIN", new_y="NEXT")
    vals = [(r["monthly_with_review"] if show_review else r["monthly"]) for r in sched]
    pdf.bars(vals, [money(v) for v in vals], [f"Year {r['year']}" for r in sched])

    pdf.section("What this means")
    pts = []
    if q["years"] > 1 and q["style"] == "stepped" and disc:
        pts.append(f"Months 1 to 12: you pay your discounted price of {money(sched[0]['monthly'])} per month.")
        pts.append(f"From month 13 the discount reduces in equal annual steps. By year {q['years']} - the end of your agreement - "
                   "you pay the full standard price.")
    else:
        pts.append(f"Your monthly charge of {money(q['monthly_total'])} applies for the whole minimum term"
                   + (", subject to the annual price review." if q["review_pct"] > 0 else "."))
    pts.append("After your minimum term, the standard price then in force applies (see the Terms & Conditions, clause 11).")
    pts.append("If you add or remove users or modules, this schedule is recalculated in the same way.")
    if q["review_pct"] > 0:
        pts.append(f"An annual price review of {q['review_pct']:g}% applies on each anniversary of your start date. "
                   + ("The figures above include it." if show_review else "The figures above are before that review and before VAT."))
    pts.append(f"Total value of your monthly services over the minimum term: {money(q['services_value_with_review'] if show_review else q['services_value'])}"
               + (" before the annual review" if (q["review_pct"] > 0 and not show_review) else "") + ".")
    pdf.bullets(pts)

    left = [f"Company:  {cust.get('company', '')}", f"Name:  {cust.get('contact', '')}", f"Position:  {cust.get('position', '')}",
            "Date:  ____ / ____ / ________", "Signature:  ________________________________"]
    right = [f"Name:  {_blank(prepared_by)}", f"Date:  {date.today().strftime('%d/%m/%Y')}", "Signature:  ________________________"]
    pdf.sign_block(f"Agreement - I have read and agree to this Order, the Price Schedule and the {B['trading']} Terms & Conditions",
                   "For and on behalf of the Customer", left, f"For and on behalf of {B['legal']}", right)

    pdf.label = "TERMS & CONDITIONS"
    terms = parse_terms(terms_text or cfg.get("terms_customer") or CUSTOMER_TERMS, customer_subs(cfg, q))
    pdf.terms_pages(f"{B['trading']} Terms & Conditions", terms,
                    f"Provided by {B['legal']}" + (f"  |  {B['address']}" if B.get("address") else ""))
    return bytes(pdf.output())


# ─────────────────────────── PARTNER PACK ───────────────────────────
def partner_pack(cfg, sim, partner, prepared_by="", white_label=False, terms_text=None):
    B, R = cfg["brand"], cfg["reseller"]
    tier = sim["tier"]
    pdf = Doc(B, "PARTNER ORDER")
    pdf.add_page()
    today = date.today().strftime("%d %B %Y")
    pdf.doc_title(f"{B['trading']} Partner Order", f"Prepared {today}" + (f"  |  by {prepared_by}" if prepared_by else ""))
    contact = partner.get("contact", "") + (f" - {partner['position']}" if partner.get("position") else "")
    pdf.details_box([("Partner", partner.get("company", "")), ("Contact", contact), ("Email", partner.get("email", ""))],
                    [("Company no.", partner.get("company_no", "")), ("Address", partner.get("address", "")),
                     ("Telephone", partner.get("phone", ""))])

    pdf.section("Your partner tier")
    wl_txt = "Included" if tier.get("white_label") else ("Yes - " + money(R["white_label_fee"]) + "/mo" if white_label else "Co-branded")
    pdf.tiles([("Tier", tier["name"]), ("Discount off RRP", f"{sim['discount']:g}%"),
               ("Commitment", f"{int(tier['commit'])} licences" if tier["commit"] else "None"),
               ("Partner term", f"{sim['term']} months"),
               ("Ramp period", f"{int(R['ramp_months'])} months" if tier["commit"] else "n/a"),
               ("Onboarding fee", money(tier["onboarding"]) if tier["onboarding"] else "Waived"),
               ("White label", wl_txt), ("Billing", "Monthly in advance")])

    pdf.section("Wholesale price list (monthly, per unit)")
    cols = [("Module", 56, "L"), ("Unit", 28, "L"), ("RRP", 20, "R"), ("Your price", 24, "R"), ("Your margin at RRP", 34, "R"), ("Licence", 18, "C")]
    rows = [[w["name"], w["unit"], money(w["rrp"]), money(w["wholesale"]),
             f"{money(w['partner_margin'])} ({w['partner_margin_pct']:.0f}%)", "Yes" if w["counts_to_commit"] else "No"]
            for w in sim["wholesale"]]
    pdf.table(cols, rows, bold_cols=(3,), mute_cols=(2,))
    mc = cfg["minutes"]
    pdf.set_font("Helvetica", "I", 7.5); pdf.set_text_color(*MUTE)
    pdf.multi_cell(180, 4, s(f"AI minutes: {money(mc['wholesale_per_min'] * 100)} per 100 minutes wholesale (RRP {money(mc['rrp_per_min'] * 100)}). "
                             "'Licence' shows which modules count towards your commitment. Prices exclude VAT."),
                   new_x="LMARGIN", new_y="NEXT")

    pdf.section("One-off set-up (per End Customer)")
    cols = [("Item", 110, "L"), ("RRP", 35, "R"), ("Your price", 35, "R")]
    rows = [[x["name"], money(x["rrp"]), money(x["wholesale"])] for x in cfg["setup"]]
    pdf.table(cols, rows, bold_cols=(2,), mute_cols=(1,))

    # ── Commitment page ──
    pdf.label = "COMMITMENT & TIERS"
    pdf.add_page()
    pdf.doc_title("How your commitment works", "Your tier, the tier ladder and what happens if you grow")
    if tier["commit"]:
        pdf.para(f"You have committed to {int(tier['commit'])} licences. You have {int(R['ramp_months'])} months from your start date to get there. "
                 f"From month {int(R['ramp_months']) + 1}, if you are billed for fewer live licences than your commitment in a month, "
                 f"the gap is charged at {money(sim['shortfall_rate'])} per licence (the lowest licence price on your price list). "
                 "Grow past the next tier for three months in a row and you move up automatically - with a bigger discount.")
    else:
        pdf.para("The Registered tier has no commitment: you pay only for what your customers use. Grow past a tier's commitment "
                 "for three months in a row and you move up automatically - with a bigger discount.")
    pdf.ln(2)
    cols = [("Tier", 30, "L"), ("Commitment", 30, "C"), ("Discount off RRP", 32, "C"), ("Onboarding", 28, "R"), ("White label", 28, "C"), ("", 32, "L")]
    rows = []
    for t in R["tiers"]:
        rows.append([t["name"], f"{int(t['commit'])}" if t["commit"] else "None", f"{t['discount']:g}%",
                     money(t["onboarding"]) if t["onboarding"] else "Waived", "Included" if t.get("white_label") else "Optional",
                     "<- your tier" if t["name"] == tier["name"] else ""])
    pdf.table(cols, rows, bold_cols=(0,))
    bonus = [f"{t['months']} months: +{t['bonus']:g}%" for t in R["terms"] if t["bonus"]]
    pdf.set_font("Helvetica", "I", 7.5); pdf.set_text_color(*MUTE)
    pdf.multi_cell(180, 4, s("Longer partner terms add to your discount - " + ", ".join(bonus) + ". "
                             f"Wholesale prices never fall below our cost plus {R['floor_margin_pct']:g}%, so a few modules carry a smaller discount than your tier."),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.section("Key points")
    pdf.bullets([
        f"Partner term: {sim['term']} months, then rolling 12 months unless either side gives {int(cfg['notice_days'])} days' notice.",
        "Each End Customer subscription runs for at least 12 months from its own go-live date.",
        "You set your own prices to your customers. You pay us whether or not your customer pays you.",
        f"Wholesale prices rise by {R['annual_review_pct']:g}% on each anniversary of your start date (annual price review).",
        "You provide first-line support; we support your team (second line) and provide training and sales material.",
        f"We will not approach customers you introduce to sell to them directly (see clause 14 of the Partner Terms).",
    ])
    left = [f"Company:  {partner.get('company', '')}", f"Name:  {partner.get('contact', '')}", f"Position:  {partner.get('position', '')}",
            "Date:  ____ / ____ / ________", "Signature:  ________________________________"]
    right = [f"Name:  {_blank(prepared_by)}", f"Date:  {date.today().strftime('%d/%m/%Y')}", "Signature:  ________________________"]
    pdf.sign_block(f"Agreement - I have read and agree to this Partner Order, the Wholesale Price List and the {B['trading']} Partner Terms",
                   "For and on behalf of the Partner", left, f"For and on behalf of {B['legal']}", right)

    pdf.label = "PARTNER TERMS"
    terms = parse_terms(terms_text or cfg.get("terms_reseller") or RESELLER_TERMS, reseller_subs(cfg, sim["term"]))
    pdf.terms_pages(f"{B['trading']} Partner Terms", terms,
                    f"Provided by {B['legal']}" + (f"  |  {B['address']}" if B.get("address") else ""))
    return bytes(pdf.output())


# ─────────────────────────── PARTNER ROI PROJECTION ───────────────────────────
def partner_roi_pdf(cfg, sim, partner, plan):
    B = cfg["brand"]
    pdf = Doc(B, "PARTNER OPPORTUNITY")
    pdf.add_page()
    name = partner.get("company") or "your business"
    pdf.doc_title(f"Your {B['trading']} partner opportunity", f"Prepared for {name}  |  {date.today().strftime('%d %B %Y')}")
    T = sim["totals"]
    pdf.tiles([("Profit over term", money(T["profit"], 0)), ("Return on spend", f"{sim['roi_pct']:.0f}%"),
               ("Monthly profit by end", money(sim["end_mrr_profit"], 0)),
               ("Pays back", f"Month {sim['payback_month']}" if sim["payback_month"] else "Not within term")])
    pdf.section("The plan behind these numbers")
    pdf.bullets(plan)
    pdf.section("Year by year")
    rows = []
    for y in range(0, sim["term"], 12):
        seg = sim["rows"][y:y + 12]
        rev = sum(r["revenue"] for r in seg); cost = sum(r["wholesale"] + r["shortfall"] + r["fees"] for r in seg)
        rows.append([f"Year {y // 12 + 1}", f"{seg[-1]['customers']:.0f}", f"{seg[-1]['licences']:.0f}", money(rev, 0), money(cost, 0),
                     money(rev - cost, 0), money(seg[-1]["cumulative"], 0)])
    pdf.table([("Year", 22, "L"), ("Customers", 22, "R"), ("Licences", 22, "R"), ("Your revenue", 30, "R"), ("Your cost", 28, "R"),
               ("Profit", 28, "R"), ("Running total", 28, "R")], rows, bold_cols=(5,))
    vals = [sim["rows"][min(len(sim["rows"]) - 1, y + 11)]["cumulative"] for y in range(0, sim["term"], 12)]
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*INK)
    pdf.cell(0, 5, "Running profit at the end of each year", new_x="LMARGIN", new_y="NEXT")
    pdf.bars([max(0, v) for v in vals], [money(v, 0) for v in vals], [f"Year {i + 1}" for i in range(len(vals))])
    pc = sim["per_customer"]
    pdf.section("Per typical customer")
    pdf.bullets([f"You charge {money(pc['resale'])} a month and pay us {money(pc['wholesale'])} - "
                 f"{money(pc['profit'])} profit a month per customer.",
                 f"Set-up: you charge {money(pc['setup_resale'])} and pay us {money(pc['setup_wholesale'])}."])
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 7); pdf.set_text_color(*MUTE)
    pdf.multi_cell(180, 3.6, s("Illustrative projection based on the assumptions above. It is not a forecast or a guarantee of results. "
                               "Figures exclude VAT and the annual price review, and assume customers pay you on time."),
                   new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
