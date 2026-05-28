# 01 — Frontend & Mobile Experience Enhancements

**Category:** UX / Infrastructure
**Priority:** Medium → High (depends on user feedback post-launch)
**Prerequisite:** Sprint 1–4 complete ✅

---

## When to Do This vs Sprint 5 & 6

**Short answer: Do the Quick Wins (Track 0) now, before sharing with users. Do everything else after Sprint 5 & 6.**

Here is the reasoning:

Sprint 5 (Rate Limiting & API Hardening) and Sprint 6 (Onboarding & Polish) are
backend-heavy and don't conflict with UI work. However, the React migration (Track 2)
is a large undertaking that would make Sprint 5/6 harder to implement and test because
the entire frontend would be in flux. The correct order is:

```
Sprint 4 ✅ → Track 0 Quick Wins → Sprint 5 → Sprint 6 → Track 1 CSS → Track 3 WhatsApp Bot → Track 2 React
```

**Do before sharing with users (now):**
- Track 0 — Quick wins: profile dropdown, toast messages, Indian number formatting,
  empty states. Low effort, high first-impression impact.

**Do after Sprint 5 & 6:**
- Track 1 — Mobile CSS fixes: good enough to unblock sharing, but do a proper
  pass after Sprint 6 when the feature set is stable.
- Track 3 — WhatsApp bot: Sprint 7, standalone.
- Track 2 — React migration: only if user base grows or mobile becomes a blocker.

---

## Track 0 — Quick Wins (Current Streamlit Stack)

**Effort:** 2–3 days
**Impact:** High first-impression improvement — makes the app feel like a real product
**When to do:** Now, before sharing with first external users

These are low-effort changes that immediately make SpendSense look and feel
like a professional web app rather than a data tool.

### 0.1 — Profile Dropdown in Header (Most Impactful)

**Current:** Sign Out is a plain button in the header row alongside the moon/sun toggle.

**Target:** A profile avatar (user initial in a circle) that opens a small dropdown menu:
- 👤 Signed in as user@email.com (non-clickable, greyed)
- 🔑 Change Password → navigates to Settings → My Account
- 🔒 Privacy Notice → opens GitHub PRIVACY.md in new tab
- ─────────────────
- 🚪 Sign Out

This is the standard pattern users expect from every web app (Gmail, Notion, Linear).
It also frees up header space and makes the header feel clean.

**Implementation note:** Streamlit doesn't have native dropdowns in the header.
This can be approximated with a `st.popover()` (available since Streamlit 1.31)
containing buttons, or with a CSS-injected custom dropdown.

### 0.2 — My Account Navigation Rethink

**Current:** Change Password and Delete Account are buried at the bottom of the
Settings tab, below Monthly Bills, Spending Caps, and Saved Shortcuts.

**Target:** My Account should feel like a separate destination, not a settings item.

Two approaches (pick one):
- **Profile page:** Clicking the avatar dropdown → "My Account" opens a dedicated
  Streamlit page (using `st.switch_page()` with multi-page support).
- **Modal/expander at top of Settings:** Move the entire My Account section to the
  very top of Settings tab, before My Take-home. It's more personal than operational.

Change Password and Delete Account in particular should be clearly separated
from operational settings — they serve a completely different mental model.

### 0.3 — Toast Notifications for Success Messages

**Current:** Success messages appear as static coloured divs that persist until
the next page rerun.

**Target:** Use Streamlit's built-in `st.toast()` for transient success feedback:
- Expense saved ✅
- Password changed ✅
- Income saved ✅
- Template added ✅

Reserve the persistent green banners for important confirmations (account deleted,
export downloaded). Toast is better for routine actions.

### 0.4 — Indian Number Formatting

**Current:** ₹1,20,000 displays as ₹120,000 (Western format).

**Target:** ₹1,20,000 (Indian lakh format — familiar to the target user).

