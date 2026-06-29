/**
 * Category icons and lists — ported from frontend/app.py
 * CATEGORY_ICONS, FIXED_CATEGORIES, VAR_CATEGORIES
 */
export const CATEGORY_ICONS: Record<string, string> = {
  Food:          "🍔",
  Travel:        "🚗",
  Groceries:     "🛒",
  Shopping:      "🛍️",
  Medical:       "💊",
  Entertainment: "🎬",
  Gifts:         "🎁",
  Course:        "📚",
  Miscellaneous: "📦",
  Housing:       "🏠",
  Savings:       "💰",
  EMI:           "💳",
  Investments:   "📈",
  Utilities:     "⚡",
  Insurance:     "🛡️",
  Household:     "🧺",
};

// Bills with a fixed monthly amount
export const FIXED_CATEGORIES = [
  "Housing",
  "EMI",
  "Savings",
  "Investments",
  "Insurance",
  "Utilities",
  "Household",
];

// Day-to-day variable spending categories
export const VAR_CATEGORIES = [
  "Food",
  "Travel",
  "Groceries",
  "Shopping",
  "Medical",
  "Entertainment",
  "Gifts",
  "Course",
  "Miscellaneous",
];
