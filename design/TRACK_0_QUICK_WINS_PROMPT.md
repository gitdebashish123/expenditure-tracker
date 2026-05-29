# SpendSense — Track 0 Quick Wins Implementation Prompt
## UI Polish Before Sharing with First Users

Reference: `todo/01-frontend-mobile-whatsapp-enhancements.md` → Track 0

---

## Context

Sprint 4 is complete. SpendSense is deployed on Railway. Before sharing
with the first external user, these 7 quick wins make the app feel like
a real product rather than a data tool. All changes are in `frontend/app.py`
only — no backend changes needed.

**Project root:** `/Users/debashish/Desktop/ai-projects/expenditure-tracker`
**Only file to modify:** `frontend/app.py`
**Python version:** 3.13
**Streamlit version:** ≥1.40 (st.popover and st.toast are available)

**Current header structure:**
```python
col_title, col_theme, col_logout, col_month = st.columns([3, 0.5, 0.7, 1])
# col_logout currently has a plain "👤 D  Sign out" button
```

**Current Settings tab order:**
1. 💰 My Take-home
2. 📋 Monthly Bills
3. 🎯 Spending Caps
4. ⚡ Saved Shortcuts
5. 📥 My Data (export)
6. 👤 My Account (change password, last login, danger zone)
   ← currently buried at the bottom, below all operational settings

**Known existing helpers:**
- `fmt_month(m)` — formats "2026-05" as "May 2026"
- `api(method, path, **kwargs)` — authenticated API helper
- `T` dict — theme colours (T["text"], T["sub"], T["muted"], T["card"], T["card2"], T["border"])
- `CATEGORY_ICONS` dict — emoji per category
- `st.toast()` — available, already used in a few places (fav template log)
- `st.popover()` — available since Streamlit 1.31

**Important:** `frontend/app.py` is ~1,500 lines. All edits must use
a Python script saved to a file (not heredoc) to avoid bash escaping issues.
Pattern: `python3 /tmp/fix_name.py` where the script is written with
`open('/tmp/fix_name.py', 'w')` first.

---

## Implementation Order

Execute steps in this order. Verify syntax after each step.

```
Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7 → Final verify
```

Syntax check after every step:
```bash
python3 -c "import ast; ast.parse(open('frontend/app.py').read()); print('OK')"
```

---

## Step 1 — `fmt_inr()` Helper for Indian Number Formatting

**What:** Add a `fmt_inr(amount)` function that formats numbers in Indian
lakh style: ₹1,20,000 instead of ₹1,20,000 (Western: ₹120,000).

**Where to add:** In the `# ── Helpers` section, right after the `fmt_month()` function.

**Exact function to add:**

```python
def fmt_inr(amount):
    """
    Format a number in Indian lakh/crore style.
    Examples: 1500 → ₹1,500 | 150000 → ₹1,50,000 | 15000000 → ₹1,50,00,000
    Negative amounts show as -₹1,50,000 (negative sign before rupee symbol).
    """
    if amount is None:
        return "₹0"
    negative = amount < 0
    amount = abs(amount)

    # Convert to integer string (no decimals for display)
    s = str(int(round(amount)))

    # Indian comma placement: last 3 digits, then every 2
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        # Insert comma every 2 digits from right in rest
        parts = []
        while len(rest) > 2:
            parts.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.append(rest)
        parts.reverse()
        formatted = ",".join(parts) + "," + last3

    prefix = "-₹" if negative else "₹"
    return prefix + formatted
```

**After adding:** Do a global search-replace of the most common amount formatting
patterns throughout `app.py` to use `fmt_inr()`:

Replace all occurrences of:
- `f"\\u20b9{amount:,.0f}"` → `fmt_inr(amount)` (where `amount` is a variable)
- `f"\\u20b9{rem:,.0f}"` → `fmt_inr(rem)`
- `f"\\u20b9{total_income:,.0f}"` → `fmt_inr(total_income)`
- `f"\\u20b9{paid_total:,.0f}"` → `fmt_inr(paid_total)`
- `f"\\u20b9{unpaid_total:,.0f}"` → `fmt_inr(unpaid_total)`
- `f"\\u20b9{variable:,.0f}"` → `fmt_inr(variable)`
- `f"\\u20b9{remaining:,.0f}"` → `fmt_inr(remaining)`
- `f"\\u20b9{item['amount']:,.0f}"` → keep as-is (dict access in f-strings is trickier)

**Note:** Only replace `\u20b9{var:,.0f}` patterns where the variable is a
simple Python variable name. Leave dict/attribute access patterns unchanged
to avoid breaking the f-string syntax — those can be left for a future cleanup.

