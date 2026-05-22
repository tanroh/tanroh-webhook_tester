import streamlit as st
import requests
import uuid
from datetime import datetime, date
import random

st.set_page_config(page_title="Financial Webhook Tester", layout="wide", page_icon="📡")

# ── Auto-generate a webhook.site URL once per session ─────────────────────────

def get_webhook_site_url():
    try:
        resp = requests.post("https://webhook.site/token", timeout=5)
        token_uuid = resp.json().get("uuid", "")
        if token_uuid:
            return f"https://webhook.site/{token_uuid}", token_uuid
    except Exception:
        pass
    return "", ""

if "ws_url" not in st.session_state:
    url, uid = get_webhook_site_url()
    st.session_state["ws_url"] = url
    st.session_state["ws_uuid"] = uid

# ── Sample data ───────────────────────────────────────────────────────────────

ASSETS = {
    "Cash & Equivalents":    {"type": "current",     "category": "cash"},
    "Accounts Receivable":   {"type": "current",     "category": "receivable"},
    "Inventory":             {"type": "current",     "category": "inventory"},
    "Real Estate":           {"type": "non-current", "category": "property"},
    "Equipment & Machinery": {"type": "non-current", "category": "fixed"},
    "Marketable Securities": {"type": "current",     "category": "investment"},
    "Intellectual Property": {"type": "non-current", "category": "intangible"},
    "Motor Vehicles":        {"type": "non-current", "category": "fixed"},
}

CREDITORS = {
    "ANZ Bank":            {"type": "secured",   "instrument": "term_loan"},
    "Commonwealth Bank":   {"type": "secured",   "instrument": "overdraft"},
    "ATO":                 {"type": "unsecured", "instrument": "tax_liability"},
    "Trade Creditors":     {"type": "unsecured", "instrument": "accounts_payable"},
    "Westpac Leasing":     {"type": "secured",   "instrument": "finance_lease"},
    "Private Investor":    {"type": "unsecured", "instrument": "private_note"},
    "NAB Invoice Finance": {"type": "secured",   "instrument": "invoice_finance"},
    "Supplier Credit":     {"type": "unsecured", "instrument": "trade_credit"},
}

LIABILITIES = {
    "Mortgage":               {"type": "long-term",  "category": "secured_debt"},
    "Business Loan":          {"type": "long-term",  "category": "term_debt"},
    "Credit Card Facility":   {"type": "short-term", "category": "revolving"},
    "GST Payable":            {"type": "short-term", "category": "tax"},
    "Wages Payable":          {"type": "short-term", "category": "payroll"},
    "Superannuation Payable": {"type": "short-term", "category": "payroll"},
    "Hire Purchase":          {"type": "long-term",  "category": "secured_debt"},
    "Deferred Tax Liability": {"type": "long-term",  "category": "tax"},
}

ENTITIES = [
    "Acme Holdings Pty Ltd",
    "Blue Ridge Ventures Pty Ltd",
    "Southgate Capital Group",
    "Ironwood Enterprises Pty Ltd",
    "Pacific Coast Trading Co",
]

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("📡 Webhook Listener")

    webhook_url = st.text_input(
        "Endpoint URL",
        value=st.session_state["ws_url"],
        help="Auto-generated from webhook.site — or paste your own.",
    )

    if st.session_state.get("ws_url"):
        st.link_button(
            "🌐 Open listener in browser",
            url=st.session_state["ws_url"],
            use_container_width=True,
        )

    if st.button("🔄 Generate new webhook.site URL", use_container_width=True):
        url, uid = get_webhook_site_url()
        st.session_state["ws_url"] = url
        st.session_state["ws_uuid"] = uid
        st.rerun()

    st.divider()
    st.header("🏢 Entity")
    entity_name = st.selectbox("Company / Entity", ENTITIES)
    entity_abn  = st.text_input("ABN", value="51 824 753 556")
    report_date = st.date_input("Report Date", value=date.today())

    st.divider()
    st.header("🎲 Quick Fill")
    if st.button("Randomise all", use_container_width=True):
        st.session_state["random_seed"] = random.randint(0, 9999)
        st.rerun()
    if st.button("Clear randomise", use_container_width=True):
        st.session_state.pop("random_seed", None)
        st.rerun()

# ── Random seed ───────────────────────────────────────────────────────────────

seed = st.session_state.get("random_seed", None)
rng  = random.Random(seed)

def rand_amount(lo=5_000, hi=2_000_000):
    return round(rng.uniform(lo, hi), 2)

