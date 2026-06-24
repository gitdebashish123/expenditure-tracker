# Implementation Plan: Today's Mantra — Phase 1
**Spec**: `.claude/specs/06_todays-mantra-phase1.md`
**Date**: 2026-06-22
**Branch**: Not specified in spec or CLAUDE.md — confirm with user before
starting. Given this is new-feature work (not a continuation of the
06261-ui-enhancement bug-fix sprint), recommend a dedicated branch, e.g.
`feature/todays-mantra`, rather than reusing
`feature/sprint06261-ui-enhancement`. Confirm before implementation.

---

## Overview

3 items, all landing in the same two files in practice (`ai_parser.py` +
`main.py` on the backend, `QuickAddTab.tsx` + `types/index.ts` on the
frontend). Item 1 is the real work; Items 2 and 3 are small follow-ons in
the same component that naturally get written in the same pass as Item 1's
card, per the spec's own Implementation Order note.

No new database tables, no cron job, no new dependencies — confirmed
against current code that everything Phase 1 needs already exists:
`get_balance_summary()` and `get_monthly_spent_by_category()` in
`budget_rules.py` are unchanged and sufficient; `budget_projection()` in
`main.py` already has the `days_left` / `days_in_month` calculation
pattern to copy; `ai_parser.py`'s existing `get_budget_insight()` is the
working prompt-pattern template (compute numbers in Python, ask Claude for
one short sentence).

Ordered smallest-blast-radius first: backend function → backend endpoint →
frontend type → frontend card (with reorder + Tara copy folded in, since
all three touch the same render block).

---

## Pre-implementation note: model ID

`ai_parser.py`'s two existing functions both call
`model="claude-sonnet-4-5-20250929"`. The new `generate_daily_mantra()`
function must use this **same** model id — copy it from the existing file,
don't introduce a different one. (Context: a previous incident in this
codebase involved a retired model id, `claude-sonnet-4-20250514`, being
hardcoded in a different part of the AI parsing logic and causing a
production 422 error. Confirm whichever id is copied is still valid at
implementation time, the same way that incident was fixed.)

---

## Item 1 — Backend: `generate_daily_mantra()` + `GET /insights/mantra/{month_key}` + frontend card

**Scope**: Backend + Frontend
**Files**:
- `backend/ai_parser.py` — new function
- `backend/main.py` — new endpoint
- `frontend/react/src/types/index.ts` — new response type
- `frontend/react/src/components/tabs/QuickAddTab.tsx` — new card component
  + section

### Backend: `ai_parser.py`

Add `generate_daily_mantra(context: dict) -> str`, placed after the
existing `get_budget_insight` function (end of file). Do not modify
`get_budget_insight` itself — it stays as-is, scoped to single-category
budget-breach warnings.

```python
def generate_daily_mantra(context: dict) -> str:
    """
    Generate a single warm, personal daily insight from precomputed
    balance/spending numbers. Distinct from get_budget_insight, which is
    scoped to single-category budget-breach warnings only.

    Expected context keys:
        remaining: float
        days_left: int
        daily_budget: float       # remaining / days_left, 0 if days_left == 0
        total_income: float
        top_category: str | None
        top_category_spent: float
    """
    prompt = f"""A user's financial snapshot for the rest of this month:
- Remaining balance: ₹{context['remaining']:.0f}
- Days left in month: {context['days_left']}
- Daily budget if spread evenly: ₹{context['daily_budget']:.0f}/day
- Total income this month: ₹{context['total_income']:.0f}
- Top spending category so far: {context.get('top_category') or 'N/A'} (₹{context.get('top_category_spent', 0):.0f})

Generate ONE warm, encouraging, specific insight sentence (max 30 words).
Rules:
- No guilt, no judgment, no financial jargon.
- Reference at least one concrete number from above.
- Be specific and personal, not a generic motivational quote.
- Use ₹ symbol for amounts.
- Return ONLY the sentence, no preamble, no quotation marks."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
```

Note: prompt deliberately omits any instruction to attempt salary-spike
detection, weekend-ratio analysis, or recurring-merchant patterns — the
context dict simply doesn't contain that data, so the model can't invent
trend claims it has no basis for. This keeps the sentence honest given
what's actually computed (see spec's "Explicitly out of scope").