**Verification:**
```python
# Quick test in Python shell
# fmt_inr(1500) → "₹1,500"
# fmt_inr(150000) → "₹1,50,000"
# fmt_inr(1500000) → "₹15,00,000"
# fmt_inr(-50000) → "-₹50,000"
# fmt_inr(0) → "₹0"
```

---

## Step 2 — `fmt_date()` Helper for Consistent Date Language

**What:** Add a `fmt_date(date_str)` function that returns human-friendly
relative dates. Use it consistently in the Expenses tab and Today's Entries.

**Where to add:** In the `# ── Helpers` section, after `fmt_inr()`.

**Exact function to add:**

```python
def fmt_date(date_str):
    """
    Format a date string (YYYY-MM-DD) in human-friendly relative terms.
    Today → "Today"
    Yesterday → "Yesterday"
    Current year → "28 May"
    Previous year → "28 May 2025"
    """
    try:
        if isinstance(date_str, str):
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            d = date_str  # already a date object
        today     = date.today()
        yesterday = date.today().__class__.fromordinal(today.toordinal() - 1)
        if d == today:
            return "Today"
        elif d == yesterday:
            return "Yesterday"
        elif d.year == today.year:
            return d.strftime("%-d %b")   # "28 May"
        else:
            return d.strftime("%-d %b %Y")  # "28 May 2025"
    except Exception:
        return str(date_str)
```

**Where to apply:** Replace `exp_date.strftime("%d %b %Y")` in Tab 4
(Expenses) date group headers with `fmt_date(exp_date)`.

---

## Step 3 — Profile Dropdown with st.popover

**What:** Replace the plain "👤 D  Sign out" button in `col_logout` with
a proper `st.popover()` that shows a dropdown menu containing:
- User email (non-clickable display text)
- Divider
- 🔑 Change Password button (scrolls to Settings → My Account)
- 🔒 Privacy Notice link
- 🚪 Sign Out button

**Where:** Replace the entire `with col_logout:` block.

**Current code to replace:**
```python
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
```

**New code:**
```python
with col_logout:
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    email_initial = st.session_state.user_email[0].upper() if st.session_state.user_email else "?"
    with st.popover(f"👤 {email_initial}", use_container_width=False):
        # User info header
        st.markdown(
            f"<div style='color:{T['sub']};font-size:0.78rem;padding:4px 0 8px;"
            f"border-bottom:1px solid {T['border']};margin-bottom:8px;'>"
            f"Signed in as<br><b style='color:{T['text']};'>"
            f"{st.session_state.user_email}</b></div>",
            unsafe_allow_html=True,
        )
        # Change Password — sets a flag to scroll to the account section
        if st.button("🔑 Change Password", key="popover_pw", use_container_width=True):
            st.session_state.scroll_to_account = True
            st.rerun()
        # Privacy Notice
        PRIV_URL = "https://github.com/gitdebashish123/expenditure-tracker/blob/main/PRIVACY.md"
        st.markdown(
            f"<a href='{PRIV_URL}' target='_blank' "
            f"style='color:#a5b4fc;font-size:0.85rem;text-decoration:none;"
            f"display:block;padding:6px 0;'>🔒 Privacy Notice</a>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<hr style='border:none;border-top:1px solid {T['border']};margin:8px 0;'>",
            unsafe_allow_html=True,
        )
        # Sign Out
        if st.button("🚪 Sign Out", key="popover_signout", use_container_width=True):
            st.session_state.token         = None
            st.session_state.user_email    = None
            st.session_state.user_is_admin = False
            st.session_state.auth_error    = None
            st.rerun()
```

**Also add to the Auth Session State initialisation block** (near the top,
where other session state keys are initialised):
```python
if "scroll_to_account" not in st.session_state:
    st.session_state.scroll_to_account = False
```

**Change Password navigation:** The "Change Password" button in the popover
sets `st.session_state.scroll_to_account = True`. At the top of the Settings
tab (Tab 5), check this flag and if set, expand the Change Password expander
and clear the flag:
```python
# At the very top of `with tab5:` block, before settings_section calls
if st.session_state.get("scroll_to_account"):
    st.session_state.scroll_to_account = False
    # Streamlit doesn't support programmatic tab switching, so just show
    # a banner pointing the user to the account section below
    st.info("👇 Scroll down to My Account to change your password.")
```

---

## Step 4 — Move My Account to Top of Settings Tab

**What:** Move the entire "My Account" section (sections 6 — change password,
last login, danger zone) from the bottom of the Settings tab to the TOP,
before "My Take-home".

**Why:** Account management is personal/security-critical. It should not sit
below operational settings like Monthly Bills and Spending Caps. The current
position requires scrolling past ~400px of unrelated content to reach it.

**How:** In Tab 5 (`with tab5:`), the current order is:
1. My Take-home
2. Monthly Bills
3. Spending Caps
4. Saved Shortcuts
5. My Data (export)
6. My Account ← move this to position 1

