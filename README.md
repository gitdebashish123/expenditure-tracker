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

## 🗄️ Database Migrations

When upgrading from a single-user to multi-user setup (Sprint 2),
run the schema migration script once:

```bash
# 1. Start the backend first so the user table and default admin are created
uv run uvicorn backend.main:app --port 8000
# Wait for "Application startup complete", then Ctrl+C

# 2. Run the migration
uv run python migrate_add_user_id.py
```

This adds `user_id` to all data tables and assigns any existing data to
the default admin account (`admin@spendsense.local`). Safe to re-run —
skips columns that already exist.

| Migration script | What it does |
|---|---|
| `migrate_add_user_id.py` | Adds `user_id` FK to all 6 data tables (Sprint 2.1) |

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

## 🔒 HTTPS Setup

### Local Development

**Prerequisites**
- nginx: `brew install nginx` (if not already installed)
- openssl: pre-installed on Mac — verify with `openssl version`

**One-time setup per machine**

```bash
# Step 1 — Generate self-signed certificate
bash nginx/generate_certs.sh
```

```bash
# Step 2 — (Optional but recommended) Trust the cert in Mac Keychain
# Removes the "Your connection is not private" browser warning permanently
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  nginx/certs/spendsense.crt
```

```bash
# Step 3 — Start the app (nginx starts automatically)
./start.sh
```

**Access URLs after HTTPS setup**

| Service | URL |
|---|---|
| Frontend | https://localhost:8443 |
| API Docs | https://localhost:8444/docs |

> **First visit browser warning** — on the first visit, your browser will show
> a security warning because the certificate is self-signed (not issued by a
> trusted authority). Click **Advanced → Proceed to localhost** to continue.
> If you ran the Keychain trust command above, this warning will not appear.

> **Certificate renewal** — the self-signed cert is valid for 365 days.
> Re-run `bash nginx/generate_certs.sh` after a year to regenerate it.

---

### 📱 iPhone / Mobile Access

iPhone does not trust self-signed certificates without a manual profile
installation, so HTTP is used directly for local mobile development.

1. Make sure your phone is on the **same WiFi network** as your Mac
2. Find your Mac's local IP:
   ```bash
   ipconfig getifaddr en0
   ```
3. Open in Safari: `http://192.168.x.x:8501`

No HTTPS setup is needed on the iPhone for local development.

---

### 🚂 Production HTTPS — Railway (Recommended)

HTTPS is **fully automatic** on Railway — zero configuration required.

- Railway provisions and renews the TLS certificate automatically
- No nginx, no certbot, no certificate files needed
- HTTPS is active from the very first deploy

**Steps:**
1. Push your code to GitHub
2. Connect the repo to Railway (railway.app → New Project → Deploy from GitHub)
3. Set environment variables in the Railway dashboard (`ANTHROPIC_API_KEY` etc.)
4. Railway deploys and assigns a `https://your-app.railway.app` URL automatically

**Verify HTTPS is working:**
```bash
curl https://your-app.railway.app/months
# expect: JSON array of months
```

---

### 🎨 Production HTTPS — Render (Alternative)

Same as Railway — HTTPS is automatic on every deploy.

- Custom domain supported on the free tier
- Certificate provisioned and renewed by the platform
- No additional configuration needed beyond setting environment variables

---

### 🛠️ Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| **Streamlit blank screen after HTTPS** | WebSocket headers missing in nginx config | Check `nginx/spendsense-frontend.conf` — all three WebSocket headers must be present: `Upgrade`, `Connection`, `proxy_http_version 1.1` |
| **Browser shows security warning** | Self-signed certificate not trusted | Click **Advanced → Proceed to localhost**, or run the `sudo security add-trusted-cert` Keychain command |
| **iPhone connection refused on HTTPS** | Expected — iOS rejects untrusted self-signed certs | Use HTTP directly: `http://192.168.x.x:8501` |
| **Port 8443 or 8444 already in use** | Another process is using the port | Run `lsof -i :8443` to identify the process, then `kill <PID>` |

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
