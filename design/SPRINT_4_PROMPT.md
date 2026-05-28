# SpendSense — Sprint 4 Implementation Prompt
## User Trust & Transparency

Reference: `design/MULTI_USER_ROADMAP.md` → Sprint 4

---

## Context

Sprint 4 makes SpendSense safe and transparent to share with real users.
Three commits cover data export, account management, and a privacy notice.

**Current state entering Sprint 4:**
- Sprint 1 ✅ — Auth (JWT, login, register)
- Sprint 2 ✅ — Data isolation (`user_id` on all tables, all queries scoped)
- Sprint 3 ✅ — Docker + Railway deployment (live at `https://frontend-production-22a3.up.railway.app`)

**Stack:**
- Backend: FastAPI + SQLModel, `backend/main.py`
- Frontend: Streamlit, `frontend/app.py` (~1,100 lines, single file)
- Auth: JWT via `backend/auth.py`, `get_current_user` dependency on all protected endpoints
- Project root: `/Users/debashish/Desktop/ai-projects/expenditure-tracker`
- Package manager: `uv` — always use `uv add`, never pip

**Known existing endpoints (do not duplicate):**
- `GET /auth/me` — returns `UserResponse` (id, email, is_active, is_admin, created_at, last_login)
- All other endpoints protected with `Depends(get_current_user)`

---

## Commit 4.1 — Data Export

**Goal:** Users can download their own expense data as CSV at any time.

### Step 1 — Backend: Add Export Endpoints to `backend/main.py`

Add a `CSVResponse` import at the top of `main.py`:

```python
from fastapi.responses import StreamingResponse
import csv
import io
```

Add two new export endpoints — both protected with `Depends(get_current_user)`:

**Endpoint A — Export single month:**

```
GET /export/csv/{month_key}
Header: Authorization: Bearer <token>
Response: CSV file download
Filename: spendsense_{month_key}.csv
```

Requirements:
- Query all `Expense` rows for `month_key` where `user_id == current_user.id`
- Include both fixed and variable expenses
- CSV columns in this order:
  `date, vendor, category, amount, note, type, paid`
  where `type` = "fixed" or "variable"
- Sort by date ascending
- Return as `StreamingResponse` with `media_type="text/csv"` and
  `Content-Disposition: attachment; filename=spendsense_{month_key}.csv`
- If no expenses found for the month, return an empty CSV (header row only)

**Endpoint B — Export full history:**

```
GET /export/csv/all
Header: Authorization: Bearer <token>
Response: CSV file download
Filename: spendsense_all_{today_date}.csv
```

Requirements:
- Query ALL `Expense` rows where `user_id == current_user.id`
- Same CSV columns as above, plus a `month` column first
- Sort by date ascending
- Filename includes today's date: `spendsense_all_2026-05-28.csv`

**Important:** The route `GET /export/csv/all` must be defined **before**
`GET /export/csv/{month_key}` in `main.py` to avoid FastAPI treating "all"
as a `month_key` parameter value.

### Step 2 — Frontend: Add Download Buttons in Settings Tab

In `frontend/app.py`, add a new settings section at the **bottom** of the
Settings tab (Tab 5), after the "Saved Shortcuts" section:

```python
settings_section("📥", "My Data",
    "Download your expense history as a spreadsheet-compatible CSV file.")
```

Two download buttons:
1. **"⬇️ Download This Month"** — calls `GET /export/csv/{sel_month}`
2. **"⬇️ Download Full History"** — calls `GET /export/csv/all`

**Implementation note for Streamlit downloads:**
The `api()` helper returns JSON — it cannot handle file downloads. Use
`requests.get` directly with the token header for these two calls:

```python
r = requests.get(
    f"{API_BASE}/export/csv/{sel_month}",
    headers={"Authorization": f"Bearer {st.session_state.token}"},
    timeout=30,
)
if r.status_code == 200:
    st.download_button(
        label="⬇️ Download This Month",
        data=r.content,
        file_name=f"spendsense_{sel_month}.csv",
        mime="text/csv",
        key="dl_month",
    )
```

Repeat the same pattern for full history. Show both buttons side by side
using `st.columns([1, 1])`.

If the request fails, show a brief error message inline (not `st.error` which
interrupts the layout).

### Verification — Commit 4.1