Python implementation: replace `f"₹{amount:,.0f}"` with a custom `fmt_inr(amount)`
helper that formats using Indian comma placement (last 3 digits, then every 2 digits).

Example: 1500000 → ₹15,00,000 not ₹1,500,000.

### 0.5 — Friendly Empty States

**Current:** Empty sections show "No expenses found" or nothing at all.

**Target:** Contextual guidance that helps new users get started:

| Section | Empty State Message |
|---|---|
| Quick Add — Today's Entries | "Nothing logged today. Type 'zomato 350, ola 120' above to get started." |
| Dashboard | "No data yet this month. Log your first expense in Quick Add." |
| Expenses tab | "No transactions this month. Head to Quick Add to log expenses." |
| Fixed tab | "No fixed expenses set up yet. Go to Settings → Monthly Bills to add your rent, EMI, and subscriptions." |

### 0.6 — Browser Tab Title Shows Balance

**Current:** Tab title is always "SpendSense".

**Target:** "SpendSense · ₹21,450 left" — users with multiple tabs instantly
know their remaining balance without switching to the tab.

Implementation: `st.set_page_config(page_title=f"SpendSense · {balance_str}")`
called after the balance is loaded.

### 0.7 — Consistent Date Language

**Current:** Some dates show as "2026-05-28", others as "28 May 2026".

**Target:** Use human-friendly relative dates consistently throughout:
- Today's entries: "Today", "Yesterday"
- Older entries: "28 May" (current year) or "28 May 2025" (previous year)
- Month selector: "May 2026" (already done ✅)

---

## Track 1 — Mobile CSS Fixes (Current Streamlit Stack)

**Effort:** 2–3 days (after Sprint 5 & 6 when feature set is stable)
**Impact:** Medium — makes Streamlit usable on mobile without a full rewrite
**When to do:** After Sprint 6, before React migration decision

### Problems to Fix

| Problem | Root Cause |
|---|---|
| Column layouts collapse or overflow | `st.columns()` doesn't adapt to narrow screens |
| Header row too cramped | 4 elements squeezed on 375px screen |
| Balance cards unreadable side-by-side | `[1,1,1]` columns too narrow on mobile |
| Input/button tap targets too small | Streamlit defaults below 44px min height |
| Login card too narrow | `[1, 2, 1]` column split leaves middle column cramped |
| Tab labels truncated | 5 emoji+text tabs overflow on narrow screen |
| Tables overflow horizontally | No `overflow-x: auto` scroll container |
| Font sizes don't scale | Fixed `rem`/`px` — no `@media` breakpoints |
| No bottom navigation | Tabs at top are hard to reach on mobile |
| Settings tab too long | Everything on one scrollable page on small screen |

### Fixes to Implement

- Inject `@media (max-width: 480px)` CSS via `st.markdown` for responsive breakpoints
- Stack balance cards vertically on mobile using CSS column override
- Shorten tab labels to emoji-only on narrow screens (➕ 📊 📋 ⚙️)
- Increase button/input `min-height` to 48px for finger-friendly tap targets
- Change login card columns to `[0.1, 2, 0.1]` on mobile (near full width)
- Wrap `st.dataframe` tables in `overflow-x: auto` scroll container
- Simplify header — move month selector below title on small screens
- Scale down `.app-title` and card value font sizes at mobile breakpoints
- Floating action button (+) visible on all tabs for Quick Add

### Information Architecture Improvements

Current tab structure has problems — Fixed Expenses is only relevant once a month
but sits as a permanent tab. Proposed restructure:

```
Current:                          Better:
⚡ Quick Add                      💸 Today (Quick Add + today entries)
📌 Fixed                          📊 Overview (Dashboard)
📊 Dashboard          →           📋 History (Expenses list)
📋 Expenses                       ⚙️ Settings (Bills, budgets, shortcuts, fixed)
⚙️ Settings                       [Avatar] → Account page
```

This reduces visible tabs from 5 to 4 and moves Fixed Expenses into Settings
where it belongs — a one-time-per-month configuration, not a daily workflow.

