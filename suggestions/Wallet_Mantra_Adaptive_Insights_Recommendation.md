# Wallet Mantra – Adaptive Insights Section (Replacing "What Changed?")

## Why reconsider "What Changed?"

The current **What Changed?** section only provides value when users have:
- Previous month data
- Consistent expense tracking

Many users will not satisfy these conditions:
- First-time users
- Users returning after long gaps
- Users with inconsistent tracking

Showing empty or misleading comparisons weakens the overall experience.

---

# Recommendation

Replace the fixed **What Changed?** section with:

## 💡 Insights

The content should adapt based on the user's available data.

---

# Scenario 1 – First Month

Show onboarding insights.

Example:
- You've logged 42 expenses so far.
- Groceries account for 28% of your spending.
- Continue tracking this month to unlock monthly comparisons.

Purpose:
- Encourage instead of showing missing data.

---

# Scenario 2 – Previous Month Available

Display genuine month-over-month comparisons.

Examples:
- Food ↑ 18%
- Shopping ↑ ₹2,300
- Travel ↓ 42%

Purpose:
- Highlight meaningful spending trends.

---

# Scenario 3 – Inconsistent Tracking

Avoid misleading comparisons.

Instead display tracking quality.

Example:
- Expenses tracked on 12 days this month.
- Last month: 4 days.
- Monthly comparisons become more accurate with consistent tracking.

Purpose:
- Educate users and encourage better habits.

---

# Scenario 4 – Missing Months

If recent months are unavailable:
- Compare only with the last complete month.
- Otherwise skip comparisons.

Never compare months separated by long gaps.

---

# Future Tara Integration

Eventually Tara should generate personalised insights.

Examples:
- Food spending increased by 24%.
- Grocery budget exceeded.
- All bills cleared.
- Savings target achieved.
- Logged expenses on 26 days.
- Weekend spending accounts for 62% of monthly expenses.

---

# Suggested Insight Engine

IF first month
→ Show onboarding insights

ELSE IF previous month exists
→ Show month comparison

ELSE IF tracking quality is low
→ Show tracking insights

ELSE IF budgets exist
→ Show budget insights

ELSE
→ Show interesting spending patterns

---

# Benefits

- Works for first-time users.
- Works for inconsistent trackers.
- Works for long-term users.
- Avoids misleading comparisons.
- Always provides useful insights.
- Naturally evolves into Tara AI.

---

# Final Recommendation

Rename:

**What Changed?**

to

**💡 Insights**

This makes the section dynamic, personalised, and valuable for every user regardless of historical data.
