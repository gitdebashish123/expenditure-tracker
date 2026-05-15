import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime
import calendar

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

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.main { background: #0a0a0f; }
.block-container { padding: 1.5rem 1rem; max-width: 900px; margin: auto; }

h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

/* Header */
.app-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 20px;
    padding: 24px 28px;
    margin-bottom: 24px;
    border: 1px solid rgba(255,255,255,0.07);
    position: relative;
    overflow: hidden;
}
.app-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.app-title { font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 800;
    color: white; margin: 0; letter-spacing: -1px; }
.app-subtitle { color: rgba(255,255,255,0.5); font-size: 0.85rem; margin-top: 4px; }

/* Balance cards */
.balance-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 24px; }
.bal-card {
    background: #111118;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 18px;
}
.bal-card.main { background: linear-gradient(135deg, #6366f1, #8b5cf6); border: none; }
.bal-label { color: rgba(255,255,255,0.5); font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 1px; margin-bottom: 6px; }
.bal-amount { font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 700;
    color: white; }
.bal-amount.positive { color: #34d399; }
.bal-amount.negative { color: #f87171; }

/* Input box */
.input-zone {
    background: #111118;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 20px;
}

/* Warning banners */
.warn-danger {
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.3);
    border-left: 4px solid #ef4444;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0;
    color: #fca5a5;
    font-size: 0.88rem;
}
.warn-warning {
    background: rgba(245,158,11,0.1);
    border: 1px solid rgba(245,158,11,0.25);
    border-left: 4px solid #f59e0b;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0;
    color: #fcd34d;
    font-size: 0.88rem;
}

/* Category progress bars */
.cat-row {
    display: flex;
    align-items: center;
    margin-bottom: 14px;
    gap: 12px;
}
.cat-name { color: white; font-size: 0.85rem; width: 120px; flex-shrink: 0; }
.cat-bar-bg { flex: 1; background: rgba(255,255,255,0.06); border-radius: 99px; height: 8px; }
.cat-bar-fill { height: 8px; border-radius: 99px; transition: width 0.5s ease; }
.cat-amounts { color: rgba(255,255,255,0.5); font-size: 0.78rem; width: 100px;
    text-align: right; flex-shrink: 0; }

/* Expense rows */
.exp-row {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    gap: 12px;
}
.exp-icon { width: 36px; height: 36px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    background: rgba(255,255,255,0.06); font-size: 1.1rem; flex-shrink: 0; }
.exp-vendor { color: white; font-size: 0.88rem; font-weight: 500; }
.exp-cat { color: rgba(255,255,255,0.4); font-size: 0.75rem; }
.exp-amount { margin-left: auto; font-family: 'Syne', sans-serif;
    font-size: 0.95rem; font-weight: 600; color: #f87171; flex-shrink: 0; }
.exp-fixed { color: rgba(255,255,255,0.25); font-size: 0.78rem; }

/* Section headers */
.section-title {
    font-family: 'Syne', sans-serif;
    color: rgba(255,255,255,0.9);
    font-size: 0.95rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 24px 0 14px;
}

/* Success toast */
.toast-success {
    background: rgba(52,211,153,0.12);
    border: 1px solid rgba(52,211,153,0.3);
    border-radius: 10px;
    padding: 12px 16px;
    color: #6ee7b7;
    font-size: 0.88rem;
    margin: 8px 0;
}

/* Streamlit overrides */
.stTextInput > div > div > input {
    background: #1a1a28 !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: white !important;
    font-size: 1rem !important;
    padding: 14px 16px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    width: 100% !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.5px !important;
}
.stButton > button:hover { opacity: 0.9 !important; transform: translateY(-1px) !important; }
.stSelectbox > div > div { background: #1a1a28 !important; border-radius: 12px !important; }
.stNumberInput > div > div > input { background: #1a1a28 !important; color: white !important; }
.stTabs [data-baseweb="tab-list"] { background: #111118; border-radius: 12px; padding: 4px; }
.stTabs [data-baseweb="tab"] { color: rgba(255,255,255,0.5) !important; border-radius: 8px; }
.stTabs [aria-selected="true"] { background: #6366f1 !important; color: white !important; }
div[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────

def api(method, path, **kwargs):
    try:
        r = requests.request(method, f"{API_BASE}{path}", timeout=30, **kwargs)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Backend not running. Start it with: `uvicorn backend.main:app --reload`")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def fmt_inr(amount):
    if amount >= 100000:
        return f"₹{amount/100000:.1f}L"
    elif amount >= 1000:
        return f"₹{amount/1000:.1f}K"
    return f"₹{amount:,.0f}"


def bar_color(pct):
    if pct >= 100: return "#ef4444"
    if pct >= 80: return "#f59e0b"
    if pct >= 60: return "#6366f1"
    return "#34d399"


# ── Header ────────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="app-header">
    <div class="app-title">💸 SpendSense</div>
    <div class="app-subtitle">Personal Expenditure Tracker · {MONTH_DISPLAY}</div>
</div>
""", unsafe_allow_html=True)

# ── Load Summary ──────────────────────────────────────────────────────────

summary = api("GET", "/summary/current/now")

if summary:
    bal = summary["balance"]
    rem = bal["remaining"]
    remaining_color = "positive" if rem >= 0 else "negative"

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
            <div class="bal-label">Total Spent</div>
            <div class="bal-amount">₹{bal['total_spent']:,.0f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Warnings
    if summary.get("warnings"):
        for w in summary["warnings"]:
            css = "warn-danger" if w["level"] == "danger" else "warn-warning"
            st.markdown(f'<div class="{css}">{w["message"]}</div>', unsafe_allow_html=True)

# ── Main Tabs ─────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs(["⚡ Quick Add", "📊 Dashboard", "📋 Expenses", "⚙️ Settings"])


# ═══════════════════════════════════════════════════════
# TAB 1: QUICK ADD
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
            expense_text = st.text_input(
                "Expense Input",
                placeholder="e.g. zomato 500, ola 200, bigbasket 1200",
                label_visibility="collapsed"
            )
        with col2:
            expense_date = st.date_input("Date", value=date.today(), label_visibility="collapsed")

        submitted = st.form_submit_button("➕ Add Expenses")

    if submitted and expense_text.strip():
        with st.spinner("🤖 Parsing with AI..."):
            result = api("POST", "/expenses/parse", json={
                "text": expense_text,
                "date_override": expense_date.isoformat()
            })

        if result:
            saved = result.get("saved", [])
            st.markdown(f'<div class="toast-success">✅ Saved {len(saved)} expense(s)</div>',
                       unsafe_allow_html=True)

            # Show parsed items
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

            # Inline warnings
            for w in result.get("warnings", []):
                css = "warn-danger" if w["level"] == "danger" else "warn-warning"
                st.markdown(f'<div class="{css}">{w["message"]}</div>', unsafe_allow_html=True)

            # Updated balance
            if result.get("balance"):
                b = result["balance"]
                rem = b["remaining"]
                color = "#34d399" if rem >= 0 else "#f87171"
                st.markdown(f"""
                <div style="background:#111118; border-radius:12px; padding:16px; margin-top:14px; text-align:center; border:1px solid rgba(255,255,255,0.07);">
                    <div style="color:rgba(255,255,255,0.5); font-size:0.8rem;">Updated Remaining Balance</div>
                    <div style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:{color};">₹{rem:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)

            st.rerun()

    # Recent quick entries
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
                    <div>
                        <div class="exp-vendor">{e['vendor']}</div>
                        <div class="exp-cat">{e['category']}</div>
                    </div>
                    <div class="exp-amount">-₹{e['amount']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:rgba(255,255,255,0.3); font-size:0.85rem; padding:20px 0; text-align:center;">No expenses logged today</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 2: DASHBOARD
# ═══════════════════════════════════════════════════════
with tab2:
    if summary:
        bal = summary["balance"]

        # Spend breakdown
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Fixed Expenses", f"₹{bal['fixed_total']:,.0f}",
                     delta=None, delta_color="off")
        with col2:
            st.metric("Variable Expenses", f"₹{bal['variable_total']:,.0f}",
                     delta=None, delta_color="off")
        with col3:
            savings_rate = bal.get("savings_rate", 0)
            st.metric("Savings Rate", f"{savings_rate:.1f}%")

        # Category breakdown
        st.markdown('<div class="section-title">Budget Tracker</div>', unsafe_allow_html=True)

        cats = [c for c in summary.get("categories", []) if c["limit"] > 0]
        if cats:
            for cat in sorted(cats, key=lambda x: x["pct"], reverse=True):
                icon = CATEGORY_ICONS.get(cat["category"], "📦")
                color = bar_color(cat["pct"])
                pct_display = min(cat["pct"], 100)
                st.markdown(f"""
                <div class="cat-row">
                    <div class="cat-name">{icon} {cat['category']}</div>
                    <div class="cat-bar-bg">
                        <div class="cat-bar-fill" style="width:{pct_display}%; background:{color};"></div>
                    </div>
                    <div class="cat-amounts">₹{cat['spent']:,.0f} / ₹{cat['limit']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)

        # Monthly chart
        st.markdown('<div class="section-title">Spending by Category</div>', unsafe_allow_html=True)
        all_expenses = api("GET", f"/expenses/{CURRENT_MONTH}")
        if all_expenses:
            df = pd.DataFrame(all_expenses)
            df = df[df["is_fixed"] == False]
            if not df.empty:
                cat_totals = df.groupby("category")["amount"].sum().sort_values(ascending=False)
                chart_df = pd.DataFrame({"Amount (₹)": cat_totals})
                st.bar_chart(chart_df)


# ═══════════════════════════════════════════════════════
# TAB 3: EXPENSES LIST
# ═══════════════════════════════════════════════════════
with tab3:
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
            # Summary row
            total = df["amount"].sum()
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:8px;">
                <span style="color:rgba(255,255,255,0.5); font-size:0.82rem;">{len(df)} transactions</span>
                <span style="font-family:'Syne',sans-serif; color:#f87171; font-weight:700;">Total: ₹{total:,.0f}</span>
            </div>
            """, unsafe_allow_html=True)

            # Group by date
            df["date"] = pd.to_datetime(df["date"])
            for expense_date, group in df.sort_values("date", ascending=False).groupby("date", sort=False):
                date_str = expense_date.strftime("%d %b %Y")
                day_total = group["amount"].sum()
                st.markdown(f"""
                <div style="color:rgba(255,255,255,0.4); font-size:0.75rem; margin:14px 0 6px;
                    display:flex; justify-content:space-between;">
                    <span>{date_str}</span><span>₹{day_total:,.0f}</span>
                </div>
                """, unsafe_allow_html=True)

                for _, row in group.iterrows():
                    icon = CATEGORY_ICONS.get(row["category"], "📦")
                    fixed_badge = '<span class="exp-fixed"> · Fixed</span>' if row["is_fixed"] else ""
                    note_html = f'<span style="color:rgba(255,255,255,0.3); font-size:0.75rem;"> · {row["note"]}</span>' if pd.notna(row.get("note")) and row.get("note") else ""
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
# TAB 4: SETTINGS
# ═══════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-title">Budget Limits</div>', unsafe_allow_html=True)

    budgets = api("GET", "/budgets") or []
    if budgets:
        with st.form("update_budgets"):
            updated = {}
            cols = st.columns(2)
            for i, bl in enumerate(budgets):
                with cols[i % 2]:
                    icon = CATEGORY_ICONS.get(bl["category"], "📦")
                    new_val = st.number_input(
                        f"{icon} {bl['category']}",
                        value=int(bl["limit_amount"]),
                        step=500,
                        key=f"budget_{bl['category']}"
                    )
                    updated[bl["category"]] = new_val

            if st.form_submit_button("💾 Save Budget Limits"):
                for cat, limit in updated.items():
                    api("PUT", "/budget", json={"category": cat, "limit_amount": limit})
                st.success("✅ Budget limits updated!")
                st.rerun()

    st.markdown('<div class="section-title">Add Income</div>', unsafe_allow_html=True)
    with st.form("add_income"):
        col1, col2 = st.columns(2)
        with col1:
            income_source = st.text_input("Source", value="Infosys Salary")
        with col2:
            income_amount = st.number_input("Amount (₹)", value=146709, step=1000)
        income_note = st.text_input("Note (optional)", placeholder="April salary credit")
        if st.form_submit_button("➕ Add Income"):
            api("POST", "/income", json={
                "source": income_source,
                "amount": income_amount,
                "note": income_note
            })
            st.success(f"✅ Income of ₹{income_amount:,.0f} added!")
            st.rerun()

    st.markdown('<div class="section-title">Seed Fixed Expenses</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        seed_month = st.text_input("Month (YYYY-MM)", value=CURRENT_MONTH)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Seed Fixed for Month"):
            api("POST", f"/seed/{seed_month}")
            st.success(f"✅ Fixed expenses seeded for {seed_month}!")
            st.rerun()
