# SpendSense - Sprint 5 Implementation Prompt
## Rate Limiting & API Hardening

Reference: `design/MULTI_USER_ROADMAP.md` -> Sprint 5

---

## Git Workflow

All Sprint 5 work goes on a feature branch:

```bash
git checkout develop
git checkout -b feature/sprint5-hardening
# implement all 3 commits
git checkout develop
git merge feature/sprint5-hardening --no-ff -m "feat: Sprint 5 - Rate Limiting & API Hardening"
git push
# When ready for production:
git checkout main
git merge develop --no-ff -m "release: Sprint 5"
git push origin main
git checkout develop
```

---

## Commit 5.1 - Rate Limiting

**Goal:** Prevent API abuse and control Anthropic AI costs.

### Dependencies

```bash
uv add slowapi
```

### Step 1 - Add decode_token() to `backend/auth.py`

Add before `decode_access_token()`:

```python
def decode_token(token: str) -> dict:
    """
    Decode a JWT token and return the raw payload.
    Used by the rate limiter to extract user email as the rate limit key.
    Does NOT raise HTTPException - raises JWTError on invalid token.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

### Step 2 - Add imports to `backend/main.py`

```python
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
```

### Step 3 - Create limiter (before `app = FastAPI(...)`)

```python
def get_rate_limit_key(request: Request):
    """Use JWT email as rate limit key if available, else IP address."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            from backend.auth import decode_token
            payload = decode_token(auth[7:])
            return payload.get("sub", get_remote_address(request))
        except Exception:
            pass
    return get_remote_address(request)

limiter = Limiter(key_func=get_rate_limit_key)
```

### Step 4 - Register limiter on app (after CORS middleware)

```python
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### Step 5 - Apply @limiter.limit() decorators

**CRITICAL:** `request: Request` MUST be the FIRST parameter in every
rate-limited endpoint. slowapi raises TypeError at startup if it is not first.

```python
# AI parsing - 30/hour per user (cost control)
@app.post("/expenses/parse")
@limiter.limit("30/hour")
def parse_and_save(request: Request, input: ExpenseInput, ...):

# Login - 10/hour per IP (brute force protection)
@app.post("/auth/login", response_model=TokenResponse)
@limiter.limit("10/hour", key_func=get_remote_address)
def login(request: Request, req: LoginRequest, ...):

# Register - 5/hour per IP
@app.post("/auth/register", response_model=UserResponse, status_code=201)
@limiter.limit("5/hour", key_func=get_remote_address)
def register(request: Request, req: RegisterRequest, ...):

# Summary - 300/hour
@app.get("/summary/{month_key}")
@limiter.limit("300/hour")
def get_summary(request: Request, month_key: str, ...):

# Expenses - 300/hour
@app.get("/expenses/{month_key}")
@limiter.limit("300/hour")
def get_expenses(request: Request, month_key: str, ...):

# Manual expense - 300/hour
@app.post("/expenses/manual")
@limiter.limit("300/hour")
def add_manual_expense(request: Request, exp: ManualExpense, ...):

# Export - 20/hour
@app.get("/export/csv/all")
@limiter.limit("20/hour")
def export_all_csv(request: Request, ...):

@app.get("/export/csv/{month_key}")
@limiter.limit("20/hour")
def export_month_csv(request: Request, month_key: str, ...):
```

### Step 6 - Handle 429 in `frontend/app.py` api() helper

Add after the 401 check in `api()`:

```python
if r.status_code == 429:
    st.warning("Too many requests. Please wait a moment before trying again.")
    return None
```

### Verification - Commit 5.1

```bash
# Start backend
uv run uvicorn backend.main:app --reload --port 8000 &
sleep 3

# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@spendsense.local","password":"changeme123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Verify rate limit headers present
curl -s -X POST http://localhost:8000/expenses/parse \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"test 100"}' -v 2>&1 | grep -i "x-ratelimit"
# expect: X-RateLimit-Limit and X-RateLimit-Remaining headers

# Test brute force protection (11 login attempts)
for i in $(seq 1 11); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"x@x.com","password":"wrong"}')
  echo "Attempt $i: $CODE"
done
# expect: first 10 return 401, 11th returns 429
```

---

## Commit 5.2 - Input Validation & Sanitisation

**Goal:** Reject malformed input, prevent injection, enforce field limits.

### Dependencies

```bash
uv add bleach
# If bleach fails on Python 3.13 use: uv add nh3
# nh3 replacement: nh3.clean(v, tags=set()) instead of bleach.clean(v, tags=[], strip=True)
```

### Imports to add to `backend/main.py`

```python
from pydantic import field_validator
import bleach  # or: import nh3
```

### Validators to add to Pydantic models

**ExpenseInput:**
```python
@field_validator("text")
@classmethod
def sanitise_text(cls, v):
    if len(v) > 500:
        raise ValueError("Input text must be under 500 characters")
    return bleach.clean(v, tags=[], strip=True).strip()
```

**ManualExpense:**
```python
@field_validator("vendor")
@classmethod
def sanitise_vendor(cls, v):
    if len(v) > 100:
        raise ValueError("Vendor name must be under 100 characters")
    return bleach.clean(v, tags=[], strip=True).strip()

@field_validator("amount")
@classmethod
def positive_amount(cls, v):
    if v <= 0:
        raise ValueError("Amount must be greater than 0")
    if v > 10_000_000:
        raise ValueError("Amount exceeds maximum allowed value")
    return round(v, 2)

@field_validator("note")
@classmethod
def sanitise_note(cls, v):
    if v and len(v) > 300:
        raise ValueError("Note must be under 300 characters")
    return bleach.clean(v, tags=[], strip=True).strip() if v else v
```

**IncomeInput** - add validators for:
- `amount`: must be > 0 and <= 100_000_000
- `source`: max 100 chars, bleach-sanitised

**FixedTemplateCreate** - add validators for:
- `name`: max 100 chars, bleach-sanitised
- `amount`: must be > 0

**RegisterRequest** - replace existing inline validation with field_validators:
```python
@field_validator("email")
@classmethod
def valid_email(cls, v):
    v = v.strip().lower()
    if len(v) > 255:
        raise ValueError("Email too long")
    if "@" not in v or "." not in v.split("@")[-1]:
        raise ValueError("Invalid email format")
    return v

@field_validator("password")
@classmethod
def strong_password(cls, v):
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if len(v) > 128:
        raise ValueError("Password too long")
    return v
```

**Note:** Remove the duplicate `if "@" not in req.email` and `if len(req.password) < 8`
checks from the `register()` endpoint body after adding field_validators.

### Request size middleware (add after `app.add_exception_handler(...)`)

```python
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Reject requests larger than 10KB to prevent payload abuse."""
    max_size = 10 * 1024  # 10KB
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_size:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request payload too large. Maximum size is 10KB."},
        )
    return await call_next(request)
