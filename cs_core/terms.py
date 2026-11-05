"""Default Terms & Conditions text.

Format: a line starting "## " is a clause heading; blank lines separate paragraphs.
Placeholders in {CURLY} brackets are filled in from the quote and the brand settings.
Both texts can be edited in the app (Admin > Terms). Have them reviewed by a solicitor
before relying on them.
"""

CUSTOMER_TERMS = """## 1. ABOUT THESE TERMS
These terms apply to the {BRAND} services listed on your {BRAND} Service Order (the Services), which {PROVIDER} ("we", "us") provides to the customer named on the Order ("you"). Together with the Order and the Price Schedule they form the whole agreement for the Services. They are a stand-alone agreement and do not depend on you buying any other product or service from us.

"Order" means the {BRAND} Service Order and Price Schedule you sign. "Minimum Term" means the term shown on the Order, starting on the date the Services are first made available to you (the Start Date). "Charges" means the prices on the Order as they change under clause 11. "Customer Content" means call recordings, transcripts, text and other data that you or your users put into, or create using, the Services.

## 2. THE SERVICES
{BRAND} is a cloud-based call intelligence service. Depending on the modules on your Order it can transcribe, summarise and score calls, answer calls with an AI receptionist, connect to your CRM and portal, and report on call activity. It works with compatible telephony platforms; we will confirm compatibility before the Start Date. We provide the Services with reasonable skill and care. We do not promise that they will be uninterrupted or error-free. We may carry out maintenance, updates and improvements, and will give notice of planned work that is likely to affect you where we reasonably can.

## 3. YOUR ACCOUNT AND USERS
The Services are for business use only. You must give us accurate information, keep login details secure, and you are responsible for everything done under your accounts. Accounts and modules are for the users and modules on your Order and must not be shared between people to avoid paying for extra users. Tell us promptly if you think an account has been compromised. You may add users or modules at any time; they are charged at the prices then applying and run to the end of the Minimum Term.

## 4. AI OUTPUT
Parts of the Services use artificial intelligence, including language models and speech recognition supplied by third parties. AI output (transcripts, summaries, scores, classifications, suggestions and automated call handling) can contain mistakes, omissions or inappropriate content, and can differ from one run to the next. You must review AI output before relying on it. It is not legal, financial, HR, medical or other professional advice. Do not use output on its own to make decisions about a person (for example disciplinary, employment or credit decisions) without meaningful human review. We give no warranty that output is accurate, complete or fit for any particular purpose.

## 5. RECORDING, CONSENT AND LAWFUL USE
You are responsible for making sure that recording, transcribing and analysing calls is lawful. In the UK this includes the Investigatory Powers Act 2016, the Telecommunications (Lawful Business Practice) (Interception of Communications) Regulations 2000, the UK GDPR and the Data Protection Act 2018. You must have a lawful basis, tell callers and staff that calls are recorded and analysed (including by AI) and why, and keep your own privacy notices up to date. We do not decide what you record. If you use the Services for calls with people outside the UK, you are responsible for complying with local consent laws.

## 6. DATA PROTECTION
For personal data in Customer Content you are the controller and we are your processor. We will: (a) process it only on your documented instructions (these terms, the Order and your use of the Services are your instructions); (b) make sure anyone we allow to access it is bound by confidentiality; (c) keep appropriate technical and organisational security measures; (d) use sub-processors (such as hosting and AI providers) only under written terms giving the same level of protection, and give you a list on request and notice of significant changes, with a right to object; (e) help you respond to data subject requests and meet your security, impact assessment and breach obligations; (f) tell you without undue delay after becoming aware of a personal data breach affecting your data; (g) not transfer personal data outside the UK without lawful safeguards, such as an adequacy decision or approved contractual clauses; (h) provide the information reasonably needed to show compliance and allow reasonable audits on notice, no more than once a year unless a regulator requires otherwise; and (i) when the Services end, let you export your Customer Content for 30 days and then delete it, unless the law requires us to keep it. Further detail of the processing (subject matter, duration, types of data and data subjects) is in our data processing schedule, available from {EMAIL}.

## 7. YOUR CONTENT AND OUR RIGHTS
You own your Customer Content. You give us a limited licence to use it only as needed to provide, secure and support the Services to you. We will not sell it or use it to train our own AI models, and we require our AI providers to process it only to deliver the Services. We own or license the platform, software, prompts, scoring methods, designs and documentation, and you must not copy or reverse engineer them. We may use anonymised usage statistics that do not identify you or any individual to run and improve the Services.

## 8. ACCEPTABLE USE
You must not use the Services: unlawfully (including to record calls without a lawful basis); to upload malware or harmful or infringing content; to reverse engineer, scrape or extract source code, prompts or models; to resell, sublicense or give access to others without our written consent; for bulk, automated or excessive use beyond normal business use for your own calls, including training your own AI models on the output; or to get around limits, minute bundles or security. Minute bundles are for your own call volumes. We may suspend access to stop a breach of this clause and will tell you as soon as reasonably possible.

## 9. THIRD PARTY SERVICES
The Services connect to services we do not control, such as telephony platforms, CRMs, AI and speech providers and hosting. We are not responsible for outages, changes or behaviour of those services, but we will use reasonable efforts to restore affected integrations promptly.

## 10. CHARGES AND PAYMENT
All Charges exclude VAT. Monthly Charges are invoiced monthly in advance and are payable by Direct Debit, or otherwise within 14 days of the invoice date. A late payment fee of {LATE_FEE} applies if an invoice is more than 7 days overdue, and we may also claim interest and compensation under the Late Payment of Commercial Debts (Interest) Act 1998. One-off set-up charges are shown separately on the Order{SETUP_SENTENCE}. Where a module includes a minutes bundle, usage above the bundle is charged at our standard per-minute rate then in force, which we will confirm on request. Unused minutes do not carry over.

## 11. DISCOUNTS AND PRICE CHANGES
{PRICE_CLAUSE}

## 12. TERM, RENEWAL AND CANCELLATION
The Services start on the Start Date and continue for the Minimum Term of {TERM}. At the end of the Minimum Term, and of each renewal, they renew automatically for {RENEWAL} unless either party gives at least {NOTICE} days' written notice to end them at the end of the then-current term. If you cancel during the Minimum Term (other than because of our material breach that we have not fixed), the Charges for the rest of the Minimum Term, at the prices in the Price Schedule, become payable.

## 13. SUSPENSION AND TERMINATION
We may suspend or end the Services if an invoice stays unpaid 7 days after we notify you, if you breach clause 5 or 8, or if you become insolvent. Either party may end the Services if the other commits a material breach and does not fix it within 30 days of notice. When the Services end, your access stops, unpaid Charges become due, and clause 6(i) applies to your data. Clauses that by their nature should continue (including 4, 5, 7 and 14 to 18) do so.

## 14. WARRANTIES AND LIABILITY
Except as set out here, the Services are provided "as is" and "as available" and all implied warranties are excluded as far as the law allows. Nothing limits liability for death or personal injury caused by negligence, for fraud, or for anything else that cannot be limited by law. Subject to that: we are not liable for loss of profit, business, goodwill or any indirect or consequential loss; we are not liable for loss caused by your reliance on AI output or by your unlawful recording or use of calls; and our total liability for all claims in a contract year is limited to the Charges you paid for the Services in the 12 months before the claim arose.

## 15. INDEMNITY
You will cover our reasonable losses and costs arising from third party claims that result from your breach of clause 5 or 8, your Customer Content, or your unlawful recording or use of calls. We will tell you promptly of any claim and let you help defend it.

## 16. CONFIDENTIALITY
Each party must protect the other's confidential information with reasonable care, use it only for this agreement, and not disclose it except to staff, advisers and sub-processors who need it or where the law requires. This lasts for 3 years after the agreement ends.

## 17. CHANGES TO THESE TERMS
We may update these terms where reasonably necessary, for example for changes in law, security, new features, or if the {BRAND} business moves to a new company. We will give you at least 30 days' notice of any material change by email or in the Services. If a change is materially to your disadvantage you may end the Services without charge within that period; otherwise continued use means you accept it.

## 18. GENERAL
This is the whole agreement for the Services and replaces anything said before it. Neither party is liable for delay caused by events outside its reasonable control. If part of these terms cannot be enforced, the rest continues. Only the parties can enforce this agreement (Contracts (Rights of Third Parties) Act 1999). You may not transfer your rights without our written consent; we may transfer ours to another company in our group, or to a company that takes over the {BRAND} business, on notice to you. Notices must be in writing to the contact details on the Order. English law applies and the courts of England and Wales have exclusive jurisdiction. Questions: {EMAIL}.
"""

