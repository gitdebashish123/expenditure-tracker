# Implementation Plan: Accessibility Pass + Parser-Failure Manual Fallback
**Spec**: `.claude/specs/28_accessibility-and-parser-fallback.md`
**Date**: 2026-06-30
**Status**: ✅ Implemented 2026-06-30
**Branch**: `feature/sprint0726p1-ui-enhancement`

---

## Overview

5 items total — 0 require backend changes (backend already supports manual entry). All
frontend-only. Items are ordered smallest-blast-radius first: single-file CSS token change
→ additive ARIA props → additive CSS @media rule + one JS change → single-file form
addition → multi-file layout changes.

---

## Item 1 — Contrast tokens
**Scope**: Frontend-only
**File**: `frontend/react/src/index.css`

**Root cause (verified)**:
- Dark mode `--text-muted: rgba(255, 255, 255, 0.30)` at line 21. Against `--bg: #0a0a0f`
  (line 13), the rendered solid colour is approximately `#535353` → contrast ratio ~3.3:1.
  WCAG AA requires 4.5:1 for normal text, 3:1 for large UI text.
- Dark mode `--text-sub: rgba(255, 255, 255, 0.55)` at line 20 → rendered ~`#8f8f8f` →
  contrast ~5.1:1 — passes, but verify with Lighthouse since many components use it for
  body-size text.
- Light mode `--text-muted: rgba(26, 26, 46, 0.35)` at line 52. Against `--bg: #f4f4f8`
  (line 44), rendered solid colour is approximately `#a8a8ac` → contrast ratio ~2:1 —
  fails badly.
- Light mode `--text-sub: rgba(26, 26, 46, 0.55)` at line 51 → ~`#7a7a8a` → ~3.6:1 —
  below 4.5:1 for normal text.

**What to do**:

Raise both tokens in dark and light mode until they clear 4.5:1 against their respective
`--bg`. Suggested starting values (verify with Lighthouse/axe after applying):

```css
/* Dark mode (:root) */
--text-sub:   rgba(255, 255, 255, 0.65);   /* was 0.55 — already near-passing for large text */
--text-muted: rgba(255, 255, 255, 0.45);   /* was 0.30 — raises rendered colour to ~#757575 */

/* Light mode (html.light) */
--text-sub:   rgba(26, 26, 46, 0.65);      /* was 0.55 */
--text-muted: rgba(26, 26, 46, 0.55);      /* was 0.35 */
```

The Tailwind override map at `index.css:100–109` remaps `text-white/20–25` to `--text-muted`
and `text-white/30–70` to `--text-sub` — no changes needed to that block, the token values
propagate automatically.

**Acceptance**: Lighthouse Accessibility score shows no contrast violations on muted/sub text
in either theme.

---

## Item 3 — ARIA labels + keyboard focus
**Scope**: Frontend-only
**Files**:
- `frontend/react/src/index.css` (1 CSS rule addition)
- `frontend/react/src/components/tabs/FixedTab.tsx` (line 196)
- `frontend/react/src/components/tabs/PoolCard.tsx` (line 73)
- `frontend/react/src/components/shared/SpendDonut.tsx` (outer wrapper)

*Note: most icon-only buttons already have `aria-label` — Header theme toggle (line 46),
NotificationBell (line 55), ProfileDropdown (line 40), HistoryTab edit/delete (lines 101,
110), FixedExpenseRow tick/pencil (lines 65, 116), PoolCard entry tick/delete (lines 118,
149), KPI dots (line 64), IncomeSection edit/delete (lines 337, 362). The items below are
the gaps.*

**Root cause (verified)**:

1. **FixedTab category collapse button** (`FixedTab.tsx:196–200`): full-width `<button>`
   with no `aria-label` or `aria-expanded`. It announces nothing useful to screen readers.

2. **PoolCard expand/collapse header button** (`PoolCard.tsx:73–96`): `<button>` with no
   `aria-label` or `aria-expanded`. Pool name is inside a `<span>` child (not a label).

