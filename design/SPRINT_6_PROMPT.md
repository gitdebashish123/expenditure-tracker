# SpendSense — Sprint 6 Implementation Prompt
## Onboarding & Multi-user Polish

Reference: `design/MULTI_USER_ROADMAP.md` -> Sprint 6

---

## Context

Sprints 1-5 and Track 0 UI Quick Wins are complete. SpendSense is live on Railway
with rate limiting, input validation, and security headers in place.

Sprint 6 makes SpendSense ready for a small group of trusted users by adding:
- A guided first-time setup wizard (so new users are not lost on an empty dashboard)
- A basic admin panel (so you can manage users without touching the database)
- Automated user acceptance testing

**Project root:** `/Users/debashish/Desktop/ai-projects/expenditure-tracker`
**Backend:** `backend/main.py` (FastAPI) + `backend/models.py` (SQLModel)
**Frontend:** `frontend/app.py` (Streamlit, ~1,600 lines)
**Python:** 3.13, package manager: `uv`
**Live URL:** `https://frontend-production-22a3.up.railway.app`

**Git workflow for this sprint:**
```bash
git checkout develop
git checkout -b feature/sprint6-onboarding
# implement all 4 commits
git checkout develop
git merge feature/sprint6-onboarding --no-ff -m "feat: Sprint 6 - Onboarding & Multi-user Polish"
git push
# When ready for production:
git checkout main
git merge develop --no-ff -m "release: Sprint 6"
git push origin main
git checkout develop
```

---

## Commit 6.1 — Registration Flow Polish

**Goal:** Registration feels intentional and secure.

### Step 1 — Add `import re` to `frontend/app.py` imports

```python
import re
```

### Step 2 — Password strength indicator in register form

In `show_login_page()`, in the register form section, move `reg_email` and
`reg_password` **outside** the `st.form()` block so Streamlit re-renders them
on every keystroke. Place the strength bar immediately after `reg_password`.
Only `reg_confirm` and the submit button remain inside `st.form()`.

```python
# Outside the form — re-renders on every keystroke
reg_email    = st.text_input("Email", placeholder="your@email.com",
                             label_visibility="collapsed", key="reg_email")
reg_password = st.text_input("Password (min 8 characters)", placeholder="Password",
                             type="password",
                             label_visibility="collapsed", key="reg_password")

# Live password strength bar — updates on every keystroke
if reg_password:
    checks = [
        len(reg_password) >= 8,
        any(c.isupper() for c in reg_password),
        any(c.isdigit() for c in reg_password),
        any(c in "!@#$%^&*" for c in reg_password),
    ]
    score = sum(checks)
    colours = ["#ef4444", "#f97316", "#eab308", "#22c55e"]
    labels  = ["Weak", "Fair", "Good", "Strong"]
    colour  = colours[score - 1] if score > 0 else "#374151"
    label   = labels[score - 1]  if score > 0 else ""
    st.markdown(
        f'<div style="height:4px;border-radius:2px;background:{colour};'
        f'width:{score * 25}%;margin-top:4px;"></div>'
        f'<div style="font-size:0.75rem;color:{colour};margin-top:2px;">{label}</div>',
        unsafe_allow_html=True,
    )

# Only confirm + submit live inside the form
with st.form("register_form"):
    reg_confirm  = st.text_input("Confirm Password", placeholder="Confirm Password",
                                 type="password",
                                 label_visibility="collapsed", key="reg_confirm")
    reg_submitted = st.form_submit_button("Create Account", use_container_width=True)
```

**Note:** Moving `reg_email` and `reg_password` outside the form enables the
strength bar to update live on every keystroke. The form only wraps
`reg_confirm` and the submit button — this prevents accidental double-submit
while keeping the Enter key working. `st.session_state.reg_email` and
`st.session_state.reg_password` are read directly in the `if reg_submitted:`
block (Streamlit persists widget state by key).

### Step 3 — Client-side email validation in register form

In the `if reg_submitted:` block, before the existing `len(reg_password) < 8` check,
add:

```python
elif not re.match(r"^[^@]+@[^@]+\.[^@]+$", reg_email):
    st.session_state.auth_error = "Please enter a valid email address."
    st.rerun()
```

### Verification — Commit 6.1