PRICE_CLAUSE_STEPPED = (
    "Any discount shown on your Order is introductory and applies in full to the Charges for the first 12 months of the Minimum Term only. "
    "From the start of month 13 the discount reduces in equal steps each contract year, so that in the final year of the Minimum Term you pay "
    "the full standard price for your modules. The Price Schedule on your Order shows the monthly Charges for each year; the price does not "
    "jump to the full standard price after the first year. After the Minimum Term, the standard prices then in force apply. Standard prices "
    "are shown on the Order as at the date it was prepared; we may change them for any period after the Minimum Term on 30 days' written notice. "
    "{REVIEW_SENTENCE} If you add or remove users or modules, the Price Schedule is recalculated on the same basis."
)

PRICE_CLAUSE_FIXED = (
    "Any discount shown on your Order applies to the Charges for the whole of the Minimum Term. After the Minimum Term, the standard prices "
    "then in force apply. Standard prices are shown on the Order as at the date it was prepared; we may change them for any period after the "
    "Minimum Term on 30 days' written notice. {REVIEW_SENTENCE} If you add or remove users or modules, the Price Schedule is recalculated on "
    "the same basis."
)

PRICE_CLAUSE_SINGLE = (
    "Any discount shown on your Order applies to the Charges for the Minimum Term. After the Minimum Term, the standard prices then in force "
    "apply. Standard prices are shown on the Order as at the date it was prepared; we may change them for any period after the Minimum Term "
    "on 30 days' written notice. If you add or remove users or modules, the Charges change accordingly."
)

