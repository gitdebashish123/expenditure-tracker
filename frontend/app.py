import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime
from collections import defaultdict

API_BASE = "http://localhost:8000"
CURRENT_MONTH = date.today().strftime("%Y-%m")

CATEGORY_ICONS = {
    "Food": "\U0001f354", "Travel": "\U0001f697", "Groceries": "\U0001f6d2", "Shopping": "\U0001f6cd\ufe0f",
    "Medical": "\U0001f48a", "Entertainment": "\U0001f3ac", "Gifts": "\U0001f381", "Course": "\U0001f4da",
    "Miscellaneous": "\U0001f4e6", "Housing": "\U0001f3e0", "Savings": "\U0001f4b0", "EMI": "\U0001f4b3",
    "Investments": "\U0001f4c8", "Utilities": "\u26a1", "Insurance": "\U0001f6e1\ufe0f", "Household": "\U0001f3e1"
}
FIXED_CATEGORIES = ["Housing", "EMI", "Savings", "Investments", "Insurance", "Utilities", "Household"]
VAR_CATEGORIES   = ["Food", "Travel", "Groceries", "Shopping", "Medical", "Entertainment", "Gifts", "Course", "Miscellaneous"]

# ── Auth Session State ────────────────────────────────────────────────
# Initialised before any api() call and before theme — must stay here
if "token" not in st.session_state:
    st.session_state.token = None           # JWT string or None
if "user_email" not in st.session_state:
    st.session_state.user_email = None      # email of logged-in user
if "user_is_admin" not in st.session_state:
    st.session_state.user_is_admin = False  # True = Sprint 6.3 admin panel
if "auth_error" not in st.session_state:
    st.session_state.auth_error = None      # error message shown on login form
if "show_register" not in st.session_state:
    st.session_state.show_register = False  # toggle between login and register form

# ── Theme ────────────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

THEME = {
    "dark": {
        "bg": "#0a0a0f", "card": "#111118", "card2": "#1a1a28",
        "border": "rgba(255,255,255,0.07)", "text": "white",
        "sub": "rgba(255,255,255,0.4)", "muted": "rgba(255,255,255,0.25)",
        "header_bg": "linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%)",
    },
    "light": {
        "bg": "#f5f5f7", "card": "#ffffff", "card2": "#f0f0f5",
        "border": "rgba(0,0,0,0.08)", "text": "#1a1a2e",
        "sub": "rgba(0,0,0,0.5)", "muted": "rgba(0,0,0,0.3)",
        "header_bg": "linear-gradient(135deg,#e8eaf6 0%,#c5cae9 50%,#9fa8da 100%)",
    },
}
T = THEME[st.session_state.theme]
is_dark = st.session_state.theme == "dark"

st.set_page_config(page_title="SpendSense", page_icon="\U0001f4b8", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; background:{T["bg"]}; }}
.main {{ background: {T["bg"]}; }}
.block-container {{ padding: 1.5rem 1rem; max-width: 900px; margin: auto; }}
h1, h2, h3 {{ font-family: 'Syne', sans-serif !important; color:{T["text"]} !important; }}

.app-header {{
    background: {T["header_bg"]}; border-radius: 20px; padding: 20px 28px; margin-bottom: 20px;
    border: 1px solid {T["border"]};
}}
.app-title {{ font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 800;
    color: {'white' if is_dark else '#1a1a2e'}; margin: 0; letter-spacing: -1px; }}
.app-subtitle {{ color: {T["sub"]}; font-size: 0.82rem; margin-top: 2px; }}

.balance-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 16px; }}
.bal-card {{ background: {T["card"]}; border: 1px solid {T["border"]}; border-radius: 16px; padding: 18px; }}
.bal-card.main {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); border: none; }}
.bal-label {{ color: {T["sub"]}; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }}
.bal-amount {{ font-family: 'Syne', sans-serif; font-size: 1.35rem; font-weight: 700; color: {T["text"]}; }}
.bal-sub {{ color: {T["muted"]}; font-size: 0.72rem; margin-top: 4px; }}

.month-badge {{
    display: inline-block; background: rgba(99,102,241,0.2); border: 1px solid rgba(99,102,241,0.4);
    border-radius: 8px; padding: 3px 10px; font-size: 0.78rem; color: #a5b4fc;
    font-family: 'Syne', sans-serif; font-weight: 600;
}}
.past-badge {{
    display: inline-block; background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.3);
    border-radius: 8px; padding: 3px 10px; font-size: 0.78rem; color: #fcd34d;
    font-family: 'Syne', sans-serif; font-weight: 600;
}}

.warn-danger {{ background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.3);
    border-left: 4px solid #ef4444; border-radius: 10px; padding: 12px 16px; margin: 8px 0; color: #fca5a5; font-size: 0.88rem; }}
.warn-warning {{ background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.25);
    border-left: 4px solid #f59e0b; border-radius: 10px; padding: 12px 16px; margin: 8px 0; color: #fcd34d; font-size: 0.88rem; }}
.salary-banner {{
    background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.3);
    border-left: 4px solid #6366f1; border-radius: 10px; padding: 14px 18px; margin: 8px 0;
    color: #a5b4fc; font-size: 0.88rem;
}}
.due-banner {{
    background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.25);
    border-left: 4px solid #ef4444; border-radius: 10px; padding: 12px 16px; margin: 6px 0;
    color: #fca5a5; font-size: 0.85rem;
}}

