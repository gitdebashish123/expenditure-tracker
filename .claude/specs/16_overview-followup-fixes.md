# Spec: Overview Tab — Follow-up Fixes (Post Spec 15 Review)
**Date**: 2026-06-28
**Status**: 🔴 Ready to implement
**Branch**: `feature/sprint06261-ui-enhancement`
**Follows**: `15_overview-ux-review-and-refinements.md`
**Source**: iPhone 15 Safari screenshot review at 2:30–2:31 AM, June 28, 2026

---

## Context

Spec 15 was partially implemented. A second round of iPhone 15 screenshots confirmed 6 of 8
items were fixed. This spec captures the 3 remaining issues plus 1 new issue discovered
during the second review.

**Already resolved (do not re-implement):**
- ✅ 1A — Category Winner Miscellaneous filter
- ✅ 1B — Spending Signals card clipping
- ✅ 2A — "Coming Up" rename
- ✅ 2C — Duplicate trophy icon (🌱 Tiny win)
- ✅ 2F — Header compressed to single row
- ✅ 3C — Money Moments story labels

**Open items addressed in this spec:**

| # | Issue | Source |
|---|-------|--------|
| A | "June in One Sentence" too long (4 lines, 47 words) | New observation |
| B | 📅 emoji in "Coming Up" heading renders as Jul 17 | New observation |
| C | Financial Pulse tile heights uneven | Spec 15 Issue 2D (not fixed) |
| D | Tracking Summary disclaimer — verify conditional logic | Spec 15 Issue 2E (status unclear) |

---

## Issue A — "June in One Sentence" is too long

**Symptom**: The AI-generated summary sentence in the story card now reads:
> "With 3 days remaining in June 2026, fixed bills reached 98% completion, variable spending
> totaled ₹52,066, and the remaining balance stands at ₹3,479 after prioritizing ₹34,000
> towards savings."

