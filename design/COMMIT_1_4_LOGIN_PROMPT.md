# SpendSense — Commit 1.4 Implementation Prompt
## Streamlit Login Screen

Reference: `design/MULTI_USER_ROADMAP.md` → Sprint 1, Commit 1.4

---

## Context

SpendSense is a personal expenditure tracker with:
- **Frontend**: Streamlit (`frontend/app.py`) — single file, ~900 lines
- **Backend**: FastAPI on port 8000, fully authenticated since Commit 1.3
- **Auth endpoints** (already implemented, public):
  - `POST /auth/login` — body: `{"email": "...", "password": "..."}` → returns `{"access_token": "eyJ...", "token_type": "bearer"}`
  - `POST /auth/register` — body: `{"email": "...", "password": "..."}` → returns user object, no token
  - `GET /auth/me` — header: `Authorization: Bearer <token>` → returns user profile
- **All other endpoints** return `401` without a valid Bearer token
- **Project root**: `/Users/debashish/Desktop/ai-projects/expenditure-tracker`
- **Package manager**: `uv` — always use `uv add`, never pip

### Why NOT streamlit-authenticator

Do **not** use the `streamlit-authenticator` library. It manages its own
credentials store separately from the User table in the database, making it
incompatible with the JWT auth system already built in Commit 1.3.

Instead, build a **custom login form** that calls the existing FastAPI
`/auth/login` endpoint and stores the returned JWT in `st.session_state`.

---

## Architecture Overview

```
app.py starts
     │
     ▼
Is st.session_state["token"] set AND valid?
     │
     ├── No ──► show_login_page()   ← only this renders
     │              │
     │              ├── Login form → POST /auth/login → store token
     │              └── Register form → POST /auth/register → prompt to log in
     │
     └── Yes ─► show_main_app()    ← existing dashboard renders
                    │
                    └── all api() calls include Authorization: Bearer <token>
                        if any call returns 401 → clear token → rerun → login page
```

**Key principle:** The login page and the main app are mutually exclusive.
When `token` is missing or expired, only the login page renders.
When `token` is valid, only the main app renders. No mixing.

---

## Step 1 — Session State Design

At the top of `app.py`, define the session state keys used for auth:

```python
# Initialise auth session state — must happen before any api() call
if "token" not in st.session_state:
    st.session_state.token = None          # JWT string or None
if "user_email" not in st.session_state:
    st.session_state.user_email = None     # email of logged-in user
if "user_is_admin" not in st.session_state:
    st.session_state.user_is_admin = False
if "auth_error" not in st.session_state:
    st.session_state.auth_error = None     # error message to show on login form
if "show_register" not in st.session_state:
    st.session_state.show_register = False # toggle between login and register form
```

Do NOT initialise `theme` here — it is already initialised later. Keep the
existing theme initialisation block exactly where it is.

---

## Step 2 — Update the `api()` Helper

The existing `api()` function makes unauthenticated calls. It must be updated
to automatically include the Bearer token from session state on every request,
and handle 401 responses by clearing the token and forcing a rerun to the
login page.

Replace the existing `api()` function with:

```python
def api(method, path, **kwargs):
    """
    Make an authenticated API call.
    - Automatically adds Authorization: Bearer <token> header if token exists
    - On 401: clears token, sets auth_error, triggers rerun to login page
    - On connection error: shows backend-not-running message
    """
    headers = kwargs.pop("headers", {})
    if st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state.token}"

    try:
        r = requests.request(method, f"{API_BASE}{path}",
                             timeout=30, headers=headers, **kwargs)

        if r.status_code == 401:
            # Token expired or invalid — force back to login
            st.session_state.token = None
            st.session_state.user_email = None
            st.session_state.user_is_admin = False
            st.session_state.auth_error = "Your session has expired. Please log in again."
            st.rerun()

        r.raise_for_status()
        return r.json()

    except requests.exceptions.ConnectionError:
        st.error("⚠️ Backend not running. Start with: `uv run uvicorn backend.main:app --reload`")
        return None
    except requests.exceptions.HTTPError:
        # Non-401 HTTP errors (400, 403, 404, 422, 500) — return None silently
        # Callers handle missing data gracefully already
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None
```

**Important:** The existing `api()` call to `/months` at the top of the file
(used to populate the month selector) runs before the login check. This is
fine — it will return `None` if unauthenticated (401), and the login page
will render instead of the main app.

---

## Step 3 — Login Page Function

Create a standalone function `show_login_page()` that renders the entire
login/register UI. It must:

### Visual requirements
- Match the existing dark/light theme (use `T` dict and `is_dark` which are
  already computed before this function is called)
- Center a card on the page — max width 420px, centred with columns
- Show the SpendSense logo/title at the top of the card
- Clean, minimal — no tabs, no sidebar

