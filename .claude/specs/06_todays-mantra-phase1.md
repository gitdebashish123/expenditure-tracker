# Spec: Today's Mantra — Phase 1 (on-demand daily insight)
**Date**: 2026-06-22
**Status**: Open — awaiting implementation

## Context

Two rounds of external product feedback (informal reviews, not from the
user) independently converged on the same core gap: Wallet Mantra's UI
currently reads as a generic expense tracker, with no surfaced "magic"
matching the app's name and ambition. The backend already has the
beginning of an answer — `backend/ai_parser.py`'s `get_budget_insight()`
generates a short, warm, LLM-phrased money insight from structured
numbers — but it is defined and **never called anywhere** in the app today.

The full feedback (see prior conversation) proposed a much larger system:
nightly cron aggregation, precomputed `daily_snapshots` / `user_analytics`
/ `mantra_history` tables, behavioral pattern detection (salary-day
spikes, recurring-merchant intervals, weekend ratios), a named assistant
persona, a conversational "Ask Tara" chat layer, monthly narrative
summaries, and a "Peace of Mind Score."

**This spec deliberately scopes down to Phase 1 only**: a single daily
insight card, computed on-demand (no cron, no new precomputed analytics
tables), reusing data the backend already computes today. The larger
system is real and worth pursuing later, but only once this minimal
version proves the feature is worth the investment. Everything beyond
Phase 1 is explicitly out of scope here — see "Explicitly out of scope"
below.

---

## Issue 1 — No daily insight is ever shown to the user

**What exists today**: `get_budget_insight(category, spent, limit, month)`
in `backend/ai_parser.py` calls Claude with a tight, well-formed prompt
("Generate a SHORT, friendly 1-sentence warning or tip, max 15 words") and
returns a single sentence. It is fully functional in isolation but is not
imported or called from `backend/budget_rules.py`, `backend/main.py`, or
anywhere in the frontend. Grepping the codebase confirms zero call sites.

**What's missing**: A way to generate a *general* daily insight (not
specific to one over-budget category) and a UI surface to show it. The
Today tab (`frontend/react/src/components/tabs/QuickAddTab.tsx`) currently
renders, top to bottom: NL input form → favourites chips → today's
entries. There is no card of any kind above the input.

**Affected file(s)**:
- `backend/ai_parser.py` — needs a new function, distinct from
  `get_budget_insight` (which stays as-is, scoped to single-category
  warnings)
- `backend/main.py` — needs one new endpoint
- `frontend/react/src/components/tabs/QuickAddTab.tsx` — needs a new card
  rendered first, above the existing "Log Expenses" section
- `frontend/react/src/types/index.ts` — needs one new response type

**Fix approach**:

### Backend: new function in `ai_parser.py`

Add `generate_daily_mantra(context: dict) -> str`, separate from
`get_budget_insight`. Input is a small dict of already-computed numbers —
mirroring the architecture's "Layer 1/2 compute, Layer 3 only phrases"
principle from the reviewed feedback, which is correct and worth keeping
even at this minimal scope. Example shape:
```python
{
    "remaining": 6646,
    "days_left": 9,
    "daily_budget": 738,        # remaining / days_left
    "total_income": 150000,
    "top_category": "Food",
    "top_category_spent": 5891,
}
```
Prompt should explicitly request ONE sentence, no more than ~30 words,
warm tone, no guilt/judgment language, optionally referencing the top
spending category if it's notably large — directly following the tone
guidance already present in `get_budget_insight`'s own prompt ("Be
helpful, not preachy"). Do not attempt salary-day-spike detection,
weekend-ratio analysis, or recurring-merchant pattern detection in this
function — those require historical trend data this spec does not build
(see "Explicitly out of scope"). This phase covers insight categories
**B (positive reinforcement, where trivially derivable), C (predictions),
and F (gentle warnings)** from the original feedback's taxonomy — not A
(spending behavior trends) or D (pattern recognition), both of which need
multi-month history this app may not yet have for most users.

### Backend: new endpoint in `main.py`

