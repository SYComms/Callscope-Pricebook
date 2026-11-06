"""Call Scope Partners area - each reseller's own quoting tool (?page=partners).

Resellers sign in with the login you create for them in Provider > Admin > Partner accounts.
They quote their own customers at their own prices and download Call Scope paperwork 'supplied by' them.
They never see Call Scope's own costs, other partners, Zoho or the Provider tools.
"""
import base64
import copy
import html as html_lib
import inspect
import io
import os
import re
import time
from datetime import date

import pandas as pd
import streamlit as st

from cs_core.config import ROOT, load_config, verify_password
from cs_core.pricing import money, customer_quote, max_discount_for, wholesale_list
from cs_core.pdfs import customer_pack

try:
    from streamlit_drawable_canvas import st_canvas
    CANVAS_OK = True
except Exception:
    CANVAS_OK = False

LOGO = os.path.join(ROOT, "assets", "callscope_logo.png")

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




# ─────────────────────────── helpers ───────────────────────────
def esc(v):
    return html_lib.escape(str(v if v is not None else ""), quote=True)


def render_html(markup, target=None):
    (target or st).markdown(" ".join(l.strip() for l in markup.splitlines() if l.strip()), unsafe_allow_html=True)


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


def show_df(df):
    try:
        st.dataframe(df, hide_index=True, width="stretch")
    except TypeError:
        st.dataframe(df, hide_index=True, use_container_width=True)


def kpi_row(items):
    cols = st.columns(len(items))
    for c, (label, value, note, *tone) in zip(cols, items):
        render_html(f'<div class="pe-kpi {tone[0] if tone else ""}"><div class="l">{esc(label)}</div><div class="v">{esc(value)}</div>'
                    + (f'<div class="n">{esc(note)}</div>' if note else "") + "</div>", c)


def view_switch(options, key):
    if st.session_state.get(key) not in options:
        st.session_state[key] = options[0]
    try:
        v = st.segmented_control("View", options, key=key, label_visibility="collapsed")
    except AttributeError:
        v = st.radio("View", options, key=key, horizontal=True, label_visibility="collapsed")
    return v or options[0]


def safe_file(x):
    return re.sub(r"[^A-Za-z0-9]+", "_", x or "").strip("_") or "Quote"


