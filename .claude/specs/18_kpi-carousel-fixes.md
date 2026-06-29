# Spec 18 — KPI Carousel Fixes + Sentence Prompt
**Date**: 2026-06-28
**Status**: 🔴 Ready to implement
**Branch**: `feature/sprint06261-ui-enhancement`
**Follows**: `17_kpi-carousel.md`
**Source**: Desktop + iPhone 15 Safari screenshots, June 28, 2026 (post spec 17 implementation)

---

## Context

Spec 17 was implemented. The carousel renders correctly visually on mobile —
card gradients, WM watermark, stacked deck behind, peek of next card, and dots
are all working as designed. Two functional bugs and two visual issues were
identified in the post-implementation screenshots.

**What is working (do not touch):**
- ✅ Card gradients (green / purple / amber)
- ✅ WM watermark on card surface
- ✅ Stacked deck effect behind active card on mobile
- ✅ Peek of next card at right edge on mobile
- ✅ Dot indicators rendering and positioning
- ✅ Card label, value, subtitle layout inside each card

**Issues addressed in this spec:**

| # | Issue | Type | Priority |
|---|-------|------|----------|
| 18A | Swipe gesture not working in iPhone Safari | Bug | P0 |
| 18B | Desktop: active card larger than side cards | Layout | P1 |
| 18C | Desktop: cards too tall / excess padding | Visual | P1 |
| 18D | "June in One Sentence" still too long (carry-over from spec 16) | Backend | P1 |

---

## Issue 18A — Swipe not working in iPhone Safari

**Symptom**: The carousel does not respond to horizontal swipe gestures on
iPhone 15 Safari. Cards are visible but static — swiping left/right either
scrolls the page or does nothing.

**Root cause**: Safari iOS intercepts `touchmove` events for page scrolling
before custom handlers can fire. Two compounding problems:

1. React's synthetic `onTouchMove` prop registers the listener as `passive: true`
   by default. A passive listener cannot call `e.preventDefault()`, so Safari's
   native scroll wins and the swipe is swallowed.

2. Without direction detection (horizontal vs vertical), `preventDefault()` would
   also block vertical page scrolling — which would break the entire page scroll.
   The fix must detect direction first, then lock only horizontal movement.

**Fix**: Replace the React synthetic `onTouchMove` prop with an imperative
`addEventListener` call using `{ passive: false }`, attached via `useEffect`.

```tsx
// In the KPI carousel component:

const carouselRef = useRef<HTMLDivElement>(null);
const touchStartX = useRef(0);
const touchStartY = useRef(0);
const isHorizontalSwipe = useRef<boolean | null>(null);

useEffect(() => {
  const el = carouselRef.current;
  if (!el) return;

  const onTouchStart = (e: TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
    touchStartY.current = e.touches[0].clientY;
    isHorizontalSwipe.current = null; // reset direction lock
  };

  const onTouchMove = (e: TouchEvent) => {
    const dx = e.touches[0].clientX - touchStartX.current;
    const dy = e.touches[0].clientY - touchStartY.current;

    // Determine swipe direction on first move only
    if (isHorizontalSwipe.current === null) {
      isHorizontalSwipe.current = Math.abs(dx) > Math.abs(dy);
    }

    if (isHorizontalSwipe.current) {
      e.preventDefault(); // stops Safari page scroll — only works with passive:false
      // Apply live drag translation to active card here if desired
    }
  };

  const onTouchEnd = (e: TouchEvent) => {
    if (!isHorizontalSwipe.current) return;

    const dx = e.changedTouches[0].clientX - touchStartX.current;
    const dt = e.timeStamp - touchStartTime.current; // for velocity
    const velocity = Math.abs(dx) / dt;

    const SWIPE_THRESHOLD = 40;   // px
    const VELOCITY_THRESHOLD = 0.3; // px/ms

    if (dx < -SWIPE_THRESHOLD || (dx < 0 && velocity > VELOCITY_THRESHOLD)) {
      // Swipe left — advance
      if (activeKpiIndex < 2) setActiveKpiIndex(i => i + 1);
    } else if (dx > SWIPE_THRESHOLD || (dx > 0 && velocity > VELOCITY_THRESHOLD)) {
      // Swipe right — retreat
      if (activeKpiIndex > 0) setActiveKpiIndex(i => i - 1);
    }
  };

  // CRITICAL: passive: false is what makes this work in Safari
  el.addEventListener('touchstart', onTouchStart, { passive: true });
  el.addEventListener('touchmove',  onTouchMove,  { passive: false });
  el.addEventListener('touchend',   onTouchEnd,   { passive: true });

  return () => {
    el.removeEventListener('touchstart', onTouchStart);
    el.removeEventListener('touchmove',  onTouchMove);
    el.removeEventListener('touchend',   onTouchEnd);
  };
}, [activeKpiIndex]); // re-attach when index changes so closure is fresh
```