That is 47 words across 4 lines on iPhone 15. It reads like a bullet list in sentence form,
not a summary sentence. The previous version ("With 3 days remaining in June 2026, nearly
all fixed bills were paid and ₹34,000 was allocated to savings, leaving a balance of ₹3,479
after ₹52,066 in variable spending.") was 35 words and read naturally.

**Root cause**: The AI prompt generating this sentence has no word/line count constraint,
or the constraint was loosened when the prompt was last edited.

**Fix**: Tighten the system prompt for the "June in One Sentence" AI call with an explicit
hard constraint. The prompt instruction should include:

```
HARD LIMIT: Respond in exactly ONE sentence. Maximum 30 words. 
Do not use semicolons or list-style constructions. 
Conversational tone. Focus on: bills completion, savings allocated, remaining balance.
Omit variable spending total unless it fits within the word limit.
```

The target output shape is:
> "Nearly all bills are paid, ₹34,000 went to savings, and ₹3,479 remains with 3 days left."
> (18 words — ideal)

**Affected files**:
- `backend/main.py` or `backend/ai_parser.py` — whichever file contains the
  "June in One Sentence" prompt string

**Acceptance criteria**:
- Summary sentence is ≤ 30 words.
- Renders in 1–2 lines on iPhone 15 (390px) at the current font size.
- Covers at least two of: bills status, savings, remaining balance.
- No semicolons; single sentence; no "and X and Y and Z" chaining.

---

## Issue B — 📅 emoji in "Coming Up" heading renders as Jul 17

**Symptom**: The "Coming Up" section heading uses 📅 (U+1F4C5, Calendar emoji).
On Apple platforms (iPhone, iPad, Mac), this emoji is hardcoded to display as July 17 —
the date Apple uses for WWDC. It does not reflect the current date and misleads users
into thinking "Jul 17" is a relevant date.

This is the same issue that was fixed in spec 13 (Issue B) for the story card illustration.
The same emoji was inadvertently introduced again when the "Coming Up" section was renamed.

**Fix**: Replace 📅 with 🔔 in the "Coming Up" section heading.

```tsx
// From:
<h2>📅 Coming Up</h2>

// To:
<h2>🔔 Coming Up</h2>
```

🔔 (bell) communicates "upcoming / alert" without any date rendering issue.
Alternative acceptable: 🗓️ (U+1F5D3, spiral calendar) which has no hardcoded date.

**Preferred**: 🔔 — cleaner visual weight on dark background, clearly communicates
"something is due soon."

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — "Coming Up" section heading

**Acceptance criteria**:
- "Coming Up" heading shows 🔔 emoji on all platforms.
- No Jul 17 date rendering anywhere on the Overview tab.
- Section content (Term Insurance card + Expected month-end balance row) unchanged.

---

## Issue C — Financial Pulse tile heights uneven

**Symptom**: In the 2×2 Financial Pulse grid (Stability | Lifestyle / Savings | Consistency),
the bottom-right "Consistency" tile description wraps to two lines:
> "Tracked expenses on 28 days this month."

While the bottom-left "Savings" tile is one line:
> "Savings below target."

This makes the bottom row taller than the top row, breaking the visual balance of the grid.

**Fix**: Add a `min-height` to each tile card element so all four tiles share the same
minimum height. The description text should always wrap fully — never truncate — but the
tile container enforces a consistent floor height.

```tsx
// On each Financial Pulse tile card element, add:
style={{ minHeight: '120px' }}

// Or via Tailwind (if used):
className="... min-h-[120px]"
```

Adjust the pixel value to match the actual rendered height of the tallest tile.
The two-line "Consistency" tile at current font size is the reference — measure it and
use that as the `min-height` for all four tiles.

**Do not** truncate or cap description text. The tile must show the full description
regardless of length; the `min-height` only sets a floor, not a ceiling.

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Financial Pulse tile cards

**Acceptance criteria**:
- All four Financial Pulse tiles render at the same height.
- No description text is truncated.
- 2×2 grid looks visually balanced on iPhone 15.
- No regression on desktop (tiles may be taller on desktop — that is acceptable).

---

## Issue D — Tracking Summary disclaimer: verify conditional logic

**Symptom**: In the second-round screenshots (Image 3 and 4), the Tracking Summary card
shows only:
> "📊 Tracked this month — 26 days"
> "Last month — 2 days (orange)"

The disclaimer text ("Monthly comparisons become more accurate with consistent daily
tracking.") is not visible. This could mean either:

- ✅ The conditional logic from spec 15 Issue 2E was implemented correctly and the
  disclaimer is hidden because fewer than 3 days remain in June — which is the correct behaviour.
- ❌ The disclaimer text was hardcoded away (removed entirely) rather than made conditional.

**Fix**: Verify which of the above is true by checking the source code.

If the disclaimer is **conditionally hidden** (correct): no code change needed.
Document the condition in a comment for future reference:
```tsx
{/* Disclaimer shown only when: lastMonthTrackedDays < 7 AND daysRemainingInMonth > 3 */}
```

If the disclaimer was **hardcoded removed**: restore it with the conditional logic:
```tsx
{lastMonthTrackedDays < 7 && daysRemainingInMonth > 3 && (
  <p className="text-xs text-muted mt-2">
    Monthly comparisons become more accurate with consistent daily tracking.
  </p>
)}
```

**Affected files**:
- `frontend/react/src/components/tabs/OverviewTab.tsx` — Tracking Summary disclaimer

**Acceptance criteria**:
- Disclaimer is hidden when ≤ 3 days remain in the current month (as is the case now, June 28).
- Disclaimer is visible in early/mid month when last month's tracking was sparse (< 7 days).
- A code comment documents the condition clearly.

---

## Reminder: Open Item NOT in This Spec

**Issue 1A Part B — AI parser Miscellaneous categorization** remains open and is tracked
separately. Visible evidence in the new screenshots: "SBI · Mutual Fund" is still
categorized as "Miscellaneous" in Money Moments (Image 3). Mutual Fund is a well-defined
financial category. This should be the first item in the AI improvement sprint.

---

## Implementation Order

| # | Issue | Type | Effort | File |
|---|-------|------|--------|------|
| 1 | B — Replace 📅 with 🔔 in Coming Up heading | Frontend | XS | OverviewTab.tsx |
| 2 | C — Financial Pulse tile min-height | Frontend | XS | OverviewTab.tsx |
| 3 | D — Verify/restore Tracking Summary disclaimer logic | Frontend | XS | OverviewTab.tsx |
| 4 | A — Tighten "June in One Sentence" AI prompt | Backend | S | main.py / ai_parser.py |

Do B, C, D first (all in OverviewTab.tsx, single pass). Then A (backend prompt change).

---

## Files Modified

- `frontend/react/src/components/tabs/OverviewTab.tsx` — Issues B, C, D
- `backend/main.py` or `backend/ai_parser.py` — Issue A (prompt string)

## Files NOT Modified

- `frontend/react/src/types/index.ts`
- `frontend/react/src/index.css` (unless Tailwind min-height class unavailable)
- Any other component
