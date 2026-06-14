# Wallet Mantra — Project Context for Claude

## What This Project Is
A personal expenditure tracker with natural-language expense input, powered by the Anthropic Claude API.
The user types prompts like `zomato 500, ola 200` and the app auto-categorises, saves, and tracks budgets.

## Tech Stack
- **Runtime**: Python 3.13 (uv-managed CPython 3.13.8)
- **Package manager**: `uv` — always use `uv run`, `uv add`, `uv sync`. Never use `pip` directly.
- **Backend**: FastAPI + Uvicorn, SQLite via SQLModel
- **AI**: Anthropic Claude API (`claude-sonnet-4-20250514`) for expense parsing and budget insights
- **Frontend**: Streamlit (dark theme, mobile-optimised)
- **Config**: `config.yaml` — salary, fixed expenses, budget limits, vendor→category mappings

## Project Structure
```
expenditure-tracker/
├── backend/
│   ├── main.py          # FastAPI REST API
│   ├── models.py        # SQLite schema (SQLModel)
│   ├── ai_parser.py     # Claude API: parses natural language → structured expenses
│   └── budget_rules.py  # Budget limit checks, balance calculation, fixed expense seeding
├── frontend/
│   └── app.py           # Streamlit UI
├── data/
│   └── expenses.db      # SQLite DB (auto-created on first run)
├── config.yaml          # Source of truth for salary, budgets, fixed expenses
├── pyproject.toml       # uv project definition
└── start.sh             # Starts both backend + frontend
```

## Key Domain Facts
- **Net monthly salary**: ₹1,46,709 (Infosys)
- **Fixed expenses total**: ~₹1,04,555/month (rent, EMIs, RDs, MFs, insurance, cook, milk, etc.)
- **Variable budget available**: ~₹42,154/month
- **Budget limits** (variable categories): Food ₹2,000 · Travel ₹4,000 · Groceries ₹5,000 · Shopping ₹3,000 · Medical ₹5,000 · Entertainment ₹2,000
- **Warning thresholds**: 80% → warning, 100% → danger alert

## Running Locally
```bash
# Start everything
./start.sh

# Or separately
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
uv run streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501
```

## Environment
- `ANTHROPIC_API_KEY` must be set in shell environment
- Mobile access: `http://<mac-local-ip>:8501` (same WiFi)
- API docs: `http://localhost:8000/docs`

## Coding Conventions
- All new packages added via `uv add <package>` — never pip
- DB changes go in `backend/models.py`, business logic in `backend/budget_rules.py`
- AI prompt changes go in `backend/ai_parser.py`
- `config.yaml` is the only place to change salary, limits, or fixed expense amounts — not hardcoded in Python
- Month keys are always `"YYYY-MM"` strings (e.g. `"2026-05"`)

## Planned v2 Features
- Telegram bot for even faster logging
- Google Sheets write-back sync
- UPI/SMS auto-parsing
- OCR receipt scanning
- Monthly summary report (email/WhatsApp)
