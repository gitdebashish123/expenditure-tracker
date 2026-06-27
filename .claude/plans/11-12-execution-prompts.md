# Execution Prompts: Sprint 11 Remaining + Sprint 12
**Date**: 2026-06-27
**Plan 11 remaining**: Items 9b (F2a), 10 (F4), 11 (W1) — 3 prompts
**Plan 12**: Items 1–8 — 6 prompts (backend grouped, frontend by scenario)

---

# ── SPRINT 11 REMAINING ────────────────────────────────────────────

## Prompt 11-A — Item 9b (F2a): First-month prompt branching + frontend safety net

```
Read `.claude/plans/11-overview-review-fixes.md` Item 9 (F2/F2a section) and
`.claude/specs/11_overview-review-fixes.md` section F2a before making any changes.

This item has TWO parts — backend and frontend. Do them in order.

─── BACKEND ───
Read `backend/main.py`. Find the existing `/insights/monthly-insight/{month_key}` endpoint
added in sprint 11 Item 9.

It currently uses a single prompt regardless of whether the user has prior month data.
The fix is to branch the prompt on `is_first_month`.

Step 1 — Detect first month:
  is_first_month = (prev_balance is None or prev_balance.get("variable_total", 0) == 0)

Step 2 — Extract these variables before the if/else:
  top_category  = categories[0]["category"] if categories else "N/A"
  top_amount    = categories[0]["total"]    if categories else 0
  savings_total = balance.get("savings_total", 0)
  savings_pct   = round(savings_total / balance["total_income"] * 100) if balance["total_income"] else 0
  unpaid_count  = balance.get("fixed_unpaid_count", 0)  # adapt to actual field name in the balance dict

Step 3 — When is_first_month is True, use this prompt:
  "This is the user's first tracked month in Wallet Mantra. Generate exactly ONE short,
   encouraging, forward-looking observation (maximum 20 words). Do not reference any
   comparison to prior months, percentages, or changes. Focus only on what is notable
   or positive about this month's actual data.

   Month: {month_key}
   Top spending category: {top_category} at ₹{top_amount}
   Savings this month: ₹{savings_total} ({savings_pct}% of income)
   Bills paid: {'all' if unpaid_count == 0 else f'{unpaid_count} remaining'}

   Respond with a single sentence only. No preamble."

Step 4 — When is_first_month is False, keep the existing prompt but append this guard line:
  "Do not mention percentage changes unless both the current month and prior month values
   are non-zero and meaningful."

Do NOT change the cache logic, error handling, or endpoint path.
Adapt all field names to match what actually exists in the balance dict — read the dict
structure before writing.

─── FRONTEND ───
Read `frontend/react/src/components/tabs/OverviewTab.tsx`. Find the monthlyInsight card
added in sprint 11 Item 9 — it lives inside the Monthly Breakdown column (`flex flex-col
gap-3`), below `<BalanceBreakdown />`, and uses `flex-1` to fill remaining height.

Do NOT move the card. Its current position is correct and final.

Add an isSafeInsight guard so first-month users never see comparative language even if
the backend slips through:

  const isSafeInsight = (text: string, isFirstMonth: boolean): boolean => {
    if (!isFirstMonth) return true;
    const comparativeTerms = ["% from", "last month", "compared to", "jumped",
                              "increased by", "decreased by"];
    return !comparativeTerms.some(term => text.toLowerCase().includes(term));
  };

  const isFirstMonth = prevSummary === null;

Replace the existing render condition on the Insight card:
  {monthlyInsight && ( ... )}
with:
  {monthlyInsight && isSafeInsight(monthlyInsight, isFirstMonth) && ( ... )}

Also confirm the card's root div retains `flex-1` so column height parity is preserved:
  <div
    className="flex-1 rounded-2xl border p-4"
    style={{ borderColor: "var(--border)", background: "var(--card)" }}
  >

Place isSafeInsight and isFirstMonth near the other derived variables above the return,
not inside the JSX.

Confirm TypeScript build clean after both changes.
```