### Backend: `main.py`

Add a small in-process cache (module-level dict, no new file) near the top
of the `# ── Insights` section, and the new endpoint immediately after
`budget_projection()` (before the `# ── Data Export` comment block, to
keep all `/insights/*` routes grouped together as they already are):

```python
# ── Mantra cache (in-memory, per-process, resets on restart) ────────────────
# Keyed by (user_id, date_string) — avoids calling Claude on every page load.
# Not a DB table by design for Phase 1 — see spec 06's "Explicitly out of
# scope" section. Revisit only if this proves insufficient in practice.
_mantra_cache: dict[tuple[int, str], str] = {}


@app.get("/insights/mantra/{month_key}")
def daily_mantra(month_key: str, session: Session = Depends(get_session),
                 current_user: User = Depends(get_current_user)):
    from backend.ai_parser import generate_daily_mantra
    import calendar
    from datetime import date as dt

    today = dt.today()
    cache_key = (current_user.id, today.isoformat())
    if cache_key in _mantra_cache:
        return {"mantra": _mantra_cache[cache_key]}

    year, month = map(int, month_key.split("-"))
    days_in_month = calendar.monthrange(year, month)[1]
    days_left = max(days_in_month - today.day, 0) if month_key == today.strftime("%Y-%m") else 0

    balance = get_balance_summary(session, month_key, user_id=current_user.id)
    spent_by_cat = get_monthly_spent_by_category(session, month_key, user_id=current_user.id)

    top_category = None
    top_category_spent = 0
    if spent_by_cat:
        top_category = max(spent_by_cat, key=spent_by_cat.get)
        top_category_spent = spent_by_cat[top_category]

    remaining = balance["remaining"]
    daily_budget = remaining / days_left if days_left > 0 else remaining

    context = {
        "remaining": remaining,
        "days_left": days_left,
        "daily_budget": daily_budget,
        "total_income": balance["total_income"],
        "top_category": top_category,
        "top_category_spent": top_category_spent,
    }

    try:
        mantra = generate_daily_mantra(context)
    except Exception:
        # Fail silently at the API layer too — frontend already handles
        # a failed fetch by simply not rendering the card (see Item 1,
        # frontend section). Returning a 200 with empty string keeps the
        # frontend's existing "don't render if falsy" logic simple,
        # though raising 500 and letting the frontend catch() it is
        # equally valid — pick whichever is simpler at implementation time.
        raise HTTPException(status_code=502, detail="Mantra generation failed")

    _mantra_cache[cache_key] = mantra
    return {"mantra": mantra}
```

Import note: `generate_daily_mantra` is imported locally inside the
function rather than added to the existing top-of-file
`from backend.ai_parser import parse_expense_input` line — either works;
moving it to the top-level import alongside `parse_expense_input` is
slightly cleaner and preferred if convenient, but not required.

**Cache behavior to verify at implementation time**: `days_left` is
computed as `0` for any `month_key` that isn't the current month (e.g. if
the user is viewing a past month via `selMonth`). In that case
`daily_budget` is just set equal to `remaining`, which avoids a
division-by-zero — confirm this reads sensibly in the generated sentence,
or consider simply not calling this endpoint at all when `selMonth` isn't
the current month (the frontend's `QuickAddTab.tsx` doesn't currently use
`selMonth` to look at past months in its UI anyway — the Today tab is
inherently "today," so this edge case may not be reachable in practice;
worth a quick sanity check rather than over-engineering for it).

### Frontend: `types/index.ts`

Add near the other small response-shape interfaces (e.g. near
`DueReminder`):
```typescript
export interface DailyMantra {
  mantra: string;
}
```

### Frontend: `QuickAddTab.tsx`

Add a new component, `TodaysMantraCard`, either inline in this file (above
the `QuickAddTab` export, matching how this file is already structured
with no separate sub-component file) or as a new file under
`frontend/react/src/components/shared/TodaysMantraCard.tsx` if preferring
consistency with how `BudgetHealthCard` etc. are separated out — either is
fine; inline is slightly faster to ship for Phase 1 given it's only used
in one place.

