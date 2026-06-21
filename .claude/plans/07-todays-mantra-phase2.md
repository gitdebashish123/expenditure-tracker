# Implementation Plan: Today's Mantra — Phase 2
**Spec**: `.claude/specs/07_todays-mantra-phase2.md`
**Date**: 2026-06-22
**Branch**: Not specified in spec or CLAUDE.md — confirm with user before
starting. Recommend a dedicated branch, e.g. `feature/todays-mantra-phase2`
(or continuing on `feature/todays-mantra` if that branch from Phase 1 is
still alive and unmerged) rather than reusing an unrelated sprint branch.

---

## Overview

5 issues, all backend-led except Issue 5 (frontend-only, fully
independent). Re-verified against the actual implemented Phase 1 code
(not just the spec's description) immediately before writing this plan —
`backend/main.py`'s `daily_mantra()`, `backend/ai_parser.py`'s
`generate_daily_mantra()`, `frontend/react/src/components/tabs/QuickAddTab.tsx`'s
`TodaysMantraCard`, and `frontend/react/src/types/index.ts`'s
`DailyMantra` type all match what the spec describes exactly — no drift
since Phase 1 shipped.

Ordered smallest-blast-radius first: Issue 5 (pure frontend styling, zero
backend dependency) → Issue 2 (one-line backend addition) → Issue 1 (the
real prerequisite, slightly larger) → Issue 3 (depends on 1+2) → Issue 4
(depends on 1, touches both backend and frontend).

Note: this order is **risk-ordered**, not the spec's own priority order
(which lists Issue 1 first as highest-impact). Either sequencing is valid;
this plan front-loads the cheapest, lowest-risk items first to bank early
wins, since Issues 1–4 all touch the same two backend files and benefit
from being done as a connected sequence rather than interleaved with
unrelated work.

---

## Item 1 — Mantra card visual distinctness (spec Issue 5)

**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/QuickAddTab.tsx`
(`TodaysMantraCard` only)

**Current state (verified)**:
```tsx
<div className="bg-dark-card border border-white/10 rounded-2xl p-4">
  <p className="text-xs font-syne font-bold uppercase tracking-widest mb-2"
     style={{ color: 'var(--text-sub)' }}>
    🪷 From Tara
  </p>
  <p className="text-white text-sm leading-relaxed">
    {mantra}
  </p>
</div>
```
This is visually identical in structure to other generic cards in the same
file (e.g. the saved-expense cards, the balance card) — same background,
same border treatment.

**What to do**: Add a subtle accent treatment so the card reads as
distinct from data cards, using only existing CSS variables (`--accent`,
`--accent2` — already defined in `index.css`, confirmed in earlier review
of that file during Phase 1 planning):

```tsx
<div
  className="rounded-2xl p-4 border"
  style={{
    background: 'var(--card)',
    borderColor: 'var(--accent)',
    borderOpacity: 0.2,
    boxShadow: '0 0 24px -8px var(--accent2)',
  }}
>
  <p className="text-xs font-syne font-bold uppercase tracking-widest mb-2"
     style={{ color: 'var(--accent)' }}>
    🪷 From Tara
  </p>
  <div className="h-px w-12 mb-3" style={{ background: 'var(--accent)', opacity: 0.4 }} />
  <p className="text-white text-sm leading-relaxed italic">
    {mantra}
  </p>
</div>
```

Key changes from current: heading color shifts to the accent color
(currently `--text-sub`, matching every other muted card label — making it
`--accent` colored is a small but real differentiator), a thin divider
line is added between heading and sentence (the feedback's "divider line"
ask), a soft box-shadow glow using `--accent2` (the feedback's "soft
purple glow" ask, achieved via the existing accent2 variable rather than a
new color), and the sentence itself becomes `italic` (interpreting the
feedback's "handwritten quote style" as italic + whitespace rather than a
literal font change, per the spec's explicit guidance not to introduce a
new typeface).

**Note**: exact shadow/opacity values above are a reasonable starting
point, not gospel — adjust to taste once actually rendered; this is a
visual judgment call best made by looking at it live, not by matching the
plan's numbers exactly.

**Acceptance criteria**: Card is visually distinguishable from other cards
on the Today tab at a glance; no new fonts or colors introduced outside
the existing `--accent`/`--accent2` variable set.

---

## Item 2 — Surface `fixed_unpaid_total` in mantra context (spec Issue 2)

**Scope**: Backend-only
**Files**: `backend/main.py` (`daily_mantra()`), `backend/ai_parser.py`
(`generate_daily_mantra()`)

**Current state (verified)**: `daily_mantra()` already computes
`balance = get_balance_summary(...)` and already has the full dict in
scope (including `fixed_unpaid_total`, confirmed present in
`get_balance_summary`'s return dict in `budget_rules.py`) — but only pulls
`balance["remaining"]` and `balance["total_income"]` into the `context`
dict passed to `generate_daily_mantra()`. The `fixed_unpaid_total` key is
sitting unused in a variable already in scope.

**What to do**:

In `backend/main.py`, `daily_mantra()`, add one line to the `context`
dict construction:
```python
context = {
    "remaining": remaining,
    "days_left": days_left,
    "daily_budget": daily_budget,
    "total_income": balance["total_income"],
    "top_category": top_category,
    "top_category_spent": top_category_spent,
    "fixed_unpaid_total": balance["fixed_unpaid_total"],   # ← new
}
```

In `backend/ai_parser.py`, `generate_daily_mantra()`, update the prompt to
include this figure and instruct on when it's worth mentioning:
```python
prompt = f"""A user's financial snapshot for the rest of this month:
- Remaining balance: ₹{context['remaining']:.0f}
- Days left in month: {context['days_left']}
- Daily budget if spread evenly: ₹{context['daily_budget']:.0f}/day
- Total income this month: ₹{context['total_income']:.0f}
- Top spending category so far: {context.get('top_category') or 'N/A'} (₹{context.get('top_category_spent', 0):.0f})
- Remaining unpaid fixed commitments: ₹{context.get('fixed_unpaid_total', 0):.0f}

Generate ONE warm, encouraging, specific insight sentence (max 30 words).
Rules:
- No guilt, no judgment, no financial jargon.
- Reference at least one concrete number from above.
- Be specific and personal, not a generic motivational quote.
- If remaining unpaid fixed commitments is ₹0, this is worth highlighting
  as a positive — e.g. everything left to spend is discretionary. Only
  mention this when it's true and feels like the most relevant thing to
  say; don't force it into every sentence.
- Use ₹ symbol for amounts.
- Return ONLY the sentence, no preamble, no quotation marks."""
```

Also update the function's docstring to document the new expected context
key, matching the existing docstring's style (it already lists expected
keys).

**Acceptance criteria**: When `fixed_unpaid_total` is 0, the mantra is
capable of reflecting that (not guaranteed every time — phrasing choice
remains the model's, per the prompt's own "only mention when relevant"
instruction).

---

## Item 3 — Month-over-month comparison data in mantra context (spec Issue 1)

**Scope**: Backend-only
**Files**: `backend/main.py` (`daily_mantra()`), `backend/ai_parser.py`
(`generate_daily_mantra()`)

**Current state (verified)**: `daily_mantra()` computes `top_category` via
`max(spent_by_cat, key=spent_by_cat.get)` from the *current* month's
`get_monthly_spent_by_category()` call only. No previous-month data is
fetched anywhere in this function. Separately, `month_over_month()`
(same file, the `/insights/mom/{month_key}` endpoint) already derives
previous month-keys with correct year-rollover handling:
```python
for offset in range(2, -1, -1):
    m = month - offset
    y = year
    while m <= 0:
        m += 12
        y -= 1
    months.append(f"{y:04d}-{m:02d}")
```
This produces `[month-2, month-1, month]` in order. `daily_mantra()`
should reuse the same rollover logic for just one offset (the immediately
preceding month), not duplicate-and-diverge it.

**What to do**:

In `backend/main.py`, `daily_mantra()`, after `top_category` is
determined, compute the previous month's key and fetch that category's
spend for it:

```python
# Previous month-key (same rollover logic as month_over_month())
prev_month = month - 1
prev_year = year
if prev_month <= 0:
    prev_month += 12
    prev_year -= 1
prev_month_key = f"{prev_year:04d}-{prev_month:02d}"

top_category_prev_month_spent = None
if top_category:
    prev_spent_by_cat = get_monthly_spent_by_category(
        session, prev_month_key, user_id=current_user.id
    )
    if top_category in prev_spent_by_cat:
        top_category_prev_month_spent = prev_spent_by_cat[top_category]
```

Add to the context dict:
```python
"top_category_prev_month_spent": top_category_prev_month_spent,
```

In `backend/ai_parser.py`, `generate_daily_mantra()`, the prompt needs a
conditional line — only include the comparison figure when it's not
`None`, and instruct the model accordingly:

```python
comparison_line = ""
if context.get("top_category_prev_month_spent") is not None:
    comparison_line = (
        f"- Same category last month: ₹{context['top_category_prev_month_spent']:.0f}\n"
    )

prompt = f"""A user's financial snapshot for the rest of this month:
- Remaining balance: ₹{context['remaining']:.0f}
- Days left in month: {context['days_left']}
- Daily budget if spread evenly: ₹{context['daily_budget']:.0f}/day
- Total income this month: ₹{context['total_income']:.0f}
- Top spending category so far: {context.get('top_category') or 'N/A'} (₹{context.get('top_category_spent', 0):.0f})
{comparison_line}- Remaining unpaid fixed commitments: ₹{context.get('fixed_unpaid_total', 0):.0f}

Generate ONE warm, encouraging, specific insight sentence (max 30 words).
Rules:
- No guilt, no judgment, no financial jargon.
- Reference at least one concrete number from above.
- Be specific and personal, not a generic motivational quote.
- Only make a comparison to last month if the "Same category last month"
  figure is provided above — never imply a trend you don't have a number
  for.
- If remaining unpaid fixed commitments is ₹0, this is worth highlighting
  as a positive — e.g. everything left to spend is discretionary. Only
  mention this when it's true and feels like the most relevant thing to
  say; don't force it into every sentence.
- Use ₹ symbol for amounts.
- Return ONLY the sentence, no preamble, no quotation marks."""
```

This combines Item 2's `fixed_unpaid_total` line and Item 3's
`comparison_line` into one coherent prompt — if implementing Items 2 and 3
in the same session (recommended, since both touch the same prompt
string), write the final prompt once rather than editing it twice.

**Acceptance criteria**:
- When previous-month data exists for the top category, the context dict
  includes a real number, and the prompt explicitly permits (but doesn't
  force) a comparison.
- When no previous-month data exists (new user, month 1 of usage), the
  comparison line is omitted entirely from the prompt — not sent as
  `None` or `0`, which could mislead the model into thinking ₹0 was
  actually spent last month.
- No fabricated comparisons — verified by reading actual generated output
  during manual testing (see Definition of Done).

---

## Item 4 — Lightweight angle rotation (spec Issue 3)

**Scope**: Backend-only
**Files**: `backend/main.py` only

**Depends on**: Items 2 and 3 (needs `fixed_unpaid_total == 0` and
`top_category_prev_month_spent` to exist as signals to rotate between).

**Current state (verified)**: `daily_mantra()` has exactly one cache dict
today:
```python
_mantra_cache: dict[tuple[int, str], str] = {}
```
No concept of "what angle was used" exists anywhere.

**What to do**:

Add a second small in-memory dict near the existing `_mantra_cache`
declaration:
```python
# Tracks which "angle" was used in the most recent mantra per user, so
# consecutive days don't always lead with the same angle when more than
# one is available. In-memory only, same lifecycle as _mantra_cache —
# resets on restart. Not persisted by design (see spec 07's "Explicitly
# out of scope": no new mantra_history table at this stage).
_mantra_last_type: dict[int, str] = {}
```

In `daily_mantra()`, after computing `top_category_prev_month_spent` and
`fixed_unpaid_total` availability, determine which angles are available
this run:
```python
available_angles = ["forecast"]  # always available
if top_category_prev_month_spent is not None:
    available_angles.append("comparison")
if balance["fixed_unpaid_total"] == 0:
    available_angles.append("commitments")

last_angle = _mantra_last_type.get(current_user.id)
preferred_angles = [a for a in available_angles if a != last_angle] or available_angles
chosen_angle = preferred_angles[0]  # simple deterministic pick; first available non-repeat
```

Pass `chosen_angle` into `generate_daily_mantra()` as an additional
argument (not part of the numeric `context` dict — it's an instruction,
not a data point):
```python
mantra = generate_daily_mantra(context, preferred_angle=chosen_angle)
_mantra_last_type[current_user.id] = chosen_angle
```

In `backend/ai_parser.py`, update `generate_daily_mantra`'s signature:
```python
def generate_daily_mantra(context: dict, preferred_angle: str = "forecast") -> str:
```
And append a soft steering line to the prompt before the final "Return
ONLY the sentence" instruction:
```python
angle_hint = {
    "forecast": "Today, lean toward a forecast/pacing angle (daily budget, days left).",
    "comparison": "Today, lean toward comparing this month to last month for the top category.",
    "commitments": "Today, lean toward highlighting that fixed commitments are fully covered.",
}.get(preferred_angle, "")
```
Insert `angle_hint` into the prompt as one more rule line. This is a soft
steer, not a hard constraint — the model still writes the actual sentence
and may not follow it literally if the numbers don't support it well;
that's acceptable per the spec's own "best-effort variation" acceptance
criterion.

**Acceptance criteria**: Across two consecutive days where more than one
angle is available, the chosen angle differs (verified via the
`_mantra_last_type` dict's behavior, not by guaranteeing the generated
text itself uses different words — the steer is best-effort). When only
one angle is available, generation still proceeds normally with no error.

---

## Item 5 — "Why?" reveal (spec Issue 4)

**Scope**: Backend + Frontend
**Files**: `backend/main.py` (`daily_mantra()` response shape),
`frontend/react/src/types/index.ts` (`DailyMantra`),
`frontend/react/src/components/tabs/QuickAddTab.tsx`
(`TodaysMantraCard`)

**Depends on**: Item 3 (for `top_category_prev_month_spent` to exist as
something worth showing).

**Current state (verified)**: `daily_mantra()` returns
`{"mantra": mantra}` only — no context numbers reach the frontend.
`DailyMantra` in `types/index.ts` is `{ mantra: string }`. The cache
(`_mantra_cache`) stores only the sentence string, not the context —
meaning a cache hit currently can't supply "Why?" data either, since the
numbers were never retained.

**What to do**:

### Backend: cache shape change

The existing `_mantra_cache: dict[tuple[int, str], str]` needs to store
the context alongside the sentence, since a cache hit (same-day revisit)
must still be able to answer "Why?" without recomputing. Change to:
```python
_mantra_cache: dict[tuple[int, str], dict] = {}
```
storing `{"mantra": mantra, "context": context}` as the cached value
instead of the bare string. Update both the cache-read branch and the
cache-write branch accordingly:
```python
if cache_key in _mantra_cache:
    return _mantra_cache[cache_key]
...
result = {
    "mantra": mantra,
    "context": {
        "remaining": remaining,
        "days_left": days_left,
        "top_category": top_category,
        "top_category_spent": top_category_spent,
        "top_category_prev_month_spent": top_category_prev_month_spent,
        "fixed_unpaid_total": balance["fixed_unpaid_total"],
    },
}
_mantra_cache[cache_key] = result
return result
```

### Frontend: type update

```typescript
export interface DailyMantra {
  mantra: string;
  context: {
    remaining: number;
    days_left: number;
    top_category: string | null;
    top_category_spent: number;
    top_category_prev_month_spent: number | null;
    fixed_unpaid_total: number;
  };
}
```

### Frontend: `TodaysMantraCard`

Update the fetch type and add a collapsible "Why?" section:
```tsx
function TodaysMantraCard() {
  const { selMonth } = useMonth();
  const [data, setData] = useState<DailyMantra | null>(null);
  const [showWhy, setShowWhy] = useState(false);

  useEffect(() => {
    api.get<DailyMantra>(`/insights/mantra/${selMonth}`)
      .then(r => setData(r.data))
      .catch(() => {});
  }, [selMonth]);

  if (!data) return null;
  const { mantra, context } = data;

  return (
    <section>
      <div /* ...Item 1's styling... */>
        <p /* heading */>🪷 From Tara</p>
        <div /* divider */ />
        <p className="text-white text-sm leading-relaxed italic">
          {mantra}
        </p>
        <button
          onClick={() => setShowWhy(v => !v)}
          className="text-xs mt-2 underline"
          style={{ color: 'var(--text-muted)' }}
        >
          {showWhy ? "Hide" : "Why?"}
        </button>
        {showWhy && (
          <div className="mt-2 text-xs space-y-1" style={{ color: 'var(--text-sub)' }}>
            {context.top_category && (
              <p>
                Top category: {context.top_category} — {fmtInr(context.top_category_spent)} this month
                {context.top_category_prev_month_spent != null &&
                  ` vs ${fmtInr(context.top_category_prev_month_spent)} last month`}
              </p>
            )}
            <p>{context.days_left} days left, {fmtInr(context.remaining)} remaining</p>
            {context.fixed_unpaid_total === 0 && (
              <p>All fixed commitments paid this month</p>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
```

No new network call on "Why?" click — `context` is already present in the
same response that supplied `mantra`.

**Acceptance criteria**: "Why?" toggle appears below the sentence;
clicking it reveals real numbers with zero additional network requests;
collapsed by default; doesn't change card height/layout when collapsed.

---

## Execution Order

| # | Item | Effort | Risk | Depends on |
|---|------|--------|------|------------|
| 1 | Card visual distinctness | ~30 min | None — pure styling | — |
| 2 | Surface `fixed_unpaid_total` | ~20 min | Low — one field, already computed | — |
| 3 | Month-over-month comparison data | ~1.5h | Low — reuses existing rollover logic and existing query function | — |
| 4 | Lightweight angle rotation | ~1h | Low — new in-memory dict, no schema change | Items 2, 3 |
| 5 | "Why?" reveal | ~1h | Low — cache shape change needs care (read AND write branches) | Item 3 |

Recommend implementing Items 2 and 3 together in one backend session since
both edit the same prompt string in `generate_daily_mantra()` — building
the final combined prompt once avoids editing it twice. Item 4 naturally
follows once both data points exist. Item 5's cache shape change (string →
dict) is the one part of this plan that touches existing working code
(not purely additive) — review that diff carefully, since getting the
cache read/write mismatch wrong would silently break the existing
same-day caching behavior from Phase 1.

---

## Definition of Done
- `cd frontend/react && npm run build` passes (zero TypeScript errors,
  zero ESLint warnings)
- Backend starts cleanly with no import errors
- Manually verified: with at least one full previous month of expense
  data, the mantra is capable of producing a comparison-grounded sentence
  (Item 3) — confirm by reading actual generated output, not just that
  the code runs
- Manually verified: with a user who has fully paid fixed expenses this
  month, the mantra is capable of reflecting that (Item 2)
- Manually verified: across two consecutive days (or by manually clearing
  `_mantra_cache`/`_mantra_last_type` to simulate a new day), the chosen
  angle differs when more than one is available (Item 4)
- Manually verified: "Why?" toggle reveals real numbers with no new
  network request visible in browser devtools (Item 5)
- Manually verified: a brand-new user with no previous-month data still
  gets a mantra with no error (Item 3's `None`-handling path)
- Card visually distinct from other Today-tab cards at a glance (Item 1)
- Re-confirm Phase 1's original acceptance criteria still hold — a failed
  mantra fetch should still not break the rest of the Today tab; this
  plan doesn't change that error-handling path, but worth re-verifying
  given the response shape changed (cache value structure, endpoint
  return shape)