Add `GET /insights/mantra/{month_key}`. Reuses
`get_balance_summary()` and `get_monthly_spent_by_category()` (both
already exist in `budget_rules.py`) to build the context dict, computes
`days_left` the same way `budget_projection()` already does (via
`calendar.monthrange` and today's date), then calls
`generate_daily_mantra()`. Returns `{"mantra": "<one sentence>"}`.

**Caching, minimal version**: to avoid calling Claude on every single page
load/tab switch, cache the generated mantra for the remainder of the
calendar day. Simplest viable approach for this phase: an in-memory dict
keyed by `(user_id, date)` inside the FastAPI process (cleared on
restart), NOT a new database table. This avoids building `mantra_history`
as a persistent schema change — acceptable for Phase 1 given Railway free
tier / low-traffic single-process deployment; revisit with a real DB-backed
cache only if this proves insufficient in practice.

### Frontend: new card in `QuickAddTab.tsx`

Add a `TodaysMantraCard` section, rendered as the first section in the
component (above "Log Expenses"). Fetches
`GET /insights/mantra/${selMonth}` on mount, shows a loading skeleton
briefly, then the returned sentence in a visually distinct card (suggest:
similar visual weight to `BudgetHealthCard`, a lotus/sparkle icon per the
"🪷" styling already used elsewhere in the app's emoji language, e.g.
`BudgetHealthCard`'s safe-tier dot). Do not block the rest of the tab on
this — if the fetch fails, fail silently (no error banner) and simply
don't render the card, matching the existing pattern in `OverviewTab`'s
`load()` (`catch { /* leave state as null */ }`).

**Acceptance criteria**:
- Opening the Today tab shows a single one-sentence insight card above
  the expense logging form, generated from the user's actual current-month
  data (not a generic/static message).
- The same sentence is shown if the tab is revisited later the same day
  (basic caching working).
- A new day produces a new (and not obviously repeated) sentence.
- If the backend call fails for any reason, the rest of the Today tab
  still renders normally — the mantra card simply doesn't appear.
- The sentence tone matches the existing `get_budget_insight` style:
  short, warm, non-judgmental, no financial jargon.

**Priority**: High — this is the single highest-leverage, lowest-cost item
across both rounds of feedback; the backend pattern already exists and
only needs to be generalized and surfaced.

---

## Issue 2 — Today tab section ordering doesn't lead with the insight

**What exists today**: `QuickAddTab.tsx` renders sections in this order:
NL input form → favourites chips → today's entries. Both rounds of
feedback specifically called out that the "emotional reward" (the
insight) should come before data entry, not after.

**What's missing**: Nothing structurally — this is a pure ordering change
that becomes trivial once Issue 1's card exists.

**Affected file(s)**:
- `frontend/react/src/components/tabs/QuickAddTab.tsx`

**Fix approach**: Once `TodaysMantraCard` exists (Issue 1), render it as
the first section, before "Log Expenses." No other section needs to move —
favourites and today's entries staying where they are is fine; the
feedback's core complaint is specifically about insight-before-input, not
a full restructure.

**Acceptance criteria**:
- `TodaysMantraCard` is the first visible section on the Today tab,
  above the NL input form.

**Priority**: Medium — small follow-on to Issue 1, not separately
buildable (depends on it directly).

---

## Issue 3 — Naming: persona for the insight feature

**Decision (2026-06-22, revised): "Tara" — named persona.**
The user initially chose to stay unbranded ("Today's Mantra," no persona)
but has since revised this decision: the feature will use **Tara** as its
named persona, per the original round-2 feedback's top recommendation
("Star that guides you" — familiar Indian name, warm, non-intimidating).
Recommended framing: **Wallet Mantra, powered by Tara** — Tara is the
assistant persona; Wallet Mantra remains the app/brand name. This mirrors
the feedback's own suggested positioning and avoids the two names
competing for primacy.

**What exists today**: All AI-driven copy in the app (warnings, the new
mantra) is unattributed — just shown as plain text with no identity behind
it.

**Fix approach**: Use "Tara" in card copy and labels. Concretely:
- Card heading: **"Tara's Today's Mantra"** or simply **"From Tara"**
  above the generated sentence (exact wording is a small copy decision,
  not a structural one — pick whichever reads more naturally once the
  card is actually built and visible; both are acceptable per this spec).
- The generated sentence itself (from `generate_daily_mantra()` in Issue
  1) does **not** need to contain the word "Tara" inline — e.g. it doesn't
  need to literally say "Tara thinks..."; the persona is established by
  the card's heading/attribution, not by forcing third-person phrasing
  into every generated sentence, which risks sounding stilted. If natural
  third-person phrasing emerges from the prompt without being forced, that's
  fine too — but this is not a hard requirement.
- No backend logic changes are needed for naming — this is presentation
  layer only (card heading text in `QuickAddTab.tsx`).

**Affected file(s)**:
- `frontend/react/src/components/tabs/QuickAddTab.tsx` (card label/heading
  text: "Tara" attribution)

**Acceptance criteria**: The mantra card visibly attributes its insight to
"Tara" (via heading or label), distinguishing it from a generic/unbranded
system message.

**Priority**: Low — cosmetic, but now resolved; no longer pending a
decision.

---

## Explicitly out of scope (deferred, not part of this spec)

To keep this buildable as a small, self-contained pass rather than the
full system described in the reviewed feedback:

- **Nightly cron / scheduled aggregation job** — no Railway cron
  configured today (`railway.toml` has no `[cron]` or scheduled service
  section); this would be new infrastructure, not a flip of a switch.
  Phase 1's on-demand + same-day in-memory caching approach avoids needing
  this entirely.
- **New persistent tables** (`daily_snapshots`, `user_analytics`,
  `mantra_history` as a DB table) — Phase 1's in-memory per-day cache
  substitutes for a persistent `mantra_history` table; the other two
  aren't needed until pattern-recognition insights (category D from the
  feedback's taxonomy) are attempted.
- **Pattern recognition insights** (salary-day spend spikes, recurring
  merchant interval detection, weekend-spend ratios) — these need
  multi-month historical trend computation this spec does not build, and
  are likely unreliable with the data volume a single/few users currently
  have.
- **"Ask Tara" conversational chat layer** — a materially larger feature
  (chat UI, multi-turn context, financial-reasoning prompt design for
  affordability/projection questions); deserves its own dedicated spec,
  not a sub-item here. Note: with "Tara" now confirmed as the persona name
  (Issue 3), a future conversational layer can reuse the same name and
  framing ("Ask Tara") directly — no separate naming decision needed when
  that spec is written.
- **"Money Memories" monthly narrative summaries** and **"Letters from
  your wallet"** — emotionally high-stakes content generation; explicitly
  deferred until the much lower-stakes one-line daily mantra has proven
  the insight-quality bar can be met consistently.
- **"Peace of Mind Score"** — needs real design work on the scoring
  formula before being worth building; a placeholder formula risks
  producing a number that feels arbitrary or unfair.
- **Donut chart de-emphasis** (round 1 feedback) — a separate, smaller
  layout change, not dependent on or blocking this spec; can be done
  independently if desired.
- **History tab "Yesterday — Spent ₹X" summary card** (round 1 feedback)
  — also separate and independent; not included here to keep this spec
  focused on the Today tab only.

---

## Files NOT modified by this spec
- `backend/budget_rules.py` — reused as-is (`get_balance_summary`,
  `get_monthly_spent_by_category`); no changes needed to existing
  functions.
- `backend/models.py` — no schema changes; Phase 1 deliberately avoids
  new tables (see "Explicitly out of scope").
- `frontend/react/src/components/tabs/OverviewTab.tsx`,
  `HistoryTab.tsx` — out of scope; this spec is Today-tab only.

---

## Implementation Order

| # | Issue | Priority | Effort | Files |
|---|-------|----------|--------|-------|
| 1 | Backend mantra generation + endpoint + frontend card | High | ~4–6h | `ai_parser.py`, `main.py`, `QuickAddTab.tsx`, `types/index.ts` |
| 2 | Today tab section reorder | Medium | ~10 min | `QuickAddTab.tsx` (same file as Issue 1 — effectively free once 1 is done) |
| 3 | Persona naming — "Tara" | Low | ~10 min (copy only) | `QuickAddTab.tsx` (same file — card heading text alongside Issues 1/2) |

Issues 1, 2, and 3 will all likely land in the same implementation pass
since they touch the same file (`QuickAddTab.tsx`) — the card's existence
(1), its position (2), and its "Tara" attribution heading (3) are
naturally written together rather than as separate edits.
