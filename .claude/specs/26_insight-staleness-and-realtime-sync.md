# Spec 26 — Insight/Story/Mantra Staleness + First-Month Comparison Fix
**Date**: 2026-06-29
**Status**: ✅ Complete (implemented 2026-06-29) — ⚠️ **Item 1 only partially applied; see follow-up**
**Branch**: `feature/sprint06261-ui-enhancement` *(confirm active branch before starting)*
**Follows**: `25_settings-tab-redesign.md`
**Follow-up**: `27_insight-staleness-followup-invalidation-gaps.md` (June-30 verification found `toggle_paid`, `update_fixed_amount`, `log_from_template`, `bulk_delete_expenses` still missing the Item 1 invalidation call)
**Source**: live self-feedback, June 28 2026 (WhatsApp screenshot, 5:21 PM) — the AI-generated
"month in one sentence", "Insight", and "Today's mantra" are out of sync with the live balance.

---

## Context

All three AI-generated narrative surfaces (**Monthly Story** / "June in one sentence",
**Monthly Insight** / "✨ Insight", and **Today's Mantra**) are served from in-memory
caches in `backend/main.py`. The caches are **not invalidated by every mutation that
changes the underlying numbers**, and the mantra cache key is **mismatched** with its
invalidation key, so they go stale the moment the user toggles a bill, edits income, or
changes a cap.

**Evidence (screenshot, June 28 5:21 PM):**
- KPI card: **Bills Paid ₹97,567 / Out of ₹97,567** → 100% paid
- Monthly breakdown: **Balance ₹1,297**
- "June in one sentence" still reads: **"Bills are 98% paid with ₹3,359 remaining for the
  final two days."** ← stale on both the % (98 vs 100) and the remaining (₹3,359 vs ₹1,297)

A fifth, separate issue: the **Insight** asserts comparative figures ("variable spending
jumped 72%") for a user who only began entering data **this month**, i.e. there is no
meaningful prior month to compare against.

This spec is **backend-heavy** (caching + insight context logic) with one small frontend
guard for first-month detection.

---

## Root cause analysis (verified against current code)

### Cache wiring — `backend/main.py`

```python
# line 1276
_story_cache:   dict[tuple[int, str], str] = {}   # key = (user_id, month_key)
_insight_cache: dict[tuple[int, str], str] = {}   # key = (user_id, month_key)

# line 1282
def _invalidate_month_caches(user_id, month_key):
    _story_cache.pop((user_id, month_key), None)
    _mantra_cache.pop((user_id, month_key), None)   # ← wrong key for mantra (see below)
    _insight_cache.pop((user_id, month_key), None)
```

`_invalidate_month_caches` is called from **only the expense CRUD endpoints**:
- `POST /expenses/parse` (line 584)
- `POST /expenses/manual` (line 610)
- `PATCH /expenses/{id}` (lines 644, 646)
- `DELETE /expenses/{id}` (line 672)

**Mutations that change the numbers but DO NOT invalidate** (confirmed — no call present):
| Endpoint | Line | Affects |
|---|---|---|
| `PATCH /fixed/{id}/toggle` | 691 | `fixed_paid_total` / `fixed_unpaid_total` → bills %, remaining → **Issue #1** |
| `PATCH /fixed/{id}/amount` | 704 | fixed totals, remaining |
| `POST /income` | 1022 | `total_income`, remaining → **Issue #2** |
| `PUT /income/{id}` | 1078 | `total_income`, remaining → **Issue #2** |
| `DELETE /income/{id}` | 1062 | `total_income`, remaining → **Issue #2** |
| `PUT /budget` | 992 | caps (insight context) |
| `PATCH /pools/entries/{id}/toggle` | 1822 | paid totals, remaining |
| `PATCH /pools/entries/{id}` | 1800 | amounts |
| `DELETE /pools/entries/{id}` | 1836 | totals |
| `POST /pools/{id}/entries/{month}` | 1773 | totals |
| `POST/PUT/DELETE /fixed-templates/*` | 857/874/913 | next-seed totals |

### Mantra cache key mismatch — **Issue #4**

`daily_mantra` (line 1288) **stores** under a *date* key but invalidation **pops** a
*month* key — they can never match, so mantra invalidation is a complete no-op:

```python
# line 1295 — stored under date
cache_key = (current_user.id, today.isoformat())     # e.g. (1, "2026-06-28")
_mantra_cache[cache_key] = result                    # line 1369

# line 1284 — invalidation pops month
_mantra_cache.pop((user_id, month_key), None)        # e.g. (1, "2026-06")  ← never hits
```

Net effect: the mantra is generated **once per calendar day** and frozen, regardless of any
balance change that day → **out of sync with real-time balance**.

### First-month comparison — **Issue #5**

`get_balance_summary` (`budget_rules.py:77`) **never returns `None`** — it always returns a
populated dict (zero-filled when no data). Consequences:

1. **Backend** `monthly_insight` (line 1446) detects first month via
   `prev_balance.get("variable_total", 0) == 0`. This is the *only* guard, and it's fragile:
   any stray prior-month variable row (test data, a single mis-dated expense) flips it to the
   comparative branch.
2. The comparative prompt (`ai_parser.py:230`) only *asks* the model not to cite % changes
   "unless both … non-zero and meaningful" — the model does not reliably obey, so "jumped
   72%" leaks through.
3. **Frontend** `OverviewTab.tsx:265` computes `isFirstMonth = prevSummary === null`, but
   `/summary/{prevMonthKey}` returns a **zero-filled object, never null** → `isFirstMonth`
   is effectively *always false* → the `isSafeInsight()` comparative-term filter
   (lines 178-182) never blocks anything.

---

## Item 1 — Invalidate caches on every balance-affecting mutation
**Scope**: Backend-only · **Priority**: highest (fixes #1, #2, #3)

Add `_invalidate_month_caches(current_user.id, <month_key>)` after `session.commit()` in
every mutation listed in the table above. For endpoints where `month_key` is on the row
object, derive it from the affected record (e.g. `exp.month_key`, `entry.month_key`). For
`PUT /budget` (caps are not month-scoped) invalidate the **current** month at minimum;
simplest correct option is a small `_invalidate_all_user_caches(user_id)` helper that clears
every cache entry whose key starts with `user_id` — use that for budget/template changes
where the affected month set is ambiguous.

**Acceptance:** after toggling a bill paid / editing income / changing a cap, re-fetching
`/insights/story`, `/insights/monthly-insight`, `/insights/mantra` returns text reflecting
the new numbers (no stale %, no stale remaining).

---

## Item 2 — Fix mantra cache key + invalidation
**Scope**: Backend-only · **Priority**: high (fixes #4) · depends on Item 1's helper

Two coupled changes in `daily_mantra` (line 1288) and `_invalidate_month_caches`:

- Make the stored key and the invalidation key consistent. Recommended: key the mantra by
  `(user_id, month_key, today.isoformat())` so it's both per-day *and* invalidatable per
  month; then in `_invalidate_month_caches` pop **all** mantra entries matching
  `(user_id, month_key, *)`:
  ```python
  for k in [k for k in _mantra_cache if k[0] == user_id and k[1] == month_key]:
      _mantra_cache.pop(k, None)
  ```
- Alternatively, adopt the `_invalidate_all_user_caches(user_id)` helper from Item 1 and
  have it clear mantra entries by `user_id` prefix too — simpler, slightly broader.

**Acceptance:** logging an expense (or any Item-1 mutation) on the current day regenerates
the mantra against the updated balance on next fetch; mantra still caches within a day when
nothing changed.

---

## Item 3 — Decide caching policy for the *current* month
**Scope**: Backend-only · **Priority**: medium · design decision needed

Even with perfect invalidation, the current (live) month changes constantly. Two options —
**pick one in the plan**:

- **(A) Don't cache the current month at all.** In `monthly_story` / `monthly_insight`,
  only read/write the cache when `month_key < current_month`. Past months are immutable, so
  they stay cached forever; the live month is always freshly generated. Costs one extra LLM
  call per dashboard load for the current month.
- **(B) Short TTL on the current month** (e.g. 60-120 s) while keeping past months permanent.
  Fewer LLM calls, but a bounded window of staleness remains.

**Recommendation: (A)** — correctness over a marginal LLM-cost saving, and it makes the
"instantly reflects" expectation from the feedback literally true. Item 1's invalidation
still matters for past-month edits and to bound option (B) if chosen.

**Acceptance:** changing today's numbers and reloading the Overview shows an updated
story/insight without any manual cache reset.

---

## Item 4 — Robust first-month detection + hard guard on comparative insight
**Scope**: Backend + Frontend · **Priority**: medium (fixes #5)

**Backend** (`monthly_insight`, line 1446):
- Replace the fragile `variable_total == 0` check with a real "has the user any tracked
  activity before this month?" test — e.g. count `Expense` (and `IncomeEntry`) rows for this
  user with `month_key < this month`. If none, `is_first_month = True`. (Add a small helper
  in `budget_rules.py`.)
- When **not** first month, only pass `prev_variable_total` into the prompt if it is
  **non-zero**; otherwise force the first-month (non-comparative) prompt branch so the model
  can never be handed a near-zero denominator that produces inflated percentages.

**Frontend** (`OverviewTab.tsx`):
- `isFirstMonth` must not rely on `prevSummary === null` (the endpoint never returns null).
  Derive it from whether the previous summary has any real activity
  (`prevSummary == null || prevSummary.balance.variable_total === 0`), or better, expose an
  explicit `is_first_month` flag from a backend endpoint and consume that.
- Keep `isSafeInsight()` as a backstop, but it should now actually fire for true first-month
  users.

**Acceptance:** a user whose first entries are in the current month sees an encouraging,
**non-comparative** insight (no "jumped X%", no "vs last month").

---

## Files
- `backend/main.py` — cache invalidation calls (Items 1, 2), current-month cache policy
  (Item 3), first-month detection in `monthly_insight` (Item 4)
- `backend/budget_rules.py` — new helper(s): prior-activity check for first-month detection
- `backend/ai_parser.py` — only if Item 4 needs the comparative prompt hardened further
- `frontend/react/src/components/tabs/OverviewTab.tsx` — first-month derivation (Item 4)

## Order of execution (smallest blast radius first)
1. **Item 1** — additive invalidation calls; isolated, no behaviour change beyond freshness.
2. **Item 2** — mantra key fix; small, depends on Item 1's helper.
3. **Item 4** — first-month logic; backend + one frontend line.
4. **Item 3** — caching-policy decision; touches the read path of two endpoints, do last.

## Out of scope
- Persisting caches across process restart (still in-memory; acceptable).
- Redesign of the story/insight/mantra copy or prompts beyond the first-month guard.
- Any visual/layout change to the Overview cards (the render code is already correct — the
  bug is purely data freshness).

## Note for implementers
The frontend render for Story (`OverviewTab.tsx:318-357`) and Insight (lines 366-378) is
**intact and correct** — earlier suspicion that a commit "removed" them was wrong (verified
across commits `b233121`, `fa59c07`, `44a4909`). They render `null` only because the backend
returned stale/failed data. This spec fixes the data path, not the JSX.
