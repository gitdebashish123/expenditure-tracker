# Implementation Plan: Today Tab + Overview Tab Redesign
**Spec**: `.claude/specs/08_today-overview-redesign.md`
**Date**: 2026-06-25
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

11 items total — 3 require backend + frontend, 8 are frontend-only.
Items are ordered smallest-blast-radius-first. T3 and T4 both touch `QuickAddTab.tsx` and should be done in the same pass. O1, O4, O5, O6 all touch only `OverviewTab.tsx` and can be done in sequence without merge risk.

**O3 (Peace of Mind Score) is unblocked** — formula weights confirmed by user on 2026-06-25.

**⚠️ T2 prerequisite** — `tara.png` does not currently exist in `frontend/react/public/` (only an `icons/` subfolder is present). The Tara avatar image must be placed at `frontend/react/public/tara.png` before T2 can be implemented. The spec says the asset was uploaded as `Tara-image.png` during the review session — the user must copy/save it to that path.

**⚠️ O6 endpoint discrepancy** — The spec references `GET /insights/due-reminders/{month_key}` but the actual path in `main.py` is `GET /fixed/due-reminders/{month_key}` (line 802). Additionally, that endpoint only returns expenses where `today.day >= tmpl.due_day` (overdue bills, not upcoming). The plan addresses this with a client-side approach using all unpaid fixed data already in `summary.balance`.

---

## Item 1 — T3: Richer empty state + suggestion chips on Today tab

**Scope**: Frontend-only

**Files**:
- `frontend/react/src/components/tabs/QuickAddTab.tsx` — lines 371–380 (current empty state `<div>`)

**Root cause**: Current empty state (lines 372–380) is minimal — two lines of plain text:
```tsx
<div className="text-center py-8">
  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
    Nothing logged today.
  </p>
  <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
    Type something like:{" "}
    <span className="text-indigo-400">zomato 350, ola 120</span>
  </p>
</div>
```
The spec wants an icon, a static friendly sub-label, and 3 tappable chips that pre-fill the NL input.

**What to do**: Replace the empty state `<div>` with:
```tsx
<div className="text-center py-8 space-y-3">
  <div className="text-3xl">🧾</div>
  <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
    Nothing logged today.
  </p>
  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
    Start your day by logging something small.
  </p>
  <div className="flex gap-2 justify-center flex-wrap mt-2">
    {(["tea 20", "uber 180", "milk 60"] as const).map(suggestion => (
      <button
        key={suggestion}
        onClick={() => setText(suggestion)}
        className="text-xs px-3 py-1.5 rounded-full border transition-colors"
        style={{
          borderColor: 'var(--accent)',
          color:       'var(--accent)',
          background:  'transparent',
        }}
      >
        {suggestion}
      </button>
    ))}
  </div>
</div>
```
`setText` is already in scope inside `QuickAddTab`. The chips pre-fill the NL input; the user then taps "Add Expenses" — no auto-submit.

**Acceptance criteria**:
- Empty state has icon + heading + sub-label + 3 chips.
- Tapping a chip pre-fills the NL input (does not auto-submit).
- Non-empty list rendering is unchanged.

---

## Item 2 — T4: Ask Tara FAB (shell only)

**Scope**: Frontend-only

**Files**:
- `frontend/react/src/components/tabs/QuickAddTab.tsx` — add import for `MessageCircle` from lucide-react; add FAB at the bottom of the return div

**Root cause**: No FAB exists. `useToast` and `toast()` are already imported and in scope (lines 9, 126).

**What to do**:

1. Update the lucide import (line 8) to add `MessageCircle`:
   ```tsx
   import { Loader2, Zap, MessageCircle } from "lucide-react";
   ```

2. At the bottom of `QuickAddTab`'s return `<div className="space-y-6">`, after the closing `</section>` of Section 3 and before the outer closing `</div>`, add:
   ```tsx
   {/* Ask Tara FAB — shell only, chat backend not yet built */}
   <button
     onClick={() => toast("Ask Tara is coming soon! 🪷")}
     aria-label="Ask Tara"
     style={{
       position:     'fixed',
       bottom:       '72px',
       right:        '16px',
       width:        '52px',
       height:       '52px',
       borderRadius: '50%',
       background:   'var(--accent)',
       color:        '#fff',
       display:      'flex',
       alignItems:   'center',
       justifyContent: 'center',
       zIndex:       30,
       border:       'none',
       boxShadow:    '0 4px 16px rgba(0,0,0,0.3)',
       cursor:       'pointer',
     }}
   >
     <MessageCircle size={22} />
   </button>
   ```

`72px` clears the bottom nav (`h-16` = 64px) plus 8px breathing room. The FAB only renders inside `QuickAddTab`, so it doesn't appear on other tabs.