3. **SpendDonut chart** (`SpendDonut.tsx`): Recharts renders an SVG with no accessible
   label. The legend list IS present visually as sibling elements, but there is no
   programmatic association — a screen reader hits the chart SVG with no context, then
   separately reads the legend.

4. **Focus-visible**: No global `:focus-visible` rule exists in `index.css`. Many buttons
   use `focus:outline-none` inline, which silently removes the browser's default focus
   ring. Tailwind's `@tailwindcss/forms` plugin covers inputs, but buttons/tabs have no
   visible ring when keyboard-navigated.

**What to do**:

### index.css — global focus-visible ring (append after existing base rules, ~line 80)

```css
/* Keyboard focus ring — visible for keyboard nav, suppressed for mouse/touch */
:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
```

This pairs with Tailwind's `focus:outline-none` on mouse-clicked buttons — `focus-visible`
only fires when focus arrived via keyboard, so the ring appears for keyboard users but not
after a tap/click.

### FixedTab.tsx — category collapse button (line 196)

Add `aria-label` and `aria-expanded` to the existing `<button>`:

```tsx
<button
  onClick={() => toggleCategory(cat)}
  aria-label={`${cat} — ${isCollapsed ? "expand" : "collapse"} category`}
  aria-expanded={!isCollapsed}
  className="w-full flex items-center justify-between mb-2 hover:opacity-80 transition-opacity"
>
```

### PoolCard.tsx — expand/collapse header button (line 73)

```tsx
<button
  onClick={() => setExpanded(e => !e)}
  aria-label={`${pool.name} — ${expanded ? "collapse" : "expand"}`}
  aria-expanded={expanded}
  className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 transition-colors"
>
```

### SpendDonut.tsx — chart accessibility

Wrap the `<ResponsiveContainer>` in a `<div>` with `role="img"` and `aria-label` describing
what the chart shows, then add `aria-hidden="true"` to the container so the raw SVG paths
are skipped. The existing legend/category list already contains all the data as readable
text — this ensures screen readers read the legend, not the SVG.

Non-sidebar variant (line 89):
```tsx
<div role="img" aria-label="Category spending breakdown chart">
  <ResponsiveContainer width="100%" height={180}>
    {/* existing PieChart … */}
  </ResponsiveContainer>
</div>
```

Sidebar variant (line 40):
```tsx
<div role="img" aria-label="Category spending breakdown chart" className="w-28 flex-shrink-0">
  <ResponsiveContainer width="100%" height={120}>
    {/* existing PieChart … */}
  </ResponsiveContainer>
</div>
```

The legend list below the chart (`<div className="grid grid-cols-2 …">` in the default
variant and the sibling `<div className="flex-1 …">` in sidebar) already has all text
values — no changes needed there.

**Acceptance**: All interactive controls reachable by Tab key show a visible accent-coloured
ring. Icon-only buttons announce a descriptive label. Chart data is readable by a screen
reader via the legend.

---

## Item 4 — Reduced motion
**Scope**: Frontend-only
**Files**:
- `frontend/react/src/index.css` (add `@media (prefers-reduced-motion: reduce)` block)
- `frontend/react/src/components/shared/KpiCarousel.tsx` (line 34 — JS smooth scroll)

**Root cause (verified)**:

- `index.css:256` — `.kpi-scroller` has `scroll-behavior: smooth` — always on.
- `index.css:307` — `.kpi-dot` has `transition: width 250ms ease, background 250ms ease`.
- `index.css:334–336` — `.kpi-card-shell` has `transition: transform 250ms ...` for
  hover/active states on the desktop row.
- `KpiCarousel.tsx:34` — `el.scrollTo({ left: slide.offsetLeft, behavior: 'smooth' })` —
  JS smooth scroll fired when a dot is clicked.
- `tailwind.config.ts` defines `fadeIn` (0.3s) and `slideUp` (0.25s) animations used via
  `animate-fade-in` (QuickAddTab post-parse expense cards, line 322) and `animate-slide-up`
  (Toast). No reduced-motion suppression exists for either.
- No `prefers-reduced-motion` media query anywhere in the codebase.