Attach `carouselRef` to the carousel stage div:
```tsx
<div ref={carouselRef} className="kpi-carousel-stage">
```

Remove any existing `onTouchStart` / `onTouchMove` / `onTouchEnd` React props
from this div — they must not coexist with the imperative listeners.

**Also add to the carousel stage element in CSS / Tailwind:**
```css
touch-action: pan-y; /* allow vertical page scroll; horizontal handled by JS */
```
Or as Tailwind: `className="... touch-pan-y"`

**Elastic boundary resistance** (nice-to-have, implement only if time allows):
On card 1 swiping right, or card 3 swiping left, show a max 20px elastic drag
and snap back on `touchend`. If this adds complexity, skip it — a hard stop is
also acceptable.

**Affected files:**
- `frontend/react/src/components/tabs/OverviewTab.tsx`
  (or `frontend/react/src/components/ui/KpiCarousel.tsx` if extracted)

**Acceptance criteria:**
- [ ] Swiping left on card 1 advances to card 2 on iPhone 15 Safari
- [ ] Swiping left on card 2 advances to card 3
- [ ] Swiping right retreats one card
- [ ] No wrap: swiping left on card 3 does nothing
- [ ] Swiping left on carousel does NOT scroll the page vertically
- [ ] Swiping vertically on carousel DOES still scroll the page normally
- [ ] Fast flick (velocity > 0.3px/ms) triggers advance even under 40px drag
- [ ] Dot indicator updates on each successful swipe

---

## Issue 18B — Desktop: active card disproportionately larger than side cards

**Symptom**: On desktop, the Remaining (green) card is significantly wider and
taller than the Income (purple) and Bills Paid (amber) cards. The side cards
appear clipped/cut off on the right. This is because the spec 17 `d-active` /
`d-side` scale classes (designed for a centered-focal desktop layout) are being
applied, making the active card ~46% wider than the side cards.

**Correct desktop behaviour**: All three cards **equal width and equal height**
in a simple horizontal row. No scale differential on desktop. The
center-enlarged pattern is mobile-only (and even on mobile it's the stacking
effect, not scale, that conveys which card is active).

**Fix**: On desktop (≥ 768px), render all three cards at identical dimensions
in a `flex` row. Remove `d-active` / `d-side` width/scale classes entirely on
desktop. The active state on desktop is communicated by the dot indicator and
optionally a subtle border highlight — not by size.

```tsx
{/* Desktop: equal-width row */}
<div className="hidden md:flex gap-4 px-0">
  {kpiCards.map((card, i) => (
    <KpiCard
      key={card.id}
      card={card}
      isActive={i === activeKpiIndex}
      className="flex-1" // equal width via flex
      onClick={() => setActiveKpiIndex(i)}
    />
  ))}
</div>
```

Desktop active card indicator — subtle only, do not change size:
```css
/* Optional: faint ring on active card on desktop */
.kpi-card-desktop-active {
  box-shadow: 0 0 0 2px rgba(255,255,255,0.15), 0 8px 32px rgba(0,0,0,0.4);
}
```

**Affected files:**
- `frontend/react/src/components/tabs/OverviewTab.tsx`
  (or `KpiCarousel.tsx`)

**Acceptance criteria:**
- [ ] All three cards same width on desktop (each ~1/3 of container minus gaps)
- [ ] All three cards same height on desktop
- [ ] No card is clipped or cut off on desktop
- [ ] Cards fill the full width of the content area on desktop
- [ ] Clicking any card on desktop sets it as active (dot updates)

---

## Issue 18C — Desktop: cards too tall with excess vertical padding

**Symptom**: The green Remaining card on desktop appears ~180px tall with
substantial empty space between the label row and the value. The spec target
was 140px. This is likely a `height` or `min-height` that is too large, or
`padding` that is too generous for desktop.

**Fix**: Set explicit `height: 140px` on desktop card, `height: 150px` on
mobile card. Adjust internal padding so label + value + subtitle are
vertically distributed without excess whitespace.

Target internal layout for a 140px card:
```
[padding-top: 18px]
💰 REMAINING          WM    ← label row
                            ← ~16px gap
₹3,479                      ← value (font-size: 30–32px)
Left for the month          ← subtitle (font-size: 11px)
[padding-bottom: 18px]
```

```css
/* Mobile */
.kpi-card {
  height: 150px;
  padding: 18px 20px;
}

/* Desktop */
@media (min-width: 768px) {
  .kpi-card {
    height: 140px;
    padding: 18px 24px;
  }
}
```

Or via Tailwind on the card element:
```tsx
className={`... h-[150px] md:h-[140px]`}
```

**Affected files:**
- `frontend/react/src/components/tabs/OverviewTab.tsx` or `KpiCarousel.tsx`
- `frontend/react/src/index.css` if card height is set via CSS class

