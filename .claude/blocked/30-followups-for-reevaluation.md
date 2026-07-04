# Follow-ups — Spec 30: User-Type AI Classification

**Origin**: `.claude/specs/30_user-type-ai-classification.md`
**Plan**: `.claude/plans/30-user-type-ai-classification.md`
**Status**: Plan fully implemented (5/5 items) — these are *not* blockers to that completion, they're two things worth a deliberate look later.
**Date noted**: 2026-07-02

---

## 1. Live tone QA never happened

**What's done**: All five plan items landed and pass `py_compile` / `import backend.main` cleanly. `classify_user_type()` was also run against the real local dataset (`data/expenses.db`) for a few user IDs and returned `"new"` / `"inconsistent"` without error — confirming the grouped SQL query is valid against live data.

**What's not done**: No live Anthropic API call was made to actually read the generated mantra/story/insight sentences for a `"new"`, `"inconsistent"`, and `"consistent"` user side by side. The plan's own Definition of Done calls for exactly this ("Manual test against a live backend for three distinct users/months... confirm copy matching the intended tone per type").

**Why it wasn't done here**: doing so means running the FastAPI server with a valid `ANTHROPIC_API_KEY`, hitting `/insights/mantra`, `/insights/story`, `/insights/monthly-insight` for accounts in each of the three states, and eyeballing the sentences — real API spend and manual judgment, not something to do silently as part of a code-edit pass.

**Also not exercised**: no user in the current local dataset came back as `"consistent"` (3+ active months in the last 4) during the sanity check, so that branch of `classify_user_type` was verified by code review against the spec's threshold, not against a real row set. Worth deliberately checking against a user with enough history once one exists, or seeding one.

**Action needed**: run the backend locally (`uv run uvicorn backend.main:app --reload`), pick/seed a user in each of the three states, and read the actual generated sentences for tone before calling this feature done from a product standpoint.

---

## 2. `classify_user_type` changes edge-case behavior vs. the old `is_first_month` logic

**What changed**: the old `monthly_insight` logic (`backend/main.py`, now removed) forced the non-comparative prompt branch whenever `prev_variable_total` was falsy — i.e. **any** single ₹0-variable prior month, regardless of the rest of the user's history. `classify_user_type` instead looks at up to 4 prior months and only returns `"consistent"` when 3+ of them have ≥5 entries.

**Concrete case that now behaves differently**: a user with an active month, then a quiet ₹0-variable month (e.g. traveling, or just didn't log), then two more active months — under the old logic this always read as `is_first_month=True` (non-comparative) purely because of that one quiet month's *most recent prior* status. Under `classify_user_type`, this user could read as `"consistent"` if 3 of the last 4 months clear the ≥5-entries bar, even though the immediately preceding month was quiet.

**Is this a bug?** No — it's the intended richer multi-month view the spec asked for (spec context section explicitly calls the old binary flag "too coarse"). Flagging it here only so it's a known, deliberate behavior shift if someone later asks "why did this user suddenly get comparison language when they didn't before" — the answer is: the classifier now looks further back than one month, by design.

**Action needed**: none required to close this out. Worth a quick sanity check once real usage data accumulates — if `"consistent"` users start seeing comparisons against a quiet single month more often than feels right, that's the place to look (`backend/budget_rules.py:classify_user_type`, the `active_months` threshold).

---

## Minor cleanup noticed, not part of either follow-up above

`has_prior_activity()` (`backend/budget_rules.py`) is now unused anywhere in the repo — its only caller (`monthly_insight` in `main.py`) was removed as part of Item 5. It was left in place because deleting it was outside this plan's stated file scope (the plan only called for removing the `main.py` import/call site). Safe to delete in a future pass if nothing else picks it up.