**What to do**:

### index.css — add reduced-motion overrides (append near the end of the file)

```css
@media (prefers-reduced-motion: reduce) {
  /* Suppress CSS transitions and animations */
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }

  /* KPI carousel: remove smooth-scroll at the CSS level */
  .kpi-scroller {
    scroll-behavior: auto;
  }

  /* KPI dot pill expansion — instant, no width transition */
  .kpi-dot {
    transition: none;
  }
}
```

The global `animation-duration: 0.01ms` covers `animate-fade-in` and `animate-slide-up`
from Tailwind without needing to touch `tailwind.config.ts`.

### KpiCarousel.tsx — JS smooth scroll (line 30–35)

Replace the hardcoded `behavior: 'smooth'` with a runtime check:

```tsx
const scrollToCard = useCallback((index: number) => {
  const el = carouselRef.current;
  if (!el) return;
  const slide = el.children[index] as HTMLElement | undefined;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (slide) el.scrollTo({ left: slide.offsetLeft, behavior: reducedMotion ? 'auto' : 'smooth' });
}, []);
```

**Acceptance**: With `prefers-reduced-motion: reduce` set (DevTools → Rendering → Emulate),
the KPI carousel snaps instantly on dot tap, the expense cards after parse appear without
the fade-in animation, and no CSS transitions play.

---

## Item 5 — Parser-failure manual fallback
**Scope**: Frontend-only (backend already supports this)
**File**: `frontend/react/src/components/tabs/QuickAddTab.tsx`

**Root cause (verified)**:

`handleParse` catch block at `QuickAddTab.tsx:210–212`:
```tsx
} catch {
  toast("Failed to parse expenses. Try again.", { type: "error" });
}
```
No fallback path exists. `POST /expenses/manual` at `backend/main.py:590` is confirmed
present and accepts `{vendor, amount, category, note?, expense_date?}`. Its response
shape is `{expense: Expense, warnings: Warning[]}` — **different from parse** which
returns `{saved: Expense[], warnings: Warning[], balance: {remaining: number}}`.

All valid categories are available as keys of `CATEGORY_ICONS` (already imported in
`QuickAddTab.tsx:4`).

**What to do**:

Add three pieces to `QuickAddTab.tsx`:

### 1 — New state flag (in the NL parse form state block, ~line 143)

```tsx
const [parseError, setParseError] = useState(false);
```

### 2 — Set and clear the flag in handleParse (~line 189)

```tsx
const handleParse = async (e: React.FormEvent) => {
  e.preventDefault();
  if (!text.trim()) return;
  setParsing(true);
  setLastResult(null);
  setParseError(false);          // ← clear on each new attempt
  try {
    const { data } = await api.post<ParseResult>("/expenses/parse", {
      text: text.trim(),
      date_override: date,
    });
    setLastResult(data);
    setText("");
    refreshToday();
    if (data.saved.length > 0) {
      onExpenseAdded?.();
      setMantraRefresh(k => k + 1);
      toast(`${data.saved.length} expense${data.saved.length > 1 ? "s" : ""} saved`, { icon: "⚡" });
    }
  } catch {
    setParseError(true);         // ← show fallback instead of just a toast
  } finally {
    setParsing(false);
  }
};
```

### 3 — Inline fallback form (replace or augment the current `lastResult &&` block, ~line 298)

Add a new sub-component (inside the same file, above `QuickAddTab`) or inline — inline
is simpler given this is a single-use form:

```tsx
{parseError && (
  <ManualEntryFallback
    date={date}
    onSaved={(exp) => {
      setParseError(false);
      refreshToday();
      onExpenseAdded?.();
      setMantraRefresh(k => k + 1);
      toast("Expense saved manually", { icon: "✅" });
      // Manual endpoint returns a single expense + warnings — show a
      // simple confirmation, not the multi-card parse result view.
    }}
    onDismiss={() => setParseError(false)}
  />
)}
```

Define `ManualEntryFallback` as a new function component in the same file above
`QuickAddTab` (keep it in the same file — no need for a new file):

