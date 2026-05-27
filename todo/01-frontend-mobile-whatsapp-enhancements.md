# 01 — Frontend & Mobile Experience Enhancements

**Category:** UX / Infrastructure
**Priority:** Medium → High (depends on user feedback post-launch)
**Prerequisite:** Sprint 2 (data isolation) + Sprint 3 (Railway deployment) complete

---

## Overview

SpendSense currently uses Streamlit as the frontend — a desktop-first Python
framework. On mobile devices the UI is functional but not polished. This document
captures three enhancement tracks: quick CSS fixes, a React migration, and a
WhatsApp bot for frictionless expense logging.

---

## Track 1 — Mobile CSS Fixes (Current Streamlit Stack)

**Effort:** 1–2 days
**Impact:** Medium — makes Streamlit usable on mobile without a full rewrite
**When to do:** Before sharing with first external users

### Problems to Fix

| Problem | Root Cause |
|---|---|
| Column layouts collapse or overflow | `st.columns()` doesn't adapt to narrow screens |
| Header row too cramped | 4 elements (`[3, 0.5, 0.7, 1]`) squeezed on 375px screen |
| Balance cards unreadable side-by-side | `[1,1,1]` columns too narrow on mobile |
| Input/button tap targets too small | Streamlit defaults below 44px min height |
| Login card too narrow | `[1, 2, 1]` column split leaves middle column cramped |
| Tab labels truncated | 5 emoji+text tabs overflow on narrow screen |
| Tables overflow horizontally | No `overflow-x: auto` scroll container |
| Font sizes don't scale | Fixed `rem`/`px` — no `@media` breakpoints |

### Fixes to Implement

- Inject `@media (max-width: 480px)` CSS via `st.markdown` for responsive breakpoints
- Stack balance cards vertically on mobile using CSS column override
- Shorten tab labels to emoji-only on narrow screens (➕ 📋 📊 💸 ⚙️)
- Increase button/input `min-height` to 48px for finger-friendly tap targets
- Change login card columns to `[0.1, 2, 0.1]` on mobile (near full width)
- Wrap `st.dataframe` tables in `overflow-x: auto` scroll container
- Simplify header — move month selector below title on small screens
- Scale down `.app-title` and card value font sizes at mobile breakpoints

### Limitation

No matter how much CSS is injected, Streamlit is fundamentally desktop-first.
These fixes make it usable on mobile — they don't make it feel native.

---

## Track 2 — React Frontend Migration

**Effort:** 3–4 weeks (experienced React dev) / 6–8 weeks (learning React)
**Impact:** High — full mobile responsiveness, better performance, PWA support
**When to do:** After Sprint 3, if mobile is a consistent user complaint

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
| Offline support | Not possible | Service workers |

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
| Dashboard charts | Medium–High — 2–3 days |
| Settings (4 sections) | High — 3–4 days |
| Month selector (global state) | Medium — 1 day |
| Dark/light theme | Low — half a day |
| Auth token management | Low — 1 day |
| **Total** | **~3–4 weeks** |

### Recommended Stack for React Migration

| Layer | Technology | Reason |
|---|---|---|
| Framework | React 18 + Vite | Fast dev server, modern tooling |
| Styling | Tailwind CSS | Mobile-first by default, dark mode built-in |
| Charts | Recharts | Familiar API, good mobile support |
| HTTP client | Axios | Interceptors for token injection + 401 handling |
| Routing | React Router v6 | Clean URL-based navigation |
| State | React Context + useState | Simple enough for this app size |
| PWA | vite-plugin-pwa | One config line — installable on phone home screen |

### PWA Benefit

Once React + vite-plugin-pwa is in place, SpendSense can be installed on the
iPhone and Android home screens and opens like a native app. Combined with the
WhatsApp bot (Track 3), this makes SpendSense part of someone's daily routine.

### Decision Trigger

Do this migration if:
- 3+ users consistently report mobile UX as a problem
- User base grows beyond 10–15 people
- You want features Streamlit cannot support (offline mode, push notifications,
  camera for receipt scanning)

---

## Track 3 — WhatsApp Bot

**Effort:** 1 week (Twilio sandbox to basic production)
**Impact:** Very high — solves the "I forgot to log it" problem at the root
**When to do:** After Sprint 2 + Sprint 3 as a standalone Sprint 7

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

## Summary & Recommended Order

| Track | Impact | Effort | Recommended Timing |
|---|---|---|---|
| Track 1 — CSS mobile fixes | Medium | 1–2 days | Before sharing with first users |
| Track 3 — WhatsApp bot | Very High | ~1 week | Sprint 7, after Railway deployment |
| Track 2 — React migration | High | 3–4 weeks | Only if mobile becomes a persistent blocker |

**Pragmatic path:**
1. **Track 1 now** — CSS fixes before first external user, low effort, immediate improvement
2. **Track 3 next** — WhatsApp bot after deployment, highest daily-use impact for Indian users
3. **Track 2 later** — React only if user base grows beyond 10–15 or mobile is a constant complaint

---

## Related Design Documents

- `design/MULTI_USER_ROADMAP.md` — Sprint 1–6 implementation plan
- `design/TECH_STACK_ANALYSIS.md` — Stack comparison (Streamlit vs Flask MPA)
- `design/COMMIT_3_2_RAILWAY_DEPLOY_PROMPT.md` — Railway deployment prompt

---

*Created: May 2026*
*Owner: Debashish*
*Status: Backlog — revisit after Sprint 3 deployment and first user feedback*
