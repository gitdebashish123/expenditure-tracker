# 💸 SpendSense — Personal Expenditure Tracker

A natural-language-powered expense tracker built with Python 3.12+, FastAPI, Claude AI, and Streamlit.
Log expenses by typing `zomato 500, ola 200` — Claude categorises them instantly.
Access from your Mac or any mobile browser on the same WiFi network.

---

## ✨ Features

- **Natural language input** — type `zomato 500, ola 200` and AI categorizes it instantly
- **Budget warnings** — alerts at 80% and 100% of category limits
- **Live balance** — salary minus fixed + variable spend = remaining balance
- **Monthly tracking** — auto-seeds fixed expenses each month
- **Mobile-friendly** — Streamlit UI works in any mobile browser
- **Category management** — edit budget limits from the Settings tab

---

## 🚀 Setup (Mac)

This project uses **[uv](https://docs.astral.sh/uv/)** — a fast Python package and project manager that handles your virtual environment and dependencies in one step. No need to manage `pip`, `venv`, or `python` versions manually.

### 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal (or run `source ~/.zshrc`) so `uv` is on your PATH.

Verify:
```bash
uv --version
# uv 0.5.x or later
```

### 2. Place the project

```bash
cd ~/Desktop   # or wherever you want it
cd expenditure-tracker
```

### 3. Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

To make it permanent across terminal sessions:
```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
source ~/.zshrc
```

### 4. Create the virtual environment and install dependencies

```bash
uv sync
```

This does everything in one command:
- Reads `pyproject.toml`
- Creates a `.venv/` inside the project folder
- Installs all dependencies into it (Python 3.12 is pinned automatically)

You never need to activate the venv manually — `uv run` handles it.

### 5. Run

```bash
chmod +x start.sh
./start.sh
```

Or start each service manually in two separate terminals:

```bash
# Terminal 1 — Backend API
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend UI
uv run streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501
```

---

## 📱 Access on Mobile

1. Make sure your phone is on the **same WiFi network** as your Mac
2. Find your Mac's local IP:
   ```bash
   ipconfig getifaddr en0
   ```
3. Open in your phone browser: `http://192.168.x.x:8501`

---

## 💬 Usage Examples

| You type | What gets logged |
|---|---|
| `zomato 500` | Food · Zomato · ₹500 |
| `ola 200, petrol 800` | Travel · Ola ₹200, Petrol ₹800 |
| `bigbasket 1200 weekly groceries` | Groceries · Bigbasket ₹1200 · note: weekly groceries |
| `amazon 3500 headphones` | Shopping · Amazon ₹3500 · note: headphones |
| `doctor 500, medicine 300` | Medical · Doctor ₹500, Medicine ₹300 |

---

## ⚙️ Customize

**Edit `config.yaml`** to change:
- Your salary (`salary.net_monthly`)
- Budget limits per category (`budget_limits`)
- Fixed expenses list (`fixed_expenses`)
- Vendor → category mappings (`vendor_categories`)

---

## 🗂️ Project Structure

```
expenditure-tracker/
├── backend/
│   ├── main.py          # FastAPI REST API
│   ├── models.py        # SQLite database schema
│   ├── ai_parser.py     # Claude AI expense parser
│   └── budget_rules.py  # Budget limits & balance logic
├── frontend/
│   └── app.py           # Streamlit mobile-friendly UI
├── data/
│   └── expenses.db      # SQLite database (auto-created)
├── config.yaml          # Your salary, limits, categories
├── pyproject.toml       # uv project definition & dependencies
├── start.sh             # One-command launcher (uses uv)
└── README.md
```

> `requirements.txt` is retained for reference but **not used** — `pyproject.toml` is the source of truth for uv.

---

## 🔧 uv Cheatsheet

| Task | Command |
|---|---|
| Install / sync all deps | `uv sync` |
| Add a new package | `uv add <package>` |
| Remove a package | `uv remove <package>` |
| Run any command in the venv | `uv run <command>` |
| Show installed packages | `uv pip list` |
| Upgrade all packages | `uv sync --upgrade` |

---

## 🔧 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/expenses/parse` | POST | Parse natural language and save |
| `/expenses/{month}` | GET | List expenses for a month |
| `/summary/current/now` | GET | Current month summary + warnings |
| `/budget` | PUT | Update a category limit |
| `/income` | POST | Add income entry |
| `/seed/{month}` | POST | Seed fixed expenses for a month |
| `/docs` | GET | Interactive API documentation |

---

## 🔮 Future Enhancements (v2)
- Telegram bot integration for even faster logging
- Google Sheets sync (write-back to your existing sheet)
- OCR receipt scanning
- Monthly email/WhatsApp summary report
- UPI/SMS auto-parsing
