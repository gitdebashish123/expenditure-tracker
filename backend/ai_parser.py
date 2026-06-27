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
7. IMPORTANT: Blinkit, Swiggy Instamart, BigBasket, JioMart, Zepto, DMart → always Groceries. Swiggy (food delivery) → Food.

Return ONLY a valid JSON array, no explanation, no markdown. Example:
[{{"vendor": "Zomato", "amount": 500, "category": "Food", "note": null}}, {{"vendor": "Ola", "amount": 200, "category": "Travel", "note": null}}]"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
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
        model="claude-sonnet-4-5-20250929",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_daily_mantra(context: dict, preferred_angle: str = "forecast") -> str:
    """
    Generate a single warm, personal daily insight from precomputed
    balance/spending numbers. Distinct from get_budget_insight, which is
    scoped to single-category budget-breach warnings only.

    Expected context keys:
        remaining: float
        days_left: int
        daily_budget: float       # remaining / days_left, 0 if days_left == 0
        total_income: float
        top_category: str | None
        top_category_spent: float
        top_category_prev_month_spent: float | None  # None = no prior-month data; omit from prompt
        fixed_unpaid_total: float # sum of fixed expenses not yet marked paid
    """
    angle_hint = {
        "forecast":    "Today, lean toward a forecast/pacing angle (daily budget, days left).",
        "comparison":  "Today, lean toward comparing this month to last month for the top category.",
        "commitments": "Today, lean toward highlighting that fixed commitments are fully covered.",
    }.get(preferred_angle, "")

    # Only include the comparison line when real prior-month data exists.
    # Sending None or 0 would mislead the model into thinking ₹0 was spent last month.
    comparison_line = ""
    if context.get("top_category_prev_month_spent") is not None:
        comparison_line = (
            f"- Same category last month: ₹{context['top_category_prev_month_spent']:.0f}\n"
        )

    prompt = f"""A user's financial snapshot for the rest of this month:
- Remaining balance: ₹{context['remaining']:.0f}
- Days left in month: {context['days_left']}
- Daily budget if spread evenly: ₹{context['daily_budget']:.0f}/day
- Total income this month: ₹{context['total_income']:.0f}
- Top spending category so far: {context.get('top_category') or 'N/A'} (₹{context.get('top_category_spent', 0):.0f})
{comparison_line}- Remaining unpaid fixed commitments: ₹{context.get('fixed_unpaid_total', 0):.0f}

Generate ONE warm, encouraging, specific insight sentence (max 30 words).
Rules:
- No guilt, no judgment, no financial jargon.
- Reference at least one concrete number from above.
- Be specific and personal, not a generic motivational quote.
- Only make a comparison to last month if the "Same category last month"
  figure is provided above — never imply a trend you don't have a number for.
- If remaining unpaid fixed commitments is ₹0, this is worth highlighting
  as a positive — e.g. everything left to spend is discretionary. Only
  mention this when it's true and feels like the most relevant thing to
  say; don't force it into every sentence.
- Use ₹ symbol for amounts.
{angle_hint}
- Return ONLY the sentence, no preamble, no quotation marks."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_monthly_story(context: dict) -> str:
    """
    Generate a single factual sentence summarising the month.
    Distinct from generate_daily_mantra — no motivational language,
    no Tara branding, past-tense for completed items.

    Expected context keys:
        month_label: str             # e.g. "June 2026"
        remaining: float
        fixed_completion_pct: float  # fixed_paid / (fixed_paid + fixed_unpaid) * 100
        top_category: str | None
        top_category_spent: float
        variable_total: float
        days_left: int
    """
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

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=80,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_monthly_insight(context: dict) -> str:
    """
    Generate one concise behavioural observation sentence (max 20 words).

    Required context keys (all cases):
        is_first_month: bool
        top_category: str | None
        top_category_spent: float

    First-month additional keys:
        month_key: str
        savings_total: float
        savings_pct: int
        bills_status: str   # "all" or "unpaid bills remain"

    Returning-user additional keys:
        variable_total: float
        variable_pct_of_income: int
        prev_variable_total: float | None
        fixed_paid_total: float
        fixed_total: float
    """
    if context.get("is_first_month"):
        prompt = (
            "This is the user's first tracked month in Wallet Mantra. Generate exactly ONE short, "
            "encouraging, forward-looking observation (maximum 20 words). Do not reference any "
            "comparison to prior months, percentages, or changes. Focus only on what is notable "
            "or positive about this month's actual data.\n\n"
            f"Month: {context.get('month_key', 'this month')}\n"
            f"Top spending category: {context.get('top_category') or 'N/A'} "
            f"at ₹{context.get('top_category_spent', 0):.0f}\n"
            f"Savings this month: ₹{context.get('savings_total', 0):.0f} "
            f"({context.get('savings_pct', 0)}% of income)\n"
            f"Bills paid: {context.get('bills_status', 'unknown')}\n\n"
            "Respond with a single sentence only. No preamble."
        )
    else:
        prev_var = (
            f"₹{context['prev_variable_total']:.0f}"
            if context.get("prev_variable_total") is not None
            else "N/A"
        )
        prompt = (
            "You are a financial assistant. Generate exactly ONE concise observation sentence "
            "(maximum 20 words) about this user's financial behaviour this month. "
            "Do not restate totals already visible on the dashboard. "
            "Focus on a pattern, trend, or notable behaviour.\n\n"
            f"Variable spending: ₹{context['variable_total']:.0f} ({context['variable_pct_of_income']}% of income)\n"
            f"Top category: {context.get('top_category') or 'N/A'} at ₹{context.get('top_category_spent', 0):.0f}\n"
            f"Prior month variable: {prev_var}\n"
            f"Bills paid: ₹{context['fixed_paid_total']:.0f} of ₹{context['fixed_total']:.0f}\n\n"
            "Respond with a single sentence only. No preamble, no punctuation beyond the sentence itself. "
            "Do not mention percentage changes unless both the current month and prior month values "
            "are non-zero and meaningful."
        )
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=60,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
