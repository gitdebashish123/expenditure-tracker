import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime
from collections import defaultdict

# ── Config ────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"
CURRENT_MONTH = date.today().strftime("%Y-%m")
MONTH_DISPLAY = date.today().strftime("%B %Y")

CATEGORY_ICONS = {
    "Food": "🍔", "Travel": "🚗", "Groceries": "🛒", "Shopping": "🛍️",
    "Medical": "💊", "Entertainment": "🎬", "Gifts": "🎁", "Course": "📚",
    "Miscellaneous": "📦", "Housing": "🏠", "Savings": "💰", "EMI": "💳",
    "Investments": "📈", "Utilities": "⚡", "Insurance": "🛡️", "Household": "🏡"
}

FIXED_CATEGORIES = ["Housing", "EMI", "Savings", "Investments", "Insurance", "Utilities", "Household"]

st.set_page_config(
    page_title="SpendSense",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Styles ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.main { background: #0a0a0f; }
.block-container { padding: 1.5rem 1rem; max-width: 900px; margin: auto; }
h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

.app-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 20px; padding: 24px 28px; margin-bottom: 24px;
    border: 1px solid rgba(255,255,255,0.07); position: relative; overflow: hidden;
}
.app-header::before {
    content: ''; position: absolute; top: -50%; right: -10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.app-title { font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 800;
    color: white; margin: 0; letter-spacing: -1px; }
.app-subtitle { color: rgba(255,255,255,0.5); font-size: 0.85rem; margin-top: 4px; }

.balance-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 24px; }
.bal-card { background: #111118; border: 1px solid rgba(255,255,255,0.07); border-radius: 16px; padding: 18px; }
.bal-card.main { background: linear-gradient(135deg, #6366f1, #8b5cf6); border: none; }
.bal-label { color: rgba(255,255,255,0.5); font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 1px; margin-bottom: 6px; }
.bal-amount { font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 700; color: white; }

.warn-danger {
    background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.3);
    border-left: 4px solid #ef4444; border-radius: 10px; padding: 12px 16px;
    margin: 8px 0; color: #fca5a5; font-size: 0.88rem;
}
.warn-warning {
    background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.25);
    border-left: 4px solid #f59e0b; border-radius: 10px; padding: 12px 16px;
    margin: 8px 0; color: #fcd34d; font-size: 0.88rem;
}

/* Fixed checklist */
.fixed-group-header {
    font-family: 'Syne', sans-serif; font-size: 0.78rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1.5px;
    color: rgba(255,255,255,0.35); margin: 18px 0 8px;
}
.fixed-progress-bar {
    background: rgba(255,255,255,0.06); border-radius: 99px; height: 6px; margin-bottom: 18px;
}
.fixed-progress-fill {
    height: 6px; border-radius: 99px; background: linear-gradient(90deg, #34d399, #6366f1);
    transition: width 0.4s ease;
}
.fixed-row {
    display: flex; align-items: center; padding: 10px 12px; border-radius: 12px;
    margin-bottom: 6px; background: #111118; border: 1px solid rgba(255,255,255,0.05);
    gap: 12px; transition: background 0.2s;
}
.fixed-row.paid { background: rgba(52,211,153,0.07); border-color: rgba(52,211,153,0.15); }
.fixed-name { flex: 1; color: white; font-size: 0.88rem; font-weight: 500; }
.fixed-name.paid { color: rgba(255,255,255,0.4); text-decoration: line-through; }
.fixed-amount { color: rgba(255,255,255,0.5); font-size: 0.85rem; font-family: 'Syne', sans-serif; }
.fixed-amount.paid { color: #34d399; }

.cat-row { display: flex; align-items: center; margin-bottom: 14px; gap: 12px; }
.cat-name { color: white; font-size: 0.85rem; width: 120px; flex-shrink: 0; }
.cat-bar-bg { flex: 1; background: rgba(255,255,255,0.06); border-radius: 99px; height: 8px; }
.cat-bar-fill { height: 8px; border-radius: 99px; }
.cat-amounts { color: rgba(255,255,255,0.5); font-size: 0.78rem; width: 110px; text-align: right; flex-shrink: 0; }

.exp-row {
    display: flex; align-items: center; padding: 12px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05); gap: 12px;
}
.exp-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center;
    justify-content: center; background: rgba(255,255,255,0.06); font-size: 1.1rem; flex-shrink: 0; }
.exp-vendor { color: white; font-size: 0.88rem; font-weight: 500; }
.exp-cat { color: rgba(255,255,255,0.4); font-size: 0.75rem; }
.exp-amount { margin-left: auto; font-family: 'Syne', sans-serif;
    font-size: 0.95rem; font-weight: 600; color: #f87171; flex-shrink: 0; }

.section-title {
    font-family: 'Syne', sans-serif; color: rgba(255,255,255,0.9); font-size: 0.95rem;
    font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin: 24px 0 14px;
}
.toast-success {
    background: rgba(52,211,153,0.12); border: 1px solid rgba(52,211,153,0.3);
    border-radius: 10px; padding: 12px 16px; color: #6ee7b7; font-size: 0.88rem; margin: 8px 0;
}

/* Streamlit overrides */
.stTextInput > div > div > input {
    background: #1a1a28 !important; border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important; color: white !important;
    font-size: 1rem !important; padding: 14px 16px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important; box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 600 !important;
    padding: 12px 24px !important; width: 100% !important;
    font-size: 0.9rem !important; letter-spacing: 0.5px !important;
}
.stButton > button:hover { opacity: 0.9 !important; }
.stSelectbox > div > div { background: #1a1a28 !important; border-radius: 12px !important; }
.stNumberInput > div > div > input { background: #1a1a28 !important; color: white !important; }
.stTabs [data-baseweb="tab-list"] { background: #111118; border-radius: 12px; padding: 4px; }
.stTabs [data-baseweb="tab"] { color: rgba(255,255,255,0.5) !important; border-radius: 8px; }
.stTabs [aria-selected="true"] { background: #6366f1 !important; color: white !important; }
div[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif !important; }
/* Checkbox styling */
.stCheckbox > label { color: white !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────
def api(method, path, **kwargs):
    try:
        r = requests.request(method, f"{API_BASE}{path}", timeout=30, **kwargs)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Backend not running. Start with: `uv run uvicorn backend.main:app --reload`")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None

def bar_color(pct):
    if pct >= 100: return "#ef4444"
    if pct >= 80: return "#f59e0b"
    if pct >= 60: return "#6366f1"
    return "#34d399"


# ── Header ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-header">
    <div class="app-title">💸 SpendSense</div>
    <div class="app-subtitle">Personal Expenditure Tracker · {MONTH_DISPLAY}</div>
</div>
""", unsafe_allow_html=True)

# ── Top Summary ─────────────────────────────────────────────────────────────
summary = api("GET", "/summary/current/now")

if summary:
    bal = summary["balance"]
    rem = bal["remaining"]
    fp = summary.get("fixed_progress", {})
    paid_count = fp.get("paid", 0)
    total_count = fp.get("total", 0)
    pct_done = int(paid_count / total_count * 100) if total_count else 0

    st.markdown(f"""
    <div class="balance-grid">
        <div class="bal-card main">
            <div class="bal-label">Remaining Balance</div>
            <div class="bal-amount">₹{rem:,.0f}</div>
        </div>
        <div class="bal-card">
            <div class="bal-label">Monthly Income</div>
            <div class="bal-amount">₹{bal['total_income']:,.0f}</div>
        </div>
        <div class="bal-card">
            <div class="bal-label">Fixed Paid</div>
            <div class="bal-amount">{paid_count} / {total_count}</div>
        </div>
    </div>
    <div class="fixed-progress-bar">
        <div class="fixed-progress-fill" style="width:{pct_done}%"></div>
    </div>
    """, unsafe_allow_html=True)

    if summary.get("warnings"):
        for w in summary["warnings"]:
            css = "warn-danger" if w["level"] == "danger" else "warn-warning"
            st.markdown(f'<div class="{css}">{w["message"]}</div>', unsafe_allow_html=True)


# ── Main Tabs ───────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡ Quick Add", "📌 Fixed", "📊 Dashboard", "📋 Expenses", "⚙️ Settings"])


# ═══════════════════════════════════════════════════════
# TAB 1: QUICK ADD (variable expenses)
# ═══════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-title">Log Expenses</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="color:rgba(255,255,255,0.4); font-size:0.82rem; margin-bottom:14px;">
    Type like: <code style="background:#1a1a28; padding:2px 6px; border-radius:4px; color:#a5b4fc;">zomato 500, ola 200, bigbasket 1200</code>
    </div>
    """, unsafe_allow_html=True)

    with st.form("quick_add", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            expense_text = st.text_input("Expense Input",
                placeholder="e.g. zomato 500, ola 200, bigbasket 1200",
                label_visibility="collapsed")
        with col2:
            expense_date_val = st.date_input("Date", value=date.today(), label_visibility="collapsed")
        submitted = st.form_submit_button("➕ Add Expenses")

    if submitted and expense_text.strip():
        with st.spinner("🤖 Parsing with AI..."):
            result = api("POST", "/expenses/parse", json={
                "text": expense_text,
                "date_override": expense_date_val.isoformat()
            })
        if result:
            saved = result.get("saved", [])
            st.markdown(f'<div class="toast-success">✅ Saved {len(saved)} expense(s)</div>',
                       unsafe_allow_html=True)
            cols = st.columns(min(len(saved), 3))
            for i, item in enumerate(saved):
                icon = CATEGORY_ICONS.get(item["category"], "📦")
                with cols[i % len(cols)]:
                    st.markdown(f"""
                    <div style="background:#1a1a28; border-radius:12px; padding:14px; text-align:center; margin-top:8px;">
                        <div style="font-size:1.5rem">{icon}</div>
                        <div style="color:white; font-weight:600; font-size:0.9rem; margin-top:4px">{item['vendor']}</div>
                        <div style="color:#f87171; font-family:'Syne',sans-serif; font-size:1.1rem; font-weight:700">₹{item['amount']:,.0f}</div>
                        <div style="color:rgba(255,255,255,0.4); font-size:0.75rem">{item['category']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            for w in result.get("warnings", []):
                css = "warn-danger" if w["level"] == "danger" else "warn-warning"
                st.markdown(f'<div class="{css}">{w["message"]}</div>', unsafe_allow_html=True)
            if result.get("balance"):
                b = result["balance"]
                color = "#34d399" if b["remaining"] >= 0 else "#f87171"
                st.markdown(f"""
                <div style="background:#111118; border-radius:12px; padding:16px; margin-top:14px;
                    text-align:center; border:1px solid rgba(255,255,255,0.07);">
                    <div style="color:rgba(255,255,255,0.5); font-size:0.8rem;">Updated Remaining Balance</div>
                    <div style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:{color};">
                        ₹{b['remaining']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            st.rerun()

    st.markdown('<div class="section-title">Today\'s Entries</div>', unsafe_allow_html=True)
    today_expenses = api("GET", f"/expenses/{CURRENT_MONTH}")
    if today_expenses:
        today_only = [e for e in today_expenses
                     if e["date"] == date.today().isoformat() and not e["is_fixed"]]
        if today_only:
            for e in today_only[:10]:
                icon = CATEGORY_ICONS.get(e["category"], "📦")
                st.markdown(f"""
                <div class="exp-row">
                    <div class="exp-icon">{icon}</div>
                    <div><div class="exp-vendor">{e['vendor']}</div>
                    <div class="exp-cat">{e['category']}</div></div>
                    <div class="exp-amount">-₹{e['amount']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:rgba(255,255,255,0.3); font-size:0.85rem; padding:20px 0; text-align:center;">No expenses logged today</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 2: FIXED EXPENSES CHECKLIST
# ═══════════════════════════════════════════════════════
with tab2:
    # Month selector
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div class="section-title">Fixed Expenses</div>', unsafe_allow_html=True)
    with col2:
        months_list = api("GET", "/months") or [CURRENT_MONTH]
        if CURRENT_MONTH not in months_list:
            months_list = [CURRENT_MONTH] + months_list
        sel_month = st.selectbox("Month", months_list,
            format_func=lambda m: datetime.strptime(m, "%Y-%m").strftime("%B %Y"),
            label_visibility="collapsed", key="fixed_month")

    fixed_exps = api("GET", f"/fixed/{sel_month}") or []

    if fixed_exps:
        # Group by category
        by_cat = defaultdict(list)
        for e in fixed_exps:
            by_cat[e["category"]].append(e)

        paid_total = sum(e["amount"] for e in fixed_exps if e["paid"])
        unpaid_total = sum(e["amount"] for e in fixed_exps if not e["paid"])
        total_fixed = sum(e["amount"] for e in fixed_exps)
        pct = int(paid_total / total_fixed * 100) if total_fixed else 0

        # Progress summary
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span style="color:rgba(255,255,255,0.5); font-size:0.82rem;">{sum(1 for e in fixed_exps if e['paid'])} of {len(fixed_exps)} paid · ₹{paid_total:,.0f} done</span>
            <span style="color:#f87171; font-size:0.82rem;">₹{unpaid_total:,.0f} pending</span>
        </div>
        <div class="fixed-progress-bar">
            <div class="fixed-progress-fill" style="width:{pct}%"></div>
        </div>
        """, unsafe_allow_html=True)

        for category, items in sorted(by_cat.items()):
            icon = CATEGORY_ICONS.get(category, "📦")
            cat_total = sum(i["amount"] for i in items)
            st.markdown(f'<div class="fixed-group-header">{icon} {category} · ₹{cat_total:,.0f}</div>',
                       unsafe_allow_html=True)

            for item in items:
                paid = item["paid"]
                paid_class = "paid" if paid else ""
                tick = "✅" if paid else "⬜"

                col1, col2, col3 = st.columns([0.08, 0.7, 0.22])
                with col1:
                    if st.button(tick, key=f"tick_{item['id']}", help="Toggle paid"):
                        api("PATCH", f"/fixed/{item['id']}/toggle")
                        st.rerun()
                with col2:
                    st.markdown(f"""
                    <div style="padding:8px 0; color:{'rgba(255,255,255,0.35)' if paid else 'white'};
                        font-size:0.88rem; {'text-decoration:line-through;' if paid else ''}">
                        {item['vendor']}
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    amt_color = "#34d399" if paid else "rgba(255,255,255,0.5)"
                    st.markdown(f"""
                    <div style="padding:8px 0; text-align:right; font-family:'Syne',sans-serif;
                        font-size:0.88rem; color:{amt_color};">
                        ₹{item['amount']:,.0f}
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:rgba(255,255,255,0.3); text-align:center; padding:40px 0;">No fixed expenses for this month</div>',
                   unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 3: DASHBOARD
# ═══════════════════════════════════════════════════════
with tab3:
    if summary:
        bal = summary["balance"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Fixed Expenses", f"₹{bal['fixed_total']:,.0f}")
        with col2:
            st.metric("Variable Expenses", f"₹{bal['variable_total']:,.0f}")
        with col3:
            st.metric("Savings Rate", f"{bal.get('savings_rate', 0):.1f}%")

        st.markdown('<div class="section-title">Budget Tracker</div>', unsafe_allow_html=True)
        cats = [c for c in summary.get("categories", []) if c["limit"] > 0]
        for cat in sorted(cats, key=lambda x: x["pct"], reverse=True):
            icon = CATEGORY_ICONS.get(cat["category"], "📦")
            color = bar_color(cat["pct"])
            pct_display = min(cat["pct"], 100)
            st.markdown(f"""
            <div class="cat-row">
                <div class="cat-name">{icon} {cat['category']}</div>
                <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:{pct_display}%; background:{color};"></div></div>
                <div class="cat-amounts">₹{cat['spent']:,.0f} / ₹{cat['limit']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">Spending by Category</div>', unsafe_allow_html=True)
        all_exp = api("GET", f"/expenses/{CURRENT_MONTH}")
        if all_exp:
            df = pd.DataFrame(all_exp)
            df = df[df["is_fixed"] == False]
            if not df.empty:
                cat_totals = df.groupby("category")["amount"].sum().sort_values(ascending=False)
                st.bar_chart(pd.DataFrame({"Amount (₹)": cat_totals}))


# ═══════════════════════════════════════════════════════
# TAB 4: EXPENSES LIST
# ═══════════════════════════════════════════════════════
with tab4:
    months_data = api("GET", "/months") or [CURRENT_MONTH]
    if CURRENT_MONTH not in months_data:
        months_data = [CURRENT_MONTH] + months_data

    col1, col2 = st.columns([2, 1])
    with col1:
        selected_month = st.selectbox("Month", months_data,
            format_func=lambda m: datetime.strptime(m, "%Y-%m").strftime("%B %Y"),
            label_visibility="collapsed")
    with col2:
        show_fixed = st.checkbox("Show Fixed", value=False)

    expenses = api("GET", f"/expenses/{selected_month}")
    if expenses:
        df = pd.DataFrame(expenses)
        if not show_fixed:
            df = df[df["is_fixed"] == False]
        if not df.empty:
            total = df["amount"].sum()
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:12px 0;
                border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:8px;">
                <span style="color:rgba(255,255,255,0.5); font-size:0.82rem;">{len(df)} transactions</span>
                <span style="font-family:'Syne',sans-serif; color:#f87171; font-weight:700;">Total: ₹{total:,.0f}</span>
            </div>
            """, unsafe_allow_html=True)
            df["date"] = pd.to_datetime(df["date"])
            for exp_date, group in df.sort_values("date", ascending=False).groupby("date", sort=False):
                date_str = exp_date.strftime("%d %b %Y")
                day_total = group["amount"].sum()
                st.markdown(f"""
                <div style="color:rgba(255,255,255,0.4); font-size:0.75rem; margin:14px 0 6px;
                    display:flex; justify-content:space-between;">
                    <span>{date_str}</span><span>₹{day_total:,.0f}</span>
                </div>
                """, unsafe_allow_html=True)
                for _, row in group.iterrows():
                    icon = CATEGORY_ICONS.get(row["category"], "📦")
                    note_html = f'<span style="color:rgba(255,255,255,0.3); font-size:0.75rem;"> · {row["note"]}</span>' \
                        if pd.notna(row.get("note")) and row.get("note") else ""
                    fixed_badge = ' <span style="color:rgba(255,255,255,0.2); font-size:0.75rem;">· Fixed</span>' \
                        if row["is_fixed"] else ""
                    st.markdown(f"""
                    <div class="exp-row">
                        <div class="exp-icon">{icon}</div>
                        <div style="flex:1">
                            <div class="exp-vendor">{row['vendor']}{note_html}</div>
                            <div class="exp-cat">{row['category']}{fixed_badge}</div>
                        </div>
                        <div class="exp-amount">-₹{row['amount']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:rgba(255,255,255,0.3); text-align:center; padding:40px 0;">No expenses found</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 5: SETTINGS
# ═══════════════════════════════════════════════════════
with tab5:

    # ── Manage Fixed Expense Templates ──────────────────
    st.markdown('<div class="section-title">Fixed Expense Templates</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:rgba(255,255,255,0.4); font-size:0.82rem; margin-bottom:16px;">Auto-seeded every month. Edit inline, then Save. Delete removes from future months only.</div>', unsafe_allow_html=True)

    templates = api("GET", "/fixed-templates") or []
    active_templates = [t for t in templates if t["is_active"]]

    if active_templates:
        # Column headers
        h1, h2, h3, h4, h5 = st.columns([0.28, 0.22, 0.18, 0.16, 0.16])
        with h1: st.markdown('<div style="color:rgba(255,255,255,0.3); font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; padding-bottom:6px;">Name</div>', unsafe_allow_html=True)
        with h2: st.markdown('<div style="color:rgba(255,255,255,0.3); font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; padding-bottom:6px;">Category</div>', unsafe_allow_html=True)
        with h3: st.markdown('<div style="color:rgba(255,255,255,0.3); font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; padding-bottom:6px;">Amount (₹)</div>', unsafe_allow_html=True)
        with h4: st.markdown('<div style="color:rgba(255,255,255,0.3); font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; padding-bottom:6px;">Save</div>', unsafe_allow_html=True)
        with h5: st.markdown('<div style="color:rgba(255,255,255,0.3); font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; padding-bottom:6px;">Delete</div>', unsafe_allow_html=True)

        st.markdown('<div style="border-top:1px solid rgba(255,255,255,0.07); margin-bottom:8px;"></div>', unsafe_allow_html=True)

        # Group by category with a visible divider label
        tmpl_by_cat = defaultdict(list)
        for t in active_templates:
            tmpl_by_cat[t["category"]].append(t)

        for cat, items in sorted(tmpl_by_cat.items()):
            icon = CATEGORY_ICONS.get(cat, "📦")
            st.markdown(f'<div class="fixed-group-header">{icon} {cat}</div>', unsafe_allow_html=True)

            for t in items:
                c1, c2, c3, c4, c5 = st.columns([0.28, 0.22, 0.18, 0.16, 0.16])
                with c1:
                    new_name = st.text_input("Name", value=t["name"],
                        key=f"tname_{t['id']}", label_visibility="collapsed")
                with c2:
                    new_cat = st.selectbox("Category", FIXED_CATEGORIES,
                        index=FIXED_CATEGORIES.index(t["category"]) if t["category"] in FIXED_CATEGORIES else 0,
                        key=f"tcat_{t['id']}", label_visibility="collapsed")
                with c3:
                    new_amt = st.number_input("Amount", value=int(t["amount"]),
                        step=100, key=f"tamt_{t['id']}", label_visibility="collapsed")
                with c4:
                    if st.button("💾 Save", key=f"tsave_{t['id']}"):
                        api("PUT", f"/fixed-templates/{t['id']}",
                            json={"name": new_name, "category": new_cat, "amount": new_amt})
                        st.success(f"✅ Saved {new_name}")
                        st.rerun()
                with c5:
                    if st.button("🗑️ Delete", key=f"tdel_{t['id']}"):
                        api("DELETE", f"/fixed-templates/{t['id']}")
                        st.rerun()

        # Total
        total_fixed_tmpl = sum(t["amount"] for t in active_templates)
        st.markdown(f"""
        <div style="display:flex; justify-content:flex-end; padding:10px 0;
            border-top:1px solid rgba(255,255,255,0.07); margin-top:8px;">
            <span style="color:rgba(255,255,255,0.4); font-size:0.82rem;">
                {len(active_templates)} items &nbsp;·&nbsp;
                <span style="color:white; font-family:'Syne',sans-serif; font-weight:700;">
                Total ₹{total_fixed_tmpl:,.0f}/month</span>
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Add new fixed template
    st.markdown('<div style="margin-top:16px; padding:16px; background:#111118; border-radius:14px; border:1px solid rgba(255,255,255,0.07);">', unsafe_allow_html=True)
    st.markdown('<div style="color:rgba(255,255,255,0.7); font-size:0.85rem; font-weight:600; margin-bottom:12px;">➕ Add New Fixed Expense</div>', unsafe_allow_html=True)
    with st.form("add_template", clear_on_submit=True):
        col1, col2, col3 = st.columns([0.38, 0.27, 0.35])
        with col1:
            new_tname = st.text_input("Name", placeholder="e.g. Groww MF4")
        with col2:
            new_tamt = st.number_input("Amount (₹)", min_value=0, step=100)
        with col3:
            new_tcat = st.selectbox("Category", FIXED_CATEGORIES)
        if st.form_submit_button("➕ Add Fixed Expense"):
            if new_tname and new_tamt > 0:
                api("POST", "/fixed-templates",
                    json={"name": new_tname, "category": new_tcat, "amount": new_tamt})
                st.success(f"✅ Added {new_tname} (₹{new_tamt:,.0f}) to {new_tcat}")
                st.rerun()
            else:
                st.warning("Please enter a name and amount greater than 0.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Budget Limits ────────────────────────────────────
    st.markdown('<div class="section-title">Variable Budget Limits</div>', unsafe_allow_html=True)
    budgets = api("GET", "/budgets") or []
    if budgets:
        with st.form("update_budgets"):
            updated = {}
            cols = st.columns(2)
            for i, bl in enumerate(budgets):
                with cols[i % 2]:
                    icon = CATEGORY_ICONS.get(bl["category"], "📦")
                    new_val = st.number_input(f"{icon} {bl['category']}",
                        value=int(bl["limit_amount"]), step=500, key=f"budget_{bl['category']}")
                    updated[bl["category"]] = new_val
            if st.form_submit_button("💾 Save Budget Limits"):
                for cat, limit in updated.items():
                    api("PUT", "/budget", json={"category": cat, "limit_amount": limit})
                st.success("✅ Budget limits updated!")
                st.rerun()

    # ── Add Income ──────────────────────────────────────
    st.markdown('<div class="section-title">Monthly Income</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:rgba(255,255,255,0.4); font-size:0.82rem; margin-bottom:14px;">One entry per month — saving again updates the existing amount on the dashboard.</div>', unsafe_allow_html=True)

    current_income = api("GET", f"/income/{CURRENT_MONTH}") or {}
    saved_source = current_income.get("source", "Infosys Salary")
    saved_amount = int(current_income.get("amount", 146709))
    saved_note = current_income.get("note") or ""

    with st.form("add_income"):
        col1, col2 = st.columns(2)
        with col1:
            income_source = st.text_input("Source", value=saved_source)
        with col2:
            income_amount = st.number_input("Amount (₹)", value=saved_amount, step=1000)
        income_note = st.text_input("Note (optional)", value=saved_note, placeholder="May salary credit")
        if st.form_submit_button("💾 Save Income"):
            result = api("POST", "/income", json={"source": income_source,
                "amount": income_amount, "note": income_note})
            if result:
                st.success(f"✅ Income updated to ₹{income_amount:,.0f} for {MONTH_DISPLAY}")
                st.rerun()
