# SpendSense — Tech Stack Analysis & Future Considerations

This document captures the tech stack comparison between SpendSense and a similar
Flask-based expense manager, along with recommendations for future sprint consideration.

---

## Current SpendSense Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend** | Streamlit | ≥1.40.0 | Web UI — tabs, forms, charts, dark/light theme |
| **Backend** | FastAPI | ≥0.115.0 | REST API — all business logic endpoints |
| **ASGI Server** | Uvicorn | ≥0.32.0 | Runs the FastAPI app, supports hot reload |
| **Database** | SQLite | Built-in | Local file-based database (`data/expenses.db`) |
| **ORM** | SQLModel | ≥0.0.21 | DB schema + query layer (Pydantic + SQLAlchemy) |
| **AI Model** | Claude Sonnet | — | Natural language expense parsing, budget insights |
| **AI SDK** | Anthropic Python SDK | ≥0.40.0 | API client for Claude |
| **Data manipulation** | Pandas | ≥2.2.0 | DataFrame operations, groupby for charts |
| **Excel support** | OpenPyXL | ≥3.1.5 | Reading `.xlsx` for historical data migration |
| **Config parsing** | PyYAML | ≥6.0 | Reading `config.yaml` for categories, budget limits |
| **HTTP client** | Requests | ≥2.32.0 | Frontend → Backend API calls |
| **Secrets management** | python-dotenv | ≥1.0.0 | Loads `.env` into environment variables |
| **Package manager** | uv | Latest | Dependency resolution, venv, `uv run` |
| **Python runtime** | CPython | 3.13.x | Language runtime (uv-managed) |

---

## Comparison Project — Flask MPA

A similar expense manager built with a classic server-rendered architecture.

| Layer | Technology | Details |
|---|---|---|
| **Language** | Python 3 | Backend logic |
| **Web Framework** | Flask 3.1.3 | Routing, templating, request handling |
| **WSGI Toolkit** | Werkzeug 3.1.6 | HTTP utilities, underlying Flask dependency |
| **Database** | SQLite | File-based SQL via Python's built-in `sqlite3` |
| **Templating** | Jinja2 | HTML templates (built into Flask) |
| **Frontend** | HTML + CSS + JavaScript | Vanilla — no JS framework |
| **Fonts** | Google Fonts | DM Serif Display & DM Sans |
| **Testing** | pytest + pytest-flask | Unit and route testing |
| **Version Control** | Git + GitHub | Repo: gitdebashish123/spendsmanager |

> Architecture: Classic server-rendered MPA (Multi-Page App) — no React/Vue,
> no REST API, Flask renders HTML pages directly.

---

## Head-to-Head Comparison

| Concern | SpendSense | Flask MPA |
|---|---|---|
| **Architecture** | SPA-like — Streamlit + FastAPI REST API | Classic MPA — Flask renders HTML server-side |
| **Frontend** | Streamlit widgets + custom HTML/CSS | Vanilla HTML + CSS + JS + Jinja2 |
| **API layer** | Explicit REST API (FastAPI) | No API — routes return HTML directly |
| **Validation** | Pydantic built-in (FastAPI) | Manual or plugin |
| **API docs** | Auto-generated at `/docs` | Plugin needed |
| **Async support** | Native (FastAPI/Uvicorn) | Limited (Flask 2+) |
| **Testing** | ❌ None yet | ✅ pytest + pytest-flask |
| **Mobile** | Browser-accessible | Browser-accessible |
| **UI control** | Limited (Streamlit constraints) | Full control (vanilla HTML) |
| **Dev speed** | Fast (Streamlit handles UI) | Slower (write every component) |

---

## What SpendSense Could Borrow — Recommendations

### ✅ 1. pytest — Strong Case to Adopt
**Priority: High | Recommended Sprint: 2.3**

The Flask project has `pytest + pytest-flask`. SpendSense currently has zero tests.

**Why it matters:**
- Balance calculation (`get_balance_summary`) involves multiple moving parts — fixed paid,
  pool entries, variable spend. A bug here shows wrong money figures to users.