```bash
# Open http://localhost:8501 -> Create an account
# Submit with email "notanemail" -> expect validation error, no API call made
# Submit with valid email and short password "abc" -> expect backend 422 error
# Register with valid email and strong password -> expect green success banner
```

---

## Commit 6.2 — First-time Setup Wizard

**Goal:** New users are guided through income, bills and spending caps in 3 steps.
Currently new users land on an empty dashboard with no guidance.

### Step 1 — Add `onboarding_complete` to User model in `backend/models.py`

Add one field to the `User` class after `last_login`:

```python
onboarding_complete: bool = Field(default=False)  # True after wizard is dismissed
```

### Step 2 — Add migration to `migrate_schema.py`

In the Step 2 migrations list, add:

```python
("user", "onboarding_complete", "INTEGER NOT NULL DEFAULT 0"),
```

### Step 3 — Update UserResponse in `backend/main.py`

```python
class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]
    onboarding_complete: bool = False
```

Update both `get_me()` and `register()` endpoints to pass `onboarding_complete`
when constructing `UserResponse(...)`:

```python
return UserResponse(
    id=user.id, email=user.email, is_active=user.is_active,
    is_admin=user.is_admin, created_at=user.created_at,
    last_login=user.last_login,
    onboarding_complete=user.onboarding_complete,
)
```

### Step 4 — Add `POST /auth/complete-onboarding` to `backend/main.py`

Add after `GET /auth/me`:

```python
@app.post("/auth/complete-onboarding")
def complete_onboarding(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Mark onboarding as complete for the authenticated user."""
    current_user.onboarding_complete = True
    session.add(current_user)
    session.commit()
    return {"message": "Onboarding complete"}
```

### Step 5 — Session state additions in `frontend/app.py`

Add to the Auth Session State initialisation block:

```python
if "onboarding_complete" not in st.session_state:
    st.session_state.onboarding_complete = True  # default True avoids wizard for existing users
if "onboarding_step" not in st.session_state:
    st.session_state.onboarding_step = 1
```

Update the token validation block to sync `onboarding_complete` from server:

```python
if me and st.session_state.user_email is None:
    st.session_state.user_email          = me.get("email")
    st.session_state.user_is_admin       = me.get("is_admin", False)
    st.session_state.onboarding_complete = me.get("onboarding_complete", True)
```

Also update the login success block in `show_login_page()` to capture
`onboarding_complete` from the `/auth/me` response after login:

```python
st.session_state.onboarding_complete = me.get("onboarding_complete", True)
```

Add the wizard gate after the token validation block, before `all_months`:

```python
# -- Onboarding gate ----------------------------------------------------------
if not st.session_state.get("onboarding_complete", True):
    show_onboarding_wizard()
    st.stop()
```

### Step 6 — Implement `show_onboarding_wizard()` in `frontend/app.py`

Add before the `# -- Helpers` section.

**Full implementation:**