**Acceptance criteria**:
- FAB visible bottom-right on Today tab.
- Tapping fires a toast: "Ask Tara is coming soon! 🪷".
- FAB does not appear on other tabs (it's scoped to `QuickAddTab`).

---

## Item 3 — T2: Tara avatar, "Ask Tara" button, rename expand label

**Scope**: Frontend-only (plus asset placement prerequisite)

**Files**:
- `frontend/react/public/tara.png` — must exist before this item (see prerequisite warning above)
- `frontend/react/src/components/tabs/QuickAddTab.tsx` — `TodaysMantraCard` function (lines 38–98)

**Root cause — what's in place vs. what's missing**:
- The card already has: accent border/glow, "🪷 Today's Mantra" heading, divider, italic mantra text, "Why?" expand toggle with context panel.
- Missing: Tara avatar (right-aligned portrait crop), "Ask Tara" pill button inside the card, and the label text is `"▼ Why?"` / `"▲ Hide"` — spec finalises this as `"How Tara calculated this ↓"` / `"↑ Hide"`.

**What to do**:

1. Restructure the outer `<div>` inside the card to a flex row — content on the left, avatar on the right:
   ```tsx
   <div className="rounded-2xl overflow-hidden border" style={{ ... (same styles) }}>
     <div className="flex">
       {/* Left: content */}
       <div className="flex-1 p-4">
         {/* existing heading, divider, mantra text */}
       </div>
       {/* Right: avatar — hidden below 360px width */}
       <div
         className="flex-shrink-0"
         style={{ width: '100px', alignSelf: 'stretch', position: 'relative', overflow: 'hidden' }}
       >
         <img
           src="/tara.png"
           alt="Tara"
           style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'top center' }}
           className="hidden xs:block"
         />
       </div>
     </div>
     {/* "Ask Tara" pill + expand — in a separate bottom strip inside the card */}
     <div className="px-4 pb-4 flex items-center gap-3">
       <button
         onClick={() => toast("Ask Tara is coming soon! 🪷")}
         className="text-xs font-syne font-semibold px-3 py-1.5 rounded-full"
         style={{ background: 'var(--accent)', color: '#fff' }}
       >
         Ask Tara
       </button>
       <button
         onClick={() => setShowWhy(v => !v)}
         className="text-xs font-syne font-semibold transition-opacity hover:opacity-80"
         style={{ color: 'var(--accent)' }}
       >
         {showWhy ? "↑ Hide" : "How Tara calculated this ↓"}
       </button>
     </div>
     {showWhy && (
       <div className="px-4 pb-4">
         {/* existing context panel — unchanged */}
       </div>
     )}
   </div>
   ```

2. The `TodaysMantraCard` already imports `useToast` indirectly — but it's the parent `QuickAddTab` that holds the `toast` reference, not `TodaysMantraCard` itself. Either:
   - Pass `toast` as a prop to `TodaysMantraCard`, OR
   - Add a local `useToast()` call inside `TodaysMantraCard` (both `TodaysMantraCard` and `QuickAddTab` live in the same file; adding `const { toast } = useToast();` inside `TodaysMantraCard` is cleanest — `useToast` is already imported at the file level).

   Use the second approach: add `const { toast } = useToast();` as the first line inside `TodaysMantraCard`.

3. For the avatar hide-below-360px: Tailwind doesn't have an `xs:` breakpoint by default. Either use an inline `@media (max-width: 359px) { display: none }` or a hardcoded CSS approach. Cleanest: wrap the avatar `<div>` in `<div className="hidden min-[360px]:block">` — this uses Tailwind's arbitrary min-width variant, which works without config changes.

**Acceptance criteria**:
- Avatar visible on the right side of the mantra card (≥ 360px screen).
- Avatar hidden on very narrow screens (< 360px).
- "Ask Tara" pill button inside card fires "coming soon" toast.
- Expand label reads "How Tara calculated this ↓" (not "Why?").
- "↑ Hide" shown when panel is open.

---

## Item 4 — O5: Replace MoM table with "What Changed?" rows

**Scope**: Frontend-only

**Files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Section 5 (lines 259–270), replace `<MoMTable>` with inline `WhatChanged` section

**Root cause**: Line 268 renders `<MoMTable mom={mom} />`. `MoMTable` is a dense horizontally-scrolling table that the spec explicitly calls out as the "most consistently criticised element". The `MoMTable` component itself stays unchanged; it just stops being rendered on the main Overview screen.

The `mom` state already contains:
- `mom.months` — array of month strings, e.g. `["2026-04", "2026-05", "2026-06"]`
- `mom.categories` — `Record<category, Record<month_key, amount>>`

So `months[months.length - 1]` is current month and `months[months.length - 2]` is previous.

**What to do**:

Remove the `import { MoMTable }` line (line 10). Replace Section 5 with:

```tsx
{/* ── Section 5: What Changed? ─────────────────── */}
{mom && mom.months.length >= 2 && (() => {
  const curr = mom.months[mom.months.length - 1];
  const prev = mom.months[mom.months.length - 2];
  const prevLabel = new Date(prev + "-01").toLocaleString("en-IN", { month: "short" });

  // Compute absolute change per category
  const changes = Object.entries(mom.categories)
    .map(([cat, byMonth]) => ({
      cat,
      currAmt: byMonth[curr] ?? 0,
      prevAmt: byMonth[prev] ?? 0,
      delta:   (byMonth[curr] ?? 0) - (byMonth[prev] ?? 0),
    }))
    .filter(c => c.prevAmt > 0 || c.currAmt > 0)  // skip all-zero rows
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, 4);

  const SAVINGS_CATS = new Set(["Savings", "Investments"]);

  return (
    <section>
      <h2 className="text-xs font-syne font-bold uppercase tracking-widest mb-1"
          style={{ color: 'var(--text-sub)' }}>
        What Changed?
      </h2>
      <p className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>
        vs {prevLabel}
      </p>
      <div className="space-y-0">
        {changes.map(({ cat, delta, prevAmt, currAmt }) => {
          const isUp = delta > 0;
          // For savings/investments, up is good (green); for spending, up is bad (red)
          const isSavingsCat = SAVINGS_CATS.has(cat);
          const isPositive = isSavingsCat ? isUp : !isUp;
          const dotColour = isPositive ? '#34d399' : '#f87171';
          const icon = isUp ? '↑' : '↓';
          const pct = prevAmt > 0 ? Math.abs(Math.round((delta / prevAmt) * 100)) : null;
          const label = pct != null
            ? `${icon} ${pct}% (${fmtInr(Math.abs(delta))})`
            : `${icon} ${fmtInr(Math.abs(delta))}`;

          return (
            <div key={cat} className="flex items-center gap-3 py-2.5 border-b border-white/5">
              <span className="text-lg w-5 flex-shrink-0 text-center" style={{ color: dotColour }}>
                {icon}
              </span>
              <span className="flex-1 text-sm" style={{ color: 'var(--text)' }}>{cat}</span>
              <div className="text-right">
                <span className="text-sm font-syne font-semibold" style={{ color: dotColour }}>
                  {label}
                </span>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  {fmtInr(currAmt)} this month
                </p>
              </div>
            </div>
          );
        })}
        <button
          onClick={() => toast("Full breakdown coming soon.")}
          className="text-xs mt-2 w-full text-right transition-opacity hover:opacity-70"
          style={{ color: 'var(--accent)' }}
        >
          View all →
        </button>
      </div>
    </section>
  );
})()}
```

This uses an IIFE inside JSX to keep the derivation logic local without a separate function. Add `useToast` and `toast` to `OverviewTab` if not already present (currently they're not — add `import { useToast } from "@/context/ToastContext";` and `const { toast } = useToast();` inside `OverviewTab`).

**Acceptance criteria**:
- MoM dense table no longer renders.
- "What Changed?" shows up to 4 rows of largest absolute ₹ changes.
- Colour logic inverts for Savings/Investments (up = green).
- "View all →" fires a toast.

---

## Item 5 — O4: Financial Pulse section on Overview

**Scope**: Frontend-only

**Files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — new section, added after "What Changed?" (Section 5) and before Budget Health (Section 3 in current order)

**Root cause**: No Financial Pulse section exists. All 4 signals are computable from `summary` and `mom` state already in scope.

**What to do**: Add a new section above Budget Health. The 4 signals:

| Signal | Source | Green | Amber | Red |
|--------|--------|-------|-------|-----|
| Bills | `balance.fixed_unpaid_total` | == 0 → "On Track" | > 0 → "{n} pending" | – |
| Food | `mom.categories["Food"]` — compare curr vs prev | ≤ 100% of prev | 100–130% | > 130% |
| Spending | `variable_total / days_elapsed` vs prev month daily rate | ≤ 110% of prev daily rate | 110–130% | > 130% |
| Tracking | Static placeholder | always green "Consistent" | – | – |

For days_elapsed computation: derive client-side from `selMonth` — if it's the current calendar month, `days_elapsed = new Date().getDate()`; if it's a past month, `days_elapsed = days_in_month` (use `new Date(year, month, 0).getDate()`).

```tsx
{/* ── Section: Financial Pulse ─────────────────── */}
{summary && (() => {
  const [year, month] = selMonth.split("-").map(Number);
  const today = new Date();
  const isCurrentMonth = today.getFullYear() === year && (today.getMonth() + 1) === month;
  const daysInMonth = new Date(year, month, 0).getDate();
  const daysElapsed = isCurrentMonth ? Math.max(today.getDate(), 1) : daysInMonth;

  // Bills signal
  const billsPending = balance.fixed_unpaid_total > 0;
  const billsColour = billsPending ? '#f59e0b' : '#34d399';
  const billsLabel = billsPending ? `${fmtInr(balance.fixed_unpaid_total)} pending` : "On Track";

  // Food signal (requires mom with 2+ months)
  const currMonthKey = selMonth;
  const prevMonthIdx = mom ? mom.months.indexOf(currMonthKey) - 1 : -1;
  const prevMonthKey = mom && prevMonthIdx >= 0 ? mom.months[prevMonthIdx] : null;
  const foodCurr = mom?.categories["Food"]?.[currMonthKey] ?? 0;
  const foodPrev = prevMonthKey ? (mom?.categories["Food"]?.[prevMonthKey] ?? 0) : 0;
  const foodPct = foodPrev > 0 ? (foodCurr / foodPrev) * 100 : null;
  const foodColour = foodPct == null ? '#94a3b8' : foodPct <= 100 ? '#34d399' : foodPct <= 130 ? '#f59e0b' : '#f87171';
  const foodLabel = foodPct == null ? '–' : foodPct <= 100 ? 'Healthy' : foodPct <= 130 ? 'Slightly High' : 'High';

  // Spending pace signal
  const dailyRate = daysElapsed > 0 ? balance.variable_total / daysElapsed : 0;
  const prevDaysInMonth = prevMonthKey ? new Date(Number(prevMonthKey.split("-")[0]), Number(prevMonthKey.split("-")[1]), 0).getDate() : 0;
  const varPrevTotal = prevMonthKey
    ? Object.entries(mom?.categories ?? {})
        .filter(([cat]) => !["Rent","EMI","RD","Insurance","Cook","Milk","Electricity"].includes(cat))
        .reduce((s, [, byM]) => s + (byM[prevMonthKey!] ?? 0), 0)
    : 0;
  const prevDailyRate = prevDaysInMonth > 0 ? varPrevTotal / prevDaysInMonth : 0;
  const pacePct = prevDailyRate > 0 ? (dailyRate / prevDailyRate) * 100 : null;
  const paceColour = pacePct == null ? '#94a3b8' : pacePct <= 110 ? '#34d399' : pacePct <= 130 ? '#f59e0b' : '#f87171';
  const paceLabel = pacePct == null ? '–' : pacePct <= 110 ? 'Healthy' : pacePct <= 130 ? 'Above Avg' : 'High';

  const signals = [
    { name: "Bills",     label: billsLabel, colour: billsColour, sub: billsPending ? "Check Fixed tab" : "All clear" },
    { name: "Food",      label: foodLabel,  colour: foodColour,  sub: foodPct != null ? `${Math.round(foodPct)}% of last month` : "No prior data" },
    { name: "Spending",  label: paceLabel,  colour: paceColour,  sub: "Daily rate vs last month" },
    { name: "Tracking",  label: "Consistent", colour: '#34d399', sub: "Keep it up!" },
  ];

  return (
    <section>
      <h2 className="text-xs font-syne font-bold uppercase tracking-widest mb-3"
          style={{ color: 'var(--text-sub)' }}>
        Financial Pulse
      </h2>
      <div className="grid grid-cols-2 gap-3">
        {signals.map(s => (
          <div key={s.name} className="rounded-xl p-3 border"
               style={{ background: 'var(--card)', borderColor: 'var(--border-lg)' }}>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: s.colour }} />
              <span className="text-xs font-syne font-semibold" style={{ color: 'var(--text-sub)' }}>
                {s.name}
              </span>
            </div>
            <p className="text-sm font-syne font-bold" style={{ color: s.colour }}>{s.label}</p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{s.sub}</p>
          </div>
        ))}
      </div>
    </section>
  );
})()}
```

Note: The FIXED_CATEGORIES check for "Spending pace" can't use the frontend `FIXED_CATEGORIES` constant without an import; instead, the plan uses a hardcoded exclusion list that matches what the server considers fixed. This is acceptable for Phase 1. Import `FIXED_CATEGORIES` from `@/utils/categories` instead — it's already imported in `OverviewTab.tsx` (line 6).

**Acceptance criteria**:
- 4 signal tiles on Overview.
- Bills correctly reflects `fixed_unpaid_total == 0` vs. > 0.
- Food shows "–" when no prior month data.
- Tracking always shows green "Consistent".

---

## Item 6 — O1: Financial Snapshot grid on Overview

**Scope**: Frontend-only

**Files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — insert new section before Section 1 (`BalanceBreakdown`, line 181)

**Root cause**: The Overview tab opens with `<BalanceBreakdown>` as its first section. The 4 key numbers (`remaining`, `total_income`, `fixed_paid_total`, `fixed_unpaid_total`) are already in `balance` but aren't shown as a fast-read grid before the bar.

**What to do**: Before Section 1 (`BalanceBreakdown`), insert:

```tsx
{/* ── Section 0: Financial Snapshot ─────────────── */}
<section>
  <h2 className="text-xs font-syne font-bold uppercase tracking-widest mb-3"
      style={{ color: 'var(--text-sub)' }}>
    Financial Snapshot
  </h2>
  <div className="grid grid-cols-2 gap-3">
    {[
      {
        label: "Remaining",
        value: balance.remaining,
        icon:  "💰",
        colour: balance.remaining >= 0 ? '#34d399' : '#f87171',
      },
      {
        label: "Income",
        value: balance.total_income,
        icon:  "💼",
        colour: '#6366f1',
      },
      {
        label: "Fixed Paid",
        value: balance.fixed_paid_total,
        icon:  "✅",
        colour: '#f59e0b',
      },
      {
        label: balance.fixed_unpaid_total === 0 ? "All Bills Clear ✓" : "Pending Bills",
        value: balance.fixed_unpaid_total,
        icon:  balance.fixed_unpaid_total === 0 ? "🎉" : "⏳",
        colour: balance.fixed_unpaid_total === 0 ? '#34d399' : '#f87171',
      },
    ].map(tile => (
      <div key={tile.label} className="rounded-2xl p-4 border"
           style={{ background: 'var(--card)', borderColor: 'var(--border-lg)' }}>
        <div className="flex items-center gap-1.5 mb-2">
          <span className="text-base">{tile.icon}</span>
          <p className="text-[10px] font-syne font-bold uppercase tracking-widest"
             style={{ color: 'var(--text-sub)' }}>
            {tile.label}
          </p>
        </div>
        <p className="text-lg font-syne font-bold" style={{ color: tile.colour }}>
          {fmtInr(tile.value)}
        </p>
      </div>
    ))}
  </div>
</section>
```

**Acceptance criteria**:
- 4 tiles visible immediately on Overview open, no scroll needed.
- Remaining is green/red depending on sign.
- Pending Bills shows "All Bills Clear ✓" + green when `fixed_unpaid_total == 0`.
- `BalanceBreakdown` still renders below as secondary visual.

---

## Item 7 — O6: Upcoming Reality section on Overview

**Scope**: Frontend-only (reuses existing `/fixed/due-reminders/{month_key}` endpoint)

**Files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — add `dueReminders` state + fetch in `load()`, add new section

**⚠️ Endpoint path**: The spec says `/insights/due-reminders/{month_key}` but the actual path is `/fixed/due-reminders/{month_key}` (confirmed at `main.py` line 802). Use the correct path.

**⚠️ Endpoint logic note**: The endpoint only returns expenses where `today.day >= tmpl.due_day` (i.e., bills that are on or past their due date today). It does **not** return bills due in the future. For "next due bill", sort the returned reminders by `days_overdue` ascending (least overdue first) to get the most recently due item. The "days until due" concept doesn't apply here — instead label as "X days ago" or "due today". When `fixed_unpaid_total == 0`, the fetch will return an empty array — show "All bills paid this month ✓".

**Root cause**: `DueReminder` type exists in `types/index.ts`. `load()` in `OverviewTab` currently makes 4 parallel fetches. No fetch for due-reminders or state for it exists.

**What to do**:

1. Add `dueReminders` state:
   ```tsx
   const [dueReminders, setDueReminders] = useState<DueReminder[]>([]);
   ```

2. Add `DueReminder` to the type import line (line 11):
   ```tsx
   import type { Summary, ProjectionItem, DueReminder } from "@/types";
   ```

3. Add a 5th fetch to the `load()` `Promise.all` array:
   ```tsx
   api.get<DueReminder[]>(`/fixed/due-reminders/${selMonth}`).then(r => r.data),
   ```
   Destructure it from the results and call `setDueReminders(reminders)`.

4. Add a new section after the Financial Pulse section and before Budget Health:
   ```tsx
   {/* ── Section: Upcoming Reality ────────────────── */}
   <section>
     <h2 className="text-xs font-syne font-bold uppercase tracking-widest mb-3"
         style={{ color: 'var(--text-sub)' }}>
       Upcoming Reality
     </h2>
     <div className="rounded-2xl border overflow-hidden"
          style={{ background: 'var(--card)', borderColor: 'var(--border-lg)' }}>
       {/* Next due bill row */}
       <div className="p-4">
         {dueReminders.length === 0 ? (
           <p className="text-sm font-medium" style={{ color: '#34d399' }}>
             🎉 All bills paid this month
           </p>
         ) : (
           (() => {
             const next = [...dueReminders].sort((a, b) => a.days_overdue - b.days_overdue)[0];
             return (
               <div className="flex items-center gap-3">
                 <span className="text-xl">📅</span>
                 <div className="flex-1">
                   <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                     {next.vendor}
                   </p>
                   <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                     {next.days_overdue === 0 ? "Due today" : `${next.days_overdue} day${next.days_overdue > 1 ? "s" : ""} overdue`}
                   </p>
                 </div>
                 <span className="font-syne font-bold text-sm" style={{ color: '#f87171' }}>
                   {fmtInr(next.amount)}
                 </span>
               </div>
             );
           })()
         )}
       </div>
       {/* Divider */}
       <div className="h-px mx-4" style={{ background: 'var(--border-lg)' }} />
       {/* Month-end estimate */}
       <div className="p-4">
         <div className="flex items-center justify-between">
           <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
             Expected month-end balance
           </p>
           <p className="font-syne font-bold text-sm"
              style={{ color: (balance.remaining - balance.fixed_unpaid_total) >= 0 ? '#34d399' : '#f87171' }}>
             {fmtInr(balance.remaining - balance.fixed_unpaid_total)}
           </p>
         </div>
       </div>
     </div>
   </section>
   ```

**Acceptance criteria**:
- Shows next overdue bill (least overdue first) when unpaid bills exist.
- Shows "🎉 All bills paid this month" when `dueReminders` is empty.
- Month-end balance = `remaining - fixed_unpaid_total`.

---

## Item 8 — T1: Hero Balance Card on Today tab

**Scope**: Frontend-only

**Files**:
- New: `frontend/react/src/components/shared/HeroBalanceCard.tsx`
- `frontend/react/src/pages/DashboardPage.tsx` — lines 50–97 (summary render block)

**Root cause**: `DashboardPage.tsx` line 50: `const showSummary = tab === "today" || tab === "fixed" || tab === "overview"`. Both mobile (SummaryStrip) and desktop (flip-cards) render identically for all 3 tabs. The spec wants a different, richer component specifically on the Today tab — replacing the strip/flip-cards on today only.

**What to do**:

1. Create `frontend/react/src/components/shared/HeroBalanceCard.tsx`:
   ```tsx
   import type { Summary } from "@/types";
   import { fmtInr } from "@/utils/formatInr";
   import { Wallet } from "lucide-react";

   interface Props { balance: Summary["balance"]; }

   export function HeroBalanceCard({ balance }: Props) {
     const today = new Date();
     const daysInMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
     const daysLeft = Math.max(daysInMonth - today.getDate(), 0);
     const dailyBudget = daysLeft > 0 ? balance.remaining / daysLeft : 0;
     const subLabel = balance.remaining > 0 && dailyBudget > 500
       ? `Comfortable for the next ${daysLeft} day${daysLeft !== 1 ? "s" : ""}`
       : `₹${Math.round(dailyBudget).toLocaleString("en-IN")}/day remaining`;

     return (
       <div className="space-y-3">
         {/* Main hero card */}
         <div className="rounded-2xl p-5 border"
              style={{ background: 'var(--card)', borderColor: 'var(--border-lg)' }}>
           <div className="flex items-start gap-3">
             <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: 'rgba(52,211,153,0.15)' }}>
               <Wallet size={20} style={{ color: '#34d399' }} />
             </div>
             <div>
               <p className="text-[10px] font-syne font-bold uppercase tracking-widest mb-1"
                  style={{ color: 'var(--text-sub)' }}>
                 Remaining this month
               </p>
               <p className="text-3xl font-syne font-extrabold leading-none"
                  style={{ color: balance.remaining >= 0 ? '#34d399' : '#f87171' }}>
                 {fmtInr(balance.remaining)}
               </p>
               <p className="text-xs mt-1.5" style={{ color: 'var(--text-muted)' }}>
                 {subLabel}
               </p>
             </div>
           </div>
         </div>

         {/* 3 chips */}
         <div className="grid grid-cols-3 gap-2">
           {[
             { label: "Income",        value: balance.total_income,      colour: '#6366f1' },
             { label: "Fixed Paid",    value: balance.fixed_paid_total,  colour: '#34d399' },
             { label: "Pending Bills", value: balance.fixed_unpaid_total, colour: '#f59e0b' },
           ].map(chip => (
             <div key={chip.label} className="rounded-xl p-3 text-center border"
                  style={{ background: 'var(--card)', borderColor: 'var(--border-lg)' }}>
               <p className="text-[9px] font-syne font-bold uppercase tracking-wider mb-1"
                  style={{ color: 'var(--text-muted)' }}>
                 {chip.label}
               </p>
               <p className="text-sm font-syne font-bold" style={{ color: chip.colour }}>
                 {fmtInr(chip.value)}
               </p>
             </div>
           ))}
         </div>
       </div>
     );
   }
   ```

2. In `DashboardPage.tsx`, import `HeroBalanceCard` at the top.

3. Split the `showSummary` block (lines 76–97) into two branches. Change:
   ```tsx
   const showSummary = tab === "today" || tab === "fixed" || tab === "overview";
   ```
   to keep the same value (it still controls fetching), but render differently:
   ```tsx
   {/* Today tab: hero card (replaces strip/flip-cards) */}
   {tab === "today" && balance && (
     <div className="max-w-2xl mx-auto px-4 pt-4">
       <HeroBalanceCard balance={balance} />
     </div>
   )}

   {/* Fixed/Overview tabs: keep existing strip + flip-cards */}
   {(tab === "fixed" || tab === "overview") && balance && (
     <>
       <div className="md:hidden sticky z-20 border-b px-4 py-2" style={{ top: "56px", backgroundColor: "var(--bg)", borderColor: "var(--border)" }}>
         <SummaryStrip balance={balance} />
       </div>
       <div className="hidden md:flex gap-3 max-w-2xl mx-auto px-4 pt-4">
         {flipCards.map(c => (
           <SummaryFlipCard key={c.label} label={c.label} value={c.value} colour={c.colour} />
         ))}
       </div>
     </>
   )}
   ```
   The `showSummary` variable and `flipCards` derivation (lines 50–69) remain unchanged.

**Acceptance criteria**:
- Today tab shows the hero card (large remaining balance + 3 chips).
- Fixed and Overview tabs still show SummaryStrip on mobile and flip-cards on desktop.
- No regression on those two tabs.

---

## Item 9 — O2: "This Month's Story" AI sentence on Overview

**Scope**: Backend + Frontend

**Files**:
- `backend/ai_parser.py` — new function after `generate_daily_mantra` (line ~138)
- `backend/main.py` — new endpoint, must go **before** `/summary/{month_key}` in the file ordering; insert in the `# ── Insights ──` section near the other `/insights/` routes (~line 1100 area)
- `frontend/react/src/types/index.ts` — new `MonthlyStory` interface after `DailyMantra`
- `frontend/react/src/components/tabs/OverviewTab.tsx` — new fetch in `load()`, new state, new section after Financial Snapshot (O1)

**Root cause**: No narrative summary exists. The LLM pattern (`generate_daily_mantra`) is already established in `ai_parser.py`. An in-memory cache dict pattern (`_mantra_cache`) is already established in `main.py`.

**What to do**:

### `backend/ai_parser.py`
Add after `generate_daily_mantra()`:
```python
def generate_monthly_story(context: dict) -> str:
    """
    Generate a single factual sentence summarising the month.
    Not motivational (that's Tara's job) — just clear, data-grounded summary.

    Expected context keys:
        month_label: str         # e.g. "June 2026"
        remaining: float
        fixed_completion_pct: float  # fixed_paid / (fixed_paid + fixed_unpaid) * 100
        top_category: str | None
        top_category_spent: float
        variable_total: float
        days_left: int
    """
    prompt = f"""Financial month summary for {context['month_label']}:
- Remaining balance: ₹{context['remaining']:.0f}
- Fixed bills completion: {context['fixed_completion_pct']:.0f}%
- Top spending category: {context.get('top_category') or 'N/A'} (₹{context.get('top_category_spent', 0):.0f})
- Total variable spend: ₹{context['variable_total']:.0f}
- Days left in month: {context['days_left']}

Write ONE factual sentence (max 35 words) summarising this month's finances.
Rules:
- Factual and neutral, not motivational or encouraging.
- Past-tense for completed items, forward-looking for projections.
- Do NOT start the sentence with "I".
- Reference at least one concrete number.
- No ₹ symbol is fine, but use it if referencing specific amounts.
- Return ONLY the sentence, no preamble, no quotation marks."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=120,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
```

### `backend/main.py`
Add a new cache dict near `_mantra_cache`:
```python
_story_cache: dict[tuple[int, str], str] = {}
```

Add the endpoint in the `/insights/` section (before the catch-all `/summary/{month_key}` if that exists in that area):
```python
@app.get("/insights/story/{month_key}")
def monthly_story(month_key: str, session: Session = Depends(get_session),
                  current_user: User = Depends(get_current_user)):
    cache_key = (current_user.id, month_key)
    if cache_key in _story_cache:
        return {"story": _story_cache[cache_key]}

    balance = get_balance_summary(session, month_key, user_id=current_user.id)
    spent_by_cat = get_monthly_spent_by_category(session, month_key, user_id=current_user.id)

    top_category = None
    top_category_spent = 0.0
    if spent_by_cat:
        top_category = max(spent_by_cat, key=spent_by_cat.get)
        top_category_spent = spent_by_cat[top_category]

    year, month = map(int, month_key.split("-"))
    days_in_month = calendar.monthrange(year, month)[1]
    today = dt.today()
    days_left = max(days_in_month - today.day, 0) if month_key == today.strftime("%Y-%m") else 0

    fixed_total = balance["fixed_paid_total"] + balance["fixed_unpaid_total"]
    fixed_completion_pct = (
        (balance["fixed_paid_total"] / fixed_total * 100) if fixed_total > 0 else 100.0
    )

    import calendar as _cal
    month_label = f"{today.strftime('%B') if month == today.month else _cal.month_name[month]} {year}"

    context = {
        "month_label": month_label,
        "remaining": balance["remaining"],
        "fixed_completion_pct": fixed_completion_pct,
        "top_category": top_category,
        "top_category_spent": top_category_spent,
        "variable_total": balance["variable_total"],
        "days_left": days_left,
    }

    try:
        story = generate_monthly_story(context)
    except Exception:
        raise HTTPException(status_code=502, detail="Story generation failed")

    _story_cache[cache_key] = story
    return {"story": story}
```

Note: `calendar` is already imported in `main.py` inside `daily_mantra()` as a local import. Pull it to module level (check if it's already at top-level; if not, add `import calendar` with the other imports) or use `_cal = __import__("calendar")` pattern. Also `dt` refers to `datetime` — check alias in `main.py` and use consistently. `generate_monthly_story` must be imported from `ai_parser.py` at the top of `main.py`.

### `frontend/react/src/types/index.ts`
After `DailyMantra`:
```typescript
export interface MonthlyStory {
  story: string;
}
```

### `frontend/react/src/components/tabs/OverviewTab.tsx`
1. Add `MonthlyStory` to the types import.
2. Add `const [story, setStory] = useState<string | null>(null);` state.
3. Add a 6th call to `load()`'s `Promise.all`:
   ```tsx
   api.get<MonthlyStory>(`/insights/story/${selMonth}`).then(r => r.data.story).catch(() => null),
   ```
   Destructure as `storyResult` and call `setStory(storyResult)`.
4. Add section after Financial Snapshot (O1), before BalanceBreakdown:
   ```tsx
   {story && (
     <section>
       <p className="text-[10px] font-syne font-bold uppercase tracking-widest mb-1"
          style={{ color: 'var(--text-sub)' }}>
         {selMonth.split("-")[1] && new Date(selMonth + "-01").toLocaleString("en-IN", { month: "long" })} in one sentence
       </p>
       <p className="text-sm leading-relaxed" style={{ color: 'var(--text)' }}>
         {story}
       </p>
     </section>
   )}
   ```

**Acceptance criteria**:
- Overview shows a one-sentence factual month summary after the Financial Snapshot grid.
- Sentence doesn't start with "I" and contains no motivational language.
- Section silently absent when the endpoint fails.
- Past months' stories are cached per `(user_id, month_key)` — no re-generation when switching back.

---

## Item 10 — O7: Tiny Win card on Overview

**Scope**: Backend + Frontend

**Files**:
- `backend/main.py` — new endpoint `GET /insights/tiny-win/{month_key}`, rules-based (no LLM)
- `frontend/react/src/types/index.ts` — new `TinyWin` interface
- `frontend/react/src/components/tabs/OverviewTab.tsx` — new state, fetch, bottom section

**Root cause**: No Tiny Win exists. Rules-based so no LLM cost. All data comes from `get_balance_summary()` and `get_monthly_spent_by_category()` already available in `main.py`. Previous-month food spend needs `get_monthly_spent_by_category` on `prev_month_key`.

**What to do**:

### `backend/main.py`
```python
@app.get("/insights/tiny-win/{month_key}")
def tiny_win(month_key: str, session: Session = Depends(get_session),
             current_user: User = Depends(get_current_user)):
    balance = get_balance_summary(session, month_key, user_id=current_user.id)
    spent_by_cat = get_monthly_spent_by_category(session, month_key, user_id=current_user.id)

    year, month = map(int, month_key.split("-"))
    days_in_month = calendar.monthrange(year, month)[1]
    today = dt.today()
    days_left = max(days_in_month - today.day, 0) if month_key == today.strftime("%Y-%m") else 0

    # Condition 1: all bills cleared with days to spare
    if balance["fixed_unpaid_total"] == 0 and days_left > 5:
        return {"win": f"All bills cleared with {days_left} days to spare."}

    # Condition 2: food spend down from last month
    prev_month = month - 1
    prev_year = year
    if prev_month <= 0:
        prev_month += 12
        prev_year -= 1
    prev_month_key = f"{prev_year:04d}-{prev_month:02d}"
    prev_spent = get_monthly_spent_by_category(session, prev_month_key, user_id=current_user.id)
    food_curr = spent_by_cat.get("Food", 0)
    food_prev = prev_spent.get("Food", 0)
    if food_prev > 0 and food_curr < food_prev:
        return {"win": "Food spending is down from last month."}

    # Condition 3: healthy remaining buffer
    if balance["total_income"] > 0 and (balance["remaining"] / balance["total_income"]) > 0.15:
        return {"win": "You're keeping over 15% of income available — solid buffer."}

    # Fallback
    return {"win": "You've been tracking consistently. That itself is progress."}
```

### `frontend/react/src/types/index.ts`
```typescript
export interface TinyWin {
  win: string;
}
```

### `frontend/react/src/components/tabs/OverviewTab.tsx`
Add `tinyWin` state, add fetch to `load()` (catch → `null`), add bottom section:
```tsx
{tinyWin && (
  <section>
    <div className="rounded-2xl p-4 border flex items-center gap-4"
         style={{ background: 'var(--card)', borderColor: 'var(--border-lg)' }}>
      <span className="text-2xl flex-shrink-0">🏆</span>
      <div>
        <p className="text-[10px] font-syne font-bold uppercase tracking-widest mb-1"
           style={{ color: '#f59e0b' }}>
          Tiny Win
        </p>
        <p className="text-sm leading-relaxed" style={{ color: 'var(--text)' }}>
          {tinyWin}
        </p>
      </div>
    </div>
  </section>
)}
```

**Acceptance criteria**:
- Tiny Win card at the bottom of Overview with a matched condition.
- Condition 1 takes priority; fallback always matches.
- No LLM call — purely rules-based.

---

## Item 11 — O3: Peace of Mind Score

**Scope**: Backend + Frontend

**Status**: Formula weights confirmed by user on 2026-06-25. Ready to implement.

**Formula (confirmed):**

| Sub-signal | Max pts | Condition |
|---|---|---|
| Bills paid | 35 | `fixed_unpaid_total == 0` → 35, else `35 × (paid / total)` |
| Remaining buffer | 30 | `remaining / total_income`: ≥ 20% → 30, 10–20% → 20, 5–10% → 10, < 5% → 0 |
| Spending pace | 20 | `variable_total / (total_income × 0.4)`: ≤ 80% → 20, 80–100% → 10, > 100% → 0 |
| Tracking | 15 | Always 15 (placeholder until streak tracking is built) |

**Files when unblocked**:
- `backend/budget_rules.py` — `compute_peace_of_mind(balance: dict) -> dict`
- `backend/main.py` — fold into `GET /summary/{month_key}` response (add `peace_of_mind` key) or new endpoint
- `frontend/react/src/types/index.ts` — extend `Summary` or new type
- `frontend/react/src/components/tabs/OverviewTab.tsx` — new section between "This Month's Story" (O2) and "Financial Pulse" (O4)

**Plan detail deferred** until formula is confirmed.

---

## Recommended Section Order on Overview after all items are implemented

1. Financial Snapshot grid (O1)
2. This Month's Story sentence (O2)
3. Peace of Mind Score (O3 — blocked)
4. What Changed? rows (O5)
5. Financial Pulse tiles (O4)
6. Upcoming Reality card (O6)
7. BalanceBreakdown bar (existing)
8. Spend by Category donut (existing)
9. Budget Health (existing)
10. Top Spends (existing)
11. Tiny Win card (O7)

---

## Execution Order

| # | Issue | Effort | Risk | Deps |
|---|-------|--------|------|------|
| 1 | T3 — empty state chips | XS | None | — |
| 2 | T4 — Ask Tara FAB | XS | None | — |
| 3 | T2 — avatar + Ask Tara button + rename | S | None | `tara.png` must exist first |
| 4 | O5 — What Changed? (replace MoM table) | S | None | — |
| 5 | O4 — Financial Pulse tiles | S | None | — |
| 6 | O1 — Financial Snapshot grid | XS | None | — |
| 7 | O6 — Upcoming Reality card | S | None | endpoint path is `/fixed/due-reminders/` |
| 8 | T1 — Hero Balance Card on Today | M | Low — new component + DashboardPage branch | — |
| 9 | O2 — This Month's Story (backend + frontend) | M | Low — additive endpoint + cache | — |
| 10 | O7 — Tiny Win card (backend + frontend) | S | Low — rules-based, no LLM | — |
| 11 | O3 — Peace of Mind Score | M | Medium — formula confirmed 2026-06-25 | — |

---

## Definition of Done

- `npm run build` passes (zero TypeScript errors, zero ESLint warnings)
- Items T1–T4 verified on Today tab; no regression on Fixed or Overview tabs
- Overview items verified: Financial Snapshot, Story, What Changed?, Financial Pulse, Upcoming Reality, Tiny Win all render with real data
- MoM table no longer appears on main Overview screen
- Peace of Mind deferred until formula confirmed