**New order after this change:**
1. 👤 My Account (change password, last login, danger zone)
2. 💰 My Take-home
3. 📋 Monthly Bills
4. 🎯 Spending Caps
5. ⚡ Saved Shortcuts
6. 📥 My Data (export)

**Implementation note:** The `account_info`, `fmt_last_login()`, and
`last_login_str` variables that are currently defined inline with section 6
need to move up to the top of the Tab 5 block.

The `dl_col2` block (Download Full History button) is currently orphaned
at the very bottom — it must remain inside `with dl_col2:` under the
My Data section even after the reorder. Confirm it stays in correct position.

---

## Step 5 — Replace Static Success Banners with st.toast()

**What:** Replace persistent `.toast-success` div blocks with Streamlit's
native `st.toast()` for routine success actions. Keep persistent banners
only for important confirmations.

**Actions to convert to st.toast():**

| Current | Replace with |
|---|---|
| `st.markdown('<div class="toast-success">✅ Saved N expense(s)</div>', ...)` | `st.toast(f"✅ {len(saved)} expense(s) saved", icon="✅")` |
| `st.success(f"✅ Saved ₹{income_amount:,.0f} for {month_label}")` | `st.toast(f"✅ Income saved for {month_label}", icon="💰")` |
| `st.success(f"✅ Added {new_tname} as a {kind_label}")` | `st.toast(f"✅ Added {new_tname}", icon="📋")` |
| `st.success(f"✅ Added shortcut for {fav_name}")` | `st.toast(f"✅ Added shortcut for {fav_name}", icon="⚡")` |
| `st.success("✅ Spending caps updated!")` | `st.toast("✅ Spending caps updated", icon="🎯")` |
| `st.markdown('<div class="toast-success">✅ Password changed successfully</div>', ...)` | `st.toast("✅ Password changed successfully", icon="🔑")` |

**Keep as persistent banners** (do NOT convert to toast):
- Auth errors on login page (`auth-error` div)
- Budget warnings (`warn-danger`, `warn-warning` divs)
- Delete account confirmation
- Password change errors

**Note:** `st.toast()` auto-dismisses after ~3 seconds and appears in the
bottom-right corner. It does not interrupt layout or require rerun.

---

## Step 6 — Friendly Empty States

**What:** Replace terse "No expenses found" messages with contextual,
actionable guidance for new users.

**Changes:**

**Tab 1 — Quick Add, Today's Entries (when empty):**
Replace:
```python
st.markdown(f'<div style="color:{T["sub"]};...">No expenses logged today</div>', ...)
```
With:
```python
st.markdown(f"""
<div style="text-align:center;padding:28px 16px;color:{T['sub']};">
    <div style="font-size:2rem;margin-bottom:8px;">✏️</div>
    <div style="font-size:0.9rem;font-weight:600;color:{T['text']};margin-bottom:6px;">
        Nothing logged today
    </div>
    <div style="font-size:0.82rem;">
        Type something like <code style="background:{T['card2']};padding:2px 6px;
        border-radius:4px;color:#a5b4fc;">zomato 350, ola 120</code> above to get started.
    </div>
</div>
""", unsafe_allow_html=True)
```

**Tab 2 — Fixed Expenses (when empty):**
Replace:
```python
st.markdown(f'<div style="color:{T["sub"]};text-align:center;padding:40px 0;">No fixed expenses or pools for this month</div>', ...)
```
With:
```python
st.markdown(f"""
<div style="text-align:center;padding:28px 16px;color:{T['sub']};">
    <div style="font-size:2rem;margin-bottom:8px;">📋</div>
    <div style="font-size:0.9rem;font-weight:600;color:{T['text']};margin-bottom:6px;">
        No bills set up yet
    </div>
    <div style="font-size:0.82rem;">
        Go to <b style="color:#a5b4fc;">Settings → Monthly Bills</b> to add
        your rent, EMI, subscriptions and other recurring payments.
    </div>
</div>
""", unsafe_allow_html=True)
```

**Tab 3 — Dashboard (when no summary):**
Replace:
```python
st.info("No data for this month yet.")
```
With:
```python
st.markdown(f"""
<div style="text-align:center;padding:40px 16px;color:{T['sub']};">
    <div style="font-size:2.5rem;margin-bottom:12px;">📊</div>
    <div style="font-size:1rem;font-weight:600;color:{T['text']};margin-bottom:8px;">
        No data yet this month
    </div>
    <div style="font-size:0.85rem;max-width:360px;margin:0 auto;">
        Head to <b style="color:#a5b4fc;">Quick Add</b> to log your first expense,
        or go to <b style="color:#a5b4fc;">Settings → My Take-home</b> to record
        this month's income.
    </div>
</div>
""", unsafe_allow_html=True)
```

