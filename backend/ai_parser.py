import anthropic
import json
import yaml
from pathlib import Path

client = anthropic.Anthropic()

with open("config.yaml") as f:
    config = yaml.safe_load(f)

VENDOR_CATEGORIES = config.get("vendor_categories", {})

CATEGORY_MAP_TEXT = "\n".join(
    f"- {cat.title()}: {', '.join(vendors[:5])}"
    for cat, vendors in VENDOR_CATEGORIES.items()
)


def parse_expense_input(user_input: str) -> list[dict]:
    """
    Parse natural language like 'zomato 500, ola 200, bigbasket 1200'
    into structured expense list using Claude.
    """
    prompt = f"""Parse the following expense input into a JSON array of expense objects.

Input: "{user_input}"

Category mapping guide (use these, or infer smartly for unknown vendors):
{CATEGORY_MAP_TEXT}

Rules:
1. Each expense object must have: vendor (string), amount (number), category (string), note (optional string)
2. Category must be one of: Food, Travel, Groceries, Shopping, Medical, Entertainment, Gifts, Course, Miscellaneous
3. Amounts are in Indian Rupees (₹)
4. If vendor is unclear, use "Miscellaneous" category
5. Vendor name should be clean and title-cased (e.g., "Zomato", "Ola")
6. Extract note if user provides context like "zomato 500 lunch with team" → note: "lunch with team"

Return ONLY a valid JSON array, no explanation, no markdown. Example:
[{{"vendor": "Zomato", "amount": 500, "category": "Food", "note": null}}, {{"vendor": "Ola", "amount": 200, "category": "Travel", "note": null}}]"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    expenses = json.loads(raw)
    return expenses


def get_budget_insight(category: str, spent: float, limit: float, month: str) -> str:
    """Generate a smart warning/insight message for budget breaches."""
    pct = (spent / limit * 100) if limit > 0 else 0

    if pct < 70:
        return None

    prompt = f"""A user's {category} spending is at ₹{spent:.0f} out of ₹{limit:.0f} limit ({pct:.0f}%) for {month}.
Generate a SHORT, friendly 1-sentence warning or tip (max 15 words). Be helpful, not preachy. Use ₹ symbol."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