---

## Prompt 11-B — Item 10 (F4): Remove Financial Snapshot heading; reduce KPI tiles to 3

```
Read `.claude/plans/11-overview-review-fixes.md` Item 10 and
`.claude/specs/11_overview-review-fixes.md` section F4 before making any changes.

Read `frontend/react/src/components/tabs/OverviewTab.tsx`. Find Section 0 —
the block that renders the "Financial Snapshot" heading and the KPI tile grid.

Make exactly three changes:

1. Remove the "Financial Snapshot" <h2> (or equivalent heading element) and its
   wrapping section label entirely. The KPI cards should have no named heading above them.

2. In the tiles array, remove the 4th tile — the "Pending Bills" or "All Bills Clear ✓"
   tile. The Bills Paid tile already shows this information via its subtitle (implemented
   in sprint 11 Item 2 / P1). Do not touch the other 3 tiles.

3. Change the KPI grid wrapper from grid-cols-2 to grid-cols-3 so the 3 tiles sit in a
   single row.

Do NOT change any other section, any tile content, or any subtitle logic.

Confirm:
- No "Financial Snapshot" text anywhere in the rendered output.
- Exactly 3 tiles: Remaining, Income, Bills Paid.
- Single grid-cols-3 row.
- TypeScript build clean.
```

---

## Prompt 11-C — Item 11 (W1): What Changed? gap detection

```
Read `.claude/plans/11-overview-review-fixes.md` Item 11 and
`.claude/specs/11_overview-review-fixes.md` section W1 before making any changes.

Read `frontend/react/src/components/tabs/OverviewTab.tsx`. Find the What Changed?
section — the IIFE or block that builds and renders the `changes` array.

This item is FRONTEND ONLY. Three steps:

Step 1 — Add isConsecutiveMonth helper. Place it near the top of the What Changed? block,
before any changes array is built:

  const isConsecutiveMonth = (current: string, prior: string): boolean => {
    const [cy, cm] = current.split("-").map(Number);
    const [py, pm] = prior.split("-").map(Number);
    const expectedPriorMonth = cm === 1 ? 12 : cm - 1;
    const expectedPriorYear  = cm === 1 ? cy - 1 : cy;
    return py === expectedPriorYear && pm === expectedPriorMonth;
  };

Step 2 — After the existing curr / prev derivation, add:
  const hasValidComparison = prev !== null && isConsecutiveMonth(curr, prev);

Step 3 — Wrap the existing comparison rows JSX in a hasValidComparison guard.
When false, show the gap notice instead:

  {hasValidComparison ? (
    <div>
      {/* existing changes.map rows — do NOT change these */}
      {/* existing View all button — do NOT change this */}
    </div>
  ) : (
    <div className="py-4 text-center space-y-1">
      <p className="text-sm" style={{ color: "var(--text-sub)" }}>
        📅 Last tracked month was{" "}
        {new Date(prev + "-01").toLocaleString("en-IN", { month: "long", year: "numeric" })}.
      </p>
      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
        Monthly comparisons work best with consecutive months.
      </p>
    </div>
  )}

IMPORTANT:
- This guard applies ONLY to the multi-month (2+ prior months) branch.
- The first-month fallback ("Spending Highlights") and single-prior-month branches
  already have their own paths — do NOT touch them.
- The existing changes.map rows and View all button inside hasValidComparison must
  be identical to the current code — do not refactor them.
- Verify January → December year rollover works: when current = "2026-01" and
  prior = "2025-12", isConsecutiveMonth must return true.

Confirm TypeScript build clean after.
```

---

## Prompt 11-Final — Sprint 11 verification

