"""Zoho CRM look-up (read-only) - same connection and Secrets as the SYGroup Pricebook.

Secrets: ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN (EU data centre unless ZOHO_DC is set).
Optional: ZOHO_REG_FIELD = API name of the Companies House number field on the Account.
Scope needed for the refresh token: ZohoCRM.modules.READ,ZohoCRM.settings.READ
"""
import re
import time

import requests


class Zoho:
    def __init__(self, get_secret, state):
        """get_secret(key) -> str ; state = a dict-like (st.session_state) used to cache the access token."""
        self._get = get_secret
        self.state = state

    def sec(self, key):
        v = (self.state.get("_zoho_over", {}) or {}).get(key) or self._get(key) or ""
        return "".join(str(v).split()).strip("\"'")

    @property
    def dc(self):
        return (self.sec("ZOHO_DC") or "eu").lower()

    def configured(self):
        return bool(self.sec("ZOHO_CLIENT_ID") and self.sec("ZOHO_CLIENT_SECRET") and self.sec("ZOHO_REFRESH_TOKEN"))

    def token(self, fresh=False):
        tok = self.state.get("_zoho_tok")
        if tok and tok[1] > time.time() and not fresh:
            return tok[0]
        r = requests.post(f"https://accounts.zoho.{self.dc}/oauth/v2/token", timeout=15, data={
            "grant_type": "refresh_token", "client_id": self.sec("ZOHO_CLIENT_ID"),
            "client_secret": self.sec("ZOHO_CLIENT_SECRET"), "refresh_token": self.sec("ZOHO_REFRESH_TOKEN")})
        try:
            j = r.json()
        except Exception:
            raise RuntimeError(f"Zoho rejected the sign-in (status {r.status_code}, accounts.zoho.{self.dc}). "
                               "Check the client ID, client secret and refresh token in Secrets.")
        if "access_token" not in j:
            raise RuntimeError(f"Zoho sign-in failed ({j.get('error', r.status_code)}) - the refresh token or client details may be wrong")
        self.state["_zoho_tok"] = (j["access_token"], time.time() + 3000)
        return j["access_token"]

    def get(self, path, params=None):
        r = requests.get(f"https://www.zohoapis.{self.dc}/crm/v6/{path}", timeout=20, params=params or {},
                         headers={"Authorization": f"Zoho-oauthtoken {self.token()}"})
        if r.status_code == 204 or not r.content:
            return {}
        try:
            return r.json()
        except Exception:
            raise RuntimeError(f"Zoho gave an unexpected reply (status {r.status_code}): {r.text[:120]!r}")

    # ── search ──
    def search(self, text):
        """Accounts first, then Leads -> (results, note)."""
        res, note = [], ""
        j = self.get("Accounts/search", {"word": text, "per_page": 10})
        if j.get("code") and "data" not in j:
            raise RuntimeError(f"Zoho: {j.get('message') or j.get('code')}")
        for r in j.get("data", []) or []:
            r["_type"] = "Account"
            res.append(r)
        try:
            lj = self.get("Leads/search", {"word": text, "per_page": 10})
            for r in lj.get("data", []) or []:
                r["_type"] = "Lead"
                r["Account_Name"] = r.get("Company") or r.get("Full_Name") or ""
                r["Billing_City"] = r.get("City") or ""
                res.append(r)
        except Exception as e:
            note = f"Leads couldn't be searched ({e})"
        return res, note

    def load(self, rec):
        """Full record + contacts for an Account or Lead -> (record, [contacts])."""
        if rec.get("_type") == "Lead":
            j = self.get(f"Leads/{rec['id']}")
            r = (j.get("data") or [{}])[0]
            name = f"{r.get('First_Name') or ''} {r.get('Last_Name') or ''}".strip() or r.get("Full_Name") or ""
            acct = dict(r)
            acct.update({"Account_Name": r.get("Company") or "", "Phone": r.get("Phone") or r.get("Mobile") or "",
                         "Billing_Street": r.get("Street") or "", "Billing_City": r.get("City") or "",
                         "Billing_State": r.get("State") or "", "Billing_Code": r.get("Zip_Code") or ""})
            contacts = [{"Full_Name": name, "Email": r.get("Email") or "", "Phone": r.get("Mobile") or r.get("Phone") or "",
                         "Title": r.get("Designation") or ""}] if (name or r.get("Email")) else []
            return acct, contacts
        j = self.get(f"Accounts/{rec['id']}")
        acct = (j.get("data") or [{}])[0]
        contacts = []
        try:
            cj = self.get(f"Accounts/{rec['id']}/Contacts", {"fields": "First_Name,Last_Name,Email,Title,Phone,Mobile", "per_page": 20})
            for c in cj.get("data") or []:
                contacts.append({"Full_Name": f"{c.get('First_Name') or ''} {c.get('Last_Name') or ''}".strip(),
                                 "Email": c.get("Email") or "", "Phone": c.get("Phone") or c.get("Mobile") or "",
                                 "Title": c.get("Title") or ""})
        except Exception:
            pass
        return acct, contacts

    def fill_values(self, acct, contact):
        """Zoho record -> the app's customer/partner fields (only non-empty values)."""
        addr = ", ".join(str(acct.get(k) or "").strip() for k in ("Billing_Street", "Billing_City", "Billing_State", "Billing_Code")
                         if str(acct.get(k) or "").strip())

        def find(pat):
            for k, v in acct.items():
                if isinstance(v, (str, int)) and str(v).strip() and re.search(pat, k, re.I):
                    return str(v).strip()
            return ""
        reg_field = self.sec("ZOHO_REG_FIELD")
        reg = str(acct.get(reg_field) or "").strip() if reg_field else ""
        reg = reg or find(r"companies.?house|company.?(no|num|reg)|reg.?(no|num)")
        out = {"company": str(acct.get("Account_Name") or "").strip(), "phone": str(acct.get("Phone") or "").strip(),
               "address": addr, "company_no": reg}
        if contact:
            out["contact"] = str(contact.get("Full_Name") or "").strip()
            out["position"] = str(contact.get("Title") or "").strip()
            out["email"] = str(contact.get("Email") or "").strip()
            if not out["phone"]:
                out["phone"] = str(contact.get("Phone") or "").strip()
        return {k: v for k, v in out.items() if v}

    # ── token helper (grant code -> refresh token) ──
    def exchange_grant(self, client_id, client_secret, code, dc="eu"):
        r = requests.post(f"https://accounts.zoho.{dc}/oauth/v2/token", timeout=20, data={
            "grant_type": "authorization_code", "client_id": client_id, "client_secret": client_secret, "code": code})
        try:
            j = r.json()
        except Exception:
            raise RuntimeError(f"Zoho rejected the request (status {r.status_code}) - most likely the client secret is wrong or cut off.")
        if not j.get("refresh_token"):
            raise RuntimeError(f"Zoho said: {j.get('error', r.status_code)} - the code is probably used or expired. Generate a fresh one.")
        return j["refresh_token"]
