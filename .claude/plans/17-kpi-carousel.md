# Implementation Plan: KPI Carousel (Spec 17)
**Spec**: `.claude/specs/17_kpi-carousel.md`
**Date**: 2026-06-28
**Completed**: 2026-06-28 ✅ — build clean, zero TS errors
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

2 items — both frontend-only. No backend changes. No new API endpoints.
Tackle **Item 1 first** (CSS only, zero risk), then **Item 2** (component replacement).

---

## Item 1 — Add KPI Carousel CSS to `index.css`

**Scope**: Frontend-only  
**File**: `frontend/react/src/index.css` — append after line 194 (end of file, after the `/* ── Flip card */` block)

**Root cause**: No KPI carousel styles exist yet. The Flip card block ends at line 194 and is currently the last rule in the file.

**What to do**:

Append the following block verbatim to the end of `frontend/react/src/index.css` after line 194:

```css
/* ══════════════════════════════════════════════════════════════
   KPI CAROUSEL — Spec 17
   ══════════════════════════════════════════════════════════════ */

/* Card gradients — dark (default) */
.kpi-card-remaining { background: linear-gradient(135deg, #0a4a2e 0%, #0d6b3f 35%, #1a9e58 70%, #00c96e 100%); }
.kpi-card-income    { background: linear-gradient(135deg, #1a0a4a 0%, #2e1080 35%, #5a28c8 70%, #7c55ff 100%); }
.kpi-card-bills     { background: linear-gradient(135deg, #3a1a00 0%, #7a3800 35%, #c86000 70%, #f0920a 100%); }

/* Card gradients — light mode */
html.light .kpi-card-remaining { background: linear-gradient(135deg, #0d6b3f 0%, #1a9e58 40%, #00c96e 75%, #34d399 100%); }
html.light .kpi-card-income    { background: linear-gradient(135deg, #2e1080 0%, #5a28c8 40%, #7c55ff 75%, #a78bfa 100%); }
html.light .kpi-card-bills     { background: linear-gradient(135deg, #7a3800 0%, #c86000 40%, #f0920a 75%, #fbbf24 100%); }

/* Text inside cards — always white regardless of theme */
.kpi-card-value   { color: #ffffff; }
.kpi-card-label   { color: rgba(255, 255, 255, 0.70); }
.kpi-card-sub     { color: rgba(255, 255, 255, 0.50); }
.kpi-card-pending { color: rgba(255, 180, 100, 0.90); }

/* Card shell (shared geometry + surface effects) */
.kpi-card-shell {
  border-radius: 22px;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}
.kpi-card-shell::before {
  content: "";
  position: absolute;
  top: -30%;
  left: -20%;
  width: 60%;
  height: 80%;
  background: radial-gradient(ellipse, rgba(255,255,255,0.25) 0%, transparent 70%);
  mix-blend-mode: overlay;
  pointer-events: none;
}
.kpi-card-shell::after {
  content: "";
  position: absolute;
  top: 0; right: 0; bottom: 0; left: 0;
  background: linear-gradient(135deg, transparent 45%, rgba(255,255,255,0.06) 55%, transparent 65%);
  pointer-events: none;
}

/* Left accent bar */
.kpi-card-shell .kpi-accent {
  position: absolute;
  left: 0; top: 16px; bottom: 16px;
  width: 3px;
  border-radius: 0 3px 3px 0;
}
.kpi-card-remaining .kpi-accent { background: #00c96e; }
.kpi-card-income    .kpi-accent { background: #a78bfa; }
.kpi-card-bills     .kpi-accent { background: #fbbf24; }

/* ── Mobile carousel wrapper ─────────────────────────────────── */
.kpi-carousel-wrapper {
  position: relative;
  user-select: none;
  -webkit-user-select: none;
}

/* Stage: clipped window showing active card + right peek */
.kpi-carousel-stage {
  position: relative;
  height: 186px;          /* 150px card + 18px top + 18px breathing room */
  overflow: visible;
  padding-left: 18px;
}

/* Active card */
.kpi-carousel-stage .kpi-active-card {
  width: 264px;
  height: 150px;
  position: relative;
  z-index: 10;
  transition: transform 350ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
  top: 18px;
}

/* Stacked cards behind (decorative, no content) */
.kpi-card-shell.pos-behind {
  position: absolute;
  top: 22px;
  left: 18px;
  width: 264px;
  height: 150px;
  z-index: 5;
  transform: rotate(-2deg) scale(0.94);
  transform-origin: center bottom;
}
.kpi-card-shell.pos-far-behind {
  position: absolute;
  top: 26px;
  left: 18px;
  width: 264px;
  height: 150px;
  z-index: 3;
  transform: rotate(-4deg) scale(0.88);
  transform-origin: center bottom;
}

/* Peek card (right edge) */
.kpi-card-shell.pos-peek-right {
  position: absolute;
  top: 18px;
  left: calc(18px + 264px + 8px); /* active card left + card width + gap */
  width: 264px;
  height: 150px;
  z-index: 8;
  /* only ~28px visible — parent clips at phone edge */
}

/* Dot indicators — mobile only */
.kpi-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 12px;
}
.kpi-dot {
  height: 6px;
  border-radius: 3px;
  background: var(--border-lg);
  transition: width 250ms ease, background 250ms ease;
  cursor: pointer;
  border: none;
  padding: 0;
  width: 6px;
}
.kpi-dot.active {
  width: 20px;
  background: var(--accent);
}

/* ── Desktop row (≥ 768px) — all 3 cards visible ─────────────── */
.kpi-desktop-row {
  display: none;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
@media (min-width: 768px) {
  .kpi-carousel-stage,
  .kpi-dots { display: none; }

  .kpi-desktop-row { display: flex; }

  .kpi-desktop-row .kpi-card-shell {
    height: 140px;
    transition: transform 350ms cubic-bezier(0.25, 0.46, 0.45, 0.94),
                opacity 350ms ease,
                width 350ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }
  .kpi-desktop-row .kpi-card-shell.active {
    width: 380px;
    transform: scale(1);
    opacity: 1;
    z-index: 3;
  }
  .kpi-desktop-row .kpi-card-shell.side {
    width: 260px;
    transform: scale(0.93);
    opacity: 0.6;
    z-index: 2;
    cursor: pointer;
  }
}
```

