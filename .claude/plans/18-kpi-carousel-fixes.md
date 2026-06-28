# Implementation Plan: KPI Carousel Fixes + Sentence Prompt
**Spec**: `.claude/specs/18_kpi-carousel-fixes.md`  
**Date**: 2026-06-28  
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

4 issues total — 1 backend-only (18D), 3 frontend-only (18A, 18B, 18C).  
Ordered smallest blast-radius first. 18B and 18C go in one pass (same CSS block). 18A last among frontend items because it touches gesture wiring.

---

## Item 1 — 18D: Sentence prompt too long (backend)

**Scope**: Backend-only  
**File**: `backend/ai_parser.py`, lines 155–171 (the `generate_monthly_story` function)

**Root cause**: `generate_monthly_story()` (line 162) uses a soft "hard limit: 30 words" instruction alongside bullet-list rules. The LLM treats these as suggestions, not constraints. Observed outputs are 34–38 words. The prompt also lacks explicit self-verification ("count the words") and concrete good/bad examples, which are the two techniques that reliably reduce drift.

Current prompt block (lines 155–171):
```python
prompt = f"""Financial month summary for {context['month_label']}:
- Remaining balance: ₹{context['remaining']:.0f}
- Fixed bills completion: {context['fixed_completion_pct']:.0f}%
- Top spending category: {context.get('top_category') or 'N/A'} (₹{context.get('top_category_spent', 0):.0f})
- Total variable spend: ₹{context['variable_total']:.0f}
- Days left in month: {context['days_left']}

Write ONE sentence (hard limit: 30 words) summarising this month's finances.
Rules:
- ONE sentence only. No semicolons. No list-style constructions (no "X, Y, and Z").
- Factual and neutral — not motivational or encouraging.
- Past-tense for completed items, forward-looking for projections.
- Do NOT start the sentence with "I".
- Prioritise: bills completion status, savings allocated, remaining balance.
- Include variable spending total ONLY if it fits within the 30-word limit.
- Use ₹ symbol for amounts.
- Return ONLY the sentence, no preamble, no quotation marks."""
```

**What to do**: Replace the entire `prompt = f"""..."""` block in `generate_monthly_story()` with the structurally-enforced version from the spec. Key changes:
- `STRICT RULES` framing replaces soft bullet list
- "Count the words before responding" forces self-verification
- Word limit lowered from 30 → **25** (real output will be ~25–28 with some drift)
- Concrete GOOD / BAD examples with word counts
- Semicolons explicitly banned
- `max_tokens` on line 175 stays at 80 — no change needed

Replace from `prompt = f"""Financial month summary` (line 155) through the closing `"""` (line 171):

```python
    prompt = f"""Generate a single sentence summary of this month's finances.

STRICT RULES — violating any rule makes the output wrong:
1. Exactly ONE sentence. No semicolons. No "and X and Y and Z" chaining.
2. Maximum 25 words. Count the words before responding. If over 25, rewrite.
3. Must mention exactly TWO of these three: bills status, savings amount, remaining balance.
4. Factual and neutral tone. Not motivational or encouraging.
5. Use ₹ symbol with formatted numbers (₹34,000 not ₹34000).
6. Return ONLY the sentence, no preamble, no quotation marks.

GOOD examples (all under 25 words):
- "Bills are 98% done, ₹34,000 went to savings, and ₹3,479 remains." (13 words)
- "Nearly all bills paid, ₹3,479 left after saving ₹34,000 this month." (13 words)
- "₹34,000 saved, bills at 98%, with ₹3,479 still in hand." (11 words)

BAD examples (too long or chained):
- "Bills reached 98% completion while ₹34000 was allocated to savings, leaving ₹3479 available with two days remaining after ₹52066 in variable spending this month." (too long)
- "All fixed bills were paid while ₹36062 went to savings and ₹53212 to variable spending, leaving ₹4005 for the final two days." (too long, chained)

Financial data for {context['month_label']}:
- Bills paid: {context['fixed_completion_pct']:.0f}% of fixed expenses
- Savings allocated: ₹{context.get('top_category_spent', 0):.0f} (if top category is savings)
- Remaining balance: ₹{context['remaining']:.0f}
- Days remaining: {context['days_left']}"""
```