- Data isolation (Sprint 2) is the highest-risk change — without tests you cannot
  confidently verify User A cannot see User B's data.
- AI parser output is non-deterministic — unit tests with mocked responses catch regressions.

**Recommended additions:**
```
pytest
pytest-asyncio      # for testing async FastAPI endpoints
httpx               # for in-process API testing without running a server
```

**Test coverage targets:**
- `get_balance_summary()` — unit test with known fixtures
- All `/expenses/*` endpoints — verify correct response shapes
- Data isolation — two-user scenario, cross-access must return 404
- AI parser — mock Anthropic response, verify parsing logic

---

### ✅ 2. Jinja2 — For Email & Export Templates
**Priority: Medium | Recommended Sprint: 4**

Not as a Streamlit replacement — Jinja2 is already installed as a FastAPI/Starlette
dependency. Useful for two specific output use cases:

- **Monthly summary emails** — if email reports are added (v2 roadmap), Jinja2
  renders HTML email bodies cleanly
- **Exported reports** — a formatted HTML export of monthly spend is easier with
  Jinja2 templates than building it inside Streamlit

No new dependency needed — already present in the venv.

---

### ✅ 3. werkzeug.security — For Password Hashing
**Priority: High | Recommended Sprint: 1.3**

Werkzeug is a Flask dependency but its security utilities are mature and widely used
independently. For Sprint 1.3 (password hashing during auth implementation):

```python
from werkzeug.security import generate_password_hash, check_password_hash
```

Already battle-tested, no extra install needed (comes with Starlette/FastAPI's
dependency tree), and avoids adding a separate `passlib` dependency for this purpose.

---

## What NOT to Adopt

### ❌ Flask as FastAPI Replacement
SpendSense has already outgrown what Flask offers comfortably:

| Feature | FastAPI | Flask |
|---|---|---|
| Auto API docs | ✅ Built-in | ❌ Plugin needed |
| Request validation | ✅ Pydantic built-in | ❌ Manual |
| Async support | ✅ Native | ⚠️ Limited |
| Type hints | ✅ First-class | ❌ Optional |

No reason to switch. FastAPI is the correct choice for a REST API at this scale.

### ❌ Vanilla HTML/CSS/JS as Streamlit Replacement
The Flask project's vanilla frontend gives full UI control but requires writing
every component from scratch. Streamlit's value is speed — the entire SpendSense
dashboard was built without writing a single HTML form or JS event handler.

**Known Streamlit limitation worth monitoring:** Streamlit reruns the entire Python
script on every user interaction. For a complex dashboard this causes perceptible lag
at scale.

**Future migration path if this becomes a problem:**
```
Current:   Streamlit + FastAPI
Migrate to: React (Vite) + FastAPI   ← not Flask + Jinja2
```

---

## Recommended Additions Summary

| Addition | Inspired By | Why | Sprint |
|---|---|---|---|
| `pytest` + `pytest-asyncio` + `httpx` | Flask project testing | Zero tests is a liability for auth + data isolation | 2.3 |
| `Jinja2` (for email/export) | Flask templating | Already installed, useful for HTML email + report export | 4 |
| `werkzeug.security` | Flask dependency | Mature password hashing, no extra install | 1.3 |

---

## Architectural Philosophy

| | SpendSense | Flask MPA |
|---|---|---|
| **Paradigm** | Data application | Traditional web app |
| **Best for** | Dashboards, data entry, charts | Public pages, SEO, traditional web UX |
| **UI tradeoff** | Less control, much faster dev | Full control, slower dev |
| **Scale ceiling** | ~50 users before Streamlit lag | Higher (standard web architecture) |
| **Right choice for 5–20 users** | ✅ Yes | ✅ Also yes, different approach |

For a personal finance tool used by 5–20 people, SpendSense's architecture is the
stronger choice given the data-heavy nature of the UI and the speed at which it was
built. The Flask MPA approach would make more sense for public-facing pages or SEO.

**The one genuine gap to close:** Testing. That is the clearest thing the Flask
project does better right now, and it matters most during Sprint 2 (data isolation).

---

*Last updated: May 2026*
*Owner: Debashish*