# ── Selection columns ─────────────────────────────────────────────────────────

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🏦 Assets")
    selected_assets = st.multiselect(
        "Select assets", list(ASSETS.keys()),
        default=rng.sample(list(ASSETS.keys()), 3) if seed else list(ASSETS.keys())[:3],
    )
    asset_values = {}
    for a in selected_assets:
        asset_values[a] = st.number_input(
            f"{a} (AUD)", min_value=0.0, value=rand_amount(), step=1000.0,
            format="%.2f", key=f"asset_{a}",
        )

with col2:
    st.subheader("🏛️ Creditors")
    selected_creditors = st.multiselect(
        "Select creditors", list(CREDITORS.keys()),
        default=rng.sample(list(CREDITORS.keys()), 2) if seed else list(CREDITORS.keys())[:2],
    )
    creditor_values = {}
    for c in selected_creditors:
        creditor_values[c] = st.number_input(
            f"{c} (AUD)", min_value=0.0, value=rand_amount(10_000, 500_000), step=1000.0,
            format="%.2f", key=f"creditor_{c}",
        )

with col3:
    st.subheader("📋 Liabilities")
    selected_liabilities = st.multiselect(
        "Select liabilities", list(LIABILITIES.keys()),
        default=rng.sample(list(LIABILITIES.keys()), 2) if seed else list(LIABILITIES.keys())[:2],
    )
    liability_values = {}
    for li in selected_liabilities:
        liability_values[li] = st.number_input(
            f"{li} (AUD)", min_value=0.0, value=rand_amount(5_000, 800_000), step=1000.0,
            format="%.2f", key=f"liability_{li}",
        )

# ── Build payload ─────────────────────────────────────────────────────────────

total_assets      = sum(asset_values.values())
total_creditors   = sum(creditor_values.values())
total_liabilities = sum(liability_values.values())
net_position      = total_assets - total_liabilities - total_creditors

payload = {
    "event_id":   str(uuid.uuid4()),
    "event_type": "financial_snapshot",
    "timestamp":  datetime.utcnow().isoformat() + "Z",
    "entity": {
        "name":        entity_name,
        "abn":         entity_abn,
        "report_date": str(report_date),
    },
    "assets": [
        {"name": n, "value": asset_values[n], "currency": "AUD", **ASSETS[n]}
        for n in selected_assets
    ],
    "creditors": [
        {"name": n, "amount_owing": creditor_values[n], "currency": "AUD", **CREDITORS[n]}
        for n in selected_creditors
    ],
    "liabilities": [
        {"name": n, "amount": liability_values[n], "currency": "AUD", **LIABILITIES[n]}
        for n in selected_liabilities
    ],
    "summary": {
        "total_assets":      round(total_assets, 2),
        "total_creditors":   round(total_creditors, 2),
        "total_liabilities": round(total_liabilities, 2),
        "net_position":      round(net_position, 2),
        "currency":          "AUD",
    },
}

# ── Summary metrics ───────────────────────────────────────────────────────────

st.divider()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Assets",      f"${total_assets:,.0f}")
m2.metric("Total Creditors",   f"${total_creditors:,.0f}")
m3.metric("Total Liabilities", f"${total_liabilities:,.0f}")
m4.metric("Net Position",      f"${net_position:,.0f}")

# ── Payload preview ───────────────────────────────────────────────────────────

st.divider()
st.subheader("📦 Payload Preview")
st.json(payload)

# ── Send ──────────────────────────────────────────────────────────────────────

st.divider()
btn_col, status_col = st.columns([1, 3])

with btn_col:
    send = st.button("🚀 Send to Webhook", type="primary", use_container_width=True)

with status_col:
    if send:
        target = webhook_url.strip()
        if not target:
            st.error("⚠️ No webhook URL set. Click 'Generate new webhook.site URL' in the sidebar.")
        else:
            try:
                with st.spinner(f"Sending to {target} …"):
                    resp = requests.post(
                        target,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=10,
                    )
                if resp.status_code < 300:
                    st.success(
                        f"✅ Delivered — HTTP {resp.status_code} "
                        f"({resp.elapsed.total_seconds():.2f}s). "
                        f"Switch to your listener tab to see it live."
                    )
                else:
                    st.error(f"❌ HTTP {resp.status_code}: {resp.text[:400]}")
            except requests.exceptions.Timeout:
                st.error("⏱️ Timed out after 10s.")
            except requests.exceptions.ConnectionError as e:
                st.error(f"🔌 Connection error: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