```

### Tighten CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "https://localhost:8443",
        "https://frontend-production-22a3.up.railway.app",
    ],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=False,
)
```

### Verification - Commit 5.2

```bash
# Vendor too long (101 chars)
curl -X POST http://localhost:8000/expenses/manual \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"vendor\":\"$(python3 -c "print('A'*101)")\",\"amount\":100,\"category\":\"Food\"}"
# expect: 422 Unprocessable Entity

# Negative amount
curl -X POST http://localhost:8000/expenses/manual \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vendor":"Test","amount":-50,"category":"Food"}'
# expect: 422 with "Amount must be greater than 0"

# HTML injection stripped
curl -X POST http://localhost:8000/expenses/manual \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vendor":"<script>alert(1)</script>Zomato","amount":100,"category":"Food"}'
# expect: 200 but vendor saved as "Zomato" (HTML stripped)
```

---

## Commit 5.3 - Security Headers

**Goal:** Add security headers, remove server version leakage.
API versioning deferred to Sprint 6 to avoid breaking the frontend.

### Security headers middleware (add after request size middleware)

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add security headers to every response.
    X-Content-Type-Options: prevents MIME-type sniffing
    X-Frame-Options: prevents clickjacking
    X-XSS-Protection: legacy browser XSS filter
    Strict-Transport-Security: force HTTPS for 1 year
    Referrer-Policy: control referrer on cross-origin requests
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    response.headers["X-XSS-Protection"]          = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
    response.headers.pop("server", None)
    response.headers.pop("x-powered-by", None)
    return response
```

### Update FastAPI app metadata

```python
app = FastAPI(
    title="SpendSense API",
    version="2.0.0",
    description="Personal expenditure tracker - JWT authenticated, per-user data isolation",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
```

### API versioning TODO comment

Add after `app = FastAPI(...)`:

```python
# TODO Sprint 6: Add /api/v1 prefix via APIRouter(prefix="/api/v1")
# Requires updating API_BASE in frontend and Railway env vars
```

### Verification - Commit 5.3

```bash
# Security headers present
curl -I http://localhost:8000/health
# expect:
# x-content-type-options: nosniff
# x-frame-options: DENY
# strict-transport-security: max-age=31536000; includeSubDomains
# referrer-policy: strict-origin-when-cross-origin

# Server header removed
curl -I http://localhost:8000/health | grep -i "^server:"
# expect: no output

# App still functional
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/me
# expect: user profile JSON
```

---

## Files Modified in Sprint 5

| File | Commit | Change |
|---|---|---|
| `pyproject.toml` | 5.1 | Add slowapi |
| `pyproject.toml` | 5.2 | Add bleach or nh3 |
| `backend/auth.py` | 5.1 | Add decode_token() |
| `backend/main.py` | 5.1 | Limiter setup, @limiter.limit() decorators, request: Request as first param |
| `backend/main.py` | 5.2 | field_validator imports, model validators, size middleware, CORS tighten |
| `backend/main.py` | 5.3 | Security headers middleware, FastAPI metadata, versioning TODO |
| `frontend/app.py` | 5.1 | Handle 429 in api() helper |

### Files NOT changed
- `backend/models.py`
- `backend/budget_rules.py`
- `docker-compose.yml`
- `railway.toml`
- `migrate_schema.py`

---

## Common Pitfalls

| Issue | Cause | Fix |
|---|---|---|
| TypeError on startup | `request: Request` not first param | Move it to be first parameter |
| bleach ImportError on Python 3.13 | bleach deprecated | Use `nh3` instead: `uv add nh3`, `nh3.clean(v, tags=set())` |
| CORS errors after tightening | Missing method or header | Check browser console, add missing item |
| 429 on first request | Wrong key_func | Verify get_rate_limit_key returns email or IP correctly |
| Duplicate validation errors | field_validator + endpoint body both validate | Remove inline checks from endpoint body |

---

## Pre-Sprint 5 Checklist

- [ ] On `feature/sprint5-hardening` branch
- [ ] Sprint 4 complete and merged to develop
- [ ] Track 0 UI Quick Wins merged to develop
- [ ] Local backend runs: `uv run uvicorn backend.main:app --reload`
- [ ] Railway deployment healthy: `curl https://YOUR-BACKEND.up.railway.app/health`

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Commit 5.1 complete. Implement 5.2 and 5.3 next.*