### Limitation

No matter how much CSS is injected, Streamlit is fundamentally desktop-first.
These fixes make it usable on mobile — they don't make it feel truly native.
The React migration (Track 2) is the permanent solution.

---

## Track 2 — React Frontend Migration

**Effort:** 3–4 weeks (experienced React dev) / 6–8 weeks (learning React)
**Impact:** High — full mobile responsiveness, better performance, PWA support
**When to do:** After Sprint 6, only if user base grows or mobile is a persistent blocker

### Why Migrate

| Concern | Streamlit | React |
|---|---|---|
| Mobile responsiveness | Workarounds only | First-class, full control |
| Page reruns on interaction | Full script reruns | Component-level re-renders only |
| Custom UI components | Very limited | Unlimited |
| Animation and transitions | None | Full CSS/JS control |
| Multi-page routing | Clunky | React Router, clean URLs |
| Performance at scale | Degrades with complexity | Stays fast |
| PWA / installable on phone | Not possible | Fully supported |
| Profile dropdown / modals | Hacky CSS workarounds | Native components |
| Bottom navigation bar | Not possible natively | Trivial with Tailwind |

### What Stays Unchanged

The FastAPI backend is completely unaffected — every endpoint, every auth flow,
every JWT token, every database model. React becomes a new consumer of the same
REST API. Zero backend changes required.

### Migration Effort Breakdown

| Component | Effort |
|---|---|
| Login / Register page | Low — 1–2 days |
| Dashboard balance cards | Low — 1 day |
| Quick Add (NL input) | Low — half a day |
| Fixed expenses checklist | Medium — 2 days |
| Expenses table (CRUD) | Medium — 2–3 days |
| Dashboard charts (bar, donut) | Medium–High — 2–3 days |
| Settings (4 sections) | High — 3–4 days |
| Account page (password, delete) | Medium — 1–2 days |
| Month selector (global state) | Medium — 1 day |
| Dark/light theme | Low — half a day |
| Auth token management | Low — 1 day |
| Bottom nav bar | Low — half a day |
| **Total** | **~3–4 weeks** |

### Recommended Stack for React Migration

| Layer | Technology | Reason |
|---|---|---|
| Framework | React 18 + Vite | Fast dev server, modern tooling |
| Styling | Tailwind CSS | Mobile-first by default, dark mode built-in |
| Charts | Recharts | Familiar API, good mobile support |
| HTTP client | Axios | Interceptors for token injection + 401 handling |
| Routing | React Router v6 | Clean URL-based navigation + account page routing |
| State | React Context + useState | Simple enough for this app size |
| PWA | vite-plugin-pwa | One config line — installable on phone home screen |

### PWA Benefit

Once React + vite-plugin-pwa is in place, SpendSense can be installed on the
iPhone and Android home screens and opens like a native app. Combined with the
WhatsApp bot (Track 3), this makes SpendSense genuinely part of a daily routine.

### Decision Trigger

Do this migration if any of these are true:
- 3+ users consistently report mobile UX as frustrating
- User base grows beyond 10–15 people
- You want features Streamlit cannot support (offline mode, push notifications,
  camera for receipt scanning, proper account page routing)
- The CSS workarounds in Track 1 feel like playing whack-a-mole

---

## Track 3 — WhatsApp Bot

**Effort:** 1 week (Twilio sandbox to basic production)
**Impact:** Very high — solves the "I forgot to log it" problem at the root
**When to do:** After Sprint 6 as a standalone Sprint 7

### Why This Is High Impact

The #1 reason budgeting apps fail is manual entry friction. Indian salaried
users are in WhatsApp all day. Sending "zomato 350" in a chat and getting
"✅ Zomato ₹350 logged under Food" back takes 5 seconds — no app to open,
no login, works from the notification shade.

### Architecture