```
Sprint 11 is now complete. Please verify the three remaining items were implemented
correctly by reading the relevant sections of:
  frontend/react/src/components/tabs/OverviewTab.tsx
  backend/main.py

Check F2a (Item 9b):
- backend/main.py: the /insights/monthly-insight/{month_key} endpoint contains an
  is_first_month branch. First-month prompt has no comparative language. Returning-user
  prompt has the "Do not mention percentage changes unless..." guard appended.
- OverviewTab.tsx: isSafeInsight helper and isFirstMonth flag exist above the return.
  The monthlyInsight card (inside the Monthly Breakdown column, below BalanceBreakdown,
  with flex-1) uses both conditions. Card has NOT been moved from its current position.

Check F4 (Item 10):
- OverviewTab.tsx: no "Financial Snapshot" string in JSX.
- KPI grid has exactly 3 tiles and uses grid-cols-3.

Check W1 (Item 11):
- OverviewTab.tsx: isConsecutiveMonth function exists in the What Changed? block.
- hasValidComparison guards the changes.map rows.
- The first-month and single-prior-month branches are untouched.

Run tsc --noEmit in frontend/react/ — must be clean.

Report any check that fails.
```

---

---

# ── SPRINT 12 ──────────────────────────────────────────────────────

> **Before starting sprint 12**: Merge the sprint 11 branch into main, then cut a new
> branch (suggested: `feature/sprint12-adaptive-insights`).
> Sprint 12 plan: `.claude/plans/12-adaptive-insights.md`
> Sprint 12 spec: `.claude/specs/12_adaptive-insights.md`

---

## Prompt 12-A — Items 1 + 2: Backend extensions (expense_count + days_tracked)

```
Read `.claude/plans/12-adaptive-insights.md` Items 1 and 2, and all 6 flags at the top
of the plan before making any changes.

Read `backend/main.py` fully before writing anything. Identify:
- The summary computation function that builds the /summary/{month_key} response dict
  (Flag 5: check for any existing expense_count or total_expenses field first).
- The MoM endpoint /insights/mom/{month_key} and how months_in_window is built.
- The SQLAlchemy import style used in the file (Flag 3: func, distinct import paths).

─── ITEM 1: expense_count on /summary/{month_key} ───
If a field named expense_count or total_expenses already exists in the summary dict,
skip this item and note the actual field name — it will be used as-is in prompt 12-C.

Otherwise, inside the summary computation, add:
  expense_count = db.query(func.count(Expense.id)).filter(
      Expense.user_id == user_id,
      Expense.date.startswith(month_key)
  ).scalar() or 0

Add "expense_count": expense_count to the returned dict.
Do NOT change any existing fields.

─── ITEM 2: days_tracked on /insights/mom/{month_key} ───
Inside the MoM endpoint, after months_in_window is established, add:
  days_tracked = {}
  for m in months_in_window:
      count = db.query(func.count(distinct(Expense.date))).filter(
          Expense.user_id == user_id,
          Expense.date.startswith(m)
      ).scalar() or 0
      days_tracked[m] = count

Adapt the distinct() import to match what is already used in main.py (Flag 3).
Add "days_tracked": days_tracked to the MoM endpoint's returned dict.
Do NOT change any other MoM fields.

Acceptance check:
- GET /summary/2026-06 response includes expense_count as an integer (0 if no expenses).
- GET /insights/mom/2026-06 response includes days_tracked as a dict keyed by month_key.
- Python syntax clean — run python -c "import backend.main" or equivalent to confirm.
```

---

## Prompt 12-B — Item 3: TypeScript type extensions

```
Read `.claude/plans/12-adaptive-insights.md` Item 3 before making any changes.

Read `frontend/react/src/types/index.ts` fully.

Find the Summary interface and add:
  expense_count?: number;

Find the MoMData interface and add:
  days_tracked: Record<string, number>;

Both are additive — do not remove or rename any existing field.

expense_count is optional (?) because existing cached API responses from before
prompt 12-A deployed may not include it yet.

days_tracked is required (non-optional) since after prompt 12-A it is always present.

Run tsc --noEmit in frontend/react/ — must be clean with no new errors.
```

---

## Prompt 12-C — Items 4 + 5: Scenario A (Onboarding) + Scenario B (MoM refactor)