```bash
# Export current month
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@spendsense.local","password":"changeme123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/export/csv/$(date +%Y-%m) \
  --output /tmp/test_export.csv
cat /tmp/test_export.csv
# expect: CSV with header row: date,vendor,category,amount,note,type,paid
# expect: rows for current month expenses only (not other users' data)

# Export full history
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/export/csv/all \
  --output /tmp/test_all.csv
cat /tmp/test_all.csv
# expect: CSV with header row including month column
# expect: all historical expenses for this user only

# Verify data isolation — another user should get different/empty data
```

---

## Commit 4.2 — Account Management

**Goal:** Users can change their password, see their last login, and delete
their account. All from the Settings tab.

### Step 1 — Backend: Add Account Management Endpoints to `backend/main.py`

**Add these Pydantic models** to the Request Models section:

```python
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class DeleteAccountRequest(BaseModel):
    confirmation: str   # must equal "DELETE" to proceed
```

**Add three new endpoints** — all protected with `Depends(get_current_user)`:

**Endpoint A — Change Password:**

```
PUT /auth/password
Header: Authorization: Bearer <token>
Body: {"current_password": "...", "new_password": "..."}
```

Requirements:
- Verify `current_password` against `current_user.hashed_password` using `verify_password()`
- If wrong: return `400 Bad Request` with `"Current password is incorrect"`
  (NOT 401 — the user is authenticated, just the old password is wrong)
- Validate `new_password` minimum 8 characters
- If new password same as current: return `400` with `"New password must be different"`
- Hash the new password with `hash_password()`
- Update `current_user.hashed_password` and commit
- Return `{"message": "Password updated successfully"}`
- Do NOT invalidate existing tokens — user stays logged in after password change

**Endpoint B — Delete Account:**

```
DELETE /auth/account
Header: Authorization: Bearer <token>
Body: {"confirmation": "DELETE"}
```

Requirements:
- Check `req.confirmation == "DELETE"` — if not, return `400` with
  `"Type DELETE to confirm account deletion"`
- Delete ALL data belonging to `current_user.id` in this order (cascade):
  1. `PoolEntry` where `user_id == current_user.id`
  2. `Expense` where `user_id == current_user.id`
  3. `IncomeEntry` where `user_id == current_user.id`
  4. `BudgetLimit` where `user_id == current_user.id`
  5. `ExpenseTemplate` where `user_id == current_user.id`
  6. `FixedExpenseTemplate` where `user_id == current_user.id`
  7. `User` record itself
- Commit once after all deletes
- Return `{"message": "Account deleted", "email": current_user.email}`
- The token is now invalid (user no longer exists) — frontend handles redirect

**Endpoint C — GET /auth/me is already implemented** — no change needed.
The `last_login` field is already in `UserResponse` and updated on every login.

### Step 2 — Frontend: Add Account Section to Settings Tab

Add a new settings section in the Settings tab (Tab 5), between
"My Data" (4.1) and the bottom of the tab:

```python
settings_section("👤", "My Account",
    f"Signed in as {st.session_state.user_email} · "
    f"Last login: {last_login_str}")
```

Where `last_login_str` is formatted from `me["last_login"]` — call
`api("GET", "/auth/me")` once at the top of the Settings tab block and
store the result as `account_info`. Format last_login as:
- Today: "Today at 14:32"
- Yesterday: "Yesterday at 09:15"
- Older: "28 May 2026 at 14:32"
- Never (None): "First login"

**Sub-section A — Change Password:**

Use an `st.expander("🔑 Change Password", expanded=False)` containing a form:

```
Form fields:
- Current Password (type="password")
- New Password (type="password", min 8 chars)
- Confirm New Password (type="password")

Validations (client-side before API call):
- New passwords must match
- New password must be at least 8 characters
- New password must differ from current (optional, caught by backend too)

On success:
- Show green success message: "✅ Password changed successfully"
- Clear the form (use clear_on_submit=True)

On error:
- Show red error with the backend's detail message
```

**Sub-section B — Last Login Display:**

Show a simple info line outside the expander:
```
🕐 Last login: {last_login_str}
   Sign in history is recorded for security — contact admin if you see unexpected logins.
```

**Sub-section C — Delete Account (Danger Zone):**

Use an `st.expander("⚠️ Danger Zone", expanded=False)` — render with a
red border to visually signal danger:

