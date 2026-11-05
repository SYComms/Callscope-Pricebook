# Call Scope Pricebook

Stand-alone quoting app for **Call Scope**, with two sides:

| Workspace | What it does | Paperwork |
|---|---|---|
| **Customer quote** | Direct sale to a business. Pick modules, minutes, term (12–60 months) and an introductory discount (capped by term). The discount steps down evenly each year to the standard price in the final year, or can be fixed for the term. Includes a Customer View, Price Schedule chart and an internal Margin tab. | Service Order + Price Schedule + Call Scope Terms & Conditions (PDF) |
| **Reseller partner** | Wholesale pricing by tier (Registered / Silver / Gold / Platinum), commitment, ramp and partner term. Models the partner's growth and shows their return: profit over the term, return on spend, payback, running-profit chart, tier and term comparison. | Partner Order + Wholesale Price List + Partner Terms (PDF), and a 1-page ROI projection |
| **Admin** (admin password only) | Edit services, prices, term discount caps, tiers, set-up fees, minutes rates, branding and both sets of T&Cs. | `config.json` backup / restore |

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
assets/              logo and product images
```

The T&Cs are a working draft – have them reviewed by a solicitor before use.