```
Read `.claude/plans/12-adaptive-insights.md` Items 4 and 5, and Flags 2, 4, 6
before making any changes.

Read `frontend/react/src/components/tabs/OverviewTab.tsx`:
- Check line count (Flag 6). If > 700 lines, create
  `frontend/react/src/components/shared/InsightsSection.tsx` and build sub-components
  there. Otherwise keep inline in OverviewTab.tsx.
- Confirm summary.categories sort order (Flag 4) — if not pre-sorted by spent desc,
  sort before slicing.
- Confirm expense_count field name from prompt 12-A output.
- Read the current What Changed? IIFE carefully and identify all three internal branches
  (Flag 2): first-month, single-prior-month, multi-month. Only the multi-month branch
  becomes Scenario B.

─── ITEM 4: InsightsScenarioA ───
Create this sub-component per the plan Item 4 code. Key rules:
- Sort categories by spent descending before slicing [0].
- Show expense count line only when expense_count is not null/undefined.
- Show top category line only when categories is non-empty.
- Encouragement line always present.
- No comparison language anywhere.

─── ITEM 5: InsightsScenarioB ───
Extract the MULTI-MONTH branch only from the existing What Changed? IIFE into
InsightsScenarioB per the plan Item 5 code. Key rules:
- The fmtMoM formatter already exists from sprint 11 P2 — reuse it, do not redefine.
- The changes array derivation logic must be identical to the current multi-month branch.
- The View all button must fire the same toast as before:
  "See all transactions in the History tab →"
- Do NOT touch the first-month or single-prior-month branches — leave them in place
  for now (they will be removed in prompt 12-E).

After both sub-components are defined, run tsc --noEmit — must be clean.
Do NOT yet wire them into the selector (that happens in prompt 12-E).
```

---

## Prompt 12-D — Items 6 + 7: Scenario C (Gap + Highlights) + Scenario D (Tracking Quality)

```
Read `.claude/plans/12-adaptive-insights.md` Items 6 and 7 before making any changes.

Read the file where InsightsScenarioA and InsightsScenarioB were placed in prompt 12-C
(either OverviewTab.tsx or InsightsSection.tsx) so you add the new components in the
same location.

Also check whether CATEGORY_ICONS is defined in scope — Scenario C uses it. If not,
use a fallback: CATEGORY_ICONS?.[c.category] ?? "📦".

─── ITEM 6: InsightsScenarioC ───
Build per plan Item 6. Key rules:
- prevLabel: use toLocaleString("en-IN", { month: "long", year: "numeric" }).
- Top 3 categories sorted by spent descending, sliced to 3.
- Gap notice card always renders. Top 3 section renders only when categories non-empty.
- No MoM comparison rows.

─── ITEM 7: InsightsScenarioD ───
Build per plan Item 7. Key rules:
- bothSparse = currDays < 10 && prevDays < 10 → show neutral encouragement only.
- Otherwise show the two-row day count display + explanation.
- No shame language — keep tone neutral and forward-looking.

After both are defined, run tsc --noEmit — must be clean.
Do NOT yet wire into the selector (that happens in prompt 12-E).
```

---

## Prompt 12-E — Item 8: Scenario selector + heading rename (wire-up)