```python
# -- Onboarding Wizard --------------------------------------------------------
def show_onboarding_wizard():
    """
    First-time setup wizard shown to new users after registration.
    3 steps: income -> fixed bills -> spending caps.
    Each step can be skipped. Dismissed via Skip All or completing step 3.
    """
    _, col, _ = st.columns([1, 3, 1])
    with col:
        step = st.session_state.get("onboarding_step", 1)

        # Header
        st.markdown(
            f"<div style='text-align:center;margin-bottom:24px;'>"
            f"<div style='font-size:2rem;'>&#128640;</div>"
            f"<div style='font-size:1.3rem;font-weight:700;color:{T['text']};margin:8px 0 4px;'>"
            f"Welcome to SpendSense!</div>"
            f"<div style='color:{T['sub']};font-size:0.85rem;'>"
            f"Let's set up your account in 3 quick steps.</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Progress bar
        bar_html = "".join([
            f"<div style='flex:1;height:4px;border-radius:2px;"
            f"background:{'#6366f1' if i < step else T['border']}'></div>"
            for i in range(1, 4)
        ])
        st.markdown(
            f"<div style='display:flex;gap:8px;margin-bottom:28px;'>{bar_html}</div>",
            unsafe_allow_html=True,
        )

        # ----- Step 1: Income -----
        if step == 1:
            st.markdown(
                f"<div style='font-weight:600;color:{T['text']};margin-bottom:8px;'>"
                f"&#128176; Step 1 of 3 &mdash; Your Monthly Take-home</div>",
                unsafe_allow_html=True,
            )
            st.caption("What's your salary or take-home income this month?")
            with st.form("onboard_income"):
                amt  = st.number_input("Amount", min_value=0.0, step=1000.0, value=0.0)
                note = st.text_input("Note (optional)", placeholder="e.g. June salary")
                c1, c2 = st.columns(2)
                with c1: submitted = st.form_submit_button("Save & Continue", use_container_width=True)
                with c2: skipped   = st.form_submit_button("Skip", use_container_width=True)
            if submitted and amt > 0:
                api("POST", "/income", json={"source": "Salary", "amount": amt,
                                             "note": note or None})
                st.session_state.onboarding_step = 2
                st.rerun()
            elif submitted or skipped:
                st.session_state.onboarding_step = 2
                st.rerun()

        # ----- Step 2: Bills -----
        elif step == 2:
            st.markdown(
                f"<div style='font-weight:600;color:{T['text']};margin-bottom:8px;'>"
                f"&#128203; Step 2 of 3 &mdash; Your Monthly Bills</div>",
                unsafe_allow_html=True,
            )
            st.caption("Add rent, EMI, subscriptions. You can add more later in Settings.")
            templates = api("GET", "/fixed-templates") or []
            if templates:
                st.caption(f"{len(templates)} bill(s) already configured.")
            with st.form("onboard_bill"):
                name = st.text_input("Bill name", placeholder="e.g. Rent, Jio, Netflix")
                cat  = st.selectbox("Category", FIXED_CATEGORIES)
                amt  = st.number_input("Amount", min_value=0.0, step=100.0)
                c1, c2, c3 = st.columns(3)
                with c1: add_more  = st.form_submit_button("Add Bill", use_container_width=True)
                with c2: nxt       = st.form_submit_button("Done & Continue", use_container_width=True)
                with c3: skipped   = st.form_submit_button("Skip", use_container_width=True)
            if add_more and name and amt > 0:
                api("POST", "/fixed-templates",
                    json={"name": name, "category": cat, "amount": amt})
                st.toast(f"Added {name}", icon="&#128203;")
                st.rerun()
            elif nxt or skipped:
                st.session_state.onboarding_step = 3
                st.rerun()

        # ----- Step 3: Spending caps -----
        elif step == 3:
            st.markdown(
                f"<div style='font-weight:600;color:{T['text']};margin-bottom:8px;'>"
                f"&#127919; Step 3 of 3 &mdash; Spending Caps</div>",
                unsafe_allow_html=True,
            )
            st.caption("Set monthly limits for variable spending. Adjust anytime in Settings.")
            defaults = {"Food": 5000, "Groceries": 8000, "Travel": 3000,
                        "Shopping": 3000, "Entertainment": 2000, "Medical": 2000}
            with st.form("onboard_caps"):
                caps = {}
                for cat, dflt in defaults.items():
                    caps[cat] = st.number_input(
                        f"{CATEGORY_ICONS.get(cat, '')} {cat}",
                        min_value=0.0, step=500.0, value=float(dflt),
                    )
                c1, c2 = st.columns(2)
                with c1: finished = st.form_submit_button("&#127680; Let's Go!", use_container_width=True)
                with c2: skipped  = st.form_submit_button("Skip", use_container_width=True)
            if finished:
                for cat, lim in caps.items():
                    if lim > 0:
                        api("PUT", "/budget", json={"category": cat, "limit_amount": lim})
                api("POST", "/auth/complete-onboarding")
                st.session_state.onboarding_complete = True
                st.session_state.onboarding_step     = 1
                st.toast("You're all set! Welcome to SpendSense.", icon="&#127881;")
                st.rerun()
            elif skipped:
                api("POST", "/auth/complete-onboarding")
                st.session_state.onboarding_complete = True
                st.session_state.onboarding_step     = 1
                st.rerun()

        # Skip all
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if st.button("Skip setup, go straight to the app",
                     use_container_width=True, key="skip_all_wizard"):
            api("POST", "/auth/complete-onboarding")
            st.session_state.onboarding_complete = True
            st.session_state.onboarding_step     = 1
            st.rerun()
```

### Fix for existing users after migration