REVIEW_SENTENCE = (
    "On each anniversary of the Start Date the monthly Charges then applying increase by {REVIEW} (the annual price review). "
    "{REVIEW_SHOWN}"
)


RESELLER_TERMS = """## 1. ABOUT THIS AGREEMENT
This Partner Agreement is between {PROVIDER} ("we", "us") and the partner named on the Partner Order ("you"). It sets out how you may buy the {BRAND} services (the Services) from us at wholesale prices and resell them to your own business customers (End Customers). It is made up of the Partner Order, the Wholesale Price List and these terms. If they conflict, the Partner Order applies first, then the Wholesale Price List, then these terms.

"Licence" means one unit of a monthly module that counts towards your commitment, as marked on the Wholesale Price List. "Commitment" means the number of Licences for your partner tier shown on the Partner Order. "Initial Term" means the partner term shown on the Partner Order, starting on the date we first make the partner portal available to you (the Start Date).

## 2. APPOINTMENT
We appoint you as a non-exclusive reseller of the Services in the United Kingdom for the term of this agreement. You buy from us and sell to End Customers in your own name and on your own account. You are not our agent, and nothing in this agreement creates a partnership, joint venture or employment. You must not make promises, give warranties or accept obligations on our behalf. We remain free to appoint other partners and to sell the Services directly.

## 3. PARTNER TIERS AND COMMITMENT
Your tier, discount, Commitment and any onboarding fee are shown on the Partner Order. If the Partner Order says the onboarding fee is deferred, it is invoiced with your first End Customer order; if it says waived, it is not payable. You have a ramp period of {RAMP} months from the Start Date to reach your Commitment. From the end of the ramp period, if the number of live Licences you are billed for in a month is below your Commitment, we will charge the shortfall at the lowest wholesale Licence price on your Wholesale Price List (the Shortfall Charge). A tier with no Commitment (such as Bronze) is pay as you go: there is no Shortfall Charge and you pay only for live End Customer subscriptions.

We review tiers every quarter. If your live Licences stay at or above the next tier's Commitment for three consecutive months, we will move you up to that tier from the next billing month, and your new Commitment becomes the higher figure. You may ask to move down a tier at the end of each contract year on 30 days' notice; the onboarding fee for the lower tier is not charged again.

## 4. ORDERS AND END CUSTOMERS
You place orders for End Customers through the partner portal or as we otherwise agree. Each End Customer subscription runs for at least 12 months from its own go-live date, and is billed to you even if it runs past the end of this agreement, until it ends or moves under clause 17. You are responsible for your contract with each End Customer, for billing and collecting from them, and for their first-line support.

Your contract with each End Customer must include terms at least as protective of us as our standard {BRAND} end-user terms on: AI output, call recording and consent, acceptable use, data protection, intellectual property and limits of liability. We may give you a copy of those terms to use. You must not offer End Customers any service level, warranty or feature that we do not offer you.

## 5. WHOLESALE CHARGES AND PAYMENT
Wholesale prices are shown on your Wholesale Price List and exclude VAT. We invoice you monthly in advance for all live Licences, modules and minutes bundles, plus any Shortfall Charge and white label fee, and monthly in arrears for minutes used above bundles. One-off set-up charges are invoiced when the End Customer order is accepted. Invoices are payable by Direct Debit, or otherwise within {PAY_DAYS} days of the invoice date, without set-off or deduction.

You must pay us whether or not your End Customer pays you. If you pay late we may charge interest and compensation under the Late Payment of Commercial Debts (Interest) Act 1998, and if an invoice stays unpaid 14 days after we notify you, we may suspend new orders and, after a further 7 days, suspend the Services for your End Customers.

## 6. PRICES AND PRICE CHANGES
You are free to set your own prices to End Customers. We publish a recommended retail price (RRP) for information only. On each anniversary of the Start Date the wholesale prices then applying increase by {REVIEW} (the annual price review). We may also change wholesale prices or the RRP for other reasons (for example a change in our supplier costs or in the law) on at least 60 days' written notice; if a change other than the annual price review increases your wholesale prices by more than 10% in a year, you may end this agreement without a Shortfall Charge by giving notice within that period. Your discount from RRP for your tier will not be reduced during the Initial Term except under clause 3.

## 7. BRANDING AND WHITE LABEL
We give you a non-exclusive, non-transferable licence during this agreement to use the {BRAND} name and logos to market the Services, following our brand guidelines. You must not register or use any name, domain or social handle that includes "{BRAND}" without our written consent. If white label is on your Partner Order, we will present the End Customer portal and reports under your branding, and you must not describe the Services as your own technology in a misleading way. Marketing that names us must be approved by us before use; we will not unreasonably delay approval.

## 8. SUPPORT AND SERVICE
You provide first-line support to your End Customers. We provide second-line support to your nominated staff by email and through the partner portal, 9am to 5:30pm Monday to Friday excluding bank holidays, and will use reasonable efforts to restore the Services promptly. We will provide onboarding and product training for your staff as part of your onboarding, and sales and marketing material for your use. We will keep a service status page and tell you of planned maintenance likely to affect End Customers.

## 9. YOUR OBLIGATIONS
You must: keep enough trained staff to sell and support the Services; describe the Services accurately and not overstate what AI can do; comply with all laws that apply to your business, including consumer, marketing, data protection, anti-bribery (Bribery Act 2010), anti-slavery and sanctions laws; only sell to businesses; keep accurate records of your End Customers and give us the information we reasonably need to provide the Services; and tell us promptly of any complaint, claim or security issue involving the Services.

## 10. DATA PROTECTION
For personal data in End Customer content, the End Customer is the controller, you are its processor and we are your sub-processor. For personal data about your own staff and End Customer contacts that we need to run your account, each of us is a separate controller. We will process End Customer personal data on the terms of our data processing schedule, which you must flow down in your End Customer contract, and we will help you meet your obligations to End Customers. You must obtain any consents and give any notices needed for us to provide the Services.

## 11. AI OUTPUT AND CALL RECORDING
You must tell End Customers that AI output can contain mistakes, must be reviewed before it is relied on, and is not professional advice, and that they are responsible for making sure that recording and analysing calls is lawful. We are not responsible for loss caused by reliance on AI output or by unlawful recording or use of calls by you or an End Customer.

## 12. INTELLECTUAL PROPERTY
We and our licensors own all rights in the Services, platform, software, prompts, scoring methods, designs and documentation. You must not copy, modify, reverse engineer or build a competing product from them. You own your own brand and marketing material, and you give us a licence to use your name and logo to provide white label services and, with your consent, to list you as a partner.

## 13. CONFIDENTIALITY
Each party must protect the other's confidential information, including wholesale prices, End Customer details and product roadmaps, with reasonable care, use it only for this agreement, and not disclose it except to staff, advisers and sub-processors who need it or where the law requires. This lasts for 3 years after the agreement ends.

## 14. NON-SOLICITATION
During this agreement and for 12 months after it ends, we will not knowingly approach an End Customer you introduced to us to sell them the Services directly, unless the End Customer approaches us first, you ask us to, or the agreement ended because of your breach or insolvency. During the same period neither party will knowingly solicit for employment any of the other's staff who worked on this agreement, without consent. General advertising is not solicitation.

## 15. LIABILITY
Nothing limits liability for death or personal injury caused by negligence, for fraud, or for anything else that cannot be limited by law, or your obligation to pay the charges. Subject to that: neither party is liable for loss of profit, revenue, business, goodwill or any indirect or consequential loss; and each party's total liability for all claims in a contract year is limited to the wholesale charges paid and payable under this agreement in the 12 months before the claim arose.

## 16. INDEMNITY
You will cover our reasonable losses and costs arising from third party claims (including by End Customers) that result from your breach of clauses 4, 9, 10 or 11, or from promises you made that we did not make to you. We will tell you promptly of any claim and let you help defend it.

## 17. TERM, RENEWAL AND ENDING THE AGREEMENT
This agreement starts on the Start Date and continues for the Initial Term of {PARTNER_TERM}. It then renews automatically for 12 months at a time unless either party gives at least {NOTICE} days' written notice to end it at the end of the then-current term. Either party may end it immediately if the other commits a material breach and does not fix it within 30 days of notice, or becomes insolvent. We may end it on 14 days' notice if you do not pay an undisputed invoice within 30 days of its due date.

If you end this agreement during the Initial Term (other than because of our unremedied material breach), or we end it because of your breach, the Shortfall Charge for each remaining month of the Initial Term becomes payable, calculated as if you had no live Licences, less the charges for End Customer subscriptions you continue to pay for. When the agreement ends: existing End Customer subscriptions continue on the same wholesale terms until the end of their own term, or, if you prefer, we will offer to contract with those End Customers directly, with your agreement; you must stop using our brand; and each party must return or destroy the other's confidential information.

## 18. CHANGES TO THIS AGREEMENT
We may update these terms where reasonably necessary, for example for changes in law, security, new features, or if the {BRAND} business moves to a new company. We will give you at least 60 days' notice of any material change. If a change is materially to your disadvantage you may end this agreement without a Shortfall Charge within that period; otherwise it applies from the date given.

## 19. GENERAL
This is the whole agreement between us about the Services and replaces anything said before it. Neither party is liable for delay caused by events outside its reasonable control. If part of this agreement cannot be enforced, the rest continues. Only the parties can enforce it (Contracts (Rights of Third Parties) Act 1999). You may not transfer or subcontract your rights or obligations without our written consent; we may transfer ours to another company in our group, or to a company that takes over the {BRAND} business, on notice to you. Notices must be in writing to the contact details on the Partner Order. English law applies and the courts of England and Wales have exclusive jurisdiction. Questions: {EMAIL}.
"""