### Login form requirements
- Email field (`st.text_input`) — type="default", placeholder "your@email.com"
- Password field (`st.text_input`) — `type="password"`, placeholder "Password"
- "Sign In" button — full width, uses existing `.stButton` gradient style
- On submit:
  1. Call `POST /auth/login` with `{"email": email, "password": password}`
     — use `requests.post` directly here (NOT the `api()` helper, which
     requires a token that doesn't exist yet)
  2. On success (200):
     - Store `st.session_state.token = response["access_token"]`
     - Call `GET /auth/me` with the new token to get user details
     - Store `st.session_state.user_email = user["email"]`
     - Store `st.session_state.user_is_admin = user["is_admin"]`
     - Clear `st.session_state.auth_error`
     - Call `st.rerun()` to re-render as authenticated main app
  3. On 401: set `st.session_state.auth_error = "Invalid email or password"`
  4. On connection error: set error message about backend not running
  5. On any other error: set a generic error message
- If `st.session_state.auth_error` is set, show it as a red error banner
  above the form (not inside it)

### Register form requirements
- Toggle between login and register with a text link below the form:
  - Login page: "Don't have an account? **Register**"
  - Register page: "Already have an account? **Sign In**"
  - Clicking toggles `st.session_state.show_register` and calls `st.rerun()`
- Register form fields:
  - Email (`st.text_input`)
  - Password (`st.text_input`, `type="password"`)
  - Confirm Password (`st.text_input`, `type="password"`)
- On submit:
  1. Validate passwords match — if not, show error inline, do not call API
  2. Validate password >= 8 characters — if not, show error inline
  3. Call `POST /auth/register` with `{"email": email, "password": password}`
     — use `requests.post` directly (not `api()`)
  4. On 201 success:
     - Show green success message: "Account created! Please sign in."
     - Switch back to login form: `st.session_state.show_register = False`
     - Call `st.rerun()`
  5. On 400 "Email already registered": show specific error message
  6. On other errors: show generic error

### Login page CSS additions
Add these CSS classes to the existing `<style>` block (do NOT replace the
existing CSS, only append):

```css
/* Login page */
.login-card {
    background: {T["card"]};
    border: 1px solid {T["border"]};
    border-radius: 20px;
    padding: 36px 32px;
}
.login-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: {T["text"]};
    margin-bottom: 4px;
    letter-spacing: -0.5px;
}
.login-subtitle {
    color: {T["sub"]};
    font-size: 0.85rem;
    margin-bottom: 24px;
}
.auth-error {
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.3);
    border-left: 4px solid #ef4444;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 16px;
    color: #fca5a5;
    font-size: 0.88rem;
}
.auth-success {
    background: rgba(52,211,153,0.12);
    border: 1px solid rgba(52,211,153,0.3);
    border-left: 4px solid #34d399;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 16px;
    color: #6ee7b7;
    font-size: 0.88rem;
}
```

---

## Step 4 — Logout Button in Header

The existing header uses three columns: `[3, 0.5, 1]` for title, theme toggle,
and month selector. Add a logout button between theme toggle and month selector.

Change the column layout to `[3, 0.5, 0.7, 1]` and add a logout column:

```python
col_title, col_theme, col_logout, col_month = st.columns([3, 0.5, 0.7, 1])
```

In `col_logout`:
```python
with col_logout:
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    # Show email initial and logout button
    email_initial = st.session_state.user_email[0].upper() \
        if st.session_state.user_email else "?"
    if st.button(f"👤 {email_initial}  Sign out", key="logout_btn",
                 help=f"Signed in as {st.session_state.user_email}"):
        st.session_state.token = None
        st.session_state.user_email = None
        st.session_state.user_is_admin = False
        st.session_state.auth_error = None
        st.rerun()
```

The button label shows the first letter of the user's email as an avatar
initial (e.g. "👤 D  Sign out" for debashish@...). On click, all auth state
is cleared and the app reruns to show the login page.

---

## Step 5 — Gate the Main App

Wrap the entire main app (everything after the CSS block and helper functions)
with an auth gate. The structure must be:

```python
# ── Auth Gate ──────────────────────────────────────────────────────────────
# Everything below this point requires authentication.
# show_login_page() renders instead if token is missing or expired.

if not st.session_state.get("token"):
    show_login_page()
    st.stop()   # critical — prevents the rest of the script from executing

# ── Authenticated: Main App ────────────────────────────────────────────────
# All code below only runs when the user is authenticated.

# ... existing header, summary, tabs etc. ...
```

`st.stop()` after `show_login_page()` is **critical** — without it, Streamlit
continues executing the rest of the script after the login page renders,
causing errors because `api()` calls will fail without a token.

---

## Step 6 — Token Validation on Load

When the app loads and a token already exists in session state (e.g. after a
browser refresh), validate it immediately by calling `/auth/me`. If it returns
401, the `api()` helper will automatically clear the token and rerun.

Add this immediately after the auth gate check:

```python
if st.session_state.get("token"):
    # Validate token is still valid on every page load
    # If expired, api() will clear token and rerun to login automatically
    me = api("GET", "/auth/me")
    if me and st.session_state.user_email is None:
        # Restore user info if session state was lost (e.g. after hot reload)
        st.session_state.user_email = me.get("email")
        st.session_state.user_is_admin = me.get("is_admin", False)
```

---

## Files Modified in This Commit

| File | Change |
|---|---|
| `frontend/app.py` | Login gate, `show_login_page()`, updated `api()`, logout button |

### Files NOT modified
- `backend/main.py` — no backend changes needed
- `backend/auth.py` — no changes needed
- `backend/models.py` — no changes needed
- Any config or `.env` files

---

## Structural Order in app.py After This Commit

The file must be structured in this exact order:

```
1. imports
2. API_BASE, CURRENT_MONTH, CATEGORY_ICONS, FIXED_CATEGORIES, VAR_CATEGORIES
3. Auth session state initialisation  ← NEW (Step 1)
4. Theme initialisation (existing)
5. st.set_page_config (existing)
6. CSS block — existing styles + new login CSS appended  ← UPDATED (Step 3)
7. api() helper — updated with token injection + 401 handling  ← UPDATED (Step 2)
8. bar_color(), fmt_month() helpers (existing)
9. show_login_page() function  ← NEW (Step 3)
10. Auth gate  ← NEW (Step 5)
    if not token: show_login_page(); st.stop()
11. Token validation on load  ← NEW (Step 6)
12. Month selector data load (existing api("/months") call)
13. Header columns — updated with logout button  ← UPDATED (Step 4)
14. Salary credit reminder (existing)
15. Summary API call (existing)
16. Balance cards (existing)
17. Tabs — all 5 tabs unchanged
18. Settings tab unchanged
```

---

## Verification Steps

### 8.1 — Login page shows when not authenticated
```bash
# Start the app fresh (clear browser storage / incognito)
open http://localhost:8501
# expect: Login form visible, NOT the dashboard
# expect: No 401 errors in terminal
```

### 8.2 — Login with wrong credentials shows error
```
Enter: wrong@email.com / wrongpassword
Click: Sign In
expect: Red error banner "Invalid email or password"
expect: Form stays on screen (no rerun to dashboard)
```

### 8.3 — Login with correct credentials opens dashboard
```
Enter: admin@spendsense.local / changeme123
Click: Sign In
expect: Dashboard loads immediately
expect: Header shows "👤 A  Sign out" button
expect: Month selector and theme toggle visible
```

### 8.4 — All API calls include Bearer token
```bash
# Check browser network tab or backend logs
# Every request to /months, /summary/*, etc. should include:
# Authorization: Bearer eyJ...
```

### 8.5 — Logout clears session and returns to login
```
Click: "👤 A  Sign out"
expect: Login page appears immediately
expect: Dashboard is NOT accessible
```

### 8.6 — Expired token redirects to login with message
```bash
# Temporarily set JWT_EXPIRE_MINUTES=0 in .env, restart backend
# Login, wait 1 minute, interact with the app
# expect: Redirect to login page with message "Your session has expired. Please log in again."
# Restore JWT_EXPIRE_MINUTES=480
```

### 8.7 — Register creates a new account
```
Click: "Don't have an account? Register"
Enter: newuser@example.com / newpassword123 / newpassword123
Click: Register
expect: "Account created! Please sign in." success message
expect: Form switches back to login
```

### 8.8 — Register with mismatched passwords shows inline error
```
Enter: user@example.com / pass1234 / differentpass
Click: Register
expect: Inline error "Passwords do not match" — no API call made
```

### 8.9 — Duplicate registration rejected
```
Register: admin@spendsense.local (already exists)
expect: "Email already registered" error message
```

### 8.10 — Browser refresh keeps session alive
```
Login, then press Cmd+R
expect: Dashboard reloads (not login page)
expect: Token still valid, /auth/me called silently to validate
```

### 8.11 — Backend not running shows friendly error on login
```bash
# Stop the backend
# Try to log in
# expect: "⚠️ Backend not running" error (not a crash)
```

---

## Do Not Change in This Commit

- All 5 tab contents — Quick Add, Fixed, Dashboard, Expenses, Settings
- The `api()` function signature — callers don't change, only internals update
- Theme system — dark/light toggle continues to work on the login page too
- The existing CSS — only append new login CSS, never replace existing styles
- `backend/` — zero backend changes in this commit

---

## Known Limitation (Resolved in Sprint 2)

After this commit, all authenticated users share the same data.
Logging in as any user shows all expenses in the database.
Sprint 2 adds `user_id` filtering to every query so each user
sees only their own data.

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Prompt ready — awaiting execution approval*
