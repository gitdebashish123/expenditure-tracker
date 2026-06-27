# Implementation Plan: Overview Tab — Follow-up Fixes (Post Spec 15)
**Spec**: `.claude/specs/16_overview-followup-fixes.md`
**Date**: 2026-06-28
**Branch**: `feature/sprint06261-ui-enhancement`

---

## Overview

4 items in the spec — but **2 are already resolved** by the spec 15 implementation that landed on the same branch. Only 2 items require code changes: 1 backend, 1 frontend.

---

## Pre-flight: Items already done (no code needed)

### Issue C — Financial Pulse tile min-height (ALREADY FIXED)
`OverviewTab.tsx` line 935 currently reads:
```tsx
style={{ borderColor: "var(--border-lg)", minHeight: 120 }}
```
`minHeight: 120` was applied in the spec 15 execution. **No change needed.**

### Issue D — Tracking Summary disclaimer (ALREADY CORRECTLY IMPLEMENTED)
`InsightsSection.tsx` lines 191–224 currently contain:
```tsx
const daysRemaining = daysInMonth - today.getDate();
const showDisclaimer = prevDays < 7 && daysRemaining > 3;
...
{showDisclaimer && (
  <p className="text-xs pt-1" style={{ color: "var(--text-muted)" }}>
    Monthly comparisons become more accurate with consistent daily tracking.
  </p>
)}
```
The conditional logic exactly matches the spec. The disclaimer is correctly hidden right now because June has ≤ 3 days remaining. **No code change needed.** A clarifying comment is added in Item 2 below.

---

## Item 1 — Replace 📅 with 🔔 in "Coming Up" heading
**Scope**: Frontend-only
**File**: `frontend/react/src/components/tabs/OverviewTab.tsx` — line 678
**Depends on**: nothing

**Root cause**: Line 678 currently reads `📅 Coming Up`. The 📅 emoji (U+1F4C5) renders as "July 17" on all Apple platforms (iPhone, iPad, Mac Safari), not as a generic calendar. This is the same bug fixed in spec 13 for the story card. It was inadvertently re-introduced when the section was renamed from "Upcoming reality" to "Coming Up" in spec 15's implementation.

**Note on line 696**: A second `📅` appears at line 696 (`<span className="text-xl">📅</span>`) as the icon inside the "next due bill" row. This was present before spec 15 and is outside this spec's scope — flag for a future cleanup pass but do not change here.

**What to do**:

Before (line 678):
```tsx
          📅 Coming Up
```

After:
```tsx
          🔔 Coming Up
```

Single character change. The section comment on line 672 (`{/* ── Section 7: Upcoming Reality ──────────────────── */}`) should also be updated to reflect the current name:

Before:
```tsx
      {/* ── Section 7: Upcoming Reality ──────────────────── */}
```

After:
```tsx
      {/* ── Section 7: Coming Up (due bills + month-end balance) ─── */}
```

---

## Item 2 — Add clarifying comment to Tracking Summary disclaimer
**Scope**: Frontend-only
**File**: `frontend/react/src/components/shared/InsightsSection.tsx` — lines 191–193
**Depends on**: nothing

**Root cause**: The conditional logic is correct and working (see pre-flight above). The spec explicitly asks for a comment documenting the condition so future readers don't mistake the hidden disclaimer for a regression.

Current code (lines 191–193):
```tsx
  const daysRemaining = daysInMonth - today.getDate();
  const showDisclaimer = prevDays < 7 && daysRemaining > 3;
```

**What to do**: Add an inline comment on `showDisclaimer`:

Before:
```tsx
  const daysRemaining = daysInMonth - today.getDate();
  const showDisclaimer = prevDays < 7 && daysRemaining > 3;
```

After:
```tsx
  const daysRemaining = daysInMonth - today.getDate();
  // Show disclaimer only when last month tracking was sparse (<7 days) AND
  // there are days left in the current month to course-correct (>3 days).
  const showDisclaimer = prevDays < 7 && daysRemaining > 3;
```

---

## Item 3 — Tighten "June in One Sentence" AI prompt to ≤ 30 words
**Scope**: Backend-only
**File**: `backend/ai_parser.py` — lines 162–169 (inside `generate_monthly_story`)
**Depends on**: nothing

**Root cause**: `generate_monthly_story` (lines 140–176) currently uses this instruction block:
```python
Write ONE factual sentence (max 35 words) summarising this month's finances.
Rules:
- Factual and neutral — not motivational or encouraging.
- Past-tense for completed items, forward-looking for projections.
- Do NOT start the sentence with "I".
- Reference at least one concrete number.
- Use ₹ symbol when referencing specific amounts.
- Return ONLY the sentence, no preamble, no quotation marks.
```

The current limit is 35 words, has no prohibition on semicolons or list-style constructions, and treats variable spending total as a first-class data point alongside bills and savings. The observed output was 47 words with two semicolons and list-style structure — the model is not respecting the 35-word limit reliably, and the data provided (variable_total prominently) biases it toward covering all numbers.

**What to do**: Replace the instruction block (lines 162–169) with a tighter version:

Before:
```python
Write ONE factual sentence (max 35 words) summarising this month's finances.
Rules:
- Factual and neutral — not motivational or encouraging.
- Past-tense for completed items, forward-looking for projections.
- Do NOT start the sentence with "I".
- Reference at least one concrete number.
- Use ₹ symbol when referencing specific amounts.
- Return ONLY the sentence, no preamble, no quotation marks."""
```

After:
```python
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

Also reduce `max_tokens` from 120 to 80 (line 173) — a 30-word sentence needs at most ~50 tokens; raising the ceiling gives the model room to produce longer output:

Before:
```python
        max_tokens=120,
```

After:
```python
        max_tokens=80,
```

**Note on cache**: The in-memory `_story_cache` in `main.py` (line 1256) means the tightened prompt won't take effect for the current month until the cache is cleared. The cache is keyed on `(user_id, month_key)` and is invalidated when expenses are added (line 1263: `_story_cache.pop(...)`). For immediate testing, add a new expense or restart the server.

---

## Implementation Order Summary

| # | Item | Issue | File | Effort |
|---|------|-------|------|--------|
| — | Financial Pulse min-height | C | — | Already done |
| — | Disclaimer conditional | D | — | Already done |
| 1 | 🔔 emoji + section comment | B | OverviewTab.tsx | XS |
| 2 | Disclaimer clarifying comment | D | InsightsSection.tsx | XS |
| 3 | Tighten story prompt + max_tokens | A | ai_parser.py | XS |

**Start with Item 1** (single emoji, no logic). Item 2 next (comment only). Item 3 last (backend prompt — test after server restart or cache clear).