```
Read `.claude/plans/12-adaptive-insights.md` Item 8 and Flags 1, 6 before making
any changes.

This prompt must run AFTER prompts 12-C and 12-D are complete and TypeScript-clean.

Read `frontend/react/src/components/tabs/OverviewTab.tsx`.

Step 1 — Confirm isConsecutiveMonth exists from sprint 11 W1 (Flag 1). Do NOT redefine
it. If it was defined inside the What Changed? IIFE block, move it to a higher scope
(above the return) so the scenario selector can reference it.

Step 2 — Remove the ENTIRE existing What Changed? IIFE (the mom && (() => { ... })()
block including all three internal branches). All three branches are now handled by the
sub-components built in 12-C and 12-D.

Step 3 — In the exact location where the What Changed? block was, insert the scenario
selector per the plan Item 8 code:

  {mom && (() => {
    const curr = mom.months[mom.months.length - 1];
    const prev = mom.months.length >= 2 ? mom.months[mom.months.length - 2] : null;
    const isFirstMonth    = !prev;
    const isConsecutive   = prev ? isConsecutiveMonth(curr, prev) : false;
    const currDaysTracked = mom.days_tracked?.[curr] ?? 0;
    const prevDaysTracked = prev ? (mom.days_tracked?.[prev] ?? 0) : 0;
    const isQualityData   = prevDaysTracked >= 10;

    const scenario =
      isFirstMonth                   ? "A" :
      isConsecutive && isQualityData ? "B" :
      isConsecutive                  ? "D" :
      "C";

    return (
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-syne font-bold tracking-widest"
              style={{ color: "var(--text-sub)" }}>
            💡 Insights
          </h2>
          {scenario === "B" && prev && (
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>
              vs {new Date(prev + "-01").toLocaleString("en-IN", { month: "short" })}
            </span>
          )}
        </div>

        {scenario === "A" && <InsightsScenarioA summary={summary} />}
        {scenario === "B" && prev && (
          <InsightsScenarioB
            mom={mom}
            summary={summary}
            curr={curr}
            prev={prev}
            onViewAll={() => toast("See all transactions in the History tab →")}
          />
        )}
        {scenario === "C" && prev && <InsightsScenarioC summary={summary} prev={prev} />}
        {scenario === "D" && (
          <InsightsScenarioD currDays={currDaysTracked} prevDays={prevDaysTracked} />
        )}
      </section>
    );
  })()}

Step 4 — Search the entire file for any remaining "What changed?", "WHAT CHANGED?",
or "📊 What changed?" strings and remove them. The section comment should read:
  {/* ── Section 9: 💡 Insights ─── */}

Step 5 — If InsightsScenarioA/B/C/D were built in InsightsSection.tsx, add the import.

Run tsc --noEmit — must be clean.
```

---

## Prompt 12-Final — Sprint 12 full verification

```
Sprint 12 is complete. Verify all 8 items across backend and frontend.

─── BACKEND ───
Read backend/main.py and confirm:
- /summary/{month_key} response dict includes expense_count (integer, not null).
- /insights/mom/{month_key} response dict includes days_tracked (dict of month_key → int).
- No existing fields were removed or renamed.
- Python syntax clean.

─── TYPES ───
Read frontend/react/src/types/index.ts and confirm:
- Summary interface has expense_count?: number.
- MoMData interface has days_tracked: Record<string, number>.

─── FRONTEND ───
Read OverviewTab.tsx (and InsightsSection.tsx if created) and confirm:

Scenario selector:
- isConsecutiveMonth used (not redefined) from sprint 11 W1.
- Scenario A triggers when mom.months.length < 2.
- Scenario B triggers when consecutive + prevDaysTracked >= 10.
- Scenario D triggers when consecutive + prevDaysTracked < 10.
- Scenario C triggers when non-consecutive prior month.
- Exactly one scenario renders at a time.

Scenario A (InsightsScenarioA):
- Shows expense count when available.
- Shows top category + percentage.
- Shows encouragement line.
- No comparison language.

Scenario B (InsightsScenarioB):
- MoM rows identical to previous What Changed? multi-month behaviour.
- fmtMoM used from sprint 11 (not redefined).
- View all toast fires correctly.

Scenario C (InsightsScenarioC):
- Gap notice shows last tracked month name.
- Top 3 categories shown below.

Scenario D (InsightsScenarioD):
- Day counts shown when only prior month is sparse.
- Neutral encouragement shown when both months are sparse.

Heading:
- "💡 Insights" used in all scenarios.
- "What changed?" / "WHAT CHANGED?" / "📊 What changed?" strings absent from codebase.

Run tsc --noEmit in frontend/react/ — must be completely clean.
Report any item that fails its check.
```
