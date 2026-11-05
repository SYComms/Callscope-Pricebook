"""Call Scope Pricebook - stand-alone quoting for Call Scope.

Two sides:
  * Customer quote  - direct sale to a business: services, term, stepped introductory discount,
                      Service Order + Price Schedule + T&Cs PDF.
  * Reseller partner - wholesale pricing by tier/commitment/term, partner ROI view,
                      Partner Agreement PDF and ROI projection PDF.
Plus an Admin area for prices, tiers, branding and terms.
"""
import copy
import hmac
import io
import html as html_lib
import inspect
import json
import os
import re
from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from cs_core.config import DEFAULTS, ROOT, load_config, config_json, save_local, save_github, deep_merge
from cs_core.pricing import (money, customer_quote, max_discount_for, wholesale_list, simulate_partner,
                             compare_tiers, tier_by_name)
from cs_core.pdfs import customer_pack, partner_pack, partner_roi_pdf
from cs_core.terms import CUSTOMER_TERMS, RESELLER_TERMS
from cs_core.zoho import Zoho

try:
    from streamlit_drawable_canvas import st_canvas
    CANVAS_OK = True
except Exception:
    CANVAS_OK = False

LOGO = os.path.join(ROOT, "assets", "callscope_logo.png")
st.set_page_config(page_title="Call Scope Pricebook", page_icon=LOGO, layout="wide", initial_sidebar_state="expanded")