.fixed-group-header {{ font-family: 'Syne', sans-serif; font-size: 0.78rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1.5px; color: {T["muted"]}; margin: 18px 0 8px; }}
.fixed-progress-bar {{ background: rgba(255,255,255,0.06); border-radius: 99px; height: 6px; margin-bottom: 18px; }}
.fixed-progress-fill {{ height: 6px; border-radius: 99px; background: linear-gradient(90deg, #34d399, #6366f1); }}

.cat-row {{ display: flex; align-items: center; margin-bottom: 14px; gap: 12px; }}
.cat-name {{ color: {T["text"]}; font-size: 0.85rem; width: 120px; flex-shrink: 0; }}
.cat-bar-bg {{ flex: 1; background: rgba(255,255,255,0.06); border-radius: 99px; height: 8px; }}
.cat-bar-fill {{ height: 8px; border-radius: 99px; }}
.cat-amounts {{ color: {T["sub"]}; font-size: 0.78rem; width: 110px; text-align: right; flex-shrink: 0; }}

.exp-row {{ display: flex; align-items: center; padding: 12px 0;
    border-bottom: 1px solid {T["border"]}; gap: 12px; }}
.exp-icon {{ width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center;
    justify-content: center; background: {T["card2"]}; font-size: 1.1rem; flex-shrink: 0; }}
.exp-vendor {{ color: {T["text"]}; font-size: 0.88rem; font-weight: 500; }}
.exp-cat {{ color: {T["sub"]}; font-size: 0.75rem; }}
.exp-amount {{ margin-left: auto; font-family: 'Syne', sans-serif;
    font-size: 0.95rem; font-weight: 600; color: #f87171; flex-shrink: 0; }}

/* Swipe-to-delete container */
.swipe-row {{ position: relative; overflow: hidden; border-radius: 10px; }}

.fav-chip {{
    display: inline-flex; align-items: center; gap: 6px;
    background: {T["card2"]}; border: 1px solid {T["border"]};
    border-radius: 20px; padding: 6px 12px; cursor: pointer;
    font-size: 0.82rem; color: {T["text"]}; margin: 4px;
    transition: all 0.15s;
}}

.section-title {{ font-family: 'Syne', sans-serif; color: {T["text"]}; font-size: 0.95rem;
    font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin: 24px 0 14px; }}
.toast-success {{ background: rgba(52,211,153,0.12); border: 1px solid rgba(52,211,153,0.3);
    border-radius: 10px; padding: 12px 16px; color: #6ee7b7; font-size: 0.88rem; margin: 8px 0; }}

.stTextInput > div > div > input {{
    background: {T["card2"]} !important; border: 1px solid {T["border"]} !important;
    border-radius: 12px !important; color: {T["text"]} !important; font-size: 1rem !important; padding: 14px 16px !important; }}
.stTextInput > div > div > input:focus {{
    border-color: #6366f1 !important; box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important; }}
.stButton > button {{
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 600 !important;
    padding: 12px 24px !important; width: 100% !important; font-size: 0.9rem !important; }}
.stButton > button:hover {{ opacity: 0.9 !important; }}
.stSelectbox > div > div {{ background: {T["card2"]} !important; border-radius: 12px !important; color: {T["text"]} !important; }}
.stNumberInput > div > div > input {{ background: {T["card2"]} !important; color: {T["text"]} !important; }}
.stTabs [data-baseweb="tab-list"] {{ background: {T["card"]}; border-radius: 12px; padding: 4px; }}
.stTabs [data-baseweb="tab"] {{ color: {T["sub"]} !important; border-radius: 8px; }}
.stTabs [aria-selected="true"] {{ background: #6366f1 !important; color: white !important; }}
div[data-testid="stMetricValue"] {{ font-family: 'Syne', sans-serif !important; }}
.stCheckbox > label {{ color: {T["text"]} !important; }}
p, div, span, label {{ color: {T["text"]}; }}

/* Login page */
</style>
""", unsafe_allow_html=True)



# ── Login Page ────────────────────────────────────────────────────────────────
def show_login_page():
    """Renders login/register page. Uses requests directly — no token yet."""
    _, card_col, _ = st.columns([1, 2, 1])
    with card_col:

        st.markdown("""
        <div style="text-align:center;margin-bottom:32px;margin-top:40px;">
            <div style="font-size:2.5rem;">💸</div>
            <div class="login-title" style="text-align:center;">SpendSense</div>
            <div class="login-subtitle" style="text-align:center;">Your personal salary tracker</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.auth_error:
            css = "auth-success" if st.session_state.auth_error.startswith("✅") else "auth-error"
            st.markdown(
                f'<div class="{css}">{st.session_state.auth_error}</div>',
                unsafe_allow_html=True
            )

        if not st.session_state.show_register:
            # Login form
            with st.form("login_form"):
                email    = st.text_input("Email", placeholder="your@email.com",
                                         label_visibility="collapsed", key="login_email")
                password = st.text_input("Password", placeholder="Password",
                                         type="password",
                                         label_visibility="collapsed", key="login_password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.session_state.auth_error = "Please enter your email and password."
                    st.rerun()
                else:
                    try:
                        r = requests.post(f"{API_BASE}/auth/login",
                                          json={"email": email, "password": password},
                                          timeout=10)
                        if r.status_code == 200:
                            data = r.json()
                            st.session_state.token = data["access_token"]
                            me = requests.get(
                                f"{API_BASE}/auth/me",
                                headers={"Authorization": "Bearer " + st.session_state.token},
                                timeout=10,
                            ).json()
                            st.session_state.user_email    = me.get("email")
                            st.session_state.user_is_admin = me.get("is_admin", False)
                            st.session_state.auth_error    = None
                            st.rerun()
                        elif r.status_code == 401:
                            st.session_state.auth_error = "Invalid email or password."
                            st.rerun()
                        elif r.status_code == 403:
                            st.session_state.auth_error = "Account disabled — contact administrator."
                            st.rerun()
                        else:
                            st.session_state.auth_error = f"Login failed (status {r.status_code})."
                            st.rerun()
                    except requests.exceptions.ConnectionError:
                        st.session_state.auth_error = "Backend not running. Start with: ./start.sh"
                        st.rerun()
                    except Exception as e:
                        st.session_state.auth_error = f"Unexpected error: {e}"
                        st.rerun()

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            if st.button("Don't have an account? Create one",
                         use_container_width=True, key="go_register"):
                st.session_state.show_register = True
                st.session_state.auth_error    = None
                st.rerun()

        else:
            # Register form
            st.markdown('<div class="login-subtitle" style="text-align:center;">Create your account</div>',
                        unsafe_allow_html=True)
            with st.form("register_form"):
                reg_email    = st.text_input("Email", placeholder="your@email.com",
                                             label_visibility="collapsed", key="reg_email")
                reg_password = st.text_input("Password (min 8 characters)", placeholder="Password",
                                             type="password",
                                             label_visibility="collapsed", key="reg_password")
                reg_confirm  = st.text_input("Confirm Password", placeholder="Confirm Password",
                                             type="password",
                                             label_visibility="collapsed", key="reg_confirm")
                reg_submitted = st.form_submit_button("Create Account", use_container_width=True)

            if reg_submitted:
                if not reg_email or not reg_password:
                    st.session_state.auth_error = "Please fill in all fields."
                    st.rerun()
                elif len(reg_password) < 8:
                    st.session_state.auth_error = "Password must be at least 8 characters."
                    st.rerun()
                elif reg_password != reg_confirm:
                    st.session_state.auth_error = "Passwords do not match."
                    st.rerun()
                else:
                    try:
                        r = requests.post(f"{API_BASE}/auth/register",
                                          json={"email": reg_email, "password": reg_password},
                                          timeout=10)
                        if r.status_code == 201:
                            st.session_state.auth_error    = "✅ Account created! Please sign in."
                            st.session_state.show_register = False
                            st.rerun()
                        elif r.status_code == 400:
                            st.session_state.auth_error = r.json().get("detail", "Registration failed.")
                            st.rerun()
                        else:
                            st.session_state.auth_error = f"Registration failed (status {r.status_code})."
                            st.rerun()
                    except requests.exceptions.ConnectionError:
                        st.session_state.auth_error = "Backend not running."
                        st.rerun()
                    except Exception as e:
                        st.session_state.auth_error = f"Unexpected error: {e}"
                        st.rerun()

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Already have an account? Sign In",
                         use_container_width=True, key="go_login"):
                st.session_state.show_register = False
                st.session_state.auth_error    = None
                st.rerun()

# ── Helpers ───────────────────────────────────────────────────────────────────
def api(method, path, **kwargs):
    """
    Make an authenticated API call.
    - Injects Authorization: Bearer <token> header if token exists
    - On 401: clears session and reruns to login page
    - On connection error: shows backend-not-running message
    - On other HTTP errors: returns None silently
    """
    headers = kwargs.pop("headers", {})
    if st.session_state.get("token"):
        headers["Authorization"] = "Bearer " + st.session_state.token

    try:
        r = requests.request(method, f"{API_BASE}{path}",
                             timeout=30, headers=headers, **kwargs)

        if r.status_code == 401:
            st.session_state.token = None
            st.session_state.user_email = None
            st.session_state.user_is_admin = False
            st.session_state.auth_error = "Your session has expired. Please log in again."
            st.rerun()

        r.raise_for_status()
        return r.json()

    except requests.exceptions.ConnectionError:
        st.error("Backend not running. Start with: uv run uvicorn backend.main:app --reload")
        return None
    except requests.exceptions.HTTPError:
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None
def bar_color(pct):
    if pct >= 100: return "#ef4444"
    if pct >= 80:  return "#f59e0b"
    if pct >= 60:  return "#6366f1"
    return "#34d399"

def fmt_month(m):
    return datetime.strptime(m, "%Y-%m").strftime("%B %Y")


# ── Auth Gate ────────────────────────────────────────────────────────────────
# Everything below requires authentication.
# If token is missing or expired, show login page and stop execution.
if not st.session_state.get("token"):
    show_login_page()
    st.stop()

# ── Token Validation on Load ──────────────────────────────────────────────────
# Validates token on every page load (e.g. after browser refresh).
# If expired, api() will auto-clear token and rerun to login page.
me = api("GET", "/auth/me")
if me and st.session_state.user_email is None:
    # Restore user info if session state was lost (e.g. after hot reload)
    st.session_state.user_email    = me.get("email")
    st.session_state.user_is_admin = me.get("is_admin", False)

# ── Header row: title + theme toggle + month selector ─────────────────────────
all_months = api("GET", "/months") or []
if CURRENT_MONTH not in all_months:
    all_months = [CURRENT_MONTH] + all_months
all_months = sorted(set(all_months), reverse=True)

col_title, col_theme, col_logout, col_month = st.columns([3, 0.5, 0.7, 1])
with col_title:
    st.markdown(f"""
    <div class="app-header">
        <div class="app-title">\U0001f4b8 SpendSense</div>
        <div class="app-subtitle">Personal Expenditure Tracker</div>
    </div>
    """, unsafe_allow_html=True)
with col_theme:
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    moon = "\U0001f319" if is_dark else "\u2600\ufe0f"
    if st.button(moon, key="theme_toggle", help="Toggle dark/light mode"):
        st.session_state.theme = "light" if is_dark else "dark"
        st.rerun()
with col_logout:
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    email_initial = st.session_state.user_email[0].upper() if st.session_state.user_email else "?"
    if st.button(
        f"👤 {email_initial}  Sign out",
        key="logout_btn",
        help=f"Signed in as {st.session_state.user_email}"
    ):
        st.session_state.token = None
        st.session_state.user_email = None
        st.session_state.user_is_admin = False
        st.session_state.auth_error = None
        st.rerun()
with col_month:
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    sel_month = st.selectbox("Month", all_months, index=0, format_func=fmt_month,
                              label_visibility="collapsed", key="global_month")

is_current  = sel_month == CURRENT_MONTH
month_label = fmt_month(sel_month)
badge_class = "month-badge" if is_current else "past-badge"
badge_text  = f"{'📅 ' if is_current else '🕐 '}{month_label}"


# ── Salary credit reminder (days 1-3 of month, income not set) ───────────────
if is_current and date.today().day <= 3:
    income_check = api("GET", f"/income/check/{CURRENT_MONTH}")
    if income_check and not income_check.get("is_set"):
        st.markdown(
            '\u2194\ufe0f <div class="salary-banner">'
            '\U0001f4b0 <b>Salary credited this month?</b> '
            'Go to <b>Settings \u2192 Monthly Credit</b> to record it so your balance stays accurate.'
            '</div>',
            unsafe_allow_html=True
        )


# ── Summary ───────────────────────────────────────────────────────────────────
summary = api("GET", f"/summary/{sel_month}")

if summary:
    bal         = summary["balance"]
    rem         = bal["remaining"]
    fp          = summary.get("fixed_progress", {})
    paid_count  = fp.get("paid", 0)
    total_count = fp.get("total", 0)
    pct_done    = int(paid_count / total_count * 100) if total_count else 0
    rem_color   = "#34d399" if rem >= 0 else "#f87171"
    total_income   = bal.get("total_income", 0)
    income_display = f"\u20b9{total_income:,.0f}" if total_income > 0 else "Not set"

    st.markdown(f'<div style="margin-bottom:12px;"><span class="{badge_class}">{badge_text}</span></div>',
                unsafe_allow_html=True)

    cards_html = (
        '<div class="balance-grid">'
        f'<div class="bal-card main">'
        '<div class="bal-label">Remaining Balance</div>'
        f'<div class="bal-amount" style="color:{rem_color};">\u20b9{rem:,.0f}</div>'
        '<div class="bal-sub">After all paid expenses</div>'
        '</div>'
        f'<div class="bal-card">'
        '<div class="bal-label">Monthly Income</div>'
        f'<div class="bal-amount">{income_display}</div>'
        f'<div class="bal-sub">\u20b9{bal.get("variable_total",0):,.0f} variable spent</div>'
        '</div>'
        f'<div class="bal-card">'
        '<div class="bal-label">Fixed Paid / Pending</div>'
        f'<div class="bal-amount">{paid_count} / {total_count}</div>'
        f'<div class="bal-sub">\u20b9{bal.get("fixed_paid_total",0):,.0f} paid \xb7 \u20b9{bal.get("fixed_unpaid_total",0):,.0f} pending</div>'
        '</div>'
        '</div>'
        f'<div class="fixed-progress-bar"><div class="fixed-progress-fill" style="width:{pct_done}%"></div></div>'
    )
    st.markdown(cards_html, unsafe_allow_html=True)

    if is_current and summary.get("warnings"):
        for w in summary["warnings"]:
            css = "warn-danger" if w["level"] == "danger" else "warn-warning"
            st.markdown(f'<div class="{css}">{w["message"]}</div>', unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["\u26a1 Quick Add", "\U0001f4cc Fixed", "\U0001f4ca Dashboard", "\U0001f4cb Expenses", "\u2699\ufe0f Settings"])


# ═══════════════════════════════════════════════════════
# TAB 1: QUICK ADD
# ═══════════════════════════════════════════════════════
with tab1:
    if not is_current:
        st.markdown(f"""
        <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.25);
            border-radius:12px;padding:14px 18px;color:#fcd34d;font-size:0.88rem;margin-bottom:16px;">
            \u26a0\ufe0f Viewing <b>{month_label}</b>. Quick Add always logs to the current month.
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Log Expenses</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{T["sub"]};font-size:0.82rem;margin-bottom:14px;">Type like: <code style="background:{T["card2"]};padding:2px 6px;border-radius:4px;color:#a5b4fc;">zomato 500, ola 200, bigbasket 1200</code></div>', unsafe_allow_html=True)

    with st.form("quick_add", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            expense_text = st.text_input("Expense Input",
                placeholder="e.g. zomato 500, ola 200, bigbasket 1200",
                label_visibility="collapsed")
        with col2:
            expense_date_val = st.date_input("Date", value=date.today(), label_visibility="collapsed")
        submitted = st.form_submit_button("\u2795 Add Expenses")

    if submitted and expense_text.strip():
        with st.spinner("\U0001f916 Parsing with AI..."):
            result = api("POST", "/expenses/parse", json={
                "text": expense_text,
                "date_override": expense_date_val.isoformat()
            })
        if result:
            saved = result.get("saved", [])
            st.markdown(f'<div class="toast-success">\u2705 Saved {len(saved)} expense(s)</div>', unsafe_allow_html=True)
            cols = st.columns(min(len(saved), 3))
            for i, item in enumerate(saved):
                icon = CATEGORY_ICONS.get(item["category"], "\U0001f4e6")
                with cols[i % len(cols)]:
                    st.markdown(f"""
                    <div style="background:{T['card2']};border-radius:12px;padding:14px;text-align:center;margin-top:8px;">
                        <div style="font-size:1.5rem">{icon}</div>
                        <div style="color:{T['text']};font-weight:600;font-size:0.9rem;margin-top:4px">{item['vendor']}</div>
                        <div style="color:#f87171;font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700">\u20b9{item['amount']:,.0f}</div>
                        <div style="color:{T['sub']};font-size:0.75rem">{item['category']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            for w in result.get("warnings", []):
                css = "warn-danger" if w["level"] == "danger" else "warn-warning"
                st.markdown(f'<div class="{css}">{w["message"]}</div>', unsafe_allow_html=True)
            if result.get("balance"):
                b = result["balance"]
                color = "#34d399" if b["remaining"] >= 0 else "#f87171"
                st.markdown(f"""
                <div style="background:{T['card']};border-radius:12px;padding:16px;margin-top:14px;
                    text-align:center;border:1px solid {T['border']};">
                    <div style="color:{T['sub']};font-size:0.8rem;">Updated Remaining Balance</div>
                    <div style="font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;color:{color};">
                        \u20b9{b['remaining']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            st.rerun()

    # ── Favourites / Quick Templates ──────────────────────────────────────
    fav_templates = api("GET", "/expense-templates") or []
    if fav_templates:
        st.markdown('<div class="section-title">Quick Add Favourites</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:{T["sub"]};font-size:0.8rem;margin-bottom:10px;">Tap to log instantly</div>', unsafe_allow_html=True)

        # Render as chips — 3 per row
        cols = st.columns(3)
        for i, tmpl in enumerate(fav_templates):
            icon = CATEGORY_ICONS.get(tmpl["category"], "\U0001f4e6")
            with cols[i % 3]:
                if st.button(
                    f"{icon} {tmpl['name']}\n\u20b9{tmpl['amount']:,.0f}",
                    key=f"fav_{tmpl['id']}",
                    help=f"{tmpl['vendor']} \u2022 {tmpl['category']}"
                ):
                    result = api("POST", f"/expense-templates/{tmpl['id']}/log")
                    if result:
                        st.toast(f"\u2705 Logged {tmpl['vendor']} \u20b9{tmpl['amount']:,.0f}", icon="\u26a1")
                        st.rerun()

    # ── Today's Entries with swipe-to-delete ──────────────────────────────
    st.markdown('<div class="section-title">Today\'s Entries</div>', unsafe_allow_html=True)

    # Swipe-to-delete JS injection
    st.markdown("""
    <script>
    function initSwipe() {
        document.querySelectorAll('.swipe-exp-row').forEach(row => {
            if (row._swipeInited) return;
            row._swipeInited = true;
            let startX = 0;
            row.addEventListener('touchstart', e => { startX = e.touches[0].clientX; }, {passive:true});
            row.addEventListener('touchend', e => {
                const dx = e.changedTouches[0].clientX - startX;
                if (dx < -80) {
                    row.style.transform = 'translateX(-80px)';
                    row.querySelector('.swipe-del-btn')?.classList.remove('hidden');
                } else if (dx > 20) {
                    row.style.transform = 'translateX(0)';
                    row.querySelector('.swipe-del-btn')?.classList.add('hidden');
                }
            }, {passive:true});
        });
    }
    const obs = new MutationObserver(initSwipe);
    obs.observe(document.body, {childList:true, subtree:true});
    initSwipe();
    </script>
    <style>
    .swipe-exp-row { transition: transform 0.2s ease; }
    .swipe-del-btn { position:absolute; right:0; top:0; bottom:0; width:70px;
        background:#ef4444; display:flex; align-items:center; justify-content:center;
        font-size:1.3rem; cursor:pointer; border-radius:0 10px 10px 0; }
    .swipe-del-btn.hidden { display:none; }
    </style>
    """, unsafe_allow_html=True)

    today_expenses = api("GET", f"/expenses/{CURRENT_MONTH}")
    if today_expenses:
        today_only = [e for e in today_expenses
                     if e["date"] == date.today().isoformat() and not e["is_fixed"]]
        if today_only:
            for e in today_only[:10]:
                icon = CATEGORY_ICONS.get(e["category"], "\U0001f4e6")
                col_info, col_amt, col_del = st.columns([0.6, 0.25, 0.15])
                with col_info:
                    st.markdown(f"""
                    <div class="swipe-exp-row" style="display:flex;align-items:center;gap:10px;padding:8px 0;
                        border-bottom:1px solid {T['border']};position:relative;">
                        <div class="exp-icon">{icon}</div>
                        <div>
                            <div class="exp-vendor">{e['vendor']}</div>
                            <div class="exp-cat">{e['category']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_amt:
                    st.markdown(f"""
                    <div style="padding:8px 0;text-align:right;font-family:'Syne',sans-serif;
                        font-size:0.95rem;font-weight:600;color:#f87171;
                        border-bottom:1px solid {T['border']};">
                        -\u20b9{e['amount']:,.0f}
                    </div>
                    """, unsafe_allow_html=True)
                with col_del:
                    if st.button("\U0001f5d1\ufe0f", key=f"del_today_{e['id']}", help=f"Delete {e['vendor']}"):
                        if api("DELETE", f"/expenses/{e['id']}"):
                            st.toast(f"Deleted {e['vendor']}", icon="\U0001f5d1\ufe0f")
                            st.rerun()
        else:
            st.markdown(f'<div style="color:{T["sub"]};font-size:0.85rem;padding:20px 0;text-align:center;">No expenses logged today</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 2: FIXED EXPENSES with due reminders + Essential Pools
# ═══════════════════════════════════════════════════════
with tab2:
    st.markdown(f'<div class="section-title">Fixed Expenses \xb7 <span style="color:#6366f1">{month_label}</span></div>', unsafe_allow_html=True)

    # Due reminders (current month only)
    if is_current:
        reminders = api("GET", f"/fixed/due-reminders/{sel_month}") or []
        for r in reminders:
            overdue_txt = "due today" if r["days_overdue"] == 0 else f"{r['days_overdue']}d overdue"
            st.markdown(
                f'<div class="due-banner">\U0001f514 <b>{r["vendor"]}</b> \u20b9{r["amount"]:,.0f} '
                f'\u2014 was due on the {r["due_day"]}th ({overdue_txt})</div>',
                unsafe_allow_html=True
            )

    # ── True Fixed Expenses ─────────────────────────────────────────────
    fixed_exps = api("GET", f"/fixed/{sel_month}") or []
    if fixed_exps:
        by_cat = defaultdict(list)
        for e in fixed_exps:
            by_cat[e["category"]].append(e)

        paid_total   = sum(e["amount"] for e in fixed_exps if e["paid"])
        unpaid_total = sum(e["amount"] for e in fixed_exps if not e["paid"])
        total_fixed  = sum(e["amount"] for e in fixed_exps)
        pct          = int(paid_total / total_fixed * 100) if total_fixed else 0

        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="color:{T['sub']};font-size:0.82rem;">{sum(1 for e in fixed_exps if e['paid'])} of {len(fixed_exps)} paid \xb7 \u20b9{paid_total:,.0f} done</span>
            <span style="color:#f87171;font-size:0.82rem;">\u20b9{unpaid_total:,.0f} pending</span>
        </div>
        <div class="fixed-progress-bar"><div class="fixed-progress-fill" style="width:{pct}%"></div></div>
        """, unsafe_allow_html=True)

        for category, items in sorted(by_cat.items()):
            icon      = CATEGORY_ICONS.get(category, "\U0001f4e6")
            cat_total = sum(i["amount"] for i in items)
            st.markdown(f'<div class="fixed-group-header">{icon} {category} \xb7 \u20b9{cat_total:,.0f}</div>', unsafe_allow_html=True)
            for item in items:
                paid = item["paid"]
                tick = "\u2705" if paid else "\u2b1c"
                c1, c2, c3 = st.columns([0.08, 0.7, 0.22])
                with c1:
                    if st.button(tick, key=f"tick_{item['id']}", help="Toggle paid"):
                        api("PATCH", f"/fixed/{item['id']}/toggle")
                        st.rerun()
                with c2:
                    st.markdown(f"""
                    <div style="padding:8px 0;color:{'rgba(255,255,255,0.35)' if paid else T['text']};
                        font-size:0.88rem;{'text-decoration:line-through;' if paid else ''}">
                        {item['vendor']}
                    </div>
                    """, unsafe_allow_html=True)
                with c3:
                    amt_color = "#34d399" if paid else T["sub"]
                    st.markdown(f'<div style="padding:8px 0;text-align:right;font-family:\'Syne\',sans-serif;font-size:0.88rem;color:{amt_color};">\u20b9{item["amount"]:,.0f}</div>', unsafe_allow_html=True)

    # ── Essential Pools ─────────────────────────────────────────────────
    pools = api("GET", f"/pools/{sel_month}") or []
    if pools:
        st.markdown('<div class="section-title">Essential Pools</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:{T["sub"]};font-size:0.8rem;margin-bottom:14px;">Bills with variable amount and count \u2014 add each payment as it happens.</div>', unsafe_allow_html=True)

        for pool in pools:
            icon      = CATEGORY_ICONS.get(pool["category"], "\U0001f4e6")
            paid_t    = pool["paid_total"]
            unpaid_t  = pool["unpaid_total"]
            total_t   = paid_t + unpaid_t
            pool_pct  = int(paid_t / total_t * 100) if total_t > 0 else 0
            entry_cnt = pool["entry_count"]

            # Pool header
            pool_status = (
                "\u26a0\ufe0f No entries yet" if entry_cnt == 0
                else f"\u2705 \u20b9{paid_t:,.0f} paid" if unpaid_t == 0
                else f"\u20b9{paid_t:,.0f} paid \xb7 \u20b9{unpaid_t:,.0f} unpaid"
            )
            st.markdown(f"""
            <div style="background:{T['card']};border-radius:14px;border:1px solid {T['border']};
                padding:16px 18px;margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                    <span style="color:{T['text']};font-size:0.92rem;font-weight:700;">{icon} {pool['name']}</span>
                    <span style="color:{'#34d399' if unpaid_t == 0 and entry_cnt > 0 else '#f59e0b' if unpaid_t > 0 else T['sub']};font-size:0.8rem;">{pool_status}</span>
                </div>
            """, unsafe_allow_html=True)

            # Existing entries
            for entry in pool["entries"]:
                paid = entry["paid"]
                tick = "\u2705" if paid else "\u2b1c"
                e1, e2, e3, e4 = st.columns([0.07, 0.5, 0.22, 0.21])
                with e1:
                    if st.button(tick, key=f"ptick_{entry['id']}", help="Tap to undo / mark unpaid"):
                        api("PATCH", f"/pools/entries/{entry['id']}/toggle")
                        st.rerun()
                with e2:
                    st.markdown(f"""
                    <div style="padding:6px 0;color:{'rgba(255,255,255,0.35)' if paid else T['text']};
                        font-size:0.85rem;{'text-decoration:line-through;' if paid else ''}">
                        {entry['label']}
                        {f'<span style="color:{T["muted"]};font-size:0.73rem;"> \xb7 {entry["note"]}</span>' if entry.get("note") else ""}
                    </div>
                    """, unsafe_allow_html=True)
                with e3:
                    amt_color = "#34d399" if paid else T["sub"]
                    st.markdown(f'<div style="padding:6px 0;text-align:right;font-family:\'Syne\',sans-serif;font-size:0.88rem;color:{amt_color};">\u20b9{entry["amount"]:,.0f}</div>', unsafe_allow_html=True)
                with e4:
                    if st.button("\U0001f5d1\ufe0f", key=f"pdel_{entry['id']}", help="Remove entry"):
                        api("DELETE", f"/pools/entries/{entry['id']}")
                        st.rerun()

            # Add new entry form for this pool
            with st.form(f"add_pool_{pool['id']}", clear_on_submit=True):
                pa, pb, pc = st.columns([0.4, 0.3, 0.3])
                with pa:
                    new_label = st.text_input("Label", placeholder="e.g. Home, Rented House, Self", key=f"pl_{pool['id']}", label_visibility="collapsed",
                    help="Enter label and amount, then click Add — logged as paid immediately")
                with pb:
                    new_amount = st.number_input("Amount (\u20b9)", min_value=0, step=10, key=f"pa_{pool['id']}", label_visibility="collapsed")
                with pc:
                    add_clicked = st.form_submit_button("\u2795 Add Payment")
                if add_clicked and new_label and new_amount > 0:
                    api("POST", f"/pools/{pool['id']}/entries/{sel_month}",
                        json={"label": new_label, "amount": new_amount})
                    st.rerun()

            # Pool total
            if total_t > 0:
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:8px 0 4px;
                    border-top:1px solid {T['border']};margin-top:4px;">
                    <span style="color:{T['muted']};font-size:0.78rem;">{entry_cnt} payment(s)</span>
                    <span style="font-family:'Syne',sans-serif;font-size:0.88rem;font-weight:700;color:{T['text']};">
                        \u20b9{total_t:,.0f} total \xb7 <span style="color:#34d399;">\u20b9{paid_t:,.0f} paid</span>
                    </span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    if not fixed_exps and not pools:
        st.markdown(f'<div style="color:{T["sub"]};text-align:center;padding:40px 0;">No fixed expenses or pools for this month</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 3: DASHBOARD
# ═══════════════════════════════════════════════════════
with tab3:
    st.markdown(f'<div class="section-title">Dashboard \xb7 <span style="color:#6366f1">{month_label}</span></div>', unsafe_allow_html=True)

    if not summary:
        st.info("No data for this month yet.")
    else:
        bal       = summary["balance"]
        income    = bal.get("total_income", 0)
        fixed_paid  = bal.get("fixed_paid_total", 0)
        fixed_unpd  = bal.get("fixed_unpaid_total", 0)
        variable    = bal.get("variable_total", 0)
        remaining   = bal.get("remaining", 0)

        if income > 0:
            pp = round(fixed_paid / income * 100, 1)
            pu = round(fixed_unpd / income * 100, 1)
            pv = round(variable   / income * 100, 1)
            pr = max(round(remaining / income * 100, 1), 0)
        else:
            pp = pu = pv = pr = 0

        lbl_p = f"{pp:.0f}%" if pp > 6 else ""
        lbl_u = f"{pu:.0f}%" if pu > 6 else ""
        lbl_v = f"{pv:.0f}%" if pv > 6 else ""
        lbl_r = f"\u20b9{remaining:,.0f}" if pr > 8 else ""

        gauge_html = (
            f'<div style="background:{T["card"]};border-radius:16px;padding:18px 20px;border:1px solid {T["border"]};margin-bottom:20px;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:10px;">'
            f'<span style="color:{T["sub"]};font-size:0.78rem;text-transform:uppercase;letter-spacing:1px;">Monthly Breakdown</span>'
            '</div>'
            '<div style="display:flex;border-radius:8px;overflow:hidden;height:28px;gap:2px;">'
            f'<div style="width:{pp}%;background:#6366f1;display:flex;align-items:center;justify-content:center;font-size:0.7rem;color:white;font-weight:600;min-width:0;">{lbl_p}</div>'
            f'<div style="width:{pu}%;background:rgba(99,102,241,0.3);display:flex;align-items:center;justify-content:center;font-size:0.7rem;color:rgba(255,255,255,0.6);min-width:0;">{lbl_u}</div>'
            f'<div style="width:{pv}%;background:#f87171;display:flex;align-items:center;justify-content:center;font-size:0.7rem;color:white;font-weight:600;min-width:0;">{lbl_v}</div>'
            f'<div style="flex:1;background:rgba(52,211,153,0.25);display:flex;align-items:center;justify-content:center;font-size:0.7rem;color:#34d399;font-weight:600;">{lbl_r}</div>'
            '</div>'
            f'<div style="display:flex;gap:16px;margin-top:10px;flex-wrap:wrap;">'
            f'<span style="font-size:0.75rem;color:{T["sub"]};"><span style="display:inline-block;width:10px;height:10px;background:#6366f1;border-radius:2px;margin-right:4px;"></span>Fixed Paid \u20b9{fixed_paid:,.0f}</span>'
            f'<span style="font-size:0.75rem;color:{T["sub"]};"><span style="display:inline-block;width:10px;height:10px;background:rgba(99,102,241,0.4);border-radius:2px;margin-right:4px;"></span>Pending \u20b9{fixed_unpd:,.0f}</span>'
            f'<span style="font-size:0.75rem;color:{T["sub"]};"><span style="display:inline-block;width:10px;height:10px;background:#f87171;border-radius:2px;margin-right:4px;"></span>Variable \u20b9{variable:,.0f}</span>'
            f'<span style="font-size:0.75rem;color:#34d399;"><span style="display:inline-block;width:10px;height:10px;background:rgba(52,211,153,0.4);border-radius:2px;margin-right:4px;"></span>Remaining \u20b9{remaining:,.0f}</span>'
            '</div></div>'
        )
        st.markdown(gauge_html, unsafe_allow_html=True)

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
                p_icon = CATEGORY_ICONS.get(p["category"], "\U0001f4e6")
                dot, accent, bg, base_label = STATUS.get(p["status"], STATUS["safe"])
                label     = base_label or f"Projected \u20b9{p['projected']:,.0f}"
                bar_w     = round(min(p["pct_spent"], 100), 1)
                proj_w    = round(min(p["pct_projected"], 100), 1)
                days_info = f"{p['days_left']}d left \xb7 \u20b9{p['daily_rate']:,.0f}/day" if p["days_left"] > 0 else "Month complete"
                proj_marker = ""
                if p["status"] in ("danger", "warning") and proj_w > bar_w:
                    proj_marker = f'<div style="position:absolute;top:-2px;left:{min(proj_w,99)}%;width:2px;height:10px;background:rgba(255,255,255,0.4);border-radius:1px;"></div>'
                cards_html += (
                    f'<div style="background:{bg};border:1px solid {accent}22;border-left:3px solid {accent};border-radius:12px;padding:14px 16px;margin-bottom:10px;">'
                    f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">'
                    f'<span style="color:{T["text"]};font-size:0.88rem;font-weight:600;">{dot} {p_icon} {p["category"]}</span>'
                    f'<span style="color:{accent};font-size:0.78rem;font-weight:600;">{label}</span>'
                    '</div>'
                    f'<div style="background:rgba(255,255,255,0.06);border-radius:99px;height:6px;margin-bottom:8px;position:relative;">'
                    f'<div style="width:{bar_w}%;background:{accent};height:6px;border-radius:99px;"></div>'
                    f'{proj_marker}</div>'
                    f'<div style="display:flex;justify-content:space-between;color:{T["sub"]};font-size:0.75rem;">'
                    f'<span>\u20b9{p["spent"]:,.0f} spent of \u20b9{p["limit"]:,.0f}</span>'
                    f'<span>{days_info}</span></div></div>'
                )
            st.markdown(cards_html, unsafe_allow_html=True)

        st.markdown('<div class="section-title">Top Spends This Month</div>', unsafe_allow_html=True)
        top_spends_data = api("GET", f"/insights/top-spends/{sel_month}?limit=5") or []
        if top_spends_data:
            RANK_COLORS = ["#f59e0b", "#94a3b8", "#b45309", "#6366f1", "#6366f1"]
            top_html = ""
            for i, t in enumerate(top_spends_data):
                t_icon   = CATEGORY_ICONS.get(t["category"], "\U0001f4e6")
                date_str = datetime.strptime(t["date"], "%Y-%m-%d").strftime("%d %b")
                note_part = ""
                if t.get("note") and "Imported" not in str(t.get("note", "")) and "Quick-add" not in str(t.get("note", "")):
                    note_part = f'<span style="color:{T["muted"]};font-size:0.75rem;"> \xb7 {t["note"]}</span>'
                rc = RANK_COLORS[i]
                top_html += (
                    f'<div style="display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid {T["border"]};">'
                    f'<div style="font-family:\'Syne\',sans-serif;font-size:1.1rem;font-weight:800;color:{rc};width:24px;text-align:center;flex-shrink:0;">#{i+1}</div>'
                    f'<div style="width:36px;height:36px;border-radius:10px;background:{T["card2"]};display:flex;align-items:center;justify-content:center;font-size:1.1rem;flex-shrink:0;">{t_icon}</div>'
                    f'<div style="flex:1;"><div style="color:{T["text"]};font-size:0.88rem;font-weight:500;">{t["vendor"]}{note_part}</div>'
                    f'<div style="color:{T["sub"]};font-size:0.75rem;">{t["category"]} \xb7 {date_str}</div></div>'
                    f'<div style="font-family:\'Syne\',sans-serif;font-size:1rem;font-weight:700;color:#f87171;">\u20b9{t["amount"]:,.0f}</div>'
                    '</div>'
                )
            st.markdown(top_html, unsafe_allow_html=True)

        st.markdown('<div class="section-title">Month-over-Month</div>', unsafe_allow_html=True)
        mom = api("GET", f"/insights/mom/{sel_month}")
        if mom and mom.get("months") and mom.get("categories"):
            m_list   = mom["months"]
            cat_data = mom["categories"]
            th_cells = "".join(
                f'<th style="color:{T["sub"]};font-size:0.75rem;font-weight:600;text-align:right;padding:6px 12px;white-space:nowrap;">{datetime.strptime(m, "%Y-%m").strftime("%b %Y")}</th>'
                for m in m_list
            )
            table_html = (
                f'<div style="background:{T["card"]};border-radius:14px;border:1px solid {T["border"]};overflow:hidden;margin-top:4px;">'
                '<div style="overflow-x:auto;">'
                '<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">'
                '<thead><tr>'
                f'<th style="color:{T["sub"]};font-size:0.75rem;font-weight:600;padding:6px 12px;text-align:left;">Category</th>'
                + th_cells +
                f'<th style="color:{T["sub"]};font-size:0.75rem;font-weight:600;text-align:center;padding:6px 12px;">Trend</th>'
                '</tr></thead><tbody>'
            )
            for cat in sorted(cat_data.keys()):
                c_icon = CATEGORY_ICONS.get(cat, "\U0001f4e6")
                vals   = [cat_data[cat].get(m, 0) for m in m_list]
                if len(vals) >= 2 and vals[-2] > 0:
                    chg = (vals[-1] - vals[-2]) / vals[-2] * 100
                    trend_html = f'<span style="color:#f87171;">\u2191 {chg:.0f}%</span>' if chg > 10 else \
                                 f'<span style="color:#34d399;">\u2193 {abs(chg):.0f}%</span>' if chg < -10 else \
                                 f'<span style="color:{T["muted"]};">\u2192</span>'
                else:
                    trend_html = f'<span style="color:{T["muted"]};">\u2014</span>'
                td_cells = ""
                max_val  = max(vals) if any(vals) else 0
                for j, v in enumerate(vals):
                    is_latest = (j == len(vals) - 1)
                    is_peak   = (v == max_val and v > 0 and is_latest)
                    col = T["text"] if is_latest else T["sub"]
                    fw  = "700" if is_latest else "400"
                    cbg = "rgba(239,68,68,0.12)" if is_peak else "transparent"
                    val_str = f"\u20b9{v:,.0f}" if v > 0 else "\u2014"
                    td_cells += f'<td style="text-align:right;padding:8px 12px;color:{col};font-weight:{fw};font-family:\'Syne\',sans-serif;background:{cbg};">{val_str}</td>'
                table_html += (
                    f'<tr style="border-bottom:1px solid {T["border"]};">'
                    f'<td style="padding:8px 12px;color:{T["text"]};font-size:0.85rem;">{c_icon} {cat}</td>'
                    + td_cells +
                    f'<td style="text-align:center;padding:8px 12px;font-size:0.82rem;">{trend_html}</td></tr>'
                )
            table_html += '</tbody></table></div></div>'
            st.markdown(table_html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 4: EXPENSES — edit, bulk delete, swipe delete
# ═══════════════════════════════════════════════════════
with tab4:
    st.markdown(f'<div class="section-title">Transactions \xb7 <span style="color:#6366f1">{month_label}</span></div>', unsafe_allow_html=True)

    col_filter, col_bulk = st.columns([2, 1])
    with col_filter:
        show_fixed = st.checkbox("Include Fixed Expenses", value=False)
    with col_bulk:
        bulk_mode = st.checkbox("\u2610 Bulk Select", value=False)

    expenses = api("GET", f"/expenses/{sel_month}")
    selected_ids = []

    if expenses:
        df = pd.DataFrame(expenses)
        if not show_fixed:
            df = df[df["is_fixed"] == False]
        if not df.empty:
            total = df["amount"].sum()
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:12px 0;
                border-bottom:1px solid {T['border']};margin-bottom:8px;">
                <span style="color:{T['sub']};font-size:0.82rem;">{len(df)} transactions</span>
                <span style="font-family:'Syne',sans-serif;color:#f87171;font-weight:700;">Total: \u20b9{total:,.0f}</span>
            </div>
            """, unsafe_allow_html=True)

            df["date"] = pd.to_datetime(df["date"])

            # Edit state
            if "editing_id" not in st.session_state:
                st.session_state.editing_id = None

            for exp_date, group in df.sort_values("date", ascending=False).groupby("date", sort=False):
                date_str  = exp_date.strftime("%d %b %Y")
                day_total = group["amount"].sum()
                st.markdown(f"""
                <div style="color:{T['sub']};font-size:0.75rem;margin:14px 0 6px;
                    display:flex;justify-content:space-between;">
                    <span>{date_str}</span><span>\u20b9{day_total:,.0f}</span>
                </div>
                """, unsafe_allow_html=True)

                for _, row in group.iterrows():
                    icon        = CATEGORY_ICONS.get(row["category"], "\U0001f4e6")
                    note_html   = f'<span style="color:{T["muted"]};font-size:0.75rem;"> \xb7 {row["note"]}</span>' \
                                  if pd.notna(row.get("note")) and row.get("note") else ""
                    fixed_badge = f' <span style="color:{T["muted"]};font-size:0.75rem;">\xb7 Fixed</span>' if row["is_fixed"] else ""

                    # EDIT MODE for this row
                    if st.session_state.editing_id == row["id"]:
                        with st.container():
                            st.markdown(f'<div style="background:{T["card2"]};border-radius:12px;padding:14px;margin:6px 0;border:1px solid #6366f1;">', unsafe_allow_html=True)
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                new_vendor = st.text_input("Vendor", value=row["vendor"], key=f"ev_{row['id']}")
                                new_cat    = st.selectbox("Category", VAR_CATEGORIES,
                                    index=VAR_CATEGORIES.index(row["category"]) if row["category"] in VAR_CATEGORIES else 0,
                                    key=f"ec_{row['id']}")
                            with ec2:
                                new_amt  = st.number_input("Amount (\u20b9)", value=float(row["amount"]), step=10.0, key=f"ea_{row['id']}")
                                new_note = st.text_input("Note", value=str(row["note"]) if pd.notna(row.get("note")) else "", key=f"en_{row['id']}")
                            sb1, sb2 = st.columns(2)
                            with sb1:
                                if st.button("\U0001f4be Save", key=f"esave_{row['id']}"):
                                    api("PATCH", f"/expenses/{row['id']}", json={
                                        "vendor": new_vendor, "amount": new_amt,
                                        "category": new_cat, "note": new_note
                                    })
                                    st.session_state.editing_id = None
                                    st.rerun()
                            with sb2:
                                if st.button("\u274c Cancel", key=f"ecancel_{row['id']}"):
                                    st.session_state.editing_id = None
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                        continue

                    # NORMAL ROW
                    if bulk_mode and not row["is_fixed"]:
                        check_col, info_col, amt_col = st.columns([0.08, 0.67, 0.25])
                        with check_col:
                            checked = st.checkbox("", key=f"sel_{row['id']}", label_visibility="collapsed")
                            if checked:
                                selected_ids.append(int(row["id"]))
                        with info_col:
                            st.markdown(f"""
                            <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid {T['border']};">
                                <div class="exp-icon">{icon}</div>
                                <div style="flex:1">
                                    <div class="exp-vendor">{row['vendor']}{note_html}</div>
                                    <div class="exp-cat">{row['category']}{fixed_badge}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        with amt_col:
                            st.markdown(f'<div style="padding:8px 0;text-align:right;font-family:\'Syne\',sans-serif;font-size:0.92rem;font-weight:600;color:#f87171;border-bottom:1px solid {T["border"]};">-\u20b9{row["amount"]:,.0f}</div>', unsafe_allow_html=True)
                    else:
                        r1, r2, r3, r4 = st.columns([0.52, 0.22, 0.13, 0.13])
                        with r1:
                            st.markdown(f"""
                            <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid {T['border']};">
                                <div class="exp-icon">{icon}</div>
                                <div style="flex:1">
                                    <div class="exp-vendor">{row['vendor']}{note_html}</div>
                                    <div class="exp-cat">{row['category']}{fixed_badge}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        with r2:
                            st.markdown(f'<div style="padding:8px 0;text-align:right;font-family:\'Syne\',sans-serif;font-size:0.92rem;font-weight:600;color:#f87171;border-bottom:1px solid {T["border"]};">-\u20b9{row["amount"]:,.0f}</div>', unsafe_allow_html=True)
                        with r3:
                            if not row["is_fixed"]:
                                if st.button("\u270f\ufe0f", key=f"edit_{row['id']}", help="Edit"):
                                    st.session_state.editing_id = int(row["id"])
                                    st.rerun()
                        with r4:
                            if not row["is_fixed"]:
                                if st.button("\U0001f5d1\ufe0f", key=f"del_exp_{row['id']}", help=f"Delete {row['vendor']}"):
                                    api("DELETE", f"/expenses/{row['id']}")
                                    st.toast(f"Deleted {row['vendor']}", icon="\U0001f5d1\ufe0f")
                                    st.rerun()

            # Bulk delete button
            if bulk_mode and selected_ids:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"\U0001f5d1\ufe0f Delete {len(selected_ids)} selected", key="bulk_del"):
                    result = api("POST", "/expenses/bulk-delete", json={"ids": selected_ids})
                    if result:
                        st.toast(f"Deleted {result['count']} expenses", icon="\U0001f5d1\ufe0f")
                        st.rerun()
        else:
            st.markdown(f'<div style="color:{T["sub"]};text-align:center;padding:40px 0;">No expenses found</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TAB 5: SETTINGS — friendly, goal-oriented layout
# ═══════════════════════════════════════════════════════
with tab5:

    # ── Section helper ────────────────────────────────────────────────────
    def settings_section(icon, title, subtitle):
        st.markdown(f"""
        <div style="margin-top:28px;margin-bottom:4px;">
            <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:{T['text']};">
                {icon} {title}
            </div>
            <div style="color:{T['sub']};font-size:0.82rem;margin-top:3px;">{subtitle}</div>
        </div>
        <div style="border-bottom:1px solid {T['border']};margin-bottom:16px;"></div>
        """, unsafe_allow_html=True)

    # ════════════════════════════════════════
    # 1. MY INCOME
    # ════════════════════════════════════════
    settings_section("💰", "My Take-home", f"Your salary or income credited this month. Currently editing {month_label}.")

    current_income = api("GET", f"/income/{sel_month}") or {{}}
    saved_source   = current_income.get("source", "Infosys Salary")
    saved_amount   = int(current_income.get("amount", 0))
    saved_note     = current_income.get("note") or ""

    with st.form("income_form"):
        ic1, ic2 = st.columns([0.55, 0.45])
        with ic1:
            income_source = st.text_input("Where does it come from?", value=saved_source,
                placeholder="e.g. Infosys Salary, Freelance")
        with ic2:
            income_amount = st.number_input("How much was credited? (₹)", value=saved_amount, step=1000)
        income_note = st.text_input("Any note? (optional)", value=saved_note,
            placeholder="e.g. Includes bonus")
        if st.form_submit_button("💾 Save"):
            result = api("POST", "/income", json={"source": income_source, "amount": income_amount,
                                                   "note": income_note, "month_key": sel_month})
            if result:
                st.success(f"✅ Saved ₹{income_amount:,.0f} for {month_label}")
                st.rerun()

    # ════════════════════════════════════════
    # 2. MONTHLY BILLS
    # ════════════════════════════════════════
    settings_section("📋", "Monthly Bills",
        "Everything you pay every month. Fixed = same amount always. Variable Recurring = amount changes (like electric bill).")

    templates     = api("GET", "/fixed-templates") or []
    active_tmpls  = [t for t in templates if t["is_active"]]
    fixed_tmpls   = [t for t in active_tmpls if t.get("template_type", "fixed") == "fixed"]
    pool_tmpls    = [t for t in active_tmpls if t.get("template_type", "fixed") == "pool"]

    # ── Fixed bills (same every month) ────────────────────────────────────
    if fixed_tmpls:
        total_fixed = sum(t["amount"] for t in fixed_tmpls)
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <span style="color:{T['text']};font-size:0.88rem;font-weight:600;">Same amount every month</span>
            <span style="color:{T['sub']};font-size:0.8rem;">₹{total_fixed:,.0f}/month total</span>
        </div>
        """, unsafe_allow_html=True)

        tmpl_by_cat = defaultdict(list)
        for t in fixed_tmpls:
            tmpl_by_cat[t["category"]].append(t)

        for cat, items in sorted(tmpl_by_cat.items()):
            icon = CATEGORY_ICONS.get(cat, "📦")
            with st.expander(f"{icon} {cat} ({len(items)} bills)", expanded=False):
                for t in items:
                    row1, row2, row3, row4 = st.columns([0.38, 0.22, 0.2, 0.2])
                    with row1:
                        new_name = st.text_input("Bill name", value=t["name"],
                            key=f"tname_{t['id']}", label_visibility="collapsed")
                    with row2:
                        new_amt = st.number_input("Monthly amount (₹)", value=int(t["amount"]),
                            step=100, key=f"tamt_{t['id']}", label_visibility="collapsed")
                    with row3:
                        # Due day as a friendly dropdown
                        due_options = [0] + list(range(1, 32))
                        due_val = int(t.get("due_day") or 0)
                        new_due = st.selectbox(
                            "Remind me on",
                            due_options,
                            index=due_options.index(due_val) if due_val in due_options else 0,
                            format_func=lambda x: "No reminder" if x == 0 else f"{x}th of month",
                            key=f"tdue_{t['id']}", label_visibility="collapsed"
                        )
                    with row4:
                        bcol1, bcol2 = st.columns(2)
                        with bcol1:
                            if st.button("💾", key=f"tsave_{t['id']}", help="Save changes"):
                                api("PUT", f"/fixed-templates/{t['id']}", json={
                                    "name": new_name, "amount": new_amt,
                                    "due_day": new_due if new_due > 0 else None
                                })
                                st.toast(f"✅ Saved {new_name}")
                                st.rerun()
                        with bcol2:
                            if st.button("🗑️", key=f"tdel_{t['id']}", help="Remove this bill"):
                                api("DELETE", f"/fixed-templates/{t['id']}")
                                st.rerun()

    # ── Variable recurring bills (amount changes each month) ──────────────
    if pool_tmpls:
        st.markdown(f'<div style="color:{T["text"]};font-size:0.88rem;font-weight:600;margin:14px 0 8px;">Amount changes each month (Electric Bill, Recharge etc.)</div>', unsafe_allow_html=True)
        for t in pool_tmpls:
            icon = CATEGORY_ICONS.get(t["category"], "📦")
            pc1, pc2 = st.columns([0.75, 0.25])
            with pc1:
                st.markdown(f"""
                <div style="background:{T['card2']};border-radius:10px;padding:12px 14px;
                    border:1px solid {T['border']};">
                    <span style="color:{T['text']};font-size:0.88rem;font-weight:600;">{icon} {t['name']}</span>
                    <span style="color:{T['sub']};font-size:0.78rem;margin-left:8px;">{t['category']} · Add payments in Fixed tab each month</span>
                </div>
                """, unsafe_allow_html=True)
            with pc2:
                if st.button("🗑️ Remove", key=f"ptdel_{t['id']}"):
                    api("DELETE", f"/fixed-templates/{t['id']}")
                    st.rerun()

    # ── Add new bill ───────────────────────────────────────────────────────
    with st.expander("➕ Add a new bill", expanded=False):
        with st.form("add_bill_form", clear_on_submit=True):
            st.markdown(f'<div style="color:{T["sub"]};font-size:0.82rem;margin-bottom:12px;">Tell us about a bill you pay every month.</div>', unsafe_allow_html=True)

            b1, b2 = st.columns(2)
            with b1:
                new_tname = st.text_input("What do you call it?",
                    placeholder="e.g. Rent, Car Loan, Netflix")
            with b2:
                new_tcat = st.selectbox("What type of expense is it?", FIXED_CATEGORIES,
                    format_func=lambda x: f"{CATEGORY_ICONS.get(x, '📦')} {x}")

            b3, b4 = st.columns(2)
            with b3:
                bill_kind = st.radio(
                    "Is the amount the same every month?",
                    ["Yes, always the same", "No, it varies"],
                    help="Choose 'varies' for bills like electricity, mobile recharge"
                )
            with b4:
                new_tamt = st.number_input(
                    "How much? (₹)" if bill_kind == "Yes, always the same" else "Typical amount (₹, or 0 if unknown)",
                    min_value=0, step=100
                )

            if st.form_submit_button("➕ Add Bill"):
                if new_tname:
                    ttype = "fixed" if bill_kind == "Yes, always the same" else "pool"
                    if ttype == "fixed" and new_tamt == 0:
                        st.warning("Please enter the monthly amount for fixed bills.")
                    else:
                        api("POST", "/fixed-templates", json={
                            "name": new_tname, "category": new_tcat,
                            "amount": new_tamt, "template_type": ttype
                        })
                        kind_label = "bill" if ttype == "fixed" else "variable recurring bill"
                        st.success(f"✅ Added {new_tname} as a {kind_label}")
                        st.rerun()
                else:
                    st.warning("Please enter a name for the bill.")

    # ════════════════════════════════════════
    # 3. SPENDING CAPS
    # ════════════════════════════════════════
    settings_section("🎯", "Spending Caps",
        "Set a monthly limit for each type of discretionary expense. You'll get a warning when you're close.")

    budgets = api("GET", "/budgets") or []
    # Get current month spend for context
    cat_spent = {}
    if summary:
        for c in summary.get("categories", []):
            cat_spent[c["category"]] = c["spent"]

    if budgets:
        with st.form("update_budgets"):
            updated = {}
            cols = st.columns(2)
            for i, bl in enumerate(budgets):
                with cols[i % 2]:
                    icon    = CATEGORY_ICONS.get(bl["category"], "📦")
                    spent   = cat_spent.get(bl["category"], 0)
                    limit   = int(bl["limit_amount"])
                    pct     = round(spent / limit * 100) if limit > 0 else 0
                    bar_col = "#ef4444" if pct >= 100 else "#f59e0b" if pct >= 80 else "#34d399"
                    # Show context: spent vs current limit
                    st.markdown(f"""
                    <div style="margin-bottom:4px;display:flex;justify-content:space-between;">
                        <span style="color:{T['text']};font-size:0.85rem;">{icon} {bl['category']}</span>
                        <span style="color:{bar_col};font-size:0.78rem;">₹{spent:,.0f} spent this month</span>
                    </div>
                    """, unsafe_allow_html=True)
                    new_val = st.number_input(
                        f"Monthly cap for {bl['category']} (₹)",
                        value=limit, step=500,
                        key=f"budget_{bl['category']}",
                        label_visibility="collapsed"
                    )
                    updated[bl["category"]] = new_val

            if st.form_submit_button("💾 Save Spending Caps"):
                for cat, lim in updated.items():
                    api("PUT", "/budget", json={"category": cat, "limit_amount": lim})
                st.success("✅ Spending caps updated!")
                st.rerun()

    # ════════════════════════════════════════
    # 4. SAVED SHORTCUTS
    # ════════════════════════════════════════
    settings_section("⚡", "Saved Shortcuts",
        "Expenses you log frequently. These appear as one-tap buttons in Quick Add.")

    fav_tmpls = api("GET", "/expense-templates") or []
    if fav_tmpls:
        for t in fav_tmpls:
            icon = CATEGORY_ICONS.get(t["category"], "📦")
            fc1, fc2, fc3, fc4, fc5 = st.columns([0.3, 0.2, 0.18, 0.17, 0.15])
            with fc1:
                fn = st.text_input("Name", value=t["name"], key=f"fn_{t['id']}", label_visibility="collapsed")
            with fc2:
                fc = st.selectbox("Category", VAR_CATEGORIES,
                    index=VAR_CATEGORIES.index(t["category"]) if t["category"] in VAR_CATEGORIES else 0,
                    key=f"fc_{t['id']}", label_visibility="collapsed",
                    format_func=lambda x: f"{CATEGORY_ICONS.get(x,'📦')} {x}")
            with fc3:
                fa = st.number_input("₹", value=int(t["amount"]), step=50, key=f"fa_{t['id']}", label_visibility="collapsed")
            with fc4:
                if st.button("💾 Save", key=f"fsave_{t['id']}"):
                    api("PUT", f"/expense-templates/{t['id']}", json={"name": fn, "category": fc, "amount": fa, "vendor": fn})
                    st.toast(f"✅ Saved {fn}")
                    st.rerun()
            with fc5:
                if st.button("🗑️", key=f"fdel_{t['id']}"):
                    api("DELETE", f"/expense-templates/{t['id']}")
                    st.rerun()

        st.markdown(f'<div style="color:{T["sub"]};font-size:0.78rem;margin-top:4px;margin-bottom:16px;">{len(fav_tmpls)} shortcut(s) · sorted by most used</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="color:{T["muted"]};font-size:0.85rem;padding:12px 0;">No shortcuts yet. Add one below.</div>', unsafe_allow_html=True)

    with st.form("add_shortcut_form", clear_on_submit=True):
        sf1, sf2, sf3 = st.columns([0.38, 0.27, 0.35])
        with sf1:
            fav_name = st.text_input("What do you usually buy?", placeholder="e.g. Petrol, Cook extra")
        with sf2:
            fav_amt  = st.number_input("Usual amount (₹)", min_value=0, step=50)
        with sf3:
            fav_cat  = st.selectbox("Category", VAR_CATEGORIES,
                format_func=lambda x: f"{CATEGORY_ICONS.get(x,'📦')} {x}")
        if st.form_submit_button("➕ Add Shortcut"):
            if fav_name and fav_amt > 0:
                api("POST", "/expense-templates", json={"name": fav_name, "vendor": fav_name,
                    "category": fav_cat, "amount": fav_amt})
                st.success(f"✅ Added shortcut for {fav_name}")
                st.rerun()
            else:
                st.warning("Please fill in both name and amount.")