```python
st.markdown("""
<div style="border:1px solid rgba(239,68,68,0.3);border-radius:12px;padding:16px;
    background:rgba(239,68,68,0.05);">
""", unsafe_allow_html=True)
```

Inside the expander:
- Warning text: "This permanently deletes your account and ALL your data.
  Expenses, income entries, budget settings — everything. This cannot be undone."
- A `st.text_input` labelled 'Type "DELETE" to confirm'
- A red "Delete My Account" button (style it differently from normal buttons —
  add a CSS override for the specific key)
- On submit:
  1. Call `DELETE /auth/account` with `{"confirmation": confirmation_text}`
  2. On success (200):
     - Clear ALL session state: token, user_email, user_is_admin, auth_error
     - Set `st.session_state.auth_error = "Your account has been deleted."`
     - Call `st.rerun()` — auth gate will show login page with the message
  3. On 400: show the backend error inline

### Verification — Commit 4.2

```bash
# Test change password
curl -X PUT http://localhost:8000/auth/password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password":"changeme123","new_password":"newpass456"}'
# expect: {"message": "Password updated successfully"}

# Verify old token still works (tokens not invalidated)
curl http://localhost:8000/auth/me -H "Authorization: Bearer $TOKEN"
# expect: user profile returned

# Verify login with new password works
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@spendsense.local","password":"newpass456"}'
# expect: new token returned

# Test wrong current password
curl -X PUT http://localhost:8000/auth/password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password":"wrongpass","new_password":"newpass789"}'
# expect: 400 {"detail": "Current password is incorrect"}

# Test delete account (use a test account, NOT admin)
# First register a test account:
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"deletetest@example.com","password":"testpass123"}'
# Login as test user:
TEST_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"deletetest@example.com","password":"testpass123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
# Delete the account:
curl -X DELETE http://localhost:8000/auth/account \
  -H "Authorization: Bearer $TEST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"confirmation":"DELETE"}'
# expect: {"message": "Account deleted", "email": "deletetest@example.com"}
# Verify token is now invalid:
curl http://localhost:8000/auth/me -H "Authorization: Bearer $TEST_TOKEN"
# expect: 401 (user no longer exists)
```

---

## Commit 4.3 — Privacy Notice

**Goal:** Users understand what data is stored and what goes to Anthropic
before they commit to using SpendSense.

### Step 1 — Create `PRIVACY.md` at project root

Write a plain English privacy notice. It must cover:

**1. What we store**
- Expense entries (vendor name, amount, category, date, note)
- Income amounts and month
- Budget limits per category
- Account email and bcrypt-hashed password (never plaintext)
- Last login timestamp

**2. What we do NOT store**
- Full name, phone number, address
- Payment card details or bank account numbers
- Device information, location, or browser fingerprints
- Any data not explicitly entered by the user

**3. What goes to Anthropic API**
- When you use the natural language input ("zomato 350, ola 120"), that
  text is sent to Anthropic's Claude API for parsing
- Anthropic's privacy policy applies to that processing:
  https://www.anthropic.com/privacy
- Only the raw expense text is sent — not your email, balance, or other data

**4. Data retention**
- Your data is stored for as long as your account exists
- When you delete your account, all data is permanently deleted immediately
- No backups of deleted user data are retained after the next backup cycle

**5. How to export or delete your data**
- Export: Settings → My Data → Download CSV
- Delete account: Settings → My Account → Danger Zone → Delete My Account

**6. Who can see your data**
- Only you — all queries are scoped to your user ID
- The app administrator can see user account metadata (email, last login,
  account count) for operational purposes but cannot access expense data
  without direct database access

**7. Contact**
- Questions: raise an issue on the GitHub repo or contact the administrator

Keep the tone plain and direct. No legal jargon. The file should be readable
in under 2 minutes.

### Step 2 — Add Privacy Link to Login Page

In `frontend/app.py`, in the `show_login_page()` function, add a privacy
notice line at the very bottom of the card (after the register toggle button):

```python
st.markdown(
    f'<div style="text-align:center;margin-top:24px;color:{T["muted"]};font-size:0.75rem;">'
    'By signing in you acknowledge our '
    '<a href="https://github.com/gitdebashish123/expenditure-tracker/blob/main/PRIVACY.md" '
    'target="_blank" style="color:#a5b4fc;">Privacy Notice</a>'
    '</div>',
    unsafe_allow_html=True
)
```