```tsx
interface ManualEntryFallbackProps {
  date:      string;
  onSaved:   (exp: Expense) => void;
  onDismiss: () => void;
}

function ManualEntryFallback({ date, onSaved, onDismiss }: ManualEntryFallbackProps) {
  const [vendor,   setVendor]   = useState("");
  const [amount,   setAmount]   = useState("");
  const [category, setCategory] = useState("Food");
  const [note,     setNote]     = useState("");
  const [saving,   setSaving]   = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const amt = parseFloat(amount);
    if (!vendor.trim() || !amt || amt <= 0) return;
    setSaving(true);
    try {
      const { data } = await api.post<{ expense: Expense }>("/expenses/manual", {
        vendor: vendor.trim(),
        amount: amt,
        category,
        note:   note.trim() || undefined,
        expense_date: date,
      });
      onSaved(data.expense);
    } catch {
      // leave form open so user can retry
    } finally {
      setSaving(false);
    }
  };

  const inputCls =
    "w-full bg-dark-card2 border border-white/10 rounded-xl px-3 py-2 " +
    "text-white text-sm focus:border-accent focus:outline-none transition-colors";

  return (
    <div className="mt-4 p-4 rounded-2xl border-l-4"
         style={{ background: 'var(--card)', borderColor: 'var(--warning)' }}>
      <p className="text-xs font-syne font-bold uppercase tracking-widest mb-1"
         style={{ color: 'var(--warning)' }}>
        AI parser unavailable
      </p>
      <p className="text-xs mb-3" style={{ color: 'var(--text-sub)' }}>
        Enter the expense manually below.
      </p>
      <form onSubmit={handleSubmit} className="space-y-2">
        <input
          value={vendor}
          onChange={e => setVendor(e.target.value)}
          placeholder="Vendor / description"
          className={inputCls}
          aria-label="Vendor"
        />
        <div className="flex gap-2">
          <input
            type="number"
            min="0"
            step="any"
            value={amount}
            onChange={e => setAmount(e.target.value)}
            placeholder="Amount (₹)"
            className={`${inputCls} flex-1`}
            aria-label="Amount"
          />
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            className={`${inputCls} flex-1`}
            aria-label="Category"
          >
            {Object.keys(CATEGORY_ICONS).map(c => (
              <option key={c} value={c}>{CATEGORY_ICONS[c]} {c}</option>
            ))}
          </select>
        </div>
        <input
          value={note}
          onChange={e => setNote(e.target.value)}
          placeholder="Note (optional)"
          className={inputCls}
          aria-label="Note"
        />
        <div className="flex gap-2 pt-1">
          <button
            type="submit"
            disabled={saving || !vendor.trim() || !amount}
            className="flex-1 py-2.5 rounded-xl text-sm font-syne font-semibold
                       disabled:opacity-50 transition-opacity"
            style={{ background: 'var(--warning)', color: '#000' }}
          >
            {saving ? "Saving…" : "Save Manually"}
          </button>
          <button
            type="button"
            onClick={onDismiss}
            className="px-4 py-2.5 rounded-xl text-sm transition-colors"
            style={{ background: 'var(--card2)', color: 'var(--text-sub)' }}
          >
            Dismiss
          </button>
        </div>
      </form>
    </div>
  );
}
```

**Imports needed**: `Expense` is already imported in the types import at line 7. `CATEGORY_ICONS` is already imported at line 4. No new imports required.

**Acceptance**: Trigger a parse failure (e.g. disconnect network, then submit). The warning
banner with an inline vendor/amount/category form appears. Submitting the form logs the
expense and refreshes Today's entries without leaving the tab. "Dismiss" hides the form.

---

## Item 2 — Touch targets (44×44px minimum)
**Scope**: Frontend-only
**Files**:
- `frontend/react/src/index.css` (tap-target utility class)
- `frontend/react/src/components/tabs/HistoryTab.tsx` (lines 96–114)
- `frontend/react/src/components/tabs/FixedExpenseRow.tsx` (lines 111–119)
- `frontend/react/src/components/tabs/PoolCard.tsx` (lines 110–121, 144–152)
- `frontend/react/src/components/settings/IncomeSection.tsx` (lines 332–366)
- `frontend/react/src/index.css` (KPI dot button)