**Acceptance criteria:**
- [ ] Green card on desktop is ~140px tall (not 180px+)
- [ ] Label, value, and subtitle are evenly distributed within the card height
- [ ] No excess whitespace between label row and value on any card
- [ ] Mobile card height unchanged at ~150px

---

## Issue 18D — "June in One Sentence" still too long

**Symptom**: Across multiple user sessions and deployments, the AI-generated
summary sentence continues to exceed the 30-word limit. Current examples seen:

- "Bills reached 98% completion while ₹34000 was allocated to savings, leaving
  ₹3479 available with two days remaining after ₹52066 in variable spending
  this month." (38 words)
- "All fixed bills were paid while ₹36062 went to savings and ₹53212 to
  variable spending, leaving ₹4005 for the final two days of June." (34 words)

Both are 2–5 lines on mobile, overflowing the card.

**Root cause**: The word limit instruction in the AI prompt is either:
1. Present but not being enforced (LLM ignoring a soft instruction), or
2. Not yet deployed to production

**Fix**: Locate the "June in One Sentence" prompt in `backend/main.py` or
`backend/ai_parser.py` and replace the existing instruction with a
structurally-enforced version. Soft instructions ("keep it short") don't work
reliably — the prompt must make length compliance the primary output constraint.

**Exact prompt instruction to use:**

```python
"""
Generate a single sentence summary of this month's finances.

STRICT RULES — violating any rule makes the output wrong:
1. Exactly ONE sentence. No semicolons. No "and X and Y and Z" chaining.
2. Maximum 25 words. Count the words before responding. If over 25, rewrite.
3. Must mention exactly TWO of these three: bills status, savings amount, remaining balance.
4. Conversational tone. Write as if texting a friend, not writing a report.
5. Use ₹ symbol with formatted numbers (₹34,000 not ₹34000).

GOOD examples (count words — all under 25):
- "Bills are 98% done, ₹34,000 went to savings, and ₹3,479 remains." (13 words ✓)
- "Nearly all bills paid, ₹3,479 left after saving ₹34,000 this month." (13 words ✓)
- "₹34,000 saved, bills at 98%, with ₹3,479 still in hand." (11 words ✓)

BAD examples (too long or chained):
- "Bills reached 98% completion while ₹34000 was allocated to savings, leaving ₹3479 available with two days remaining after ₹52066 in variable spending this month." (too long ✗)
- "All fixed bills were paid while ₹36062 went to savings and ₹53212 to variable spending, leaving ₹4005 for the final two days." (too long, chained ✗)

Financial data:
- Bills paid: {bills_paid} of {total_bills} ({bills_pct}%)
- Savings allocated: {savings_amount}
- Remaining balance: {remaining_balance}
- Days remaining: {days_remaining}
"""
```

The key structural changes vs the previous prompt:
- "STRICT RULES" framing (LLMs respond better to hard rule framing than soft suggestions)
- "Count the words before responding" (forces self-verification)
- Concrete good/bad examples with word counts shown
- Word limit lowered from 30 to **25** to give a safety buffer (real output
  will be ~25–28 words even with some LLM drift)
- Semicolons explicitly banned (a common way LLMs chain two sentences)

**Affected files:**
- `backend/main.py` or `backend/ai_parser.py` — whichever contains the
  "June in One Sentence" prompt string. Search for "one sentence" or
  "sentence summary" to locate it.

**Acceptance criteria:**
- [ ] Generated sentence is ≤ 28 words in production (allowing 3-word LLM drift)
- [ ] Sentence renders in 1–2 lines on iPhone 15 at current font size
- [ ] No semicolons in output
- [ ] Contains ₹ symbol with formatted numbers (₹34,000 not ₹34000)
- [ ] Covers at least 2 of: bills status, savings, remaining balance
- [ ] Test with at least 3 fresh API calls to verify consistency

---

## Implementation Order

| # | Issue | Where | Effort |
|---|-------|--------|--------|
| 1 | 18A — Safari swipe fix | Frontend | M |
| 2 | 18B — Desktop equal card widths | Frontend | XS |
| 3 | 18C — Desktop card height | Frontend | XS |
| 4 | 18D — Sentence prompt tightening | Backend | S |

Do 18B and 18C together in one pass (both in the same card component).
Do 18A separately — it touches gesture handling, keep the diff clean.
Do 18D last — backend change, independent of frontend.

---

## Files Modified

- `frontend/react/src/components/tabs/OverviewTab.tsx`
  (or `frontend/react/src/components/ui/KpiCarousel.tsx` if extracted)
  — Issues 18A, 18B, 18C

- `frontend/react/src/index.css`
  — Issue 18C if card height is CSS-class-based

- `backend/main.py` or `backend/ai_parser.py`
  — Issue 18D (prompt string only, no logic changes)

## Files NOT Modified
- Any other component
- `frontend/react/src/types/index.ts`
- Railway / deployment config