```
User sends WhatsApp message: "zomato 350"
            ↓
WhatsApp Business API (Twilio or Meta Cloud API)
            ↓
Webhook handler — new route in existing FastAPI backend
            ↓
Calls existing POST /expenses/parse (reuses AI parsing logic)
            ↓
Expense saved to DB under user's account
            ↓
Bot replies: "✅ Zomato ₹350 logged under Food
             Balance remaining: ₹21,450"
```

The FastAPI backend already does all the heavy lifting — the bot is a thin
webhook layer on top of what already exists.

### Two Integration Options

| Option | Cost | Setup Time | Production Approval |
|---|---|---|---|
| **Twilio WhatsApp API** | ~$0.005/msg + $1.15/month | Half a day | ~1–2 weeks |
| **Meta Cloud API (direct)** | Free up to 1,000 conv/month | 1–2 days | 2–4 weeks |

**Recommendation:** Start with Twilio sandbox for development (works in minutes),
then decide between Twilio and Meta Cloud for production based on cost vs effort.

### Bot Commands to Implement

**Phase 1 — Minimum viable bot:**

| Command | Response |
|---|---|
| `zomato 350` | ✅ Zomato ₹350 logged under Food |
| `balance` | ₹21,450 remaining this month |
| `today` | Summary of today's expenses |

**Phase 2 — Extended commands:**

| Command | Response |
|---|---|
| `summary` | Monthly breakdown by category |
| `undo` | Deletes last logged expense |
| `fixed` | Lists fixed expenses + paid status |

**Phase 3 — Proactive messages (push notifications):**

| Trigger | Message |
|---|---|
| Day 1–3 of month | "Salary credited? Reply with your take-home to log it" |
| Fixed expense due today | "Electric bill due today — reply with amount to log it" |
| 80% of budget cap spent | "⚠️ Food: ₹3,800 of ₹4,000 spent this month" |

### Non-Technical Hurdle

WhatsApp Business Account approval requires business verification (name, address,
sometimes a website). For a personal tool this takes 1–4 weeks and is the main risk.

**Telegram Bot as fallback:** No approval needed, free, instant setup via BotFather,
strong usage in India. Easier to launch — consider as an alternative or parallel
channel if WhatsApp approval is slow.

---

## Full Priority Order & Timeline

| # | Change | Track | Effort | When |
|---|---|---|---|---|
| 1 | Profile dropdown (sign out, password, privacy) | 0 | 1 day | Now — before sharing |
| 2 | Toast notifications for success messages | 0 | Half day | Now |
| 3 | Indian number formatting (₹1,20,000) | 0 | Half day | Now |
| 4 | Friendly empty states | 0 | Half day | Now |
| 5 | Browser tab shows balance | 0 | 1 hour | Now |
| 6 | My Account rethink (top of settings or modal) | 0 | 1 day | Now |
| 7 | Sprint 5 — Rate limiting & API hardening | — | 3 days | Next |
| 8 | Sprint 6 — Onboarding & polish | — | 1 week | After Sprint 5 |
| 9 | Mobile CSS fixes + tab restructure | 1 | 2–3 days | After Sprint 6 |
| 10 | WhatsApp / Telegram bot | 3 | 1 week | Sprint 7 |
| 11 | Dashboard charts (bar/donut) | 1 | 1–2 days | After Sprint 6 |
| 12 | React migration + PWA | 2 | 3–4 weeks | Only if needed |

---

## Related Design Documents

- `design/MULTI_USER_ROADMAP.md` — Sprint 1–6 implementation plan
- `design/TECH_STACK_ANALYSIS.md` — Stack comparison (Streamlit vs Flask MPA)
- `design/COMMIT_3_2_RAILWAY_DEPLOY_PROMPT.md` — Railway deployment prompt

---

*Created: May 2026*
*Updated: May 2026 — added Track 0 Quick Wins, updated priority order, Sprint 5/6 sequencing*
*Owner: Debashish*
*Status: Track 0 items actionable now. Tracks 1–3 after Sprint 5 & 6.*