> **Note on savings field**: The `generate_monthly_story` context dict does not have a `savings_allocated` key — it has `top_category` and `top_category_spent`. Use the spec's example field names as labels in the prompt but populate from available keys. If a dedicated savings field is needed, it must be passed in from the call site in `main.py` (search for `generate_monthly_story(` to find where it's called and what context is assembled there). If the call site already computes savings, add it to the context dict — otherwise the prompt data block shown above is a reasonable approximation using available keys. Verify at call site before finalising the data block.

---

## Item 2 — 18B + 18C: Desktop card equal widths + height (frontend CSS + JSX)

**Scope**: Frontend-only  
**Files**:
- `frontend/react/src/index.css` — lines 346–365 (`.kpi-desktop-row .kpi-card-shell.active` and `.kpi-card-shell.side`)
- `frontend/react/src/components/tabs/OverviewTab.tsx` — line 444 (font-size differential)

**Root cause (18B)**: CSS at `index.css` line 352–361:
```css
.kpi-desktop-row .kpi-card-shell.active {
  width: 380px;    ← 46% wider than side cards
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
```
Additionally, `OverviewTab.tsx` line 444 renders `fontSize: i === activeKpiIndex ? 26 : 22` — active card has a 4px larger font, amplifying the visual size difference.

**Root cause (18C)**: CSS already sets `height: 140px` (line 347), matching the spec's target. The spec's "180px tall" observation was a visual effect caused by the 380px width + `scale(1)` vs 260px + `scale(0.93)` combined with larger font size. Fixing 18B will resolve the perceived height issue. No separate height change is needed — **verify after 18B fix before adding height overrides.**

**What to do**:

### index.css (18B fix)
Replace the `.active` and `.side` rules inside `@media (min-width: 768px)` so all desktop cards are equal width (`flex: 1`), no scale differential, no opacity dimming for side cards. Only add a subtle ring on the active card:

```css
/* Before (lines ~352–362): */
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

/* After: */
.kpi-desktop-row .kpi-card-shell {
  flex: 1;            /* equal width — each card is 1/3 of row */
  cursor: pointer;
}
.kpi-desktop-row .kpi-card-shell.active {
  box-shadow: 0 0 0 2px rgba(255,255,255,0.15), 0 8px 32px rgba(0,0,0,0.4);
}
```

Also remove the `width` transitions from the `.kpi-desktop-row .kpi-card-shell` transition property (line 348) since widths are now equal:
```css
/* Before: */
transition: transform 350ms ..., opacity 350ms ease, width 350ms ...;

/* After: */
transition: box-shadow 250ms ease;
```

Also add `flex: 1` to `.kpi-desktop-row` if not already set (ensure no `align-items: center` or `justify-content: center` fights the equal-width layout — `justify-content: stretch` or remove it):
```css
/* Current line 334–337: */
.kpi-desktop-row {
  display: none;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

/* Change align-items to stretch so cards fill equal height: */
.kpi-desktop-row {
  display: none;
  align-items: stretch;
  gap: 12px;
}
```

### OverviewTab.tsx (18B fix — font size)
Line 444: `fontSize: i === activeKpiIndex ? 26 : 22` — equalise to a single size for all desktop cards. Use 24 (midpoint) or pick 22 or 26 consistently:

```tsx
/* Before (line 444): */
<p className="kpi-card-value" style={{ fontSize: i === activeKpiIndex ? 26 : 22, fontWeight: 700, lineHeight: 1.1 }}>

/* After: */
<p className="kpi-card-value" style={{ fontSize: 24, fontWeight: 700, lineHeight: 1.1 }}>
```

---

## Item 3 — 18A: Safari swipe fix (frontend, gesture wiring)