def parse_terms(raw, subs):
    """Turn the markdown-ish text into [(heading, [paragraphs])] with placeholders filled in."""
    out, cur = [], None
    for line in (raw or "").splitlines():
        if line.startswith("## "):
            cur = [line[3:].strip(), [[]]]
            out.append(cur)
        elif cur is not None:
            if not line.strip():
                if cur[1][-1]:
                    cur[1].append([])
            else:
                cur[1][-1].append(line.strip())
    res = []
    for h, paras in out:
        txt = [" ".join(p) for p in paras if p]
        for _ in range(3):      # placeholders can contain placeholders
            for k, v in subs.items():
                h = h.replace("{" + k + "}", str(v))
                txt = [t.replace("{" + k + "}", str(v)) for t in txt]
        res.append((h, txt))
    return res


def customer_subs(cfg, q):
    from .pricing import money
    b = cfg["brand"]
    review = float(q["review_pct"])
    if q["years"] <= 1:
        price = PRICE_CLAUSE_SINGLE
    elif q["style"] == "fixed":
        price = PRICE_CLAUSE_FIXED
    else:
        price = PRICE_CLAUSE_STEPPED
    if review > 0:
        rs = REVIEW_SENTENCE
        shown = ("The Price Schedule shows the Charges including the annual price review."
                 if q.get("show_review") else
                 "The figures in the Price Schedule are before the annual price review and before VAT.")
    else:
        rs, shown = "", ""
    setup = {"spread": ", and are spread in equal monthly instalments over the first 12 months",
             "waived": ", and have been waived for this Order",
             "included": ", and are included in your separate equipment or telephony agreement with us"
             }.get(q.get("setup_mode"), " and are invoiced when the Order is accepted")
    rn = int(cfg["renewal_months"])
    return {
        "BRAND": b["trading"], "PROVIDER": b["legal"], "EMAIL": b["email"] or "the address on your Order",
        "TERM": f"{q['term']} months", "LATE_FEE": money(cfg["late_payment_fee"]),
        "RENEWAL": f"{rn} months", "NOTICE": int(cfg["notice_days"]),
        "PRICE_CLAUSE": price, "REVIEW_SENTENCE": rs, "REVIEW_SHOWN": shown,
        "REVIEW": f"{review:g}%", "SETUP_SENTENCE": setup,
    }


def reseller_subs(cfg, term):
    b, R = cfg["brand"], cfg["reseller"]
    return {
        "BRAND": b["trading"], "PROVIDER": b["legal"], "EMAIL": b["email"] or "the address on your Partner Order",
        "RAMP": int(R["ramp_months"]), "PAY_DAYS": int(R["payment_days"]),
        "REVIEW": f"{float(R['annual_review_pct']):g}%", "PARTNER_TERM": f"{int(term)} months",
        "NOTICE": int(cfg["notice_days"]),
    }