def b64_file(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""


def render_hero(eyebrow, title_a, title_b, sub, steps, active):
    parts = []
    for i, s_ in enumerate(steps):
        cls = "done" if i < active else ("active" if i == active else "")
        num = "&#10003;" if i < active else str(i + 1)
        if i:
            parts.append('<div class="pe-step-sep"></div>')
        parts.append(f'<div class="pe-step {cls}"><div class="num">{num}</div>{esc(s_)}</div>')
    render_html(f'<div class="pe-hero"><div><div class="pe-eyebrow"><span class="dot"></span>{esc(eyebrow)}</div>'
                f'<div class="pe-title">{esc(title_a)} <span>{esc(title_b)}</span></div><div class="pe-sub">{esc(sub)}</div></div>'
                f'<div class="pe-stepper">{"".join(parts)}</div></div>')


# ─────────────────────────── login ───────────────────────────
def find_account(cfg, email):
    e = (email or "").strip().lower()
    for a in cfg.get("partners", []):
        if a.get("active", True) and (a.get("email") or "").strip().lower() == e:
            return a
    return None


def login(cfg):
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        render_html(f'<div class="pe-login-head"><img src="data:image/png;base64,{b64_file(LOGO)}">'
                    '<div class="t">Call Scope Partner login</div><div class="s">Quote your customers, download paperwork, see your margin</div></div>')
        with st.container(key="card-login"):
            with st.form("partner_login"):
                email = st.text_input("Email")
                pw = st.text_input("Password", type="password")
                ok = st.form_submit_button("Sign in", **FULL_WIDTH)
            if ok:
                acct = find_account(cfg, email)
                if acct and verify_password(pw, acct.get("pw_salt"), acct.get("pw_hash")):
                    st.session_state.partner_id = acct["id"]
                    st.rerun()
                time.sleep(1.0)
                st.error("That email and password don't match a partner account.")
            if not cfg.get("partners"):
                st.caption("No partner accounts have been set up yet.")
        render_html('<div style="text-align:center;margin-top:6px"><a href="?" target="_self" style="color:#8C98B0;font-size:.88rem;'
                    'text-decoration:none">&larr; Back to the Call Scope website</a></div>')
    st.stop()


# ─────────────────────────── the partner's quote ───────────────────────────
def partner_quote(cfg, acct):
    R = cfg["reseller"]
    tier, term_p = acct.get("tier", "Bronze"), int(acct.get("term", R.get("default_term", 36)))
    wl, _ = wholesale_list(cfg, tier, term_p)
    cost = {w["id"]: w["wholesale"] for w in wl}
    mc = cfg["minutes"]
    has_now = any((st.session_state.get(f"pq_{m['id']}") or 0) > 0 for m in cfg["modules"])
    render_hero(f"{acct.get('company', '')} - partner quote", "Quote your", "customer",
                "Set your prices, build the quote, then download Call Scope paperwork supplied by you.",
                ["Customer", "Services", "Terms", "Sign"], 0 if not st.session_state.get("pc_company") else (1 if not has_now else 3))

    left, right = st.columns([2.15, 1], gap="large")
    with left:
        with st.container(key="card-cust"):
            section_header("01", "Your customer", "Who the Service Order is for")
            c1, c2 = st.columns(2)
            c1.text_input("Business name", key="pc_company")
            c2.text_input("Company number", key="pc_company_no")
            c1.text_input("Contact name", key="pc_contact")
            c2.text_input("Position", key="pc_position")
            c1.text_input("Email", key="pc_email")
            c2.text_input("Telephone", key="pc_phone")
            st.text_input("Address", key="pc_address")
            cust = {k: st.session_state.get(f"pc_{k}", "") for k in
                    ("company", "company_no", "contact", "position", "email", "phone", "address")}

        with st.container(key="card-svc"):
            section_header("02", "Services and your prices", "Your price starts at our RRP - change it to whatever you charge")
            qty, sell = {}, {}
            mods = cfg["modules"]
            for row in range(0, len(mods), 3):
                cols = st.columns(3)
                for col, m in zip(cols, mods[row:row + 3]):
                    on = (st.session_state.get(f"pq_{m['id']}") or 0) > 0
                    with col:
                        with st.container(key=f"prod-{m['id']}"):
                            render_html(('<span class="pe-on"></span>' if on else "")
                                        + f'<div class="pe-prod-name">{esc(m["name"])}</div>'
                                        f'<div class="pe-prod-price">Your cost <b>{money(cost[m["id"]])}</b> {esc(m.get("unit", ""))} · RRP {money(m["rrp"])}</div>')
                            a, b = st.columns(2)
                            qty[m["id"]] = a.number_input("Qty", 0, 500, step=1, key=f"pq_{m['id']}")
                            if f"ps_{m['id']}" not in st.session_state:
                                st.session_state[f"ps_{m['id']}"] = float(m["rrp"])
                            sell[m["id"]] = b.number_input("Your price", 0.0, 10000.0, step=1.0, format="%.2f", key=f"ps_{m['id']}")
            c1, c2 = st.columns(2)
            minutes = c1.selectbox("AI minutes bundle", [0] + list(mc["bundles"]), key="pc_minutes",
                                   format_func=lambda v: "None" if not v else f"{v:,} mins - {money(v * mc['rrp_per_min'], 0)}/mo")
            agent = next((s_ for s_ in cfg["setup"] if s_["id"] == "agent_setup"), None)
            agents = c2.number_input(f"{agent['name']} (one-off)" if agent else "Bespoke AI agent build", 0, 10, step=1, key="pc_agents")
            with st.expander("Your set-up prices"):
                setup_sell = {}
                cols = st.columns(len(cfg["setup"]))
                for c, s_ in zip(cols, cfg["setup"]):
                    if f"pss_{s_['id']}" not in st.session_state:
                        st.session_state[f"pss_{s_['id']}"] = float(s_["rrp"])
                    setup_sell[s_["id"]] = c.number_input(s_["name"], 0.0, 100000.0, step=5.0, format="%.2f", key=f"pss_{s_['id']}",
                                                          help=f"Your cost {money(s_['wholesale'])} · RRP {money(s_['rrp'])}")

        with st.container(key="card-term"):
            section_header("03", "Term and pricing", "Longer terms allow a bigger introductory discount")
            terms = [int(t["months"]) for t in cfg["customer_terms"]]
            c1, c2 = st.columns(2)
            if st.session_state.get("pc_term") not in terms:
                st.session_state.pc_term = 36 if 36 in terms else terms[-1]
            term = c1.selectbox("Minimum term", terms, key="pc_term", format_func=lambda v: f"{v} months")
            maxd = int(max_discount_for(cfg, term))
            if st.session_state.get("pc_disc", 0) > maxd:
                st.session_state.pc_disc = maxd
            disc = c2.slider(f"Introductory discount (max {maxd}%)", 0, max(maxd, 1), step=5 if maxd % 5 == 0 else 1,
                             key="pc_disc", disabled=maxd == 0)
            disc = min(disc, maxd)
            c1, c2 = st.columns(2)
            years = -(-term // 12)
            style = c1.radio("How the discount runs", ["stepped", "fixed"], key="pc_style", horizontal=True,
                             format_func=lambda v: "Steps back to standard" if v == "stepped" else "Fixed for the term") if years > 1 else "stepped"
            setup_mode = c2.selectbox("Set-up charges", ["invoice", "spread", "waived"], key="pc_setup",
                                      format_func=lambda v: {"invoice": "Invoiced on order", "spread": "Spread over 12 months",
                                                             "waived": "Waived"}[v])
            if "pc_review" not in st.session_state:
                st.session_state.pc_review = float(cfg["annual_review_pct"])
            review = st.number_input("Annual price review %", 0.0, 15.0, step=0.5, key="pc_review")

    # quote at the partner's own prices
    qcfg = copy.deepcopy(cfg)
    for m in qcfg["modules"]:
        m["rrp"] = float(sell.get(m["id"], m["rrp"]))
        m["buy"] = float(cost[m["id"]])
    for s_ in qcfg["setup"]:
        s_["rrp"] = float(setup_sell.get(s_["id"], s_["rrp"]))
        s_["buy"] = float(s_["wholesale"])
    qcfg["minutes"]["buy_per_min"] = mc["wholesale_per_min"]
    q = customer_quote(qcfg, qty, minutes=minutes, agent_setups=agents, term=term, discount=disc, style=style,
                       review_pct=review, setup_mode=setup_mode)
    has = bool(q["lines"])
    supplier = {k: acct.get(k, "") for k in ("company", "email", "phone", "address", "logo_b64")}
    prepared = st.session_state.get("partner_user_name") or acct.get("contact", "")
    fname = f"CallScope_Agreement_{safe_file(cust['company'])}_{date.today()}"
    build = lambda sign=None: customer_pack(qcfg, q, cust, prepared, False, sign=sign, supplier=supplier)
    blank_pdf = build() if has else None
    margin_mo = q["monthly_total"] - q["buy_monthly"]

    with right:
        with st.container(key="card-summary"):
            render_html('<div class="pe-sum-label">Customer pays monthly, at the start</div>')
            if has:
                strike = f'<span class="pe-sum-strike">{money(q["standard_monthly"])}</span>' if disc else ""
                render_html(f'<div class="pe-sum-big">{money(q["monthly_total"])}{strike}</div>')
                render_html(f'<div style="margin:8px 0 10px">{chip(f"{term} months", "accent")}'
                            + (chip(f"{disc:g}% off", "good") if disc else "") + chip("excl. VAT") + "</div>")
                render_html(f'<div class="pe-row">Set-up (one-off)<b>{money(q["setup_total"])}</b></div>'
                            f'<div class="pe-row">Your margin, month 1<b>{money(margin_mo)}</b></div>'
                            f'<div class="pe-row">Your margin over the term<b>{money(q["profit"], 0)}</b></div>')
                st.download_button("Download agreement pack", data=blank_pdf, file_name=f"{fname}.pdf", mime="application/pdf",
                                   type="primary", key="pdl_side", **FULL_WIDTH)
                st.caption("Your margin is never shown on the customer's paperwork.")
            else:
                render_html('<div class="pe-sum-big" style="color:var(--faint)">£0.00</div>')
                st.caption("Add a quantity to any service to start the quote.")

    st.write("")
    if not has:
        return
    view = view_switch(["Your margin", "Sign and send"], "pp_view")
    if view == "Your margin":
        kpi_row([("Customer pays (month 1)", money(q["monthly_total"]), f"standard {money(q['standard_monthly'])}"),
                 ("Your cost (month 1)", money(q["buy_monthly"]), f"{tier} partner prices"),
                 ("Your margin (month 1)", money(margin_mo), f"{(margin_mo / q['monthly_total'] * 100) if q['monthly_total'] else 0:.0f}%", "good"),
                 ("Your margin over the term", money(q["profit"], 0), f"incl. set-up, {term} months", "good")])
        st.write("")
        show_df(pd.DataFrame([{"Service": l["name"], "Qty": l["qty"], "Your price (yr 1)": money(l["price"]),
                               "Your cost": money(l["buy"]), "Margin /month": money((l["price"] - l["buy"]) * l["qty"])}
                              for l in q["lines"]]))
        low = [l["name"] for l in q["lines"] if l["price"] < l["buy"]]
        if low:
            st.warning("Priced below your cost in year 1: " + ", ".join(low) + ".")
        rows = [{"Year": f"Year {r['year']}", "Customer pays /month": money(r["monthly"]),
                 "Discount": "Standard price" if r["discount"] <= 0 else f"{r['discount']:g}% off"} for r in q["schedule"]]
        st.caption("How the customer's price moves each year (before the annual review):")
        show_df(pd.DataFrame(rows))
    else:
        st.caption("The pack: page 1 Agreement to go ahead (the only signature) - Service Order - Price Schedule - Terms & Conditions. "
                   f"Call Scope branded, supplied by {acct.get('company', '')}.")
        left, right = st.columns(2, gap="large")
        with left:
            with st.container(key="card-zsign-p"):
                section_header("A", "Send for e-signature", "Use your own e-signature tool")
                render_html('<ol class="pe-steps"><li><span><b>Download the pack</b> - the signature box on page 1 is left blank.</span></li>'
                            '<li><span><b>Upload it</b> to your e-signature tool (DocuSign, Zoho Sign, Adobe Sign...).</span></li>'
                            '<li><span><b>Place one signature field</b> on the box on page 1 and send it to your customer.</span></li></ol>')
                st.download_button("Download pack for e-signature", data=blank_pdf, file_name=f"{fname}.pdf", mime="application/pdf",
                                   type="primary", key="pdl_es", **FULL_WIDTH)
        with right:
            with st.container(key="card-onscreen-p"):
                section_header("B", "Sign now, on screen", "When you're with the customer")
                sk = "_psig"
                method = st.radio("Signature", ["Draw", "Upload a photo"], horizontal=True, key="_psigm", label_visibility="collapsed")
                if method == "Draw" and CANVAS_OK:
                    cv = st_canvas(fill_color="rgba(0,0,0,0)", stroke_width=3, stroke_color="#000000", background_color="#EAF4FB",
                                   update_streamlit=True, height=170, width=460, drawing_mode="freedraw", key="_pcanvas")
                    b1, b2 = st.columns(2)
                    if b1.button("Save signature", key="_psave", **FULL_WIDTH):
                        sig = _clean_signature(cv.image_data) if (cv is not None and cv.image_data is not None) else None
                        if sig:
                            st.session_state[sk] = sig
                        else:
                            st.warning("Nothing drawn yet.")
                    if b2.button("Clear", key="_pclear", **FULL_WIDTH):
                        st.session_state.pop(sk, None)
                else:
                    up = st.file_uploader("Photo of the signature", type=["png", "jpg", "jpeg"], key="_psigup")
                    if up:
                        from PIL import Image
                        im = Image.open(up).convert("RGB")
                        im.thumbnail((600, 200))
                        buf = io.BytesIO(); im.save(buf, format="PNG")
                        st.session_state[sk] = buf.getvalue()
                c1, c2 = st.columns(2)
                nm = c1.text_input("Signed by", key="_psname", placeholder=cust.get("contact") or "Full name") or cust.get("contact", "")
                pos = c2.text_input("Position", key="_pspos", placeholder=cust.get("position") or "e.g. Director") or cust.get("position", "")
                sig = st.session_state.get(sk)
                if sig:
                    st.image(sig, width=220, caption="Saved signature")
                if sig and nm.strip():
                    from datetime import datetime
                    signed = build({"sig": sig, "name": nm.strip(), "position": pos.strip(), "date": datetime.now().strftime("%d/%m/%Y %H:%M")})
                    st.download_button("Download signed pack", data=signed, file_name=f"{fname}_SIGNED.pdf", mime="application/pdf",
                                       type="primary", key="pdl_signed", **FULL_WIDTH)
                else:
                    st.caption("Still needed: " + ", ".join(x for x, ok in (("signature", sig), ("name", nm.strip())) if not ok))


def price_list(cfg, acct):
    R = cfg["reseller"]
    tier, term_p = acct.get("tier", "Bronze"), int(acct.get("term", R.get("default_term", 36)))
    render_hero(f"{acct.get('company', '')} - {tier} partner", "Your", "price list",
                f"What you pay Call Scope on your {tier} tier and {term_p}-month partner term, against our recommended prices.",
                ["Price list"], 0)
    wl, _ = wholesale_list(cfg, tier, term_p)
    show_df(pd.DataFrame([{"Module": w["name"], "Unit": w["unit"], "Your cost": money(w["wholesale"]), "RRP": money(w["rrp"]),
                           "Your margin at RRP": f"{money(w['partner_margin'])} ({w['partner_margin_pct']:.0f}%)"} for w in wl]))
    mc = cfg["minutes"]
    st.caption(f"AI minutes: {money(mc['wholesale_per_min'] * 100)} per 100 (RRP {money(mc['rrp_per_min'] * 100)}). All prices per month, excluding VAT.")
    st.markdown("**One-off set-up, per customer**")
    show_df(pd.DataFrame([{"Item": s_["name"], "Your cost": money(s_["wholesale"]), "RRP": money(s_["rrp"])} for s_ in cfg["setup"]]))


# ─────────────────────────── entry point ───────────────────────────
def run_partner_portal():
    st.set_page_config(page_title="Call Scope Partners", page_icon=LOGO, layout="wide", initial_sidebar_state="expanded")
    st.markdown("<style>" + CSS + "</style>", unsafe_allow_html=True)
    if "cfg" not in st.session_state:
        st.session_state.cfg = load_config()
    cfg = st.session_state.cfg
    acct = next((a for a in cfg.get("partners", []) if a.get("id") == st.session_state.get("partner_id") and a.get("active", True)), None)
    if not acct:
        st.session_state.pop("partner_id", None)
        login(cfg)
    with st.sidebar:
        logo = acct.get("logo_b64")
        render_html('<div class="pe-brand">'
                    + (f'<img src="data:image/png;base64,{logo}">' if logo else f'<img src="data:image/png;base64,{b64_file(LOGO)}">')
                    + f'<div><div class="n">{esc(acct.get("company", ""))}</div><div class="t">Call Scope partner</div></div></div>')
        st.markdown('<a href="?" target="_self" style="color:#8C98B0;font-size:.85rem;text-decoration:none">&larr; Back to the website</a>',
                    unsafe_allow_html=True)
        mode = st.radio("Workspace", ["New quote", "My price list"], key="pmode")
        st.text_input("Prepared by", key="partner_user_name", placeholder=acct.get("contact", ""))
        render_html(chip(f"{acct.get('tier', 'Bronze')} partner", "accent") + chip(f"{acct.get('term', 36)}-month term"))
        st.divider()
        if st.button("Start a new quote", **FULL_WIDTH):
            for k in [k for k in st.session_state.keys() if str(k).startswith(("pc_", "pq_", "ps_", "pss_", "_ps", "pp_"))]:
                del st.session_state[k]
            st.rerun()
        if st.button("Log out", **FULL_WIDTH):
            st.session_state.clear()
            st.rerun()
    if mode == "My price list":
        price_list(cfg, acct)
    else:
        partner_quote(cfg, acct)
