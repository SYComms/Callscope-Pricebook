# Call Scope

A Streamlit app with two parts:

- **The website (public, no login):** a product landing page with clickable cards. Each module, industry and "How it works"
  has its own page and its own link, e.g. `?page=ai-call-answer`, `?page=estate-agents`, `?page=how-it-works`.
  No pricing anywhere. Edit the words in `cs_site/content.py`.
- **The Partner area (`?page=partners`, password protected):** the quoting tool below. The "Partners" link in the
  website's top bar goes there.

## Partner area

The quoting tool has two sides:

| Workspace | What it does | Paperwork |
|---|---|---|
| **Customer quote** | Direct sale to a business. Pull the customer from Zoho, pick modules, minutes, term (12–60 months) and an introductory discount (capped by term). The discount steps down evenly each year to the standard price in the final year, or can be fixed for the term. Customer View, Price Schedule, Sign and send. | Agreement to go ahead (cover - the only signature) + Service Order + Price Schedule + Terms & Conditions |
| **Reseller partner** | Wholesale pricing by tier (Bronze pay-as-you-go / Silver / Gold / Platinum), commitment, ramp and partner term (12 months to 7 years, default 3 years), onboarding fee charged, deferred to the first order, or waived. Plan by customers or users a month - or leave the plan empty for a no-cost sign-up pack. Models the partner's growth and return: profit, return on spend, payback, running-profit chart, tier and term comparison. Sign and send. | Agreement to go ahead + Partner Order + Commitment & tiers + Partner Terms, and a 1-page ROI projection |
| **Admin** (locked - admin password) | Deal margins and contract values for the quote/plan in progress, services and prices, term discount caps, tiers, set-up fees, minutes rates, branding, both sets of T&Cs, Zoho connection (with refresh-token helper). | `config.json` backup / restore |

**Signing:** every pack starts with an *Agreement to go ahead* page. One signature there accepts the whole pack. Either download the pack and send it in Zoho Sign (drag a Signature field onto the box on page 1), or sign on screen with the customer and download the signed pack.

## Deploy (GitHub + Streamlit Cloud)

1. Create a new GitHub repo (e.g. `callscope-pricebook`) and upload **everything in this folder**, including the hidden `.streamlit` and `.github` folders.
2. On share.streamlit.io: **New app** → pick the repo → main file `app.py` → choose the URL `callscope-pricebook` → Deploy.
3. In the app's **Settings → Secrets**, paste (see `.streamlit/secrets.toml.example`):

```toml
APP_PASSWORD   = "sales-password"
ADMIN_PASSWORD = "admin-password"
# optional - makes Admin > Save permanent
GITHUB_TOKEN  = "github_pat_..."
GITHUB_REPO   = "sammyatt2010-hub/callscope-pricebook"
GITHUB_BRANCH = "main"
# Zoho CRM look-up - the same values as the SYGroup Pricebook (read-only scope)
ZOHO_CLIENT_ID     = "1000...."
ZOHO_CLIENT_SECRET = "..."
ZOHO_REFRESH_TOKEN = "1000...."
# ZOHO_REG_FIELD = "API name of the Companies House number field"   (optional)
```

The app stays locked until at least one password is set.

**Keeping price changes:** Streamlit Cloud forgets files when it restarts. With `GITHUB_TOKEN` + `GITHUB_REPO` set, Admin → *Save changes* commits `config.json` to the repo so changes stick. Make the token at GitHub → Settings → Developer settings → Fine-grained tokens, limited to this one repo, permission **Contents: Read and write**. Without a token, use *Download settings backup* and upload `config.json` to the repo yourself.

**Keep-alive:** `.github/workflows/keep-alive.yml` wakes the app every 4 hours. If you choose a different app URL, change `APP_URL` in that file.

## How the pricing works

**Customers** – Standard price = RRP × quantity. The intro discount (max per term set in Admin) applies to modules, not minutes. *Stepped*: full discount for months 1–12, then equal yearly steps to standard price in the final year (e.g. 60 months at 40% → 40/30/20/10/0%). *Fixed*: same discount all term. The annual price review (default 5%) can be shown separately or built into the schedule.

**Resellers** – Wholesale = RRP × (1 − tier discount − term bonus), never below our cost + the floor margin (default 25%). Licences = modules marked "Licence". After the ramp period (default 6 months) any gap below the commitment is charged at the cheapest licence price. Partners move up a tier automatically after 3 months above the next commitment.

## Files

```
app.py               the Streamlit app (UI)
cs_core/config.py    default prices/tiers/branding + save to GitHub
cs_core/pricing.py   all the maths (customer schedule, wholesale, partner ROI)
cs_core/pdfs.py      the PDF paperwork
cs_core/terms.py     default customer and partner T&Cs (editable in Admin)
cs_core/zoho.py      Zoho CRM customer look-up (read-only)
cs_site/content.py   all the website words (modules, industries, how it works)
cs_site/site.py      the website pages and design
assets/              logo and product images
```

The T&Cs are a working draft – have them reviewed by a solicitor before use.