# ─────────────────────────── DESIGN SYSTEM ───────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--bg:#0A0E1A;--surface:#111827;--surface-2:#161F33;--surface-3:#1C2740;--border:rgba(148,163,184,.14);--border-strong:rgba(148,163,184,.26);--text:#E7EAF3;--muted:#8C98B0;--faint:#5E6A82;--accent:#7C83FF;--accent-2:#38D6F5;--accent-soft:rgba(124,131,255,.14);--good:#34D399;--warn:#FBBF24;--risk:#FB923C;--bad:#F87171;--radius:14px;--grad:linear-gradient(135deg,#7C83FF 0%,#38D6F5 100%);}
html,body,[class*="css"],.stApp,button,input,textarea,select{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif!important}
.stApp{background:radial-gradient(1200px 500px at 85% -10%,rgba(56,214,245,.07),transparent 60%),radial-gradient(900px 500px at 10% -20%,rgba(124,131,255,.10),transparent 60%),var(--bg)}
[data-testid="stHeader"]{background:transparent}[data-testid="stDecoration"]{display:none}footer{visibility:hidden}
[class*="viewerBadge"],[data-testid="stAppDeployButton"],[data-testid="appCreatorAvatar"]{display:none!important}
h1>div>a,h2>div>a,h3>div>a,h4>div>a{display:none!important}
.block-container{padding-top:1.6rem!important;padding-bottom:3rem!important;max-width:1500px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0D1322 0%,#0A0E1A 100%);border-right:1px solid var(--border)}
[data-testid="stWidgetLabel"] p{font-size:.76rem!important;font-weight:600!important;color:var(--muted)!important;text-transform:uppercase;letter-spacing:.06em}
[data-testid="stCaptionContainer"]{color:var(--muted)!important}
[class*="st-key-card-"]{background:linear-gradient(180deg,rgba(22,31,51,.85) 0%,rgba(17,24,39,.85) 100%);border:1px solid var(--border)!important;border-radius:var(--radius);padding:22px 22px 18px;box-shadow:0 1px 0 rgba(255,255,255,.03) inset,0 20px 40px -24px rgba(0,0,0,.6);margin-bottom:18px}
[data-testid="stColumn"]:has(.st-key-card-summary),[data-testid="stColumn"]:has(.st-key-card-rsummary){position:sticky;top:1rem;align-self:flex-start}
[class*="st-key-prod-"]{background:var(--surface);border:1px solid var(--border)!important;border-radius:12px;padding:14px 14px 6px;transition:all .15s ease}
[class*="st-key-prod-"]:has(.pe-on){border-color:rgba(56,214,245,.55)!important;box-shadow:0 0 0 3px rgba(56,214,245,.10),0 12px 30px -18px rgba(56,214,245,.6)}
[data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="textarea"]{background:var(--surface)!important;border:1px solid var(--border-strong)!important;border-radius:10px!important}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within,[data-baseweb="textarea"]:focus-within{border-color:var(--accent)!important;box-shadow:0 0 0 3px var(--accent-soft)!important}
[data-baseweb="input"]>div,[data-baseweb="base-input"]{background:transparent!important}
.stButton button,.stDownloadButton button,.stFormSubmitButton button{border-radius:10px!important;font-weight:600!important;border:1px solid var(--border-strong)!important;background:var(--surface-2)!important;color:var(--text)!important;transition:all .15s ease}
.stButton button:hover,.stDownloadButton button:hover{border-color:var(--accent)!important;transform:translateY(-1px)}
.stButton button[kind="primary"],.stDownloadButton button[kind="primary"],.stFormSubmitButton button,[data-testid="stBaseButton-primary"]{background:var(--grad)!important;border:none!important;color:#0A0E1A!important;box-shadow:0 8px 24px -10px rgba(124,131,255,.8)}
.stButton button[kind="primary"] p,.stDownloadButton button[kind="primary"] p,[data-testid="stBaseButton-primary"] p,.stFormSubmitButton button p{color:#0A0E1A!important;font-weight:700!important}
[data-testid="stTabs"] [role="tablist"],[data-baseweb="tab-list"]{gap:4px;background:var(--surface);padding:4px;border-radius:12px;border:1px solid var(--border);width:fit-content;max-width:100%;overflow-x:auto}
[data-testid="stTabs"] [role="tab"],[data-baseweb="tab"]{border-radius:9px!important;padding:8px 16px!important;color:var(--muted)!important;background:transparent!important}
[data-testid="stTabs"] [role="tab"][aria-selected="true"],[data-baseweb="tab"][aria-selected="true"]{background:var(--surface-3)!important;color:var(--text)!important}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"],[data-testid="stTabs"] .react-aria-SelectionIndicator{display:none!important}
[data-testid="stButtonGroup"]{background:var(--surface);padding:4px;border-radius:12px;border:1px solid var(--border);width:fit-content;max-width:100%;margin-bottom:8px}
[data-testid="stButtonGroup"] button{border:none!important;border-radius:9px!important;background:transparent!important;color:var(--muted)!important;padding:6px 16px!important}
[data-testid="stButtonGroup"] button[kind*="Active"],[data-testid="stButtonGroup"] button[aria-checked="true"]{background:var(--surface-3)!important;color:var(--text)!important}
[data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:12px;overflow:hidden}
[data-testid="stExpander"] details{background:var(--surface);border:1px solid var(--border)!important;border-radius:12px!important}
[data-testid="stAlert"]{border-radius:12px!important}
.pe-hero{display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;padding:6px 2px 22px;margin-bottom:18px;border-bottom:1px solid var(--border)}
.pe-eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:.72rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-2);margin-bottom:8px}
.pe-eyebrow .dot{width:7px;height:7px;border-radius:50%;background:var(--good);box-shadow:0 0 0 4px rgba(52,211,153,.15)}
.pe-title{font-size:2.05rem;font-weight:800;letter-spacing:-.035em;line-height:1.1;color:var(--text)}
.pe-title span{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.pe-sub{color:var(--muted);font-size:.95rem;margin-top:8px;max-width:640px}
.pe-stepper{display:flex;align-items:center;gap:6px;background:var(--surface);border:1px solid var(--border);border-radius:999px;padding:6px;flex-wrap:wrap}
.pe-step{display:flex;align-items:center;gap:8px;padding:7px 14px 7px 7px;border-radius:999px;font-size:.82rem;font-weight:600;color:var(--faint);white-space:nowrap}
.pe-step .num{width:24px;height:24px;border-radius:50%;display:grid;place-items:center;font-size:.72rem;font-weight:700;border:1px solid var(--border-strong)}
.pe-step.done{color:var(--muted)}.pe-step.done .num{background:rgba(52,211,153,.14);border-color:rgba(52,211,153,.45);color:var(--good)}
.pe-step.active{background:var(--surface-3);color:var(--text)}.pe-step.active .num{background:var(--grad);border:none;color:#0A0E1A}
.pe-step-sep{width:14px;height:1px;background:var(--border-strong)}
.pe-section{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.pe-section .badge{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:var(--accent-soft);color:var(--accent);font-weight:800;font-size:.85rem;border:1px solid rgba(124,131,255,.3)}
.pe-section .t{font-size:1.08rem;font-weight:700;color:var(--text)}.pe-section .s{font-size:.82rem;color:var(--muted);margin-top:2px}
.pe-chip{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;font-size:.76rem;font-weight:600;background:var(--surface-3);color:var(--text);border:1px solid var(--border);white-space:nowrap;margin:0 4px 4px 0}
.pe-chip.accent{background:var(--accent-soft);color:#B9BDFF;border-color:rgba(124,131,255,.3)}
.pe-chip.good{background:rgba(52,211,153,.12);color:var(--good);border-color:rgba(52,211,153,.3)}
.pe-chip.warn{background:rgba(251,191,36,.12);color:var(--warn);border-color:rgba(251,191,36,.3)}
.pe-chip.bad{background:rgba(248,113,113,.12);color:var(--bad);border-color:rgba(248,113,113,.3)}
.pe-login-head{text-align:center;margin:8vh 0 22px}
.pe-login-head img{width:120px;background:#fff;border-radius:16px;padding:10px 14px;margin:0 auto 16px;display:block}
.pe-login-head .t{font-size:1.6rem;font-weight:800;letter-spacing:-.03em;color:var(--text)}.pe-login-head .s{color:var(--muted);font-size:.92rem;margin-top:6px}
.pe-kpi{background:var(--surface);border:1px solid var(--border);border-top:2px solid var(--accent);border-radius:14px;padding:16px 18px;height:100%}
.pe-kpi .l{font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.pe-kpi .v{font-size:1.75rem;font-weight:800;letter-spacing:-.03em;color:var(--text);margin-top:6px}
.pe-kpi .n{font-size:.78rem;color:var(--muted);margin-top:4px}
.pe-kpi.good{border-top-color:var(--good)}
.pe-brand{display:flex;align-items:center;gap:12px;padding:4px 0 14px;border-bottom:1px solid var(--border);margin-bottom:14px}
.pe-brand img{width:46px;height:46px;object-fit:contain;background:#fff;border-radius:12px;padding:4px}
.pe-brand .n{font-weight:800;color:var(--text);font-size:1.02rem;letter-spacing:-.02em}.pe-brand .t{font-size:.76rem;color:var(--muted)}
.pe-on{display:none}
.pe-flow{display:grid;grid-template-columns:1fr 34px 1fr 34px 1fr;gap:8px;align-items:stretch}
.pe-flow .arrow{display:grid;place-items:center;color:var(--accent-2);font-size:1.5rem;font-weight:800}
@media (max-width:900px){.pe-flow{grid-template-columns:1fr}.pe-flow .arrow{transform:rotate(90deg)}}
.pe-note{background:var(--accent-soft);border:1px solid rgba(124,131,255,.3);border-radius:12px;padding:10px 14px;font-size:.86rem;color:var(--text);margin-bottom:14px}
.pe-split{display:flex;height:34px;border-radius:10px;overflow:hidden;gap:2px;margin:10px 0 6px}
.pe-split div{display:grid;place-items:center;font-size:.76rem;font-weight:700;color:#0A0E1A;white-space:nowrap;overflow:hidden}
.pe-legend{display:flex;gap:18px;flex-wrap:wrap;font-size:.8rem;color:var(--muted)}
.pe-legend span:before{content:"";display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;background:var(--c)}
.pe-steps{counter-reset:s;margin:0 0 6px;padding:0;list-style:none}
.pe-steps li{counter-increment:s;display:flex;gap:10px;align-items:flex-start;color:var(--muted);font-size:.86rem;margin-bottom:10px}
.pe-steps li:before{content:counter(s);flex:none;width:22px;height:22px;border-radius:50%;display:grid;place-items:center;background:var(--accent-soft);color:var(--accent);font-weight:800;font-size:.72rem;border:1px solid rgba(124,131,255,.3)}
.pe-steps b{color:var(--text)}
.pe-prod-name{font-weight:700;color:var(--text);font-size:.95rem}
.pe-prod-price{font-size:.8rem;color:var(--muted);margin:2px 0 4px}.pe-prod-price b{color:#B9BDFF}
.pe-prod-blurb{font-size:.78rem;color:var(--faint);line-height:1.35;min-height:2.1em;margin-bottom:6px}
.pe-sum-big{font-size:2.3rem;font-weight:800;letter-spacing:-.04em;color:var(--text);line-height:1.05}
.pe-sum-label{font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.pe-sum-strike{color:var(--faint);text-decoration:line-through;font-size:.9rem;margin-left:6px}
.pe-row{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid var(--border);font-size:.86rem;color:var(--muted)}
.pe-row b{color:var(--text);font-weight:700}
.pe-row:last-child{border-bottom:none}
.pe-empty{display:flex;gap:16px;align-items:flex-start;padding:18px;border:1px dashed var(--border-strong);border-radius:14px;background:rgba(17,24,39,.5)}
.pe-empty .ic{width:44px;height:44px;border-radius:12px;background:var(--accent-soft);color:var(--accent);display:grid;place-items:center;flex:none}
.pe-empty .t{font-weight:700;color:var(--text);margin-bottom:6px}.pe-empty ol{margin:0;padding-left:18px;color:var(--muted);font-size:.86rem}
.cv-hero{background:linear-gradient(160deg,var(--surface-3) 0%,var(--surface-2) 100%);border:1px solid var(--border);border-top:2px solid var(--accent);border-radius:16px;padding:1.6rem 2rem;margin-bottom:1.2rem}
.cv-hero h2{font-size:1.7rem;font-weight:800;letter-spacing:-.03em;margin:0;color:var(--text)!important;padding:0}
.cv-hero p{color:var(--muted);margin:.35rem 0 0;font-size:.95rem}
.cv-mod{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px 16px;height:100%}
.cv-mod .q{display:inline-block;background:var(--accent-soft);color:#B9BDFF;border:1px solid rgba(124,131,255,.3);border-radius:999px;padding:1px 10px;font-size:.74rem;font-weight:700;margin-bottom:8px}
.cv-mod .n{font-weight:700;color:var(--text)}.cv-mod .b{font-size:.82rem;color:var(--muted);margin-top:4px;line-height:1.4}
.cv-img img{border-radius:12px;border:1px solid var(--border)}
@media (max-width:900px){.pe-hero{align-items:flex-start}.pe-title{font-size:1.6rem}}
"""
st.markdown("<style>" + CSS + "</style>", unsafe_allow_html=True)


# ─────────────────────────── HELPERS ───────────────────────────
def esc(v):
    return html_lib.escape(str(v if v is not None else ""), quote=True)


def render_html(markup, target=None):
    (target or st).markdown("".join(l.strip() for l in markup.splitlines()), unsafe_allow_html=True)


def chip(text, tone=""):
    return f'<span class="pe-chip {tone}">{esc(text)}</span>'


def section_header(num, title, subtitle=""):
    render_html(f'<div class="pe-section"><div class="badge">{num}</div><div><div class="t">{esc(title)}</div>'
                + (f'<div class="s">{esc(subtitle)}</div>' if subtitle else "") + "</div></div>")


def _full_width():
    try:
        if "width" in inspect.signature(st.button).parameters:
            return {"width": "stretch"}
    except (TypeError, ValueError):
        pass
    return {"use_container_width": True}


FULL_WIDTH = _full_width()


def show_df(df, **kw):
    try:
        st.dataframe(df, hide_index=True, width="stretch", **kw)
    except TypeError:
        st.dataframe(df, hide_index=True, use_container_width=True, **kw)


def kpi(label, value, note="", tone=""):
    return (f'<div class="pe-kpi {tone}"><div class="l">{esc(label)}</div><div class="v">{esc(value)}</div>'
            + (f'<div class="n">{esc(note)}</div>' if note else "") + "</div>")


def kpi_row(items):
    cols = st.columns(len(items))
    for c, it in zip(cols, items):
        render_html(kpi(*it), c)


def empty_state(title, steps, icon="list"):
    ic = ICONS.get(icon, ICONS["list"])
    render_html(f'<div class="pe-empty"><div class="ic">{ic}</div><div><div class="t">{esc(title)}</div><ol>'
                + "".join(f"<li>{esc(s)}</li>" for s in steps) + "</ol></div></div>")


def secret(key, default=""):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def safe_file(x):
    return re.sub(r"[^A-Za-z0-9]+", "_", x or "").strip("_") or "Quote"


def img_b64(path):
    import base64
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""


ICONS = {
    "list": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>',
    "users": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
}

LOGO_B64 = img_b64(LOGO)

# chart look: dark surface, recessive grid, one accent
def chart_cfg(ch):
    return (ch.configure(background="transparent")
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor="#8C98B0", titleColor="#8C98B0", gridColor="rgba(148,163,184,.12)",
                            domainColor="rgba(148,163,184,.26)", tickColor="rgba(148,163,184,.26)",
                            labelFont="Inter", titleFont="Inter", labelFontSize=11, titleFontSize=11)
            .configure_legend(labelColor="#E7EAF3", titleColor="#8C98B0"))


# ─────────────────────────── LOGIN ───────────────────────────
def login_gate():
    if st.session_state.get("role"):
        return
    app_pw, admin_pw = secret("APP_PASSWORD"), secret("ADMIN_PASSWORD")
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        render_html(f'<div class="pe-login-head"><img src="data:image/png;base64,{LOGO_B64}">'
                    '<div class="t">Call Scope Pricebook</div><div class="s">Customer quotes and partner pricing</div></div>')
        with st.container(key="card-login"):
            if not (app_pw or admin_pw):
                st.error("This app is locked because no password is set. Add APP_PASSWORD and ADMIN_PASSWORD "
                         "in Streamlit Cloud > your app > Settings > Secrets.")
                st.stop()
            with st.form("login"):
                name = st.text_input("Your name", placeholder="Shown as 'prepared by' on paperwork")
                pw = st.text_input("Password", type="password")
                ok = st.form_submit_button("Sign in", **FULL_WIDTH)
            if ok:
                if admin_pw and hmac.compare_digest(pw.encode(), str(admin_pw).encode()):
                    st.session_state.role = "admin"
                elif app_pw and hmac.compare_digest(pw.encode(), str(app_pw).encode()):
                    st.session_state.role = "sales"
                else:
                    st.error("That password isn't right.")
                    st.stop()
                st.session_state.prepared_by = name.strip()
                st.rerun()
    st.stop()


login_gate()

if "cfg" not in st.session_state:
    st.session_state.cfg = load_config()
CFG = st.session_state.cfg
IS_ADMIN = st.session_state.role == "admin"
ZH = Zoho(lambda k: secret(k), st.session_state)

# values pulled from Zoho are applied here, before the input boxes are drawn
for _prefix in ("c", "p"):
    _fill = st.session_state.pop(f"_zfill_{_prefix}", None)
    if _fill:
        for _k, _v in _fill.items():
            st.session_state[f"{_prefix}_{_k}"] = _v

# ─────────────────────────── SIDEBAR ───────────────────────────
with st.sidebar:
    render_html(f'<div class="pe-brand"><img src="data:image/png;base64,{LOGO_B64}"><div><div class="n">{esc(CFG["brand"]["trading"])} Pricebook</div>'
                f'<div class="t">{esc(CFG["brand"]["byline"])}</div></div></div>')
    modes = ["Customer quote", "Reseller partner", "Admin"]
    mode = st.radio("Workspace", modes, key="mode")
    st.text_input("Prepared by", key="prepared_by")
    st.caption("Signed in as " + ("admin" if IS_ADMIN else "sales") + (" - Zoho connected" if ZH.configured() else ""))
    st.divider()
    if st.button("Start a new quote", **FULL_WIDTH):
        keep = {"role", "prepared_by", "cfg", "mode"}
        for k in list(st.session_state.keys()):
            if k not in keep:
                del st.session_state[k]
        st.rerun()
    if st.button("Log out", **FULL_WIDTH):
        st.session_state.clear()
        st.rerun()

def render_hero(eyebrow, title_a, title_b, sub, steps, active):
    parts = []
    for i, s in enumerate(steps):
        cls = "done" if i < active else ("active" if i == active else "")
        num = "&#10003;" if i < active else str(i + 1)
        if i:
            parts.append('<div class="pe-step-sep"></div>')
        parts.append(f'<div class="pe-step {cls}"><div class="num">{num}</div>{esc(s)}</div>')
    render_html(f'<div class="pe-hero"><div><div class="pe-eyebrow"><span class="dot"></span>{esc(eyebrow)}</div>'
                f'<div class="pe-title">{esc(title_a)} <span>{esc(title_b)}</span></div><div class="pe-sub">{esc(sub)}</div></div>'
                f'<div class="pe-stepper">{"".join(parts)}</div></div>')


def details_inputs(prefix, label):
    c1, c2 = st.columns(2)
    c1.text_input(f"{label} name", key=f"{prefix}_company")
    c2.text_input("Company number", key=f"{prefix}_company_no")
    c1.text_input("Contact name", key=f"{prefix}_contact")
    c2.text_input("Position", key=f"{prefix}_position")
    c1.text_input("Email", key=f"{prefix}_email")
    c2.text_input("Telephone", key=f"{prefix}_phone")
    st.text_input("Address", key=f"{prefix}_address")
    return {k: st.session_state.get(f"{prefix}_{k}", "") for k in
            ("company", "company_no", "contact", "position", "email", "phone", "address")}


def zoho_pull(prefix):
    """'Pull from Zoho' - search Accounts and Leads, pick a contact, fill the details below."""
    with st.expander("Pull details from Zoho", expanded=False):
        if not ZH.configured():
            st.caption("Zoho isn't connected - add ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET and ZOHO_REFRESH_TOKEN to Secrets "
                       "(Admin > Zoho has a helper to make the refresh token).")
            return
        c1, c2 = columns([3, 1])
        qtxt = c1.text_input("Search Zoho", key=f"_zq_{prefix}", placeholder="Company name (accounts and leads)")
        if c2.button("Search", key=f"_zgo_{prefix}", **FULL_WIDTH) and qtxt.strip():
            try:
                res, note = ZH.search(qtxt.strip())
                st.session_state[f"_zres_{prefix}"] = res
                st.session_state[f"_zmsg_{prefix}"] = note if res else ("No matching accounts or leads. " + note).strip()
            except Exception as e:
                st.session_state[f"_zres_{prefix}"] = []
                m = str(e)
                st.session_state[f"_zmsg_{prefix}"] = ("Connected, but the refresh token can't read Accounts - make a new one in Admin > Zoho "
                                                       "with the scope ZohoCRM.modules.READ,ZohoCRM.settings.READ." if "scope" in m.lower()
                                                       else f"Couldn't reach Zoho: {m}")
        if st.session_state.get(f"_zmsg_{prefix}"):
            st.caption(st.session_state[f"_zmsg_{prefix}"])
        res = st.session_state.get(f"_zres_{prefix}") or []
        if not res:
            return
        i = st.selectbox("Matches", range(len(res)), key=f"_zpick_{prefix}",
                         format_func=lambda i: f"{res[i].get('Account_Name') or '?'} [{res[i].get('_type')}]"
                                               + (f" - {res[i].get('Billing_City')}" if res[i].get("Billing_City") else ""))
        rec = res[i]
        cache = st.session_state.setdefault("_zcache", {})
        if rec["id"] not in cache:
            try:
                cache[rec["id"]] = ZH.load(rec)
            except Exception as e:
                cache[rec["id"]] = (dict(rec), [])
                st.caption(f"Couldn't load the full record: {e}")
        acct, contacts = cache[rec["id"]]
        contact = None
        if contacts:
            ci = st.selectbox("Contact", range(len(contacts)), key=f"_zcon_{prefix}",
                              format_func=lambda i: " - ".join(x for x in (contacts[i].get("Full_Name") or "(no name)",
                                                                           contacts[i].get("Title"), contacts[i].get("Email")) if x))
            contact = contacts[ci]
        else:
            st.caption("No contact found on this record.")
        if st.button("Fill in these details", key=f"_zfill_btn_{prefix}", type="primary"):
            st.session_state[f"_zfill_{prefix}"] = ZH.fill_values(acct, contact)
            st.session_state[f"_zmsg_{prefix}"] = f"Filled from {acct.get('Account_Name') or 'Zoho'} - check the details below."
            st.rerun()


def view_switch(options, key):
    """Tab-style switcher that only draws the chosen view (keeps the signature pad visible and the page quick)."""
    if st.session_state.get(key) not in options:
        st.session_state[key] = options[0]
    try:
        v = st.segmented_control("View", options, key=key, label_visibility="collapsed")
    except AttributeError:
        v = st.radio("View", options, key=key, horizontal=True, label_visibility="collapsed")
    return v or options[0]


def columns(spec, **kw):
    try:
        return st.columns(spec, vertical_alignment="bottom", **kw)
    except TypeError:
        return st.columns(spec, **kw)


def _clean_signature(img_rgba):
    """Canvas image -> PNG bytes on white, with the pad's tint removed."""
    import numpy as np
    from PIL import Image
    im = Image.fromarray(img_rgba.astype("uint8"), "RGBA")
    if im.getbbox() is None or np.asarray(im)[:, :, 3].max() == 0:
        return None
    white = Image.new("RGBA", im.size, (255, 255, 255, 255))
    white.paste(im, mask=im.split()[3])
    arr = np.array(white.convert("RGB")).astype("int16")
    arr[np.abs(arr - np.array([234, 244, 251])).max(axis=2) < 40] = 255
    if (arr < 200).sum() < 30:
        return None
    out = Image.fromarray(arr.astype("uint8"), "RGB")
    bbox = Image.eval(out.convert("L"), lambda v: 255 - v).getbbox()
    if bbox:
        out = out.crop((max(0, bbox[0] - 10), max(0, bbox[1] - 10), min(out.width, bbox[2] + 10), min(out.height, bbox[3] + 10)))
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return buf.getvalue()


def sign_and_send(kind, build, who, fname, blank_pdf):
    """Two ways to sign the one 'Agreement to go ahead' box on page 1: Zoho Sign, or on screen now."""
    from datetime import datetime
    left, right = st.columns(2, gap="large")
    with left:
        with st.container(key=f"card-zsign-{kind}"):
            section_header("A", "Send with Zoho Sign", "One signature on page 1 covers the whole pack")
            email = who.get("email") or "the signer's email"
            render_html('<ol class="pe-steps">'
                        '<li><span><b>Download the pack</b> - its Agreement to go ahead box on page 1 is left blank for Zoho Sign.</span></li>'
                        '<li><span><b>Open Zoho Sign</b> - Send for signatures, upload the PDF and add ' + esc(email) + ' as the signer.</span></li>'
                        '<li><span><b>Drag a Signature field</b> onto the signature box on page 1 (add Date signed next to DATE if you like), then Send.</span></li>'
                        '</ol>')
            st.download_button("1. Download pack for Zoho Sign", data=blank_pdf, file_name=f"{fname}.pdf", mime="application/pdf",
                               type="primary", key=f"dl_zs_{kind}", **FULL_WIDTH)
            st.link_button("2. Open Zoho Sign", secret("ZOHO_SIGN_URL", "https://sign.zoho.eu"), **FULL_WIDTH)
            if not who.get("company"):
                st.warning("Add the company name in step 01 before sending.")
    with right:
        with st.container(key=f"card-onscreen-{kind}"):
            section_header("B", "Sign now, on screen", "When you're with them - signs the same box and dates it")
            sk = f"_sig_{kind}"
            method = st.radio("Signature", ["Draw", "Upload a photo"], horizontal=True, key=f"_sigm_{kind}",
                              label_visibility="collapsed")
            if method == "Draw" and CANVAS_OK:
                cv = st_canvas(fill_color="rgba(0,0,0,0)", stroke_width=3, stroke_color="#000000", background_color="#EAF4FB",
                               update_streamlit=True, height=170, width=460, drawing_mode="freedraw", key=f"_canvas_{kind}")
                b1, b2 = st.columns(2)
                if b1.button("Save signature", key=f"_sigsave_{kind}", **FULL_WIDTH):
                    sig = _clean_signature(cv.image_data) if (cv is not None and cv.image_data is not None) else None
                    if sig:
                        st.session_state[sk] = sig
                    else:
                        st.warning("Nothing drawn yet.")
                if b2.button("Clear", key=f"_sigclr_{kind}", **FULL_WIDTH):
                    st.session_state.pop(sk, None)
            else:
                if method == "Draw":
                    st.caption("The drawing pad isn't available here - upload a photo of the signature instead.")
                up = st.file_uploader("Photo of the signature", type=["png", "jpg", "jpeg"], key=f"_sigup_{kind}")
                if up:
                    from PIL import Image
                    im = Image.open(up).convert("RGB")
                    im.thumbnail((600, 200))
                    buf = io.BytesIO(); im.save(buf, format="PNG")
                    st.session_state[sk] = buf.getvalue()
            c1, c2 = st.columns(2)
            nm = c1.text_input("Signed by", key=f"_signame_{kind}", placeholder=who.get("contact") or "Full name") or who.get("contact", "")
            pos = c2.text_input("Position", key=f"_signpos_{kind}", placeholder=who.get("position") or "e.g. Director") or who.get("position", "")
            sig = st.session_state.get(sk)
            if sig:
                st.image(sig, width=220, caption="Saved signature")
            if sig and nm.strip():
                ts = datetime.now().strftime("%d/%m/%Y %H:%M")
                signed = build({"sig": sig, "name": nm.strip(), "position": pos.strip(), "date": ts})
                st.download_button("Download signed pack", data=signed, file_name=f"{fname}_SIGNED.pdf", mime="application/pdf",
                                   type="primary", key=f"dl_signed_{kind}", **FULL_WIDTH)
            else:
                st.caption("Still needed: " + ", ".join(x for x, ok in (("signature", sig), ("name", nm.strip())) if not ok))


# ═══════════════════════════ CUSTOMER QUOTE ═══════════════════════════
def customer_mode():
    has_now = any((st.session_state.get(f"q_{m['id']}") or 0) > 0 for m in CFG["modules"])
    render_hero("Direct customer", "Call Scope", "service quote",
                "Build the quote, show the customer their view, then send the pack for signature.",
                ["Customer", "Services", "Terms", "Sign"], 0 if not st.session_state.get("c_company") else (1 if not has_now else 3))
    left, right = st.columns([2.15, 1], gap="large")
    with left:
        with st.container(key="card-cust"):
            section_header("01", "Customer details", "Who the Service Order is for")
            zoho_pull("c")
            cust = details_inputs("c", "Business")

        with st.container(key="card-svc"):
            section_header("02", "Choose services", "Monthly modules, per unit - the customer sees these on their paperwork")
            mods = CFG["modules"]
            qty = {}
            for row in range(0, len(mods), 3):
                cols = st.columns(3)
                for col, m in zip(cols, mods[row:row + 3]):
                    k = f"q_{m['id']}"
                    on = (st.session_state.get(k) or 0) > 0
                    with col:
                        with st.container(key=f"prod-{m['id']}"):
                            render_html(('<span class="pe-on"></span>' if on else "") + f'<div class="pe-prod-name">{esc(m["name"])}</div>'
                                        f'<div class="pe-prod-price"><b>{money(m["rrp"])}</b> /mo {esc(m.get("unit", ""))}</div>'
                                        f'<div class="pe-prod-blurb">{esc(m.get("blurb", ""))}</div>')
                            qty[m["id"]] = st.number_input("Quantity", 0, 500, step=1, key=k)
            c1, c2 = st.columns(2)
            mc = CFG["minutes"]
            opts = [0] + list(mc["bundles"])
            minutes = c1.selectbox("AI minutes bundle", opts, key="c_minutes",
                                   format_func=lambda m: "None" if not m else f"{m:,} mins - {money(m * mc['rrp_per_min'], 0)}/mo")
            agent = next((s for s in CFG["setup"] if s["id"] == "agent_setup"), None)
            agents = c2.number_input(f"{agent['name']} (one-off {money(agent['rrp'], 0)})" if agent else "Bespoke AI agent build",
                                     0, 10, step=1, key="c_agents")

        with st.container(key="card-term"):
            section_header("03", "Term and pricing", "Longer terms unlock bigger introductory discounts")
            terms = [int(t["months"]) for t in CFG["customer_terms"]]
            c1, c2 = st.columns(2)
            if st.session_state.get("c_term") not in terms:
                st.session_state.c_term = terms[-1]
            term = c1.selectbox("Minimum term", terms, key="c_term", format_func=lambda m: f"{m} months")
            maxd = int(max_discount_for(CFG, term))
            if st.session_state.get("c_disc", 0) > maxd:
                st.session_state.c_disc = maxd
            disc = c2.slider(f"Introductory discount (max {maxd}% on {term} months)", 0, max(maxd, 1) if maxd else 1,
                             step=5 if maxd % 5 == 0 else 1, key="c_disc", disabled=maxd == 0)
            disc = min(disc, maxd)
            years = -(-term // 12)
            c1, c2 = st.columns(2)
            if years > 1:
                style = c1.radio("How the discount runs", ["stepped", "fixed"], key="c_style", horizontal=True,
                                 format_func=lambda s: "Steps back to standard" if s == "stepped" else "Fixed for the term")
            else:
                style = "stepped"
                c1.caption("On a 12-month term the discount applies for the whole term.")
            setup_mode = c2.selectbox("Set-up charges", ["invoice", "spread", "included", "waived"], key="c_setup",
                                      format_func=lambda s: {"invoice": "Invoiced on order", "spread": "Spread over 12 months",
                                                             "included": "In their hardware/telephony agreement",
                                                             "waived": "Waived"}[s])
            c1, c2 = st.columns(2)
            if "c_review" not in st.session_state:
                st.session_state.c_review = float(CFG["annual_review_pct"])
            review = c1.number_input("Annual price review %", 0.0, 15.0, step=0.5, key="c_review")
            show_review = c2.toggle("Show review in the Price Schedule", key="c_show_review",
                                    help="Off: schedule shows prices before the annual review (like the current paperwork). "
                                         "On: the review is built into each year's figure.")

    q = customer_quote(CFG, qty, minutes=minutes, agent_setups=agents, term=term, discount=disc, style=style,
                       review_pct=review, setup_mode=setup_mode)
    has = bool(q["lines"])
    st.session_state["_last_q"] = {"q": q, "who": cust.get("company", "")}
    prepared = st.session_state.get("prepared_by", "")
    fname = f"CallScope_Agreement_{safe_file(cust['company'])}_{date.today()}"
    build = lambda sign=None: customer_pack(CFG, q, cust, prepared, show_review, sign=sign)
    blank_pdf = build() if has else None

    with right:
        with st.container(key="card-summary"):
            render_html('<div class="pe-sum-label">Monthly at the start</div>')
            if has:
                strike = f'<span class="pe-sum-strike">{money(q["standard_monthly"])}</span>' if disc else ""
                render_html(f'<div class="pe-sum-big">{money(q["monthly_total"])}{strike}</div>')
                render_html(f'<div style="margin:8px 0 10px">{chip(f"{term} months", "accent")}'
                            + (chip(f"{disc:g}% off", "good") if disc else "") + chip("excl. VAT") + "</div>")
                render_html(f'<div class="pe-row">Set-up (one-off)<b>{money(q["setup_total"])}</b></div>')
                st.download_button("Download agreement pack", data=blank_pdf, file_name=f"{fname}.pdf",
                                   mime="application/pdf", type="primary", key="dl_c_side", **FULL_WIDTH)
                stepped = disc and style == "stepped" and years > 1
                bits = ([f"the yearly price review ({review:g}%)"] if review else []) + (["the discount stepping down each year"] if stepped else [])
                if bits:
                    st.caption("*Subject to " + " and ".join(bits) + " - outlined in the paperwork.")
            else:
                render_html('<div class="pe-sum-big" style="color:var(--faint)">£0.00</div>')
                st.caption("Add a quantity to any service to start the quote.")

    st.write("")
    if not has:
        empty_state("Nothing on the quote yet", ["Fill in the customer's details", "Add quantities to the services they want",
                                                 "Pick a term and discount - the paperwork appears here"])
        return

    view = view_switch(["Customer view", "Sign and send"], "c_view")
    if view == "Customer view":
        customer_view(q, cust, show_review)
    else:
        st.caption("The pack: page 1 Agreement to go ahead (the only signature) - Service Order - Price Schedule - Terms & Conditions.")
        sign_and_send("c", build, cust, fname, blank_pdf)


def customer_view(q, cust, show_review):
    B = CFG["brand"]
    render_html(f'<div class="cv-hero"><h2>Your {esc(B["trading"])} package</h2><p>'
                + (f"Prepared for {esc(cust['company'])} &nbsp;|&nbsp; " if cust["company"] else "")
                + f'{q["term"]}-month agreement &nbsp;|&nbsp; {esc(B["tag"])}</p></div>')
    first, last = q["schedule"][0], q["schedule"][-1]
    stepped = q["discount"] > 0 and q["style"] == "stepped" and q["years"] > 1
    kpi_row([
        ("Your monthly price", money(q["monthly_total"]), "for the first 12 months" if stepped else "for your whole term"),
        ("Standard price", money(q["standard_monthly"]), "per month, before your discount"),
        ("You save", money(q["saving_vs_standard"], 0), f"over {q['term']} months vs standard", "good"),
        ("One-off set-up", money(q["setup_total"], 0), {"invoice": "invoiced on order", "spread": "spread over 12 months",
                                                       "included": "in your equipment agreement", "waived": "waived"}[q["setup_mode"]]),
    ])
    st.write("")
    st.markdown("##### What's included")
    mods = {m["id"]: m for m in CFG["modules"]}
    items = q["lines"]
    for row in range(0, len(items), 3):
        cols = st.columns(3)
        for c, l in zip(cols, items[row:row + 3]):
            blurb = mods.get(l["id"], {}).get("blurb", "Talk-time for your AI receptionist and integrations, every month.")
            render_html(f'<div class="cv-mod"><div class="q">x {l["qty"]}</div><div class="n">{esc(l["name"])}</div>'
                        f'<div class="b">{esc(blurb)}</div></div>', c)
        st.write("")
    c1, c2 = st.columns(2)
    for c, f, cap in ((c1, "dashboard.jpg", "Manager dashboard"), (c2, "ai_combined.jpg", "AI call insight")):
        p = os.path.join(ROOT, "assets", f)
        if os.path.exists(p):
            with c:
                st.image(p, caption=cap)
    if stepped:
        st.info(f"Your {q['discount']:g}% introductory discount applies in full for 12 months, then steps down evenly each year, "
                f"reaching the standard price of {money(q['standard_monthly'])} in year {q['years']}. It never jumps in one go.")


def schedule_view(q, show_review):
    rows = []
    prev = None
    for r in q["schedule"]:
        mo = r["monthly_with_review"] if show_review else r["monthly"]
        rows.append({"Year": f"Year {r['year']}", "Months": r["months"], "Monthly charge": money(mo),
                     "Change on last year": "-" if prev is None else f"+ {money(mo - prev)}",
                     "Discount remaining": "Standard price" if r["discount"] <= 0 else f"{r['discount']:g}% off",
                     "_v": mo})
        prev = mo
    df = pd.DataFrame(rows)
    ch = alt.Chart(df).mark_bar(color="#7C83FF", cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=56).encode(
        x=alt.X("Year:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("_v:Q", title="Monthly charge (£)", axis=alt.Axis(format=",.0f")),
        tooltip=[alt.Tooltip("Year:N"), alt.Tooltip("Months:N"), alt.Tooltip("Monthly charge:N"),
                 alt.Tooltip("Discount remaining:N")])
    txt = alt.Chart(df).mark_text(dy=-8, color="#E7EAF3", font="Inter", fontWeight=600, fontSize=11).encode(
        x=alt.X("Year:N", sort=None), y="_v:Q", text="Monthly charge:N")
    st.altair_chart(chart_cfg((ch + txt).properties(height=260)), use_container_width=True)
    show_df(df.drop(columns="_v"))
    cap = (f"Includes the {q['review_pct']:g}% annual review." if show_review
           else (f"Before the {q['review_pct']:g}% annual review and VAT." if q["review_pct"] else "Excludes VAT."))
    st.caption(f"{cap} Monthly services over the term: {money(q['services_value_with_review'] if show_review else q['services_value'])}.")


def margin_view(q):
    st.caption("Internal only - never shown to the customer or on the paperwork.")
    term = q["term"]
    cost_term = q["buy_monthly"] * term + q["setup_buy"]
    rev = q["services_value"] + q["setup_total"]
    kpi_row([("Our cost /mo", money(q["buy_monthly"]), "platform + AI costs"),
             ("Profit year 1 /mo", money(q["monthly_total"] - q["buy_monthly"]), f"{(1 - q['buy_monthly'] / q['monthly_total']) * 100:.0f}% margin" if q["monthly_total"] else ""),
             ("Profit over term", money(q["profit"], 0), "before the annual review", "good"),
             ("Term margin", f"{(q['profit'] / rev * 100) if rev else 0:.0f}%", f"on {money(rev, 0)} revenue")])
    st.write("")
    df = pd.DataFrame([{"Service": l["name"], "Qty": l["qty"], "Our cost /unit": money(l["buy"]), "Year 1 price /unit": money(l["price"]),
                        "Profit /mo": money((l["price"] - l["buy"]) * l["qty"]),
                        "Margin": f"{((l['price'] - l['buy']) / l['price'] * 100) if l['price'] else 0:.0f}%"} for l in q["lines"]])
    show_df(df)
    low = [l["name"] for l in q["lines"] if l["price"] and (l["price"] - l["buy"]) / l["price"] < 0.15]
    if low:
        st.warning("Thin margin in year 1 on: " + ", ".join(low) + ". Consider a smaller discount or a longer term.")


# ═══════════════════════════ RESELLER PARTNER ═══════════════════════════
def reseller_mode():
    R = CFG["reseller"]
    render_hero("Reseller partner", "Call Scope", "partner pricing",
                "Pick a tier and term, model the partner's growth, and show them the return before they sign.",
                ["Partner", "Tier", "Growth plan", "Sign"], 0 if not st.session_state.get("p_company") else 3)
    left, right = st.columns([2.15, 1], gap="large")
    with left:
        with st.container(key="card-partner"):
            section_header("01", "Partner details", "The reseller signing the Partner Agreement")
            zoho_pull("p")
            partner = details_inputs("p", "Partner")

        with st.container(key="card-tier"):
            section_header("02", "Tier and commitment", "Bigger commitment, bigger discount - commitment is counted in licences")
            names = [t["name"] for t in R["tiers"]]
            if st.session_state.get("p_tier") not in names:
                st.session_state.p_tier = names[1] if len(names) > 1 else names[0]
            tier_name = st.radio("Partner tier", names, key="p_tier", horizontal=True)
            tier = tier_by_name(CFG, tier_name)
            render_html("".join([
                chip(f"{tier['discount']:g}% off RRP", "accent"),
                chip(f"Commit {int(tier['commit'])} licences" if tier["commit"] else "No commitment"),
                chip(f"Onboarding {money(tier['onboarding'], 0)}" if tier["onboarding"] else "Onboarding free", "" if tier["onboarding"] else "good"),
                chip("White label included", "good") if tier.get("white_label") else ""]))
            c1, c2 = st.columns(2)
            pterms = [int(t["months"]) for t in R["terms"]]
            if st.session_state.get("p_term") not in pterms:
                dt = int(R.get("default_term", 36))
                st.session_state.p_term = dt if dt in pterms else pterms[0]
            term = c1.selectbox("Partner term", pterms, key="p_term",
                                format_func=lambda m: f"{m} months" + (f"  (+{next(t['bonus'] for t in R['terms'] if int(t['months']) == m):g}% discount)"
                                                                        if next(t['bonus'] for t in R['terms'] if int(t['months']) == m) else ""))
            if tier.get("white_label"):
                c2.caption("White label is included in this tier.")
                white = True
            else:
                white = c2.toggle(f"White label (+{money(R['white_label_fee'], 0)}/mo)", key="p_white")
            onboarding_mode = "charge"
            if tier["onboarding"]:
                onboarding_mode = c1.selectbox(f"Onboarding fee ({money(tier['onboarding'], 0)})", ["charge", "defer", "waive"], key="p_onboard",
                                               format_func=lambda m: {"charge": "Charge on signing", "defer": "Defer until their first customer order",
                                                                      "waive": "Waive it"}[m])
            if not tier["commit"]:
                render_html('<div class="pe-note" style="margin:6px 0 0"><b>Pay as you go</b> - no minimum users or customers. '
                            'Set the growth plan to 0 for a no-cost sign-up pack, or put in "X a month" for an example quote.</div>')

        with st.container(key="card-plan"):
            section_header("03", "Growth plan", "Their example quote - 'if you sold X a month over the term, this is what you'd keep'")
            unit = st.radio("Plan by", ["customers", "users"], horizontal=True, key="p_unit",
                            format_func=lambda u: "Customers (businesses) a month" if u == "customers" else "Users a month")
            one = "customer" if unit == "customers" else "user"
            c1, c2, c3 = st.columns(3)
            start = c1.number_input(f"{unit.capitalize()} at launch", 0, 5000, value=2 if unit == "customers" else 0, step=1, key=f"p_start_{unit}")
            per_month = c2.number_input(f"New {unit} per month", 0, 1000, value=1 if unit == "customers" else 10, step=1, key=f"p_new_{unit}")
            churn = c3.number_input("Monthly churn %", 0.0, 10.0, value=1.0, step=0.5, key="p_churn",
                                    help=f"The share of {unit} who leave each month.")
            c1, c2, c3 = st.columns(3)
            resale_disc = c1.slider("Partner's discount to their customers", 0, 40, value=0, step=5, key="p_resale",
                                    help="0% = the partner sells at our RRP.")
            mc = CFG["minutes"]
            if unit == "customers":
                setup_pct = c2.slider("Set-up charged at % of RRP", 0, 100, value=100, step=10, key="p_setup_pct")
                mins = c3.selectbox("Minutes per customer", [0] + list(mc["bundles"]), index=1, key="p_mins",
                                    format_func=lambda m: "None" if not m else f"{m:,} mins")
                st.markdown("**Typical customer** - modules per customer, on average")
                defaults = {"portal": 5, "crm": 0, "dashboard": 1, "callscore": 3, "receptionist": 0, "widget": 0}
            else:
                setup_pct, mins = 100, 0
                c2.caption("Per-user plan: set-up fees and minute bundles are left out - they're per business, not per user.")
                st.markdown("**Each user takes** - modules per user")
                defaults = {"portal": 1, "crm": 0, "dashboard": 0, "callscore": 1, "receptionist": 0, "widget": 0}
            mix = {}
            mods = CFG["modules"]
            try:
                cols = st.columns(len(mods), vertical_alignment="bottom")
            except TypeError:
                cols = st.columns(len(mods))
            for c, m in zip(cols, mods):
                mix[m["id"]] = c.number_input(m["name"].replace("AI Integration - ", ""), 0.0, 100.0,
                                              value=float(defaults.get(m["id"], 0)), step=1.0 if unit == "users" else 0.5,
                                              format="%.0f" if unit == "users" else "%.1f", key=f"p_mix_{unit}_{m['id']}")

    kw = dict(mix=mix, minutes_per_cust=mins, start_customers=start, new_per_month=per_month, churn_pct=churn,
              resale_discount=resale_disc, setup_resale_pct=setup_pct, white_label=white,
              onboarding_mode=onboarding_mode, include_setup=(unit == "customers"), unit=unit)
    sim = simulate_partner(CFG, tier_name, term, **kw)
    has = sim["per_customer"]["resale"] > 0 and (start or per_month)
    T = sim["totals"]
    st.session_state["_last_sim"] = {"sim": sim, "who": partner.get("company", "")}
    prepared = st.session_state.get("prepared_by", "")
    fname = f"CallScope_Partner_Agreement_{safe_file(partner['company'])}_{date.today()}"
    build = lambda sign=None: partner_pack(CFG, sim, partner, prepared, white, sign=sign)
    blank_pdf = build()

    plan = [f"Partner tier: {tier_name} ({sim['discount']:g}% off RRP) on a {term}-month partner term"
            + (f", committing to {int(tier['commit'])} licences" if tier["commit"] else ", no commitment") + ".",
            f"Starts with {start:g} {one if start == 1 else unit} and adds {per_month:g} new {one if per_month == 1 else unit} a month for {term // 12 if term % 12 == 0 else term} "
            f"{'years' if term % 12 == 0 else 'months'}, with {churn:g}% leaving each month.",
            ("Typical customer: " if unit == "customers" else "Each user takes: ") + ", ".join(f"{v:g} x {next(m['name'] for m in CFG['modules'] if m['id'] == k)}" for k, v in mix.items() if v)
            + (f", {mins:,} AI minutes" if mins else "") + ".",
            f"Sells at {'our RRP' if not resale_disc else f'{resale_disc}% below RRP'}"
            + (f"; set-up charged at {setup_pct}% of RRP." if unit == "customers" else ".")]

    with right:
        with st.container(key="card-rsummary"):
            if has:
                render_html('<div class="pe-sum-label">Reseller keeps over the term</div>')
                render_html(f'<div class="pe-sum-big">{money(T["profit"], 0)}</div>')
            else:
                render_html('<div class="pe-sum-label">Sign-up pack</div>')
                render_html('<div class="pe-sum-big" style="font-size:1.5rem">'
                            + ("Nothing to pay until they sell" if (not tier["commit"] and (not tier["onboarding"] or onboarding_mode != "charge"))
                               else f"{money(tier['onboarding'] if onboarding_mode == 'charge' else 0, 0)} on signing") + '</div>')
            bonus = sim["discount"] - float(tier["discount"])
            disc_chip = chip(f"{sim['discount']:g}% off RRP", "good") + (chip(f"incl. +{bonus:g}% for {term} months") if bonus else "")
            render_html(f'<div style="margin:8px 0 10px">{chip(tier_name, "accent")}{disc_chip}{chip(f"{term} months")}</div>')
            hit = sim["commit_hit_month"]
            commit_txt = ("None - pay as you go" if not tier["commit"] else (f"Reached month {hit}" if hit else "Not reached"))
            ob = ("None" if not tier["onboarding"] else {"charge": money(tier["onboarding"], 0), "defer": "With first order",
                                                         "waive": "Waived"}[onboarding_mode])
            rows_html = ""
            if has:
                rows_html += (f'<div class="pe-row">Keeps per £1 paid to Call Scope<b>£{sim["roi_pct"] / 100:.2f}</b></div>'
                              f'<div class="pe-row">Keeps each month by the end<b>{money(sim["end_mrr_profit"], 0)}</b></div>'
                              f'<div class="pe-row">Pays back<b>{"Month " + str(sim["payback_month"]) if sim["payback_month"] else "Not in term"}</b></div>')
            rows_html += f'<div class="pe-row">Commitment<b>{commit_txt}</b></div><div class="pe-row">Onboarding fee<b>{ob}</b></div>'
            if tier["commit"]:
                rows_html += f'<div class="pe-row">Shortfall charges<b>{money(T["shortfall"], 0)}</b></div>'
            render_html(rows_html)
            if has and tier["commit"] and (not hit or hit > sim["ramp"]):
                st.warning(f"On this plan the partner doesn't reach {int(tier['commit'])} licences within the {sim['ramp']}-month ramp, "
                           "so shortfall charges apply. Compare tiers below.")
            st.download_button("Download partner pack", data=blank_pdf, file_name=f"{fname}.pdf",
                               mime="application/pdf", type="primary", key="dl_p_side", **FULL_WIDTH)

    st.write("")
    if not has:
        empty_state("No growth plan - this is a sign-up pack", [f"Add {unit} at launch or new {unit} a month to show an example quote",
                                                                "Or send the pack as it is to sign the reseller up",
                                                                "The price list and signing are below"], icon="users")
        st.write("")
        views = ["Wholesale price list", "Sign and send"]
    else:
        views = ["Partner ROI view", "Compare tiers and terms", "Wholesale price list", "Sign and send"]
    view = view_switch(views, "p_view")
    if view == "Partner ROI view":
        roi_view(sim, partner, kw)
    elif view == "Compare tiers and terms":
        compare_view(sim, kw, term)
    elif view == "Wholesale price list":
        wl = sim["wholesale"]
        show_df(pd.DataFrame([{"Module": w["name"], "Unit": w["unit"], "RRP": money(w["rrp"]), "Partner price": money(w["wholesale"]),
                               "Partner margin": f"{money(w['partner_margin'])} ({w['partner_margin_pct']:.0f}%)",
                               "Counts as licence": "Yes" if w["counts_to_commit"] else "No",
                               "Note": "Held at our floor price" if w["floored"] else ""} for w in wl]))
        mc = CFG["minutes"]
        st.caption(f"AI minutes: {money(mc['wholesale_per_min'] * 100)} per 100 wholesale (RRP {money(mc['rrp_per_min'] * 100)}). "
                   + (f"Shortfall rate: {money(sim['shortfall_rate'])} per licence. " if sim["tier"]["commit"] else "") + "Set-up: "
                   + ", ".join(f"{s['name']} {money(s['wholesale'], 0)} (RRP {money(s['rrp'], 0)})" for s in CFG["setup"]) + ".")
        fl = [w["name"] for w in wl if w["floored"]]
        if fl:
            st.info("Held at our floor price (cost + " + f"{CFG['reseller']['floor_margin_pct']:g}%): " + ", ".join(fl)
                    + ". These carry less discount than the tier headline.")
    else:
        st.caption("The pack: page 1 Agreement to go ahead (the only signature) - Partner Order - Commitment & tiers - Partner Terms.")
        st.download_button("Download the partner's ROI projection (1 page, no signature)", data=partner_roi_pdf(CFG, sim, partner, plan),
                           file_name=f"CallScope_Partner_Opportunity_{safe_file(partner['company'])}_{date.today()}.pdf",
                           mime="application/pdf", key="dl_p_roi")
        sign_and_send("p", build, partner, fname, blank_pdf)


def money_flow(items):
    """Three boxes left to right with arrows: who pays whom, and what is kept."""
    html = '<div class="pe-flow">'
    for i, (label, value, note, tone) in enumerate(items):
        if i:
            html += '<div class="arrow">&#8594;</div>'
        html += f'<div class="pe-kpi {tone}"><div class="l">{esc(label)}</div><div class="v">{esc(value)}</div><div class="n">{esc(note)}</div></div>'
    render_html(html + "</div>")


def roi_view(sim, partner, kw):
    """The reseller's quote: their customers pay them, they pay Call Scope, they keep the difference."""
    T, pc = sim["totals"], sim["per_customer"]
    unit = sim.get("unit", "customers")
    one = "customer" if unit == "customers" else "user"
    who = partner.get("company") or "the reseller"
    paid = T["wholesale"] + T["shortfall"] + T["fees"]
    term = sim["term"]
    render_html(f'<div class="pe-note"><b>This is the reseller\'s view</b> - share it with {esc(who)}. It shows what they earn. '
                'What Call Scope makes from the partnership is in Admin &gt; Deal margins.</div>')

    st.markdown(f"##### Over the {term}-month partner term")
    money_flow([("Their customers pay them", money(T["revenue"], 0), "monthly subscriptions" + (" + set-up fees" if sim.get("include_setup", True) else ""), ""),
                ("They pay Call Scope", money(paid, 0), "wholesale prices" + (", onboarding" if sim["onboarding"] else "")
                 + (", white label" if sim["white_label_fee"] else "") + (", shortfall" if T["shortfall"] else ""), ""),
                ("They keep", money(T["profit"], 0), f"{sim['margin_pct']:.0f}% of everything they bill", "good")])
    st.write("")

    st.markdown(f"##### For each typical {one}, every month")
    wmap = {w["id"]: w for w in sim["wholesale"]}
    rd = float(kw.get("resale_discount", 0)) / 100
    rows = []
    for k, qn in kw["mix"].items():
        if not qn or k not in wmap:
            continue
        w = wmap[k]
        charge, pay = w["rrp"] * (1 - rd), w["wholesale"]
        rows.append({"Item": w["name"], "Qty": f"{qn:g}", "They charge (each)": money(charge), "They pay Call Scope (each)": money(pay),
                     "They keep a month": money((charge - pay) * qn)})
    mins = kw.get("minutes_per_cust") or 0
    if mins:
        mc = CFG["minutes"]
        rows.append({"Item": f"AI minutes ({mins:,})", "Qty": "1", "They charge (each)": money(mins * mc["rrp_per_min"]),
                     "They pay Call Scope (each)": money(mins * mc["wholesale_per_min"]),
                     "They keep a month": money(mins * (mc["rrp_per_min"] - mc["wholesale_per_min"]))})
    rows.append({"Item": f"Total per {one}, per month", "Qty": "", "They charge (each)": money(pc["resale"]),
                 "They pay Call Scope (each)": money(pc["wholesale"]), "They keep a month": money(pc["profit"])})
    if sim.get("include_setup", True):
        rows.append({"Item": "One-off set-up per new customer", "Qty": "", "They charge (each)": money(pc["setup_resale"]),
                     "They pay Call Scope (each)": money(pc["setup_wholesale"]), "They keep a month": money(pc["setup_resale"] - pc["setup_wholesale"]) + " once"})
    show_df(pd.DataFrame(rows))
    st.write("")

    kpi_row([("Pays for itself", f"Month {sim['payback_month']}" if sim["payback_month"] else "Not in term",
              "when what they've kept goes above zero"),
             ("For every £1 paid to Call Scope", f"£{(T['profit'] / paid) if paid else 0:.2f}", "the reseller keeps this much"),
             ("Kept each month by the end", money(sim["end_mrr_profit"], 0), f"{sim['end_customers']:.0f} {unit}, {sim['end_licences']:.0f} licences"),
             (f"{unit.capitalize()} by the end", f"{sim['end_customers']:.0f}", f"starting {kw['start_customers']:g}, +{kw['new_per_month']:g} a month")])
    st.write("")

    df = pd.DataFrame(sim["rows"])
    df["Month"] = df["month"]
    df["Kept so far"] = df["cumulative"]
    base = alt.Chart(df).encode(x=alt.X("Month:Q", title="Month", scale=alt.Scale(domain=[1, term], nice=False),
                                        axis=alt.Axis(tickMinStep=1, values=list(range(0, term + 1, 6 if term <= 48 else 12))[1:] or [1])))
    area = base.mark_area(color="#34D399", opacity=0.14).encode(y=alt.Y("Kept so far:Q", title="Kept so far (£)", axis=alt.Axis(format=",.0f")))
    line = base.mark_line(color="#34D399", strokeWidth=2).encode(y="Kept so far:Q")
    hover = alt.selection_point(fields=["Month"], nearest=True, on="pointerover", empty=False)
    pts = base.mark_point(size=70, filled=True, color="#34D399").encode(
        y="Kept so far:Q", opacity=alt.condition(hover, alt.value(1), alt.value(0)),
        tooltip=[alt.Tooltip("Month:Q"), alt.Tooltip("Kept so far:Q", format=",.0f", title="Kept so far £"),
                 alt.Tooltip("customers:Q", format=".0f", title=unit.capitalize()), alt.Tooltip("profit:Q", format=",.0f", title="Kept that month £")]
    ).add_params(hover)
    zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="rgba(148,163,184,.4)").encode(y="y:Q")
    st.markdown("##### What the reseller keeps, building up month by month")
    st.altair_chart(chart_cfg((area + line + zero + pts).properties(height=260)), use_container_width=True)

    rows = []
    for y in range(0, term, 12):
        seg = sim["rows"][y:y + 12]
        rev = sum(r["revenue"] for r in seg)
        cost = sum(r["wholesale"] + r["shortfall"] + r["fees"] for r in seg)
        row = {"Year": f"Year {y // 12 + 1}", unit.capitalize(): f"{seg[-1]['customers']:.0f}",
               "Their customers pay them": money(rev, 0), "They pay Call Scope": money(cost, 0),
               "They keep": money(rev - cost, 0), "Kept so far": money(seg[-1]["cumulative"], 0)}
        if T["shortfall"]:
            row["of which shortfall"] = money(sum(r["shortfall"] for r in seg), 0)
        rows.append(row)
    show_df(pd.DataFrame(rows))
    st.caption("Illustrative only - excludes VAT and the annual price review. " + f"Every {one} is assumed to take the mix above.")


def compare_view(sim, kw, term):
    st.markdown("##### Same growth plan, every tier")
    tiers = compare_tiers(CFG, term, **kw)
    best = max(tiers, key=lambda s: s["totals"]["profit"])
    rows = []
    for s in tiers:
        t = s["tier"]
        hit = s["commit_hit_month"]
        rows.append({"Tier": t["name"] + ("  (best)" if s is best else ""), "Discount": f"{s['discount']:g}%",
                     "Commitment": int(t["commit"]) or "None",
                     "Commitment reached": "n/a" if not t["commit"] else (f"Month {hit}" if hit else "Not reached"),
                     "Onboarding": money(t["onboarding"], 0), "Shortfall paid": money(s["totals"]["shortfall"], 0),
                     "Reseller keeps": money(s["totals"]["profit"], 0), "Keeps per £1 paid": f"£{s['roi_pct'] / 100:.2f}",
                     "_p": s["totals"]["profit"], "_n": t["name"]})
    df = pd.DataFrame(rows)
    ch = alt.Chart(df).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, size=26).encode(
        y=alt.Y("_n:N", sort=None, title=None),
        x=alt.X("_p:Q", title="Reseller keeps over the term (£)", axis=alt.Axis(format=",.0f")),
        color=alt.condition(alt.datum._n == best["tier"]["name"], alt.value("#7C83FF"), alt.value("#3A4466")),
        tooltip=[alt.Tooltip("_n:N", title="Tier"), alt.Tooltip("Reseller keeps:N"), alt.Tooltip("Shortfall paid:N"),
                 alt.Tooltip("Keeps per £1 paid:N")])
    st.altair_chart(chart_cfg(ch.properties(height=40 * len(rows) + 30)), use_container_width=True)
    show_df(df.drop(columns=["_p", "_n"]))
    cur = sim["totals"]["profit"]
    if best["tier"]["name"] != sim["tier"]["name"]:
        st.success(f"On this plan, {best['tier']['name']} lets the reseller keep {money(best['totals']['profit'] - cur, 0)} more "
                   f"than {sim['tier']['name']} over {term} months.")
    else:
        st.success(f"{sim['tier']['name']} is the best tier for this growth plan.")

    st.markdown("##### Same tier, every partner term")
    rows = []
    for t in CFG["reseller"]["terms"]:
        s = simulate_partner(CFG, sim["tier"]["name"], int(t["months"]), **kw)
        rows.append({"Partner term": f"{t['months']} months", "Extra discount": f"+{t['bonus']:g}%", "Total discount": f"{s['discount']:g}%",
                     "Keeps per customer": money(s["per_customer"]["profit"]) + "/mo",
                     "Reseller keeps over term": money(s["totals"]["profit"], 0),
                     "Average kept per month": money(s["totals"]["profit"] / max(1, s["term"]), 0)})
    show_df(pd.DataFrame(rows))


# ═══════════════════════════ ADMIN ═══════════════════════════
def admin_unlock():
    """Sales logins can open Admin with the admin password - margins and settings stay locked otherwise."""
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        with st.container(key="card-unlock"):
            section_header('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>', "Admin is locked", "Margins, contract values and price settings")
            with st.form("unlock"):
                pw = st.text_input("Admin password", type="password")
                ok = st.form_submit_button("Unlock", **FULL_WIDTH)
            if ok:
                apw = secret("ADMIN_PASSWORD")
                if apw and hmac.compare_digest(pw.encode(), str(apw).encode()):
                    st.session_state.role = "admin"
                    st.rerun()
                st.error("That password isn't right.")


def deal_margins():
    lq, ls = st.session_state.get("_last_q"), st.session_state.get("_last_sim")
    st.caption("Internal only. Uses the customer quote and partner plan currently open in this session.")
    st.markdown("##### Customer quote" + (f" - {esc(lq['who'])}" if lq and lq.get("who") else ""))
    if lq and lq["q"]["lines"]:
        q = lq["q"]
        kpi_row([("Contract value", money(q["contract_value"], 0), f"services {money(q['services_value'], 0)} + set-up {money(q['setup_total'], 0)}"),
                 ("With annual review", money(q["services_value_with_review"] + q["setup_total"], 0), f"at {q['review_pct']:g}% a year"),
                 ("Monthly at start", money(q["monthly_total"]), f"{q['term']} months"),
                 ("Standard monthly", money(q["standard_monthly"]), f"{q['discount']:g}% intro discount")])
        st.write("")
        margin_view(q)
    else:
        st.caption("No customer quote in progress - build one in Customer quote and come back.")
    st.divider()
    st.markdown("##### Partner plan" + (f" - {esc(ls['who'])}" if ls and ls.get("who") else ""))
    if ls:
        sim = ls["sim"]; T = sim["totals"]
        paid = sim["spend"]
        our_costs = paid - T["ours"]
        st.markdown("**Call Scope - the provider**")
        money_flow([("The reseller pays Call Scope", money(paid, 0), "wholesale, set-up, fees and any shortfall", ""),
                    ("Call Scope's running costs", money(our_costs, 0), "platform, AI, minutes and set-up costs", ""),
                    ("Call Scope keeps", money(T["ours"], 0), f"{(T['ours'] / paid * 100) if paid else 0:.0f}% of what the reseller pays", "good")])
        st.write("")
        st.markdown("**Who earns what** - everything the end customers pay over the term")
        tot = T["revenue"] or 1
        parts = [("Reseller keeps", T["profit"], "#7C83FF"), ("Call Scope keeps", T["ours"], "#38D6F5"), ("Running costs", our_costs, "#5E6A82")]
        render_html('<div class="pe-split">' + "".join(
            f'<div style="flex:{max(v, 0) / tot:.4f};background:{c}">{(f"{v / tot * 100:.0f}%") if v / tot > .08 else ""}</div>' for _, v, c in parts)
            + '</div><div class="pe-legend">' + "".join(f'<span style="--c:{c}">{esc(n)} {money(v, 0)}</span>' for n, v, c in parts)
            + f'<span>End customers pay {money(T["revenue"], 0)}</span></div>')
        st.write("")
        show_df(pd.DataFrame([{"Module": w["name"], "RRP (end customer)": money(w["rrp"]), "Reseller pays Call Scope": money(w["wholesale"]),
                               "Reseller keeps /unit": money(w["partner_margin"]), "Call Scope's cost": money(w["buy"]),
                               "Call Scope keeps /unit": money(w["wholesale"] - w["buy"]),
                               "Call Scope margin": f"{((w['wholesale'] - w['buy']) / w['wholesale'] * 100) if w['wholesale'] else 0:.0f}%"}
                              for w in sim["wholesale"]]))
    else:
        st.caption("No partner plan in progress - build one in Reseller partner and come back.")


def zoho_admin():
    st.markdown("**Zoho CRM connection** - used by 'Pull details from Zoho'. It shares the Secrets of the SYGroup Pricebook.")
    if st.button("Test the Zoho connection"):
        if not ZH.configured():
            st.warning("Not connected - ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET and ZOHO_REFRESH_TOKEN aren't all in Secrets.")
        else:
            try:
                ZH.token(fresh=True)
                st.success(f"Connected to Zoho ({ZH.dc} data centre).")
            except Exception as e:
                st.error(str(e))
    st.divider()
    st.markdown("**Make a new refresh token** (only if the test fails or the token was made with the wrong scope)")
    dcs = ["eu", "com", "in", "com.au", "jp"]
    dc = st.selectbox("Zoho data centre", dcs, index=dcs.index(ZH.dc) if ZH.dc in dcs else 0, key="_zt_dc")
    st.markdown(f"1. In **api-console.zoho.{dc}** - Self Client - Generate Code, with this scope (10 minutes):")
    st.code("ZohoCRM.modules.READ,ZohoCRM.settings.READ", language=None)
    c1, c2 = st.columns(2)
    cid = c1.text_input("Client ID", value=ZH.sec("ZOHO_CLIENT_ID"), key="_zt_cid")
    cs = c2.text_input("Client Secret", type="password", key="_zt_cs",
                       placeholder="leave blank to use the one in Secrets" if ZH.sec("ZOHO_CLIENT_SECRET") else "paste the client secret")
    code = st.text_input("2. Paste the grant code", key="_zt_code", placeholder="1000.xxxxxxxx.xxxxxxxx")
    if st.button("Create refresh token", type="primary"):
        clean = lambda x: "".join(str(x).split()).strip("\"'")
        try:
            rt = ZH.exchange_grant(clean(cid), clean(cs) or ZH.sec("ZOHO_CLIENT_SECRET"), clean(code), dc)
            st.session_state["_zt_result"] = {"rt": rt, "cid": clean(cid), "cs": clean(cs) or ZH.sec("ZOHO_CLIENT_SECRET"), "dc": dc}
        except Exception as e:
            st.error(str(e))
    r = st.session_state.get("_zt_result")
    if r:
        st.success("3. Done - paste these lines into Streamlit > Settings > Secrets and save:")
        st.code(f'ZOHO_CLIENT_ID = "{r["cid"]}"\nZOHO_CLIENT_SECRET = "(your client secret)"\nZOHO_REFRESH_TOKEN = "{r["rt"]}"'
                + (f'\nZOHO_DC = "{r["dc"]}"' if r["dc"] != "eu" else ""), language="toml")
        if st.button("Use it now (this session only)"):
            st.session_state["_zoho_over"] = {"ZOHO_CLIENT_ID": r["cid"], "ZOHO_CLIENT_SECRET": r["cs"],
                                              "ZOHO_REFRESH_TOKEN": r["rt"], "ZOHO_DC": r["dc"]}
            st.session_state.pop("_zoho_tok", None)
            st.success("Active for this session.")


def admin_mode():
    render_hero("Admin", "Pricebook", "settings", "Margins, prices, tiers, branding, terms and the Zoho connection.",
                ["Edit", "Save"], 0)
    if not IS_ADMIN:
        admin_unlock()
        return
    draft = copy.deepcopy(CFG)
    tabs = st.tabs(["Deal margins", "Services", "Customer terms", "Reseller tiers", "Set-up and minutes", "Branding",
                    "Terms & Conditions", "Zoho", "Save / backup"])
    with tabs[0]:
        deal_margins()
    with tabs[7]:
        zoho_admin()

    with tabs[1]:
        st.caption("Monthly modules. Buy = our cost. RRP = standard customer price. Licence = counts towards a reseller's commitment.")
        df = pd.DataFrame(draft["modules"])[["id", "name", "unit", "buy", "rrp", "discountable", "counts_to_commit", "blurb"]]
        ed = st.data_editor(df, num_rows="dynamic", key="ad_mods", hide_index=True,
                            column_config={"id": st.column_config.TextColumn("ID", help="Short unique code, no spaces"),
                                           "buy": st.column_config.NumberColumn("Buy £", format="%.2f"),
                                           "rrp": st.column_config.NumberColumn("RRP £", format="%.2f"),
                                           "discountable": "Discountable", "counts_to_commit": "Licence"})
        draft["modules"] = [r for r in ed.fillna({"unit": "", "blurb": "", "discountable": True, "counts_to_commit": True}).to_dict("records")
                            if str(r.get("id") or "").strip() and str(r.get("name") or "").strip()]

    with tabs[2]:
        st.caption("For each customer term, the biggest introductory discount allowed.")
        ed = st.data_editor(pd.DataFrame(draft["customer_terms"]), num_rows="dynamic", key="ad_cterms", hide_index=True,
                            column_config={"months": st.column_config.NumberColumn("Term (months)", step=12),
                                           "max_discount": st.column_config.NumberColumn("Max discount %", step=5)})
        draft["customer_terms"] = sorted([r for r in ed.dropna().to_dict("records") if r["months"]], key=lambda r: r["months"])
        c1, c2, c3, c4 = st.columns(4)
        draft["annual_review_pct"] = c1.number_input("Annual price review %", 0.0, 20.0, float(draft["annual_review_pct"]), 0.5)
        draft["late_payment_fee"] = c2.number_input("Late payment fee £", 0.0, 500.0, float(draft["late_payment_fee"]), 5.0)
        draft["renewal_months"] = c3.number_input("Renewal period (months)", 1, 36, int(draft["renewal_months"]))
        draft["notice_days"] = c4.number_input("Notice period (days)", 0, 365, int(draft["notice_days"]))

    with tabs[3]:
        R = draft["reseller"]
        st.caption("Commitment = licences the partner commits to. Discount = % off RRP. White label = included free in that tier.")
        ed = st.data_editor(pd.DataFrame(R["tiers"])[["name", "commit", "discount", "onboarding", "white_label", "note"]],
                            num_rows="dynamic", key="ad_tiers", hide_index=True,
                            column_config={"commit": st.column_config.NumberColumn("Commitment", step=5),
                                           "discount": st.column_config.NumberColumn("Discount %", step=1),
                                           "onboarding": st.column_config.NumberColumn("Onboarding £", format="%.2f")})
        R["tiers"] = sorted([r for r in ed.fillna({"note": "", "white_label": False}).to_dict("records") if str(r.get("name") or "").strip()],
                            key=lambda r: r["commit"] or 0)
        st.caption("Partner terms and the extra discount each one adds.")
        ed = st.data_editor(pd.DataFrame(R["terms"]), num_rows="dynamic", key="ad_rterms", hide_index=True,
                            column_config={"months": st.column_config.NumberColumn("Term (months)", step=12),
                                           "bonus": st.column_config.NumberColumn("Extra discount %", step=0.5)})
        R["terms"] = sorted([r for r in ed.dropna().to_dict("records") if r["months"]], key=lambda r: r["months"])
        c1, c2, c3 = st.columns(3)
        R["floor_margin_pct"] = c1.number_input("Floor: cost + %", 0.0, 200.0, float(R["floor_margin_pct"]), 5.0,
                                                help="Wholesale never goes below our cost plus this %.")
        R["ramp_months"] = c2.number_input("Ramp period (months)", 0, 24, int(R["ramp_months"]))
        R["white_label_fee"] = c3.number_input("White label fee £/mo", 0.0, 2000.0, float(R["white_label_fee"]), 10.0)
        c1, c2, c3 = st.columns(3)
        R["annual_review_pct"] = c1.number_input("Partner annual review %", 0.0, 20.0, float(R["annual_review_pct"]), 0.5)
        R["payment_days"] = c2.number_input("Payment terms (days)", 0, 90, int(R["payment_days"]))

    with tabs[4]:
        st.caption("One-off set-up items. Auto: 'always' = once per order, 'per_receptionist' = one per AI Receptionist, 'optional' = chosen on the quote.")
        ed = st.data_editor(pd.DataFrame(draft["setup"]), key="ad_setup", hide_index=True, disabled=["id", "auto"],
                            column_config={"buy": st.column_config.NumberColumn("Buy £", format="%.2f"),
                                           "rrp": st.column_config.NumberColumn("RRP £", format="%.2f"),
                                           "wholesale": st.column_config.NumberColumn("Partner price £", format="%.2f")})
        draft["setup"] = ed.to_dict("records")
        M = draft["minutes"]
        c1, c2, c3, c4 = st.columns(4)
        M["buy_per_min"] = c1.number_input("Minutes: our cost per min £", 0.0, 2.0, float(M["buy_per_min"]), 0.01, format="%.2f")
        M["rrp_per_min"] = c2.number_input("Minutes: RRP per min £", 0.0, 2.0, float(M["rrp_per_min"]), 0.01, format="%.2f")
        M["wholesale_per_min"] = c3.number_input("Minutes: partner per min £", 0.0, 2.0, float(M["wholesale_per_min"]), 0.01, format="%.2f")
        b = c4.text_input("Bundle sizes", ", ".join(str(x) for x in M["bundles"]))
        try:
            M["bundles"] = [int(x) for x in re.split(r"[,\s]+", b) if x.strip()]
        except ValueError:
            st.error("Bundle sizes must be whole numbers separated by commas.")

    with tabs[5]:
        Bd = draft["brand"]
        c1, c2 = st.columns(2)
        Bd["trading"] = c1.text_input("Trading name", Bd["trading"])
        Bd["byline"] = c2.text_input("Byline", Bd["byline"])
        Bd["legal"] = c1.text_input("Legal company name (the contracting party)", Bd["legal"])
        Bd["tag"] = c2.text_input("Tagline", Bd["tag"])
        Bd["email"] = c1.text_input("Contact email", Bd["email"])
        Bd["website"] = c2.text_input("Website", Bd["website"])
        Bd["address"] = st.text_input("Registered address", Bd["address"])
        c1, c2 = st.columns(2)
        Bd["accent"] = c1.color_picker("PDF accent colour", Bd["accent"])
        Bd["navy"] = c2.color_picker("PDF dark colour", Bd["navy"])
        st.caption("To change the logo, replace assets/callscope_logo.png in the GitHub repo.")

    with tabs[6]:
        st.caption("'## ' starts a clause heading; a blank line starts a new paragraph. Words in {CURLY} brackets are filled in automatically "
                   "- keep them. Have any changes checked by a solicitor.")
        which = st.radio("Edit", ["Customer terms", "Partner terms"], horizontal=True, key="ad_which")
        fld, dflt = ("terms_customer", CUSTOMER_TERMS) if which == "Customer terms" else ("terms_reseller", RESELLER_TERMS)
        txt = st.text_area("Terms text", draft.get(fld) or dflt, height=480, key=f"ad_{fld}")
        draft[fld] = "" if txt.strip() == dflt.strip() else txt
        if draft[fld]:
            st.caption("Custom text in use. Clear the box and save to go back to the built-in default.")

    with tabs[8]:
        tok, repo, br = secret("GITHUB_TOKEN"), secret("GITHUB_REPO"), secret("GITHUB_BRANCH", "main")
        st.markdown("Changes apply to **this session** as soon as you press Save. To keep them after Streamlit restarts, "
                    "they need saving to GitHub" + (f" (`{esc(repo)}`)." if repo else " - add GITHUB_TOKEN and GITHUB_REPO to Secrets to enable it."))
        c1, c2 = st.columns(2)
        st.download_button("Download settings backup (config.json)", data=config_json(draft), file_name="config.json",
                           mime="application/json", **FULL_WIDTH)
        up = st.file_uploader("Restore settings from a config.json", type=["json"])
        if up and st.button("Restore this file"):
            try:
                st.session_state.cfg = deep_merge(DEFAULTS, json.load(up))
                st.success("Restored. Press Save to keep it.")
                st.rerun()
            except Exception as e:
                st.error(f"Couldn't read that file: {e}")
        if st.button("Reset everything to the built-in defaults"):
            st.session_state.cfg = copy.deepcopy(DEFAULTS)
            st.rerun()

    st.divider()
    c1, c2, _ = st.columns([1, 1, 2])
    if c1.button("Save changes", type="primary", **FULL_WIDTH):
        st.session_state.cfg = draft
        ok, msg = save_local(draft)
        if secret("GITHUB_TOKEN") and secret("GITHUB_REPO"):
            ok, msg = save_github(draft, secret("GITHUB_TOKEN"), secret("GITHUB_REPO"), secret("GITHUB_BRANCH", "main"))
        for k in [k for k in st.session_state.keys() if str(k).startswith("ad_")]:
            del st.session_state[k]          # editors start fresh from the saved settings
        st.session_state["_admin_msg"] = (ok, msg)
        st.rerun()
    if st.session_state.get("_admin_msg"):
        ok, msg = st.session_state.pop("_admin_msg")
        (st.success if ok else st.warning)(msg)
    c2.caption("Saving to GitHub restarts the app on Streamlit Cloud after a minute - that's normal.")


if mode == "Customer quote":
    customer_mode()
elif mode == "Reseller partner":
    reseller_mode()
elif mode == "Admin":
    admin_mode()