```tsx
function TodaysMantraCard() {
  const { selMonth } = useMonth();
  const [mantra, setMantra] = useState<string | null>(null);

  useEffect(() => {
    api.get<{ mantra: string }>(`/insights/mantra/${selMonth}`)
      .then(r => setMantra(r.data.mantra))
      .catch(() => {}); // fail silently — card simply doesn't render
  }, [selMonth]);

  if (!mantra) return null;

  return (
    <section>
      <div className="bg-dark-card border border-white/10 rounded-2xl p-4">
        <p className="text-xs font-syne font-bold uppercase tracking-widest mb-2"
           style={{ color: 'var(--text-sub)' }}>
          🪷 From Tara
        </p>
        <p className="text-white text-sm leading-relaxed">
          {mantra}
        </p>
      </div>
    </section>
  );
}
```

Card heading text "🪷 From Tara" implements spec Issue 3's decision
directly — exact wording ("From Tara" vs "Tara's Today's Mantra") is, per
the spec, a free choice; "From Tara" is used here as the more compact
option but can be swapped at implementation time with no other changes
needed.

Render `<TodaysMantraCard />` as the **first** child inside the outer
`<div className="space-y-6">`, before the existing
`{/* ── Section 1: NL Input Form ───────────────────── */}` comment and
its `<section>`. This single placement decision implements spec Issue 2
(reorder) at the same time as Item 1 — there is no separate reorder step
needed; building the card in the right position the first time accomplishes
both.

**Acceptance criteria** (combining spec Issues 1, 2, 3 since they land
together):
- Opening the Today tab shows a card labelled "🪷 From Tara" above the
  "Log Expenses" section, containing one sentence generated from the
  user's actual current balance/spending data.
- Revisiting the tab later the same day shows the same sentence (cache
  hit, no new API call content change — though a new network call still
  fires each time per the current `useEffect`, it returns the cached
  value).
- A new calendar day produces a newly-generated sentence.
- If `GET /insights/mantra/{month_key}` fails for any reason, the rest of
  the Today tab (NL input, favourites, today's entries) renders normally —
  the mantra card simply doesn't appear, no error banner.
- The card is the first visible section, above the NL input form.
- The card is attributed to "Tara" via its heading.

**Priority**: High (Item 1's backend half) / Medium (the reorder, folded
in) / Low (the naming, folded in) — per spec; implemented as one unit in
practice.

---

## Execution Order

| # | Step | Effort | Risk | Depends on |
|---|------|--------|------|------------|
| 1 | `generate_daily_mantra()` in `ai_parser.py` | ~45 min | Low — isolated new function, no existing code touched | — |
| 2 | `GET /insights/mantra/{month_key}` + in-memory cache in `main.py` | ~1.5h | Low — new route + new module-level dict, no existing routes modified | Step 1 |
| 3 | `DailyMantra` type in `types/index.ts` | ~5 min | None | — |
| 4 | `TodaysMantraCard` component + placement in `QuickAddTab.tsx` | ~1.5h | Low — additive only, existing sections unmoved except for the new card prepended | Steps 2, 3 |

Total: roughly half a day of focused work, consistent with the spec's own
~4–6h estimate for Issue 1 (Issues 2/3 add negligible extra time since
they're folded into the same component edit).

---

## Definition of Done
- `cd frontend/react && npm run build` passes (zero TypeScript errors,
  zero ESLint warnings)
- Backend starts cleanly (`uv run uvicorn backend.main:app --reload`) with
  no import errors from the new `generate_daily_mantra` function or the
  new endpoint
- Manually verified: opening the Today tab (logged in as a user with at
  least some expenses logged this month) shows the mantra card above the
  input form, with a sentence that references real numbers from that
  user's data — not a generic placeholder
- Manually verified: reloading the page within the same day still shows a
  card (cache working, no error)
- Manually verified: temporarily breaking the endpoint (e.g. stopping the
  backend) confirms the rest of the Today tab still renders normally with
  no error banner, no broken layout
- Confirm the model id used in `generate_daily_mantra` matches the
  existing, working id already used elsewhere in `ai_parser.py` (see
  "Pre-implementation note" above) — do not introduce a different or
  potentially-stale model id