```bash
sqlite3 data/expenses.db "UPDATE user SET onboarding_complete=1;"
# Then restart the backend
```

For Railway production, run via Railway shell before deploying.

### Verification — Commit 6.2

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"wizard@test.com","password":"testpass123"}'

TEST_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"wizard@test.com","password":"testpass123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $TEST_TOKEN" http://localhost:8000/auth/me
# expect: "onboarding_complete": false

curl -X POST http://localhost:8000/auth/complete-onboarding \
  -H "Authorization: Bearer $TEST_TOKEN"
# expect: {"message": "Onboarding complete"}

curl -H "Authorization: Bearer $TEST_TOKEN" http://localhost:8000/auth/me
# expect: "onboarding_complete": true

# UI: login as wizard@test.com
# expect: wizard appears on first login
# expect: Skip All goes directly to main app
# expect: wizard does NOT appear on next login
```

---

## Commit 6.3 — Admin Panel (Basic)

**Goal:** View and manage users without needing direct database access.

### Step 1 — Add `func` to sqlmodel import in `backend/main.py`

```python
from sqlmodel import Session, select, func
```

### Step 2 — Add `get_admin_user` dependency in `backend/main.py`

Add after the auth endpoints section:

```python
# -- Admin dependency ---------------------------------------------------------
def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Requires is_admin=True. Returns 403 for non-admin users."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

### Step 3 — Add admin endpoints in `backend/main.py`

Add at the end of the file, before the Pool Entries section:

```python
# -- Admin Endpoints ----------------------------------------------------------

@app.get("/admin/stats")
def admin_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user),
):
    """Overall system stats. Admin only."""
    total_users    = session.exec(select(func.count(User.id))).one()
    active_users   = session.exec(
        select(func.count(User.id)).where(User.is_active == True)
    ).one()
    total_expenses = session.exec(select(func.count(Expense.id))).one()
    return {"total_users": total_users, "active_users": active_users,
            "total_expenses": total_expenses}


@app.get("/admin/users")
def admin_list_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user),
):
    """List all users with stats. Admin only."""
    users = session.exec(select(User).order_by(User.created_at.desc())).all()
    result = []
    for user in users:
        expense_count = session.exec(
            select(func.count(Expense.id)).where(Expense.user_id == user.id)
        ).one()
        result.append({
            "id": user.id, "email": user.email,
            "is_active": user.is_active, "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "onboarding_complete": user.onboarding_complete,
            "expense_count": expense_count,
        })
    return result


@app.patch("/admin/users/{user_id}/toggle-active")
def admin_toggle_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_admin_user),
):
    """Enable or disable a user account. Admin only. Cannot disable own account."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot disable your own account")
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    session.add(user)
    session.commit()
    return {"id": user.id, "email": user.email, "is_active": user.is_active}
```

### Step 4 — Add Admin tab to `frontend/app.py`

Find the current `st.tabs([...])` call and replace with conditional version.
The existing 5 tab labels must be preserved exactly. Add `"🛡️ Admin"` as the 6th
only for admin users:

```python
_tab_labels = ["tab1", "tab2", "tab3", "tab4", "tab5"]  # use actual existing labels
if st.session_state.user_is_admin:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(_tab_labels + ["🛡️ Admin"])
else:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(_tab_labels)
    tab6 = None
```

Add admin tab content after the `with tab5:` block:

```python
if tab6:
    with tab6:
        settings_section("🛡️", "Admin Panel",
                         "User management and system overview. Visible to admins only.")

        # Stats
        stats = api("GET", "/admin/stats") or {}
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Users",    stats.get("total_users", 0))
        c2.metric("Active Users",   stats.get("active_users", 0))
        c3.metric("Total Expenses", stats.get("total_expenses", 0))

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # User list
        users = api("GET", "/admin/users") or []
        for user in users:
            c_email, c_status, c_login, c_btn = st.columns([3, 1, 2, 1])
            with c_email:
                icon = "👑" if user["is_admin"] else ("🔒" if not user["is_active"] else "👤")
                st.markdown(f"{icon} **{user['email']}**")
            with c_status:
                st.markdown("🟢 Active" if user["is_active"] else "🔴 Disabled")
            with c_login:
                last = user.get("last_login")
                st.markdown(fmt_date(last[:10]) if last else "Never")
            with c_btn:
                if not user["is_admin"]:
                    lbl = "Disable" if user["is_active"] else "Enable"
                    if st.button(lbl, key=f"toggle_{user['id']}",
                                 use_container_width=True):
                        api("PATCH", f"/admin/users/{user['id']}/toggle-active")
                        st.rerun()
```

