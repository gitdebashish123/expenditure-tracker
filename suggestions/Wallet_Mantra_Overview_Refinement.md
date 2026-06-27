# Wallet Mantra – Overview Page Refinement Summary

## Design Principle

The Overview page should remain lightweight and focused on answering:

1. What happened?
2. What's important?
3. What happens next?

Avoid turning the page into a complex analytics dashboard.

Tara's coaching and emotional engagement should primarily live on the **Today's** page.

---

# Financial Pulse

## Current Challenge

The existing cards:

- Bills
- Food
- Spending
- Tracking

feel somewhat machine-generated and add visual noise.

## Recommendation

Convert Financial Pulse into a compact health summary section.

### Examples

#### Normal Month

🟢 Bills on track

🟢 Spending pace normal

🟢 Tracking consistent

#### Higher Spending Month

🟢 Bills on track

🟠 Spending pace above normal

🟠 Food spending higher than usual

#### Strong Savings Month

🟢 Savings protected

🟢 Bills nearly complete

🟢 Tracking consistent

## Goal

Allow users to understand:

> "How healthy is my month?"

within a few seconds.

---

# Upcoming Reality

## Keep This Section

This is one of Wallet Mantra's strongest differentiators because it looks forward instead of only reporting current status.

Current information:

- Upcoming bill
- Expected month-end balance

should remain.

## Improvement

Provide context for the prediction.

Instead of:

Expected month-end balance ₹9,005

Use:

Expected month-end balance ₹9,005 if current spending pace continues.

or

Expected month-end balance ₹9,005 after upcoming commitments.

## Future Enhancements

Examples:

📅 Term Insurance due in 3 days

💰 Expected balance ₹9,005

⚠️ Lower than your typical month-end balance

or

✨ Higher than your average month-end balance

Limit the section to 2–3 insights.

---

# What's Changed?

## Current Challenge

Showing percentage changes for new users can be misleading.

Example:

↑ Groceries +272%

is not meaningful when previous month data does not exist.

---

## Recommended Logic

### Scenario 1 – Historical Data Available

Show comparisons and trends.

Examples:

↑ Groceries +272%

↓ Entertainment -38%

↑ Miscellaneous +16%

---

### Scenario 2 – First Month User

Replace comparisons with spending highlights.

Examples:

🏆 Top Category
Miscellaneous ₹27,792

🛒 Most Frequent Category
Groceries

🎯 New Expense Category
Course ₹5,891

💰 Largest Single Expense
Term Insurance ₹2,062

---

### Scenario 3 – Limited History (1–2 Months)

Show absolute insights instead of percentages.

Examples:

📚 New Category
Course ₹5,891

📦 Highest Spending Category
Miscellaneous ₹27,792

Avoid percentage-based trends until sufficient historical data exists.

---

# Recommended Overview Flow

1. Financial Snapshot
   - Remaining
   - Income
   - Fixed Paid
   - Pending Bills

2. June In One Sentence
   - AI-generated monthly summary

3. Monthly Breakdown
   - Includes one-line contextual insight

4. Spend By Category
   - Includes Category Winner

5. Financial Pulse
   - Compact monthly health indicators

6. Upcoming Reality
   - Upcoming commitments and projected balance

7. What's Changed?
   - Trends when history exists
   - Highlights for new users

---

## Final Vision

Overview should feel like:

"What happened, what's important, and what happens next?"

Today's page should remain the home of Tara's guidance, coaching, motivation, and daily financial conversations.
