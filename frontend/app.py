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
    st.markdown(f'<div class="section-title">Dashboard \xb7 <span style="color:#6366f1">{month_label}</span></div>', unsafe_allow_html=True)

    if not summary:
        st.info("No data for this month yet.")
    else:
        bal = summary["balance"]
        income      = bal.get("total_income", 0)
        fixed_paid  = bal.get("fixed_paid_total", 0)
        fixed_unpd  = bal.get("fixed_unpaid_total", 0)
        variable    = bal.get("variable_total", 0)
        remaining   = bal.get("remaining", 0)

        # ── 1. Month Fuel Gauge ────────────────────────────
        if income > 0:
            pp = round(fixed_paid / income * 100, 1)
            pu = round(fixed_unpd / income * 100, 1)
            pv = round(variable   / income * 100, 1)
            pr = max(round(remaining / income * 100, 1), 0)
        else:
            pp = pu = pv = pr = 0

        lbl_p  = f"{pp:.0f}%"  if pp > 6  else ""
        lbl_u  = f"{pu:.0f}%"  if pu > 6  else ""
        lbl_v  = f"{pv:.0f}%"  if pv > 6  else ""
        lbl_r  = f"\u20b9{remaining:,.0f}" if pr > 8 else ""

        gauge_html = (
            '<div style="background:#111118;border-radius:16px;padding:18px 20px;'
            'border:1px solid rgba(255,255,255,0.07);margin-bottom:20px;">'
            '<div style="display:flex;justify-content:space-between;margin-bottom:10px;">'
            '<span style="color:rgba(255,255,255,0.5);font-size:0.78rem;text-transform:uppercase;letter-spacing:1px;">Monthly Budget Gauge</span>'
            f'<span style="color:rgba(255,255,255,0.4);font-size:0.78rem;">\u20b9{income:,.0f} income</span>'
            '</div>'
            '<div style="display:flex;border-radius:8px;overflow:hidden;height:28px;gap:2px;">'
            f'<div style="width:{pp}%;background:#6366f1;display:flex;align-items:center;justify-content:center;font-size:0.7rem;color:white;font-weight:600;min-width:0;">{lbl_p}</div>'
            f'<div style="width:{pu}%;background:rgba(99,102,241,0.3);display:flex;align-items:center;justify-content:center;font-size:0.7rem;color:rgba(255,255,255,0.6);min-width:0;">{lbl_u}</div>'
            f'<div style="width:{pv}%;background:#f87171;display:flex;align-items:center;justify-content:center;font-size:0.7rem;color:white;font-weight:600;min-width:0;">{lbl_v}</div>'
            f'<div style="flex:1;background:rgba(52,211,153,0.25);display:flex;align-items:center;justify-content:center;font-size:0.7rem;color:#34d399;font-weight:600;">{lbl_r}</div>'
            '</div>'
            '<div style="display:flex;gap:16px;margin-top:10px;flex-wrap:wrap;">'
            f'<span style="font-size:0.75rem;color:rgba(255,255,255,0.5);"><span style="display:inline-block;width:10px;height:10px;background:#6366f1;border-radius:2px;margin-right:4px;"></span>Fixed Paid \u20b9{fixed_paid:,.0f}</span>'
            f'<span style="font-size:0.75rem;color:rgba(255,255,255,0.5);"><span style="display:inline-block;width:10px;height:10px;background:rgba(99,102,241,0.4);border-radius:2px;margin-right:4px;"></span>Pending \u20b9{fixed_unpd:,.0f}</span>'
            f'<span style="font-size:0.75rem;color:rgba(255,255,255,0.5);"><span style="display:inline-block;width:10px;height:10px;background:#f87171;border-radius:2px;margin-right:4px;"></span>Variable \u20b9{variable:,.0f}</span>'
            f'<span style="font-size:0.75rem;color:#34d399;"><span style="display:inline-block;width:10px;height:10px;background:rgba(52,211,153,0.4);border-radius:2px;margin-right:4px;"></span>Remaining \u20b9{remaining:,.0f}</span>'
            '</div></div>'
        )
        st.markdown(gauge_html, unsafe_allow_html=True)

        # ── 2. Budget Health Scorecard ──────────────────────
        st.markdown('<div class="section-title">Budget Health</div>', unsafe_allow_html=True)

        projections = api("GET", f"/insights/projection/{sel_month}") or []
        if projections:
            cards_html = ""
            STATUS = {
                "over":    ("\U0001f534", "#ef4444", "rgba(239,68,68,0.08)",  "Over budget"),
                "danger":  ("\U0001f7e0", "#f59e0b", "rgba(245,158,11,0.07)", ""),
                "warning": ("\U0001f7e1", "#eab308", "rgba(234,179,8,0.06)",  ""),
                "safe":    ("\U0001f7e2", "#34d399", "rgba(52,211,153,0.05)", "On track"),
            }
            for p in projections:
                icon    = CATEGORY_ICONS.get(p["category"], "\U0001f4e6")
                dot, accent, bg, base_label = STATUS.get(p["status"], STATUS["safe"])
                label   = base_label or f"Projected \u20b9{p['projected']:,.0f}"
                bar_w   = round(min(p["pct_spent"], 100), 1)
                proj_w  = round(min(p["pct_projected"], 100), 1)
                days_info = (f"{p['days_left']}d left \xb7 \u20b9{p['daily_rate']:,.0f}/day"
                             if p["days_left"] > 0 else "Month complete")

                proj_marker = ""
                if p["status"] in ("danger", "warning") and proj_w > bar_w:
                    left = min(proj_w, 99)
                    proj_marker = (
                        f'<div style="position:absolute;top:-2px;left:{left}%;'
                        'width:2px;height:10px;background:rgba(255,255,255,0.4);border-radius:1px;"></div>'
                    )

                cards_html += (
                    f'<div style="background:{bg};border:1px solid {accent}22;border-left:3px solid {accent};'
                    'border-radius:12px;padding:14px 16px;margin-bottom:10px;">'
                    '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">'
                    f'<span style="color:white;font-size:0.88rem;font-weight:600;">{dot} {icon} {p["category"]}</span>'
                    f'<span style="color:{accent};font-size:0.78rem;font-weight:600;">{label}</span>'
                    '</div>'
                    '<div style="background:rgba(255,255,255,0.06);border-radius:99px;height:6px;margin-bottom:8px;position:relative;">'
                    f'<div style="width:{bar_w}%;background:{accent};height:6px;border-radius:99px;"></div>'
                    f'{proj_marker}'
                    '</div>'
                    '<div style="display:flex;justify-content:space-between;color:rgba(255,255,255,0.4);font-size:0.75rem;">'
                    f'<span>\u20b9{p["spent"]:,.0f} spent of \u20b9{p["limit"]:,.0f}</span>'
                    f'<span>{days_info}</span>'
                    '</div></div>'
                )
            st.markdown(cards_html, unsafe_allow_html=True)

        # ── 3. Top 5 Variable Spends ────────────────────────
        st.markdown('<div class="section-title">Top Spends This Month</div>', unsafe_allow_html=True)

        top_spends_data = api("GET", f"/insights/top-spends/{sel_month}?limit=5") or []
        if top_spends_data:
            RANK_COLORS = ["#f59e0b", "#94a3b8", "#b45309", "#6366f1", "#6366f1"]
            top_html = ""
            for i, t in enumerate(top_spends_data):
                t_icon     = CATEGORY_ICONS.get(t["category"], "\U0001f4e6")
                date_str   = datetime.strptime(t["date"], "%Y-%m-%d").strftime("%d %b")
                note_part  = ""
                if t.get("note") and "Imported" not in str(t.get("note", "")):
                    note_part = f'<span style="color:rgba(255,255,255,0.3);font-size:0.75rem;"> \xb7 {t["note"]}</span>'
                rc = RANK_COLORS[i]
                top_html += (
                    '<div style="display:flex;align-items:center;gap:12px;padding:12px 0;'
                    'border-bottom:1px solid rgba(255,255,255,0.05);">'
                    f'<div style="font-family:\'Syne\',sans-serif;font-size:1.1rem;font-weight:800;'
                    f'color:{rc};width:24px;text-align:center;flex-shrink:0;">#{i+1}</div>'
                    f'<div style="width:36px;height:36px;border-radius:10px;background:rgba(255,255,255,0.06);'
                    f'display:flex;align-items:center;justify-content:center;font-size:1.1rem;flex-shrink:0;">{t_icon}</div>'
                    '<div style="flex:1;">'
                    f'<div style="color:white;font-size:0.88rem;font-weight:500;">{t["vendor"]}{note_part}</div>'
                    f'<div style="color:rgba(255,255,255,0.4);font-size:0.75rem;">{t["category"]} \xb7 {date_str}</div>'
                    '</div>'
                    f'<div style="font-family:\'Syne\',sans-serif;font-size:1rem;font-weight:700;color:#f87171;">'
                    f'\u20b9{t["amount"]:,.0f}</div>'
                    '</div>'
                )
            st.markdown(top_html, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.85rem;padding:16px 0;">No variable expenses logged yet.</p>', unsafe_allow_html=True)

        # ── 4. Month-over-Month Comparison ─────────────────
        st.markdown('<div class="section-title">Month-over-Month</div>', unsafe_allow_html=True)

        mom = api("GET", f"/insights/mom/{sel_month}")
        if mom and mom.get("months") and mom.get("categories"):
            m_list   = mom["months"]
            cat_data = mom["categories"]

            # Header row
            th_cells = "".join(
                f'<th style="color:rgba(255,255,255,0.5);font-size:0.75rem;font-weight:600;'
                f'text-align:right;padding:6px 12px;white-space:nowrap;">'
                f'{datetime.strptime(m, "%Y-%m").strftime("%b %Y")}</th>'
                for m in m_list
            )
            table_html = (
                '<div style="background:#111118;border-radius:14px;border:1px solid rgba(255,255,255,0.07);overflow:hidden;margin-top:4px;">'
                '<div style="overflow-x:auto;">'
                '<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">'
                '<thead><tr>'
                '<th style="color:rgba(255,255,255,0.5);font-size:0.75rem;font-weight:600;padding:6px 12px;text-align:left;">Category</th>'
                + th_cells +
                '<th style="color:rgba(255,255,255,0.5);font-size:0.75rem;font-weight:600;text-align:center;padding:6px 12px;">Trend</th>'
                '</tr></thead><tbody>'
            )

            for cat in sorted(cat_data.keys()):
                c_icon = CATEGORY_ICONS.get(cat, "\U0001f4e6")
                vals   = [cat_data[cat].get(m, 0) for m in m_list]

                if len(vals) >= 2 and vals[-2] > 0:
                    chg = (vals[-1] - vals[-2]) / vals[-2] * 100
                    if chg > 10:
                        trend_html = f'<span style="color:#f87171;">\u2191 {chg:.0f}%</span>'
                    elif chg < -10:
                        trend_html = f'<span style="color:#34d399;">\u2193 {abs(chg):.0f}%</span>'
                    else:
                        trend_html = '<span style="color:rgba(255,255,255,0.3);">\u2192</span>'
                else:
                    trend_html = '<span style="color:rgba(255,255,255,0.2);">\u2014</span>'

                td_cells = ""
                max_val  = max(vals) if any(vals) else 0
                for j, v in enumerate(vals):
                    is_latest  = (j == len(vals) - 1)
                    is_peak    = (v == max_val and v > 0 and is_latest)
                    col        = "white" if is_latest else "rgba(255,255,255,0.45)"
                    fw         = "700"   if is_latest else "400"
                    cell_bg    = "rgba(239,68,68,0.12)" if is_peak else "transparent"
                    val_str    = f"\u20b9{v:,.0f}" if v > 0 else "\u2014"
                    td_cells  += (
                        f'<td style="text-align:right;padding:8px 12px;color:{col};font-weight:{fw};'
                        f'font-family:\'Syne\',sans-serif;background:{cell_bg};">{val_str}</td>'
                    )

                table_html += (
                    '<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">'
                    f'<td style="padding:8px 12px;color:rgba(255,255,255,0.8);font-size:0.85rem;">{c_icon} {cat}</td>'
                    + td_cells +
                    f'<td style="text-align:center;padding:8px 12px;font-size:0.82rem;">{trend_html}</td>'
                    '</tr>'
                )

            table_html += '</tbody></table></div></div>'
            st.markdown(table_html, unsafe_allow_html=True)


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