### Verification — Commit 6.3

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@spendsense.local","password":"changeme123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/stats
# expect: {"total_users":N,"active_users":N,"total_expenses":N}

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/users
# expect: list with expense_count per user

# Non-admin gets 403
curl -H "Authorization: Bearer $NON_ADMIN_TOKEN" http://localhost:8000/admin/users
# expect: 403 {"detail": "Admin access required"}

# UI: login as admin -> expect Shield tab visible
# expect: stats cards, user list with Disable buttons
# expect: admin row shows crown icon, no action button
```

---

## Commit 6.4 — User Acceptance Testing

**Goal:** Automated end-to-end verification before sharing with external users.

### Create `scripts/uat_test.py`

```bash
mkdir -p /Users/debashish/Desktop/ai-projects/expenditure-tracker/scripts
```

The script registers 2 test users, runs 10 test groups, cleans up on completion.
T4 (data isolation) is the most critical test.

```python
"""
User Acceptance Test for SpendSense.
Usage:
  uv run python3 scripts/uat_test.py
  uv run python3 scripts/uat_test.py --url https://YOUR-BACKEND.up.railway.app
"""
import requests, sys, random, string
from datetime import date

BASE = sys.argv[sys.argv.index("--url") + 1] if "--url" in sys.argv else "http://localhost:8000"
PASS = True

def ok(msg):           print(f"  PASS: {msg}")
def fail(msg, d=""): global PASS; PASS = False; print(f"  FAIL: {msg} {d}")
def rand_email():     return "uat_" + "".join(random.choices(string.ascii_lowercase, k=8)) + "@test.com"
def get_token(e, pw): r = requests.post(f"{BASE}/auth/login", json={"email":e,"password":pw}); return r.json().get("access_token") if r.ok else None
def H(tok):           return {"Authorization": f"Bearer {tok}"}

print(f"\nRunning UAT against {BASE}\n")

# T1 Health
print("T1: Health")
ok("health 200") if requests.get(f"{BASE}/health").ok else fail("health")

# T2 Registration
print("T2: Registration")
e1, e2 = rand_email(), rand_email()
ok("register user1") if requests.post(f"{BASE}/auth/register", json={"email":e1,"password":"Pass123!"}).status_code == 201 else fail("register user1")
ok("register user2") if requests.post(f"{BASE}/auth/register", json={"email":e2,"password":"Pass123!"}).status_code == 201 else fail("register user2")
ok("duplicate rejected") if requests.post(f"{BASE}/auth/register", json={"email":e1,"password":"Pass123!"}).status_code == 400 else fail("duplicate email")

# T3 Login
print("T3: Login")
t1, t2 = get_token(e1, "Pass123!"), get_token(e2, "Pass123!")
ok("user1 login") if t1 else fail("user1 login")
ok("user2 login") if t2 else fail("user2 login")
ok("wrong password 401") if requests.post(f"{BASE}/auth/login", json={"email":e1,"password":"wrong"}).status_code == 401 else fail("wrong pw")

# T4 Data isolation
print("T4: Data isolation")
requests.post(f"{BASE}/expenses/manual", headers=H(t1),
              json={"vendor":"IsolationTest","amount":99,"category":"Food"})
month  = date.today().strftime("%Y-%m")
exps1  = [e["vendor"] for e in requests.get(f"{BASE}/expenses/{month}", headers=H(t1)).json()]
exps2  = [e["vendor"] for e in requests.get(f"{BASE}/expenses/{month}", headers=H(t2)).json()]
ok("user1 sees own expense")        if "IsolationTest" in exps1     else fail("user1 data missing")
ok("user2 cannot see user1 expense") if "IsolationTest" not in exps2 else fail("DATA ISOLATION BREACH")

# T5 AI parsing
print("T5: AI parsing")
ok("parse") if requests.post(f"{BASE}/expenses/parse", headers=H(t1), json={"text":"coffee 120"}).ok else fail("parse")