**Tab 4 — Expenses (when empty):**
Replace:
```python
st.markdown(f'<div style="color:{T["sub"]};text-align:center;padding:40px 0;">No expenses found</div>', ...)
```
With:
```python
st.markdown(f"""
<div style="text-align:center;padding:40px 16px;color:{T['sub']};">
    <div style="font-size:2rem;margin-bottom:8px;">💸</div>
    <div style="font-size:0.9rem;font-weight:600;color:{T['text']};margin-bottom:6px;">
        No transactions this month
    </div>
    <div style="font-size:0.82rem;">
        Log expenses in <b style="color:#a5b4fc;">Quick Add</b> — they'll appear here.
    </div>
</div>
""", unsafe_allow_html=True)
```

---

## Step 7 — Dynamic Browser Tab Title

**What:** Show the remaining balance in the browser tab title so users with
multiple tabs know their status at a glance.

**Current:**
```python
st.set_page_config(page_title="SpendSense", page_icon="\U0001f4b8", layout="wide",
                   initial_sidebar_state="collapsed")
```

`st.set_page_config()` can only be called once — it's at the top of the file
before the auth gate, so the balance isn't known yet.

**Solution:** After the balance is loaded (after `summary = api(...)`), use
a JavaScript injection to update the document title dynamically:

```python
# After summary is loaded and rem is calculated
if summary:
    bal = summary["balance"]
    rem = bal["remaining"]
    # ... existing code ...
    rem_str = fmt_inr(rem)
    title_color = "🟢" if rem >= 0 else "🔴"
    st.markdown(
        f"<script>document.title = '{title_color} {rem_str} left · SpendSense';</script>",
        unsafe_allow_html=True,
    )
```

This updates the tab title dynamically after every page load/rerun without
touching `st.set_page_config()`.

---

## Verification Steps

After all 7 steps are implemented, run the full verification suite:

### Syntax check
```bash
cd /Users/debashish/Desktop/ai-projects/expenditure-tracker
python3 -c "import ast; ast.parse(open('frontend/app.py').read()); print('✅ Syntax OK')"
```

### Visual checks (open http://localhost:8501)

**Step 1 — Indian formatting:**
- Balance cards show ₹1,50,000 style not ₹150,000
- Income display uses Indian format

**Step 2 — Date language:**
- Expenses tab shows "Today", "Yesterday", "28 May" not raw ISO dates

**Step 3 — Profile dropdown:**
- Header shows "👤 D" avatar button (not "👤 D  Sign out")
- Clicking it opens a popover with email, Change Password, Privacy Notice, Sign Out
- Sign Out works from the popover
- "Change Password" shows the scroll hint and directs to Settings

**Step 4 — My Account at top of Settings:**
- Opening Settings tab shows My Account section first
- Change Password, Last Login, Danger Zone are all accessible without scrolling

**Step 5 — Toast notifications:**
- Adding an expense shows a brief toast, not a persistent green banner
- Saving income shows a toast
- Adding a shortcut shows a toast
- Toast auto-dismisses after ~3 seconds

**Step 6 — Empty states:**
- A new user with no data sees friendly guidance, not blank space
- Each tab has a contextual, actionable empty state

**Step 7 — Tab title:**
- Browser tab shows "🟢 ₹21,450 left · SpendSense" when balance is positive
- Browser tab shows "🔴 -₹2,000 left · SpendSense" when over budget

---

## Files Modified

| File | Change |
|---|---|
| `frontend/app.py` | All 7 steps — helpers, header, settings order, empty states, tab title |

### Files NOT changed
- `backend/main.py` — no changes
- `backend/auth.py` — no changes
- `backend/models.py` — no changes
- `docker-compose.yml` — no changes
- `railway.toml` — no changes

---

## Commit

After all verification steps pass:

```bash
cd /Users/debashish/Desktop/ai-projects/expenditure-tracker
git add frontend/app.py
git commit -m "feat: Track 0 UI quick wins — profile dropdown, Indian formatting, empty states, toast notifications"
git push
```

Then merge to main to deploy to Railway:
```bash
git checkout main
git merge develop --no-ff -m "release: Track 0 UI quick wins"
git push origin main
git checkout develop
```

---

## Known Limitations of Streamlit

Some improvements described in Track 0 are not achievable in Streamlit:

| Desired | Limitation | Workaround in this prompt |
|---|---|---|
| True dropdown menu in header | Streamlit has no native dropdown | `st.popover()` — close enough |
| Tab-level routing (account page) | No programmatic tab switching | Scroll hint banner |
| Bottom navigation bar on mobile | CSS-only, complex | Deferred to Track 1 |
| Animations on success | Streamlit re-renders entire page | `st.toast()` is sufficient |

These limitations are the reason Track 2 (React migration) exists.

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Prompt ready — implement before Sprint 5*
