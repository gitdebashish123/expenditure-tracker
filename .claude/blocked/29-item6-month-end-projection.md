# Blocked — Spec 29, Item 6: Month-end projection guard

**Origin**: `.claude/specs/29_day-one-month-start-awareness.md`, Item 6
**Plan**: `.claude/plans/29-day-one-month-start-awareness.md`, Item 6
**Status**: Not implemented — spec/code divergence, needs re-scoping before any code change
**Date blocked**: 2026-07-01

---

## What the spec asked for

Suppress the "Expected month-end balance" figure in `OverviewTab.tsx` on day 1–3 of the
month, replacing it with a neutral "Check back in a few days" message. The spec's stated
root cause: the projection "divides remaining balance by days elapsed," which on day 1
(1 day elapsed) produces wildly overstated figures like ₹55k.

## Why it wasn't implemented

Read the actual current code (not just the spec's description of it) before planning, and
the described bug doesn't exist in the current implementation:

1. **The one on-screen "Expected month-end balance" element** — `OverviewTab.tsx:702-720`,
   inside the "🔔 Coming up" section — computes:
   ```tsx
   {fmtInr(balance.remaining - balance.fixed_unpaid_total)}
   ```
   No division by days elapsed or days left anywhere in this formula. On day 1,
   `balance.remaining` ≈ full income (nothing spent/paid yet) and `balance.fixed_unpaid_total`
   ≈ the full unpaid-fixed total, so the result resolves to roughly the variable budget
   available (~₹42,154 per `CLAUDE.md`) — a sensible number on day 1, not a "₹55k
   nonsensical" one. There's no `dayOfMonth`/`computedProjection` variable to guard,
   because this formula is day-invariant by construction.

2. **The only place that genuinely does day-elapsed linear extrapolation** is
   `/insights/projection/{month_key}` (`backend/main.py:1212-1269`):
   ```python
   daily_rate = spent / days_elapsed
   projected  = daily_rate * days_in_month
   ```
   With `days_elapsed = 1` on day 1, any early expense gets blown up into an overstated
   month-end figure — this is the real "day-1 extrapolation instability" bug pattern.
   But the component that renders that `projected` field —
   `frontend/react/src/components/shared/BudgetHealthCard.tsx:34`
   (`` `Projected ${fmtInr(p.projected)}` ``) — **is not wired into the app**.
   `grep -rl BudgetHealthCard frontend/react/src` only matches its own definition file;
   no page imports or renders it. The live "Spending signals" section
   (`OverviewTab.tsx:616-649`) uses `SignalCard` (`SpendingSignalsModal.tsx:19-59`)
   instead, which only reads `pct_spent`/`daily_rate` — both resolve to sensible values
   on day 1 (₹0 spent → 0%, ₹0/day) — never `p.projected`.

3. `HeroBalanceCard.tsx:11` (`dailyBudget = balance.remaining / daysLeft`) divides by
   days **left**, not elapsed — on day 1 that's `income / ~30`, a normal pacing figure,
   no anomaly.

**Conclusion**: nothing currently rendered in the app reproduces the bug as described.
The one formula that structurally could (`/insights/projection`'s `projected` field)
isn't currently shown to users anywhere.

## Options for re-evaluation

- **(a) Moot** — no user-visible bug exists today; close this item with no code change.
- **(b) Different root cause, same intent** — if the actual complaint is about
  `OverviewTab.tsx:702-720`'s "Expected month-end balance" reading oddly reassuring/early
  on day 1 (even though the number itself is technically correct), the real guard needed
  is something like `balance.fixed_paid_total === 0 && dayOfMonth <= 3` — a "nothing's
  happened yet this month" gate, not a division-by-days-elapsed fix. This changes what
  the guard condition should be.
- **(c) Revive `BudgetHealthCard`** — if the product intent is to surface the per-category
  `projected` figure somewhere (it's already computed server-side, just unused), then the
  spec's original day-elapsed guard logic would apply directly to that card once it's
  wired into a page — but that's a scope increase (adding a new visible component), not
  a bug fix, and should be scoped as its own item.

## Action needed

Ask the user which of (a)/(b)/(c) — or something else — matches what they actually
observed, then write a fresh, accurately-scoped plan item before touching
`OverviewTab.tsx` or `BudgetHealthCard.tsx`.
