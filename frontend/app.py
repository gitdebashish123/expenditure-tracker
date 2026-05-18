import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime
from collections import defaultdict

# ── Config ────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"
CURRENT_MONTH = date.today().strftime("%Y-%m")

CATEGORY_ICONS = {
    "Food": "🍔", "Travel": "🚗", "Groceries": "🛒", "Shopping": "🛍️",
    "Medical": "💊", "Entertainment": "🎬", "Gifts": "🎁", "Course": "📚",
    "Miscellaneous": "📦", "Housing": "🏠", "Savings": "💰", "EMI": "💳",
    "Investments": "📈", "Utilities": "⚡", "Insurance": "🛡️", "Household": "🏡"
}
FIXED_CATEGORIES = ["Housing", "EMI", "Savings", "Investments", "Insurance", "Utilities", "Household"]

st.set_page_config(page_title="SpendSense", page_icon="💸", layout="wide",
                   initial_sidebar_state="collapsed")

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
    border-radius: 20px; padding: 20px 28px; margin-bottom: 20px;
    border: 1px solid rgba(255,255,255,0.07);
}
.app-title { font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 800;
    color: white; margin: 0; letter-spacing: -1px; }
.app-subtitle { color: rgba(255,255,255,0.4); font-size: 0.82rem; margin-top: 2px; }