Note: Replace the GitHub URL with the actual repo URL.

### Step 3 — Add Privacy Link to Settings Footer

In `frontend/app.py`, at the very end of the Settings tab (Tab 5), add a
footer line after all sections:

```python
st.markdown(f"""
<div style="margin-top:40px;padding-top:16px;border-top:1px solid {T['border']};
    text-align:center;color:{T['muted']};font-size:0.78rem;">
    SpendSense · <a href="https://github.com/gitdebashish123/expenditure-tracker/blob/main/PRIVACY.md"
    target="_blank" style="color:#a5b4fc;">Privacy Notice</a> ·
    Your data is private and isolated to your account
</div>
""", unsafe_allow_html=True)
```

### Verification — Commit 4.3

```bash
# Confirm PRIVACY.md exists at project root
ls PRIVACY.md
# expect: file exists

# Confirm it covers all 7 required sections
grep -c "Anthropic\|export\|delete\|store\|password\|contact\|retention" PRIVACY.md
# expect: 7 or more matches

# Open the app in browser
# expect: Privacy Notice link visible below the login form
# expect: Privacy Notice link visible at bottom of Settings tab
```

---

## Files Created / Modified in Sprint 4

| File | Commit | Change |
|---|---|---|
| `backend/main.py` | 4.1 | Add `GET /export/csv/{month_key}` and `GET /export/csv/all` |
| `frontend/app.py` | 4.1 | Add "My Data" section with download buttons in Settings |
| `backend/main.py` | 4.2 | Add `PUT /auth/password` and `DELETE /auth/account` endpoints |
| `frontend/app.py` | 4.2 | Add "My Account" section with change password, last login, delete |
| `PRIVACY.md` | 4.3 | New file — plain English privacy notice |
| `frontend/app.py` | 4.3 | Add privacy link to login page and Settings footer |

---

## Implementation Order

Execute commits in order — each builds on the previous:

```
Commit 4.1 → Commit 4.2 → Commit 4.3
```

Within each commit, implement backend first then frontend:
- Backend: add to `backend/main.py`, run verification curl commands
- Frontend: add to `frontend/app.py`, test in browser

---

## Security Notes

**Change Password endpoint:**
- Return `400` (not `401`) for wrong current password — user is authenticated,
  just the old password is wrong. 401 would trigger the frontend's session expiry
  handler and log them out, which is the wrong behaviour.
- Do NOT invalidate existing JWT tokens after password change. The current JWT
  implementation has no token blacklist. Invalidation would require a Redis-based
  token blacklist (Sprint 5+ scope).

**Delete Account endpoint:**
- The `confirmation: "DELETE"` string check is a UX guard, not a security measure.
  The real security is the JWT token — only the authenticated user can call this.
- Delete in dependency order (PoolEntry before FixedExpenseTemplate, etc.) to
  avoid foreign key constraint violations.
- A single `session.commit()` after all deletes is safer than committing per table
  — if an error occurs mid-delete, nothing is committed and the account remains intact.

**Export endpoints:**
- Always verify `user_id == current_user.id` in the query — never export without
  the user filter, even though the endpoint is already protected by `get_current_user`.
  Defence in depth.

---

## Do Not Change in Sprint 4

- `backend/auth.py` — no changes needed
- `backend/models.py` — no schema changes
- `backend/budget_rules.py` — no changes
- `docker-compose.yml` — no changes
- `railway.toml` — no changes
- Existing endpoints — do not modify any existing endpoint behaviour

---

## After Sprint 4

SpendSense is ready to share with the first external user:

**Pre-sharing checklist:**
- [ ] CSV export works and only returns the user's own data
- [ ] Change password works in Settings
- [ ] PRIVACY.md exists and is linked from the login page
- [ ] Admin password changed from `changeme123` in Railway Variables
- [ ] CORS updated with production Railway frontend URL (already done in Sprint 3.2)

**Next sprint:** Sprint 5 — Rate Limiting & API Hardening (slowapi, input
validation, security headers). Not required before sharing with first users
but important before scaling beyond 5 users.

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Prompt ready — Sprint 1, 2, 3 complete. Implement Sprint 4 next.*