**Scope**: Frontend-only  
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx`

**Root cause**: Lines 249–270 implement touch handling via React synthetic event props (`onTouchStart`, `onTouchMove`, `onTouchEnd`) attached at lines 343–345. React registers synthetic `onTouchMove` as `passive: true`, which means the handler cannot call `e.preventDefault()`. Safari iOS intercepts horizontal swipes for its own scroll system before the handler fires, so swipes either scroll the page or do nothing.

Additionally, the current `handleTouchMove` (line 255–257) tracks only `dx` with no `dy` comparison — no direction detection. Without it, `preventDefault()` on any move would also block vertical page scrolling.

**What to do**:

### Step 1 — Add refs for the new approach
After the existing refs on lines 203–205, add two new refs:
```tsx
const carouselRef       = useRef<HTMLDivElement>(null);
const touchStartY       = useRef<number>(0);
const isHorizontalSwipe = useRef<boolean | null>(null);
```

### Step 2 — Remove the old synthetic handler callbacks
Delete the three `useCallback` blocks: `handleTouchStart` (lines 249–253), `handleTouchMove` (lines 255–257), and `handleTouchEnd` (lines 259–270). These are replaced entirely by the imperative `useEffect`.

Also delete `touchDeltaX` ref (line 205) — it is used only by the old handlers.

### Step 3 — Add the imperative useEffect
After the existing `useEffect(() => { load(); }, [load])` (line 243), insert:

```tsx
useEffect(() => {
  const el = carouselRef.current;
  if (!el) return;

  const onTouchStart = (e: TouchEvent) => {
    touchStartX.current    = e.touches[0].clientX;
    touchStartY.current    = e.touches[0].clientY;
    touchStartTime.current = e.timeStamp;
    isHorizontalSwipe.current = null;
  };

  const onTouchMove = (e: TouchEvent) => {
    const dx = e.touches[0].clientX - touchStartX.current;
    const dy = e.touches[0].clientY - touchStartY.current;
    if (isHorizontalSwipe.current === null) {
      isHorizontalSwipe.current = Math.abs(dx) > Math.abs(dy);
    }
    if (isHorizontalSwipe.current) {
      e.preventDefault(); // blocks Safari page scroll — only works with passive:false
    }
  };

  const onTouchEnd = (e: TouchEvent) => {
    if (!isHorizontalSwipe.current) return;
    const dx       = e.changedTouches[0].clientX - touchStartX.current;
    const dt       = e.timeStamp - touchStartTime.current;
    const velocity = Math.abs(dx) / dt;
    const triggered = Math.abs(dx) > 40 || velocity > 0.3;
    if (!triggered) return;
    if (dx < 0) {
      navigateTo(activeKpiIndex + 1);
    } else {
      navigateTo(activeKpiIndex - 1);
    }
  };

  el.addEventListener('touchstart', onTouchStart, { passive: true });
  el.addEventListener('touchmove',  onTouchMove,  { passive: false }); // passive:false is the fix
  el.addEventListener('touchend',   onTouchEnd,   { passive: true });

  return () => {
    el.removeEventListener('touchstart', onTouchStart);
    el.removeEventListener('touchmove',  onTouchMove);
    el.removeEventListener('touchend',   onTouchEnd);
  };
}, [activeKpiIndex, navigateTo]);
```

Note: the dependency on `activeKpiIndex` means the effect re-attaches on every index change, keeping the closure fresh. This is intentional and matches the pattern from the spec.

### Step 4 — Attach carouselRef and remove synthetic props
On the `.kpi-carousel-stage` div (lines 341–346), replace:

```tsx
/* Before: */
<div
  className="kpi-carousel-stage"
  onTouchStart={handleTouchStart}
  onTouchMove={handleTouchMove}
  onTouchEnd={handleTouchEnd}
>

/* After: */
<div
  ref={carouselRef}
  className="kpi-carousel-stage touch-pan-y"
>
```

`touch-pan-y` (Tailwind) maps to `touch-action: pan-y` — this signals to the browser that vertical scrolling is allowed, while horizontal movement is handled by JS. It is a CSS hint that helps browsers like Safari before the first `touchmove` fires.

---

## Execution order

1. **18D** — `backend/ai_parser.py`: prompt swap only, no logic change, backend-only. Verify by calling the `/insights/story/{month_key}` endpoint 3 times and checking word counts.
2. **18B + 18C** — `index.css` + `OverviewTab.tsx`: CSS equal-width fix + font size equalise. View on desktop and confirm all three cards are same size. Confirm height looks right (should already be 140px — add explicit `h-[140px]` inline only if it still looks tall after the width fix).
3. **18A** — `OverviewTab.tsx`: gesture wiring rewrite. Test on iPhone Safari (or BrowserStack). Verify vertical scroll still works while horizontal swipes advance/retreat cards.

---

## Files modified

| File | Items |
|------|-------|
| `backend/ai_parser.py` (lines 155–171) | 18D |
| `frontend/react/src/index.css` (lines ~334–365) | 18B, 18C |
| `frontend/react/src/components/tabs/OverviewTab.tsx` (lines 203–205, 243–270, 341–346, 444) | 18A, 18B |

## Files NOT modified
- Any other component
- `frontend/react/src/types/index.ts`
- Railway / deployment config
- `backend/main.py` (18D prompt lives entirely in `ai_parser.py`)