# T6 Input validation
print("T6: Validation")
ok("negative amount rejected") if requests.post(f"{BASE}/expenses/manual", headers=H(t1), json={"vendor":"X","amount":-1,"category":"Food"}).status_code == 422 else fail("negative amount")
ok("vendor too long rejected") if requests.post(f"{BASE}/expenses/manual", headers=H(t1), json={"vendor":"A"*101,"amount":1,"category":"Food"}).status_code == 422 else fail("vendor length")

# T7 CSV export
print("T7: CSV export")
r = requests.get(f"{BASE}/export/csv/all", headers=H(t1))
ok("csv export") if r.ok and "text/csv" in r.headers.get("content-type","") else fail("csv", r.status_code)

# T8 Onboarding
print("T8: Onboarding")
me = requests.get(f"{BASE}/auth/me", headers=H(t1)).json()
ok("onboarding_complete field present") if "onboarding_complete" in me else fail("field missing")
ok("complete-onboarding") if requests.post(f"{BASE}/auth/complete-onboarding", headers=H(t1)).ok else fail("complete-onboarding")

# T9 Security headers
print("T9: Security headers")
hdrs = requests.get(f"{BASE}/health").headers
for h in ["x-content-type-options", "x-frame-options", "strict-transport-security"]:
    ok(h) if h in hdrs else fail(f"missing {h}")

# T10 Cleanup
print("T10: Cleanup")
for tok in [t1, t2]:
    if tok:
        requests.delete(f"{BASE}/auth/account", headers=H(tok), json={"confirmation":"DELETE"})
ok("test users deleted")

print(f"\n{'ALL TESTS PASSED' if PASS else 'SOME TESTS FAILED'}\n")
sys.exit(0 if PASS else 1)
```

### Verification — Commit 6.4

```bash
uv run python3 scripts/uat_test.py
# expect: ALL TESTS PASSED

uv run python3 scripts/uat_test.py --url https://YOUR-BACKEND.up.railway.app
# expect: ALL TESTS PASSED
```

---

## Files Modified in Sprint 6

| File | Commit | Change |
|---|---|---|
| `frontend/app.py` | 6.1 | `import re`, password strength bar, email client-side validation |
| `backend/models.py` | 6.2 | Add `onboarding_complete` to User |
| `migrate_schema.py` | 6.2 | Add `user.onboarding_complete` migration |
| `backend/main.py` | 6.2 | `onboarding_complete` in UserResponse, `POST /auth/complete-onboarding` |
| `frontend/app.py` | 6.2 | Session state, wizard gate, `show_onboarding_wizard()` |
| `backend/main.py` | 6.3 | `func` import, `get_admin_user`, 3 admin endpoints |
| `frontend/app.py` | 6.3 | Admin 6th tab, conditional on `user_is_admin` |
| `scripts/uat_test.py` | 6.4 | New file — automated UAT |

### Files NOT changed
- `backend/auth.py`, `backend/budget_rules.py`
- `docker-compose.yml`, `railway.toml`

---

## Common Pitfalls

| Issue | Cause | Fix |
|---|---|---|
| `onboarding_complete` AttributeError on startup | Column not in DB | Run `migrate_schema.py` then `UPDATE user SET onboarding_complete=1` for existing users |
| Wizard shows for existing users | Migration DEFAULT 0 | `sqlite3 data/expenses.db "UPDATE user SET onboarding_complete=1;"` |
| Admin tab visible to all | Tab always created | Wrap in `if st.session_state.user_is_admin:` |
| `func` ImportError | Not in sqlmodel import | `from sqlmodel import Session, select, func` |
| Wizard infinite loop | `complete-onboarding` API failing | Set `st.session_state.onboarding_complete = True` unconditionally before `st.rerun()` |
| Progress bar HTML broken | f-string quote conflict | Use single quotes for outer f-string, double quotes inside HTML attributes |

---

## Pre-Sprint 6 Checklist

- [ ] On `feature/sprint6-onboarding` branch
- [ ] Sprint 5 merged to develop and deployed to Railway
- [ ] Local backend runs: `uv run uvicorn backend.main:app --reload`
- [ ] Railway healthy: `curl https://YOUR-BACKEND.up.railway.app/health`
- [ ] Admin password changed from `changeme123` in Railway Variables

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Prompt ready — implement after Sprint 5 is deployed*