.balance-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 16px; }
.bal-card { background: #111118; border: 1px solid rgba(255,255,255,0.07); border-radius: 16px; padding: 18px; }
.bal-card.main { background: linear-gradient(135deg, #6366f1, #8b5cf6); border: none; }
.bal-label { color: rgba(255,255,255,0.5); font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 1px; margin-bottom: 6px; }
.bal-amount { font-family: 'Syne', sans-serif; font-size: 1.35rem; font-weight: 700; color: white; }
.bal-sub { color: rgba(255,255,255,0.35); font-size: 0.72rem; margin-top: 4px; }

.month-badge {
    display: inline-block; background: rgba(99,102,241,0.2); border: 1px solid rgba(99,102,241,0.4);
    border-radius: 8px; padding: 3px 10px; font-size: 0.78rem; color: #a5b4fc;
    font-family: 'Syne', sans-serif; font-weight: 600;
}
.past-badge {
    display: inline-block; background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.3);
    border-radius: 8px; padding: 3px 10px; font-size: 0.78rem; color: #fcd34d;
    font-family: 'Syne', sans-serif; font-weight: 600;
}

.warn-danger { background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.3);
    border-left: 4px solid #ef4444; border-radius: 10px; padding: 12px 16px;
    margin: 8px 0; color: #fca5a5; font-size: 0.88rem; }
.warn-warning { background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.25);
    border-left: 4px solid #f59e0b; border-radius: 10px; padding: 12px 16px;
    margin: 8px 0; color: #fcd34d; font-size: 0.88rem; }

.fixed-group-header { font-family: 'Syne', sans-serif; font-size: 0.78rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1.5px; color: rgba(255,255,255,0.35); margin: 18px 0 8px; }
.fixed-progress-bar { background: rgba(255,255,255,0.06); border-radius: 99px; height: 6px; margin-bottom: 18px; }
.fixed-progress-fill { height: 6px; border-radius: 99px; background: linear-gradient(90deg, #34d399, #6366f1); }

.cat-row { display: flex; align-items: center; margin-bottom: 14px; gap: 12px; }
.cat-name { color: white; font-size: 0.85rem; width: 120px; flex-shrink: 0; }
.cat-bar-bg { flex: 1; background: rgba(255,255,255,0.06); border-radius: 99px; height: 8px; }
.cat-bar-fill { height: 8px; border-radius: 99px; }
.cat-amounts { color: rgba(255,255,255,0.5); font-size: 0.78rem; width: 110px; text-align: right; flex-shrink: 0; }

.exp-row { display: flex; align-items: center; padding: 12px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05); gap: 12px; }
.exp-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center;
    justify-content: center; background: rgba(255,255,255,0.06); font-size: 1.1rem; flex-shrink: 0; }
.exp-vendor { color: white; font-size: 0.88rem; font-weight: 500; }
.exp-cat { color: rgba(255,255,255,0.4); font-size: 0.75rem; }
.exp-amount { margin-left: auto; font-family: 'Syne', sans-serif;
    font-size: 0.95rem; font-weight: 600; color: #f87171; flex-shrink: 0; }

.section-title { font-family: 'Syne', sans-serif; color: rgba(255,255,255,0.9); font-size: 0.95rem;
    font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin: 24px 0 14px; }
.toast-success { background: rgba(52,211,153,0.12); border: 1px solid rgba(52,211,153,0.3);
    border-radius: 10px; padding: 12px 16px; color: #6ee7b7; font-size: 0.88rem; margin: 8px 0; }

.stTextInput > div > div > input {
    background: #1a1a28 !important; border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important; color: white !important; font-size: 1rem !important; padding: 14px 16px !important; }
.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important; box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important; }
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 600 !important;
    padding: 12px 24px !important; width: 100% !important; font-size: 0.9rem !important; }
.stButton > button:hover { opacity: 0.9 !important; }
.stSelectbox > div > div { background: #1a1a28 !important; border-radius: 12px !important; }
.stNumberInput > div > div > input { background: #1a1a28 !important; color: white !important; }
.stTabs [data-baseweb="tab-list"] { background: #111118; border-radius: 12px; padding: 4px; }
.stTabs [data-baseweb="tab"] { color: rgba(255,255,255,0.5) !important; border-radius: 8px; }
.stTabs [aria-selected="true"] { background: #6366f1 !important; color: white !important; }
div[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif !important; }
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

def fmt_month(m):
    return datetime.strptime(m, "%Y-%m").strftime("%B %Y")


# ── Global Month Selector (in header) ──────────────────────────────────────
all_months = api("GET", "/months") or []
if CURRENT_MONTH not in all_months:
    all_months = [CURRENT_MONTH] + all_months
all_months = sorted(set(all_months), reverse=True)

col_title, col_month = st.columns([3, 1])
with col_title:
    st.markdown("""
    <div class="app-header">
        <div class="app-title">💸 SpendSense</div>
        <div class="app-subtitle">Personal Expenditure Tracker</div>
    </div>
    """, unsafe_allow_html=True)
with col_month:
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    sel_month = st.selectbox(
        "Month",
        all_months,
        index=0,
        format_func=fmt_month,
        label_visibility="collapsed",
        key="global_month"
    )

is_current = sel_month == CURRENT_MONTH
month_label = fmt_month(sel_month)
badge_class = "month-badge" if is_current else "past-badge"
badge_text = f"{'📅 ' if is_current else '🕐 '}{month_label}"


# ── Summary for selected month ─────────────────────────────────────────────
summary = api("GET", f"/summary/{sel_month}")

if summary:
    bal = summary["balance"]
    rem = bal["remaining"]
    fp = summary.get("fixed_progress", {})
    paid_count = fp.get("paid", 0)
    total_count = fp.get("total", 0)
    pct_done = int(paid_count / total_count * 100) if total_count else 0
    income_display = f"₹{bal['total_income']:,.0f}" if bal['total_income'] > 0 else "Not set"
    rem_color = "#34d399" if rem >= 0 else "#f87171"

    st.markdown(f'<div style="margin-bottom:12px;"><span class="{badge_class}">{badge_text}</span></div>',
                unsafe_allow_html=True)

    st.markdown(f"""
    <div class="balance-grid">
        <div class="bal-card main">
            <div class="bal-label">Remaining Balance</div>
            <div class="bal-amount" style="color:{rem_color};">₹{rem:,.0f}</div>
            <div class="bal-sub">Income − paid fixed − variable</div>
        </div>
        <div class="bal-card">
            <div class="bal-label">Monthly Income</div>
            <div class="bal-amount">{income_display}</div>
            <div class="bal-sub">Variable budget: ₹{bal['total_income'] - bal.get('fixed_paid_total',0) - bal.get('fixed_unpaid_total',0):,.0f}</div>
        </div>
        <div class="bal-card">
            <div class="bal-label">Fixed Paid / Pending</div>
            <div class="bal-amount">{paid_count} / {total_count}</div>
            <div class="bal-sub">₹{bal.get('fixed_paid_total',0):,.0f} paid · ₹{bal.get('fixed_unpaid_total',0):,.0f} pending</div>
        </div>
    </div>
    <div class="fixed-progress-bar">
        <div class="fixed-progress-fill" style="width:{pct_done}%"></div>
    </div>
    """, unsafe_allow_html=True)

    if is_current and summary.get("warnings"):
        for w in summary["warnings"]:
            css = "warn-danger" if w["level"] == "danger" else "warn-warning"
            st.markdown(f'<div class="{css}">{w["message"]}</div>', unsafe_allow_html=True)


# ── Tabs ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡ Quick Add", "📌 Fixed", "📊 Dashboard", "📋 Expenses", "⚙️ Settings"])


# ═══════════════════════════════════════════════════════
# TAB 1: QUICK ADD — always operates on CURRENT month
# ═══════════════════════════════════════════════════════
with tab1:
    if not is_current:
        st.markdown(f"""
        <div style="background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.25);
            border-radius:12px; padding:14px 18px; color:#fcd34d; font-size:0.88rem; margin-bottom:16px;">
            ⚠️ You're viewing <b>{month_label}</b>. Quick Add always logs to the <b>current month</b>.
            Switch the month selector above to <b>{fmt_month(CURRENT_MONTH)}</b> if needed.
        </div>
        """, unsafe_allow_html=True)

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
                col_info, col_amt, col_del = st.columns([0.6, 0.25, 0.15])
                with col_info:
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; gap:10px; padding:8px 0;
                        border-bottom:1px solid rgba(255,255,255,0.05);">
                        <div class="exp-icon">{icon}</div>
                        <div>
                            <div class="exp-vendor">{e['vendor']}</div>
                            <div class="exp-cat">{e['category']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_amt:
                    st.markdown(f"""
                    <div style="padding:8px 0; text-align:right; font-family:'Syne',sans-serif;
                        font-size:0.95rem; font-weight:600; color:#f87171;
                        border-bottom:1px solid rgba(255,255,255,0.05);">
                        -₹{e['amount']:,.0f}
                    </div>
                    """, unsafe_allow_html=True)
                with col_del:
                    if st.button("🗑️", key=f"del_today_{e['id']}", help=f"Delete {e['vendor']}"):
                        result = api("DELETE", f"/expenses/{e['id']}")
                        if result:
                            st.toast(f"Deleted {e['vendor']} ₹{e['amount']:,.0f}", icon="🗑️")
                            st.rerun()
        else:
            st.markdown('<div style="color:rgba(255,255,255,0.3); font-size:0.85rem; padding:20px 0; text-align:center;">No expenses logged today</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 2: FIXED EXPENSES — follows global month selector
# ═══════════════════════════════════════════════════════
with tab2:
    st.markdown(f'<div class="section-title">Fixed Expenses · <span style="color:#6366f1">{month_label}</span></div>',
                unsafe_allow_html=True)

    fixed_exps = api("GET", f"/fixed/{sel_month}") or []

    if fixed_exps:
        by_cat = defaultdict(list)
        for e in fixed_exps:
            by_cat[e["category"]].append(e)

        paid_total = sum(e["amount"] for e in fixed_exps if e["paid"])
        unpaid_total = sum(e["amount"] for e in fixed_exps if not e["paid"])
        total_fixed = sum(e["amount"] for e in fixed_exps)
        pct = int(paid_total / total_fixed * 100) if total_fixed else 0

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
                tick = "✅" if paid else "⬜"
                c1, c2, c3 = st.columns([0.08, 0.7, 0.22])
                with c1:
                    if st.button(tick, key=f"tick_{item['id']}", help="Toggle paid"):
                        api("PATCH", f"/fixed/{item['id']}/toggle")
                        st.rerun()
                with c2:
                    st.markdown(f"""
                    <div style="padding:8px 0; color:{'rgba(255,255,255,0.35)' if paid else 'white'};
                        font-size:0.88rem; {'text-decoration:line-through;' if paid else ''}">
                        {item['vendor']}
                    </div>
                    """, unsafe_allow_html=True)
                with c3:
                    amt_color = "#34d399" if paid else "rgba(255,255,255,0.5)"
                    st.markdown(f"""
                    <div style="padding:8px 0; text-align:right; font-family:'Syne',sans-serif;
                        font-size:0.88rem; color:{amt_color};">₹{item['amount']:,.0f}</div>
                    """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:rgba(255,255,255,0.3); text-align:center; padding:40px 0;">No fixed expenses for this month</div>',
                   unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 3: DASHBOARD — follows global month selector
# ═══════════════════════════════════════════════════════
with tab3:
    st.markdown(f'<div class="section-title">Dashboard · <span style="color:#6366f1">{month_label}</span></div>',
                unsafe_allow_html=True)

    if summary:
        bal = summary["balance"]
        col1, col2, col3 = st.columns(3)
        with col1:
            paid_f = bal.get('fixed_paid_total', 0)
            unpaid_f = bal.get('fixed_unpaid_total', 0)
            st.metric("Fixed Paid", f"₹{paid_f:,.0f}",
                      delta=f"₹{unpaid_f:,.0f} pending", delta_color="inverse")
        with col2:
            st.metric("Variable Expenses", f"₹{bal['variable_total']:,.0f}")
        with col3:
            st.metric("Savings Rate", f"{bal.get('savings_rate', 0):.1f}%")

        # Budget tracker — only meaningful for current month
        cats = [c for c in summary.get("categories", []) if c["limit"] > 0]
        if cats:
            st.markdown('<div class="section-title">Budget vs Actual</div>', unsafe_allow_html=True)
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

        # Spending chart — variable only
        st.markdown('<div class="section-title">Spending by Category</div>', unsafe_allow_html=True)
        all_exp = api("GET", f"/expenses/{sel_month}")
        if all_exp:
            df = pd.DataFrame(all_exp)
            var_df = df[df["is_fixed"] == False]
            if not var_df.empty:
                cat_totals = var_df.groupby("category")["amount"].sum().sort_values(ascending=False)
                st.bar_chart(pd.DataFrame({"Amount (₹)": cat_totals}))

            # Fixed vs Variable split
            st.markdown('<div class="section-title">Fixed vs Variable Split</div>', unsafe_allow_html=True)
            split_data = {
                "Fixed (Paid)": bal.get("fixed_paid_total", 0),
                "Fixed (Pending)": bal.get("fixed_unpaid_total", 0),
                "Variable": bal.get("variable_total", 0),
            }
            split_df = pd.DataFrame({"Amount (₹)": split_data})
            st.bar_chart(split_df)


# ═══════════════════════════════════════════════════════
# TAB 4: EXPENSES LIST — follows global month selector
# ═══════════════════════════════════════════════════════
with tab4:
    st.markdown(f'<div class="section-title">Transactions · <span style="color:#6366f1">{month_label}</span></div>',
                unsafe_allow_html=True)

    show_fixed = st.checkbox("Include Fixed Expenses", value=False)

    expenses = api("GET", f"/expenses/{sel_month}")
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
                    paid_badge = ' <span style="color:#34d399; font-size:0.75rem;">· ✅</span>' \
                        if row["is_fixed"] and row.get("paid") else ""

                    r1, r2, r3 = st.columns([0.6, 0.25, 0.15])
                    with r1:
                        st.markdown(f"""
                        <div style="display:flex; align-items:center; gap:10px; padding:8px 0;
                            border-bottom:1px solid rgba(255,255,255,0.05);">
                            <div class="exp-icon">{icon}</div>
                            <div style="flex:1">
                                <div class="exp-vendor">{row['vendor']}{note_html}</div>
                                <div class="exp-cat">{row['category']}{fixed_badge}{paid_badge}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with r2:
                        st.markdown(f"""
                        <div style="padding:8px 0; text-align:right; font-family:'Syne',sans-serif;
                            font-size:0.92rem; font-weight:600; color:#f87171;
                            border-bottom:1px solid rgba(255,255,255,0.05);">
                            -₹{row['amount']:,.0f}
                        </div>
                        """, unsafe_allow_html=True)
                    with r3:
                        # Only allow delete on variable expenses; fixed rows managed via Fixed tab
                        if not row["is_fixed"]:
                            if st.button("🗑️", key=f"del_exp_{row['id']}", help=f"Delete {row['vendor']}"):
                                api("DELETE", f"/expenses/{row['id']}")
                                st.toast(f"Deleted {row['vendor']}", icon="🗑️")
                                st.rerun()
                        else:
                            st.markdown('<div style="padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.05);"></div>',
                                unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:rgba(255,255,255,0.3); text-align:center; padding:40px 0;">No expenses found</div>',
                       unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 5: SETTINGS — global, not month-specific
# ═══════════════════════════════════════════════════════
with tab5:

    # ── Fixed Expense Templates ──────────────────────────
    st.markdown('<div class="section-title">Fixed Expense Templates</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:rgba(255,255,255,0.4); font-size:0.82rem; margin-bottom:16px;">Auto-seeded every month. Edit inline, then Save. Delete removes from future months only.</div>', unsafe_allow_html=True)

    templates = api("GET", "/fixed-templates") or []
    active_templates = [t for t in templates if t["is_active"]]

    if active_templates:
        h1, h2, h3, h4, h5 = st.columns([0.28, 0.22, 0.18, 0.16, 0.16])
        with h1: st.markdown('<div style="color:rgba(255,255,255,0.3); font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; padding-bottom:6px;">Name</div>', unsafe_allow_html=True)
        with h2: st.markdown('<div style="color:rgba(255,255,255,0.3); font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; padding-bottom:6px;">Category</div>', unsafe_allow_html=True)
        with h3: st.markdown('<div style="color:rgba(255,255,255,0.3); font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; padding-bottom:6px;">Amount (₹)</div>', unsafe_allow_html=True)
        with h4: st.markdown('<div style="color:rgba(255,255,255,0.3); font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; padding-bottom:6px;">Save</div>', unsafe_allow_html=True)
        with h5: st.markdown('<div style="color:rgba(255,255,255,0.3); font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; padding-bottom:6px;">Delete</div>', unsafe_allow_html=True)
        st.markdown('<div style="border-top:1px solid rgba(255,255,255,0.07); margin-bottom:8px;"></div>', unsafe_allow_html=True)

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

    # ── Variable Budget Limits ────────────────────────────
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

    # ── Monthly Income ────────────────────────────────────
    st.markdown('<div class="section-title">Monthly Income</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:rgba(255,255,255,0.4); font-size:0.82rem; margin-bottom:14px;">Currently editing: <b style="color:white">{month_label}</b>. Change the month selector at the top to update a different month.</div>', unsafe_allow_html=True)

    current_income = api("GET", f"/income/{sel_month}") or {}
    saved_source = current_income.get("source", "Infosys Salary")
    saved_amount = int(current_income.get("amount", 0))
    saved_note = current_income.get("note") or ""

    with st.form("add_income"):
        col1, col2 = st.columns(2)
        with col1:
            income_source = st.text_input("Source", value=saved_source)
        with col2:
            income_amount = st.number_input("Amount (₹)", value=saved_amount, step=1000)
        income_note = st.text_input("Note (optional)", value=saved_note, placeholder="May salary credit")
        if st.form_submit_button("💾 Save Income"):
            result = api("POST", "/income", json={
                "source": income_source, "amount": income_amount,
                "note": income_note, "month_key": sel_month
            })
            if result:
                st.success(f"✅ Income updated to ₹{income_amount:,.0f} for {month_label}")
                st.rerun()