---

## Item 2 — Replace 3-Tile Grid with KPI Carousel in `OverviewTab.tsx`

*Depends on Item 1 being done first (CSS classes must exist).*

**Scope**: Frontend-only  
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx`

**Root cause** (verified against current code):

- Lines 276–329: `/* ── Section 0: KPI tiles */` renders a `grid grid-cols-3 gap-3` with 3 tiles using `tile.label` / `tile.value` / `tile.colour`. This layout breaks on mobile: label text clips/wraps, subtitle is ~8px unreadable.
- Line 1, import: `useRef` is **not** imported — needs to be added for touch ref.
- `useCallback` IS already imported (line 1).
- Data field mapping (current code → spec names):
  - `balance.remaining` → `remainingBalance`
  - `balance.total_income` → `totalIncome`
  - `balance.fixed_paid_total` → `billsPaid`
  - `balance.fixed_unpaid_total` → `pendingAmount` (when > 0)
  - `balance.fixed_paid_total + balance.fixed_unpaid_total` → `totalBills`

**What to do**:

### Step A — Add `useRef` to import (line 1)

```tsx
// Before:
import { useEffect, useState, useCallback } from "react";

// After:
import { useEffect, useState, useCallback, useRef } from "react";
```

### Step B — Add `activeKpiIndex` state + touch refs

Add immediately after the existing state declarations (search for where `const [balance` or the first `useState` calls are defined inside the component, before the `load` callback). Insert:

```tsx
// KPI carousel state
const [activeKpiIndex, setActiveKpiIndex] = useState(0);
const touchStartX = useRef<number>(0);
const touchStartTime = useRef<number>(0);
const touchDeltaX = useRef<number>(0);
```

### Step C — Add `kpiCards` array + carousel handlers

Add just before the `return (` statement (around line 273):

```tsx
// KPI carousel data — derived from existing balance object, no new API calls
const kpiCards = [
  {
    id: "remaining",
    label: "Remaining",
    icon: "💰",
    value: fmtInr(balance.remaining),
    subtitle: "Left for the month",
    pending: null as string | null,
  },
  {
    id: "income",
    label: "Income",
    icon: "💼",
    value: fmtInr(balance.total_income),
    subtitle: "Total this month",
    pending: null as string | null,
  },
  {
    id: "bills",
    label: "Bills Paid",
    icon: "✅",
    value: fmtInr(balance.fixed_paid_total),
    subtitle: `Out of ${fmtInr(balance.fixed_paid_total + balance.fixed_unpaid_total)}`,
    pending: balance.fixed_unpaid_total > 0
      ? `${fmtInr(balance.fixed_unpaid_total)} still pending`
      : null,
  },
];

const navigateTo = useCallback((index: number) => {
  setActiveKpiIndex(Math.max(0, Math.min(2, index)));
}, []);

const handleTouchStart = useCallback((e: React.TouchEvent) => {
  touchStartX.current = e.touches[0].clientX;
  touchStartTime.current = Date.now();
  touchDeltaX.current = 0;
}, []);

const handleTouchMove = useCallback((e: React.TouchEvent) => {
  touchDeltaX.current = e.touches[0].clientX - touchStartX.current;
}, []);

const handleTouchEnd = useCallback(() => {
  const delta = touchDeltaX.current;
  const elapsed = Date.now() - touchStartTime.current;
  const velocity = Math.abs(delta) / elapsed;
  const triggered = Math.abs(delta) > 40 || velocity > 0.3;
  if (!triggered) return;
  if (delta < 0) {
    // left swipe → advance
    navigateTo(activeKpiIndex + 1);
  } else {
    // right swipe → retreat
    navigateTo(activeKpiIndex - 1);
  }
}, [activeKpiIndex, navigateTo]);
```

### Step D — Replace the KPI grid JSX (lines 276–329)

Remove this block entirely:

```tsx
{/* ── Section 0: KPI tiles ─────────────────────────── */}
<section>
  <div className="grid grid-cols-3 gap-3">
    {[
      { ... },
      { ... },
      { ... },
    ].map(tile => (
      <div key={tile.label} ...>
        ...
      </div>
    ))}
  </div>
</section>
```

Replace with the full carousel JSX:

```tsx
{/* ── Section 0: KPI Carousel ─────────────────────────── */}
<section>
  <div className="kpi-carousel-wrapper">

    {/* Mobile: stacked-deck stage */}
    <div
      className="kpi-carousel-stage"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Far-behind decorative card */}
      <div
        className={`kpi-card-shell kpi-card-${
          kpiCards[(activeKpiIndex + 2) % 3].id
        } pos-far-behind`}
      >
        <div className="kpi-accent" />
      </div>

      {/* Behind decorative card */}
      <div
        className={`kpi-card-shell kpi-card-${
          kpiCards[(activeKpiIndex + 1) % 3].id
        } pos-behind`}
      >
        <div className="kpi-accent" />
      </div>

      {/* Active card — full content */}
      <div
        className={`kpi-card-shell kpi-card-${kpiCards[activeKpiIndex].id} kpi-active-card`}
        style={{ padding: "16px 20px" }}
      >
        <div className="kpi-accent" />
        {/* WM watermark */}
        <span
          style={{
            position: "absolute", right: 16, top: 12,
            fontSize: 20, fontWeight: 900, fontStyle: "italic",
            color: "rgba(255,255,255,0.07)",
            pointerEvents: "none",
          }}
        >
          WM
        </span>
        {/* Label row */}
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 12 }}>
          <span style={{ fontSize: 16 }}>{kpiCards[activeKpiIndex].icon}</span>
          <span className="kpi-card-label" style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            {kpiCards[activeKpiIndex].label}
          </span>
        </div>
        {/* Value */}
        <p className="kpi-card-value" style={{ fontSize: 30, fontWeight: 700, lineHeight: 1.1 }}>
          {kpiCards[activeKpiIndex].value}
        </p>
        {/* Subtitle */}
        <p className="kpi-card-sub" style={{ fontSize: 11, marginTop: 4 }}>
          {kpiCards[activeKpiIndex].subtitle}
        </p>
        {/* Pending line (Bills card only) */}
        {kpiCards[activeKpiIndex].pending && (
          <p className="kpi-card-pending" style={{ fontSize: 11, marginTop: 2 }}>
            {kpiCards[activeKpiIndex].pending}
          </p>
        )}
      </div>

      {/* Peek card (next card's left edge visible) */}
      {activeKpiIndex < 2 && (
        <div
          className={`kpi-card-shell kpi-card-${kpiCards[activeKpiIndex + 1].id} pos-peek-right`}
        >
          <div className="kpi-accent" />
        </div>
      )}
    </div>

    {/* Dot indicators — mobile only */}
    <div className="kpi-dots md:hidden">
      {kpiCards.map((card, i) => (
        <button
          key={card.id}
          className={`kpi-dot ${i === activeKpiIndex ? "active" : ""}`}
          onClick={() => navigateTo(i)}
          aria-label={`View ${card.label}`}
        />
      ))}
    </div>

    {/* Desktop: all 3 cards side by side */}
    <div className="kpi-desktop-row hidden md:flex">
      {kpiCards.map((card, i) => (
        <div
          key={card.id}
          className={`kpi-card-shell kpi-card-${card.id} ${i === activeKpiIndex ? "active" : "side"}`}
          style={{ padding: "14px 20px" }}
          onClick={() => navigateTo(i)}
        >
          <div className="kpi-accent" />
          <span
            style={{
              position: "absolute", right: 14, top: 10,
              fontSize: 18, fontWeight: 900, fontStyle: "italic",
              color: "rgba(255,255,255,0.07)",
              pointerEvents: "none",
            }}
          >
            WM
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
            <span style={{ fontSize: 14 }}>{card.icon}</span>
            <span className="kpi-card-label" style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em" }}>
              {card.label}
            </span>
          </div>
          <p className="kpi-card-value" style={{ fontSize: i === activeKpiIndex ? 26 : 22, fontWeight: 700, lineHeight: 1.1 }}>
            {card.value}
          </p>
          <p className="kpi-card-sub" style={{ fontSize: 10, marginTop: 3 }}>
            {card.subtitle}
          </p>
          {card.pending && (
            <p className="kpi-card-pending" style={{ fontSize: 10, marginTop: 2 }}>
              {card.pending}
            </p>
          )}
        </div>
      ))}
    </div>

  </div>
</section>
```

### Step E — Update the file-level JSDoc comment

Lines 21–22 mention "Balance summary cards (3-col grid)". Update to:

```tsx
// Before:
 *   1. Balance summary cards (3-col grid)

// After:
 *   1. KPI carousel (swipeable, 3 cards: Remaining / Income / Bills Paid)
```

---

## Acceptance Check (post-implementation, run locally)

After both items are done, start the Vite dev server (`npm run dev` in `frontend/react`) and verify on the browser:

1. Mobile viewport (~390px): one card visible, stacked cards behind, peek at right edge, dots below
2. Swipe left/right changes active card; dots update; no wrap past ends
3. Tapping dots navigates directly
4. Light mode (`html.light` class on `<html>`): gradients shift lighter, text stays white
5. Desktop (≥ 768px): 3 cards visible, center is active, side cards smaller/dimmed, clicking activates

Regression: rest of Overview tab (Story, BalanceBreakdown, SpendDonut, etc.) renders unchanged.