*Depends on Item 1 being done first only for consistency; can be done independently.*

**Root cause (verified)**:

| Location | Element | Current hit area | Problem |
|---|---|---|---|
| `HistoryTab.tsx:96–114` | Edit (Pencil) + Delete (Trash2) buttons | `w-7 h-7` = 28×28px | Below 44px |
| `FixedExpenseRow.tsx:111–119` | Pencil edit button | No sizing class at all | ~12×12px rendered |
| `PoolCard.tsx:110–121` | Paid tick circle | `w-5 h-5` = 20×20px | Below 44px |
| `PoolCard.tsx:144–152` | Delete button | No sizing class | ~13×13px rendered |
| `IncomeSection.tsx:332–340` | Edit button | `w-9 h-9` = 36×36px | Below 44px |
| `IncomeSection.tsx:357–365` | Delete button | `w-9 h-9` = 36×36px | Below 44px |
| `index.css:.kpi-dot` | Dot indicator buttons | `height: 6px`, `padding: 0` | ~6px hit area |

**What to do**:

### Approach: add a `.tap-target` utility in `index.css` (append near touch/mobile section)

```css
/* Minimum 44×44 tap target — icon stays visually small, hit area is padded out */
.tap-target {
  min-width:  44px;
  min-height: 44px;
  display:    inline-flex;
  align-items: center;
  justify-content: center;
}
```

Apply it instead of the existing `w-7 h-7` / `w-9 h-9` sizing classes on the problematic
buttons listed above. Leave `w-7 h-7` etc. removed (`.tap-target` replaces them). Keep all
other classes (`rounded-lg`, `hover:`, `transition-colors`, `flex-shrink-0`) unchanged.

### HistoryTab.tsx (lines 96–113)

Replace `className="w-7 h-7 flex items-center justify-center …"` on both Pencil and Trash2
buttons with `className="tap-target …"` (remove `w-7 h-7`, keep everything else).

### FixedExpenseRow.tsx (lines 111–119)

Replace the bare `<button onClick={startEdit} className="flex-shrink-0 …">` with:
```tsx
<button
  onClick={startEdit}
  className="tap-target flex-shrink-0 transition-colors hover:text-indigo-400"
  style={{ color: 'var(--text-muted)' }}
  aria-label="Edit amount for this month"
>
  <Pencil size={12} />
</button>
```

### PoolCard.tsx — paid tick (lines 110–121)

Replace `w-5 h-5` with `tap-target` (remove `w-5 h-5`, keep `rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all …`).

### PoolCard.tsx — delete button (lines 144–152)

Add `tap-target` to the delete button className.

### IncomeSection.tsx (lines 332–340, 357–365)

Replace `w-9 h-9` with `tap-target` on both the Edit and Delete buttons.

### index.css — KPI dot buttons

Add `padding: 10px` (makes the outer hit area 6+20+6 = visually 6px dot inside a 26px+ area):

```css
.kpi-dot {
  height: 6px;
  /* existing rules … */
  padding: 10px;           /* ← add: expands hit area without changing visual size */
  box-sizing: content-box; /* ← add: keep visual 6px, hit area = 26px+ */
}
```

**Acceptance**: On a mobile viewport (375px, Chrome DevTools), inspect the computed size of
each affected interactive element — all should show ≥44×44px in the box model overlay.

---

## Execution order

1. **Item 1** (index.css contrast tokens) — lowest risk, widest reach, no JS changes.
2. **Item 3** (ARIA + focus-visible) — additive only, no logic changes.
3. **Item 4** (reduced-motion) — additive CSS block + one JS guard, only changes
   behaviour for users with the preference set.
4. **Item 5** (parser fallback) — adds state and form to QuickAddTab, no changes to
   existing happy path.
5. **Item 2** (touch targets) — multi-file layout changes, do last so layout regressions
   are easy to attribute.
