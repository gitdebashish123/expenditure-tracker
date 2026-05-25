# SpendSense — Commit 1.3 Implementation Prompt
## FastAPI Backend Authentication (JWT + Password Hashing)

Reference: `design/MULTI_USER_ROADMAP.md` → Sprint 1, Commit 1.3

---

## Context

SpendSense is a personal expenditure tracker built with:
- **Backend**: FastAPI + Uvicorn, running on port 8000
- **Database**: SQLite via SQLModel ORM
- **Project root**: `/Users/debashish/Desktop/ai-projects/expenditure-tracker`
- **Package manager**: `uv` — always use `uv add`, never `pip install`

All existing endpoints are currently unprotected. This commit adds JWT-based
authentication so that every API call requires a valid token. This is a
prerequisite for Sprint 2 (data isolation — `user_id` on every table).

The Streamlit frontend (`frontend/app.py`) is **NOT modified in this commit**.
Login UI is Sprint 1.4. This commit is backend-only.

---

## Pre-Implementation Checks

Before writing any code, verify:

```bash
# Confirm uv is available
uv --version

# Confirm existing backend starts cleanly
cd /Users/debashish/Desktop/ai-projects/expenditure-tracker
uv run uvicorn backend.main:app --port 8000 --reload

# Confirm current unprotected endpoint works (baseline)
curl http://localhost:8000/months
# expect: JSON array — ["2026-05", "2026-04", ...]
```

---

## Step 1 — Add Dependencies

Add the following packages using `uv add` (do not edit `pyproject.toml` manually):

```bash
uv add python-jose[cryptography]
uv add passlib[bcrypt]
```

**Why these packages:**
- `python-jose[cryptography]` — JWT creation and verification. The `[cryptography]`
  extra provides the RS256/HS256 signing backend.
- `passlib[bcrypt]` — password hashing. The `[bcrypt]` extra uses the bcrypt
  algorithm which is slow by design, making brute-force attacks impractical.

Verify both appear in `pyproject.toml` under `[project.dependencies]` after adding.

---

## Step 2 — Add `User` Table to `backend/models.py`

Add the `User` SQLModel class to `backend/models.py`.

**Requirements:**
- Place it **before** all other model classes (it will be referenced by future
  `user_id` foreign keys in Sprint 2)
- Fields:
  - `id: Optional[int]` — primary key, auto-increment
  - `email: str` — unique, indexed, used as login identifier
  - `hashed_password: str` — bcrypt hash, never store plaintext
  - `is_active: bool` — default `True`, allows disabling accounts without deletion
  - `is_admin: bool` — default `False`, reserved for Sprint 6.3 admin panel
  - `created_at: datetime` — set on creation
  - `last_login: Optional[datetime]` — updated on each successful login, default `None`

**Do not** add `user_id` foreign keys to existing tables yet — that is Sprint 2.

---

## Step 3 — Create `backend/auth.py`

Create a new file `backend/auth.py` from scratch.

### 3a. Configuration Constants

Read from environment variables with secure defaults:

```python
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 hours default
```

**Important:** If `JWT_SECRET_KEY` is not set, raise a clear startup error:
```
RuntimeError: JWT_SECRET_KEY environment variable is not set.
Add it to your .env file: JWT_SECRET_KEY=<random-64-char-string>
```

Do not provide a default value for `SECRET_KEY` — a missing secret must be an
explicit failure, not a silent fallback to an insecure value.

### 3b. Password Hashing

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str: ...
def verify_password(plain: str, hashed: str) -> bool: ...
```

### 3c. JWT Token Creation

```python
def create_access_token(data: dict) -> str:
    # payload must include: sub (email), exp (expiry timestamp)
    # use datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
```

### 3d. JWT Token Verification

```python
def decode_access_token(token: str) -> dict:
    # raises HTTPException 401 if token is invalid, expired, or malformed
    # returns the decoded payload dict on success
```

### 3e. FastAPI Dependency — `get_current_user`

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    # 1. Decode and verify the JWT
    # 2. Extract email from payload["sub"]
    # 3. Look up User in DB by email
    # 4. If user not found or is_active=False → raise HTTPException 401
    # 5. Update user.last_login = datetime.utcnow() — but only if > 5 mins since last update
    #    (avoids a DB write on every single API call)
    # 6. Return the User object
```

Use `OAuth2PasswordBearer(tokenUrl="/auth/login")` as the scheme — this makes
Swagger UI show an "Authorize" button that works correctly for manual testing.

### 3f. Imports needed in auth.py

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from backend.models import User, get_session
import os
```

---

## Step 4 — Add Auth Endpoints to `backend/main.py`

### 4a. Imports to add

```python
from backend.auth import (
    hash_password, verify_password,
    create_access_token, get_current_user
)
```

### 4b. Pydantic Request/Response Models

Add these to the existing request models section in `main.py`:

```python
class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]
```

### 4c. POST /auth/register

```
POST /auth/register
Body: { "email": "user@example.com", "password": "securepass" }
```

Requirements:
- Validate email format (basic check — contains `@` and `.`)
- Enforce minimum password length of 8 characters
- Check if email already exists → return `400 Bad Request` with message
  `"Email already registered"`
- Hash the password with `hash_password()`
- Create and persist the `User` record
- Return `UserResponse` (never return the hashed password)
- Do **not** return a token on registration — user must explicitly log in

### 4d. POST /auth/login

```
POST /auth/login
Body: { "email": "user@example.com", "password": "securepass" }
```

Requirements:
- Look up user by email
- If not found → return `401 Unauthorized` with message `"Invalid credentials"`
  (do not reveal whether the email exists — same error for wrong email or wrong password)
- Verify password with `verify_password()`
- If password wrong → same `401` as above
- If `user.is_active` is `False` → return `403 Forbidden` with message
  `"Account disabled — contact administrator"`
- Update `user.last_login = datetime.utcnow()`
- Return `TokenResponse` with a freshly signed JWT

### 4e. GET /auth/me

```
GET /auth/me
Header: Authorization: Bearer <token>
```

Requirements:
- Protected with `Depends(get_current_user)`
- Returns `UserResponse` for the currently authenticated user
- Used by the frontend (Sprint 1.4) to verify session and show last login time

### 4f. Protect All Existing Endpoints

Add `current_user: User = Depends(get_current_user)` as a parameter to **every**
existing endpoint function in `main.py`.

**List of endpoints to protect** (all of them):
- All `/expenses/*` endpoints
- All `/fixed/*` endpoints
- All `/fixed-templates/*` endpoints
- All `/expense-templates/*` endpoints
- All `/summary/*` endpoints
- All `/budget*` endpoints
- All `/income*` endpoints
- All `/months` endpoint
- All `/seed/*` endpoints
- All `/pools/*` endpoints
- All `/insights/*` endpoints

**Exceptions — do NOT protect these:**
- `POST /auth/register` — must be public (unauthenticated users need to register)
- `POST /auth/login` — must be public (unauthenticated users need to log in)
- `GET /health` — if it exists, keep it public for deployment health checks

**Important:** The `current_user` parameter is added to function signatures but
does **not** need to be used in the function body yet. In Sprint 2, it will be
used to filter queries by `current_user.id`. For now, its presence alone enforces
authentication.

---

## Step 5 — Add `JWT_SECRET_KEY` to `.env` and `.env.example`

### .env (actual secrets file)

Generate a secure random key and add it:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Add the output to `.env`:
```
JWT_SECRET_KEY=<generated-64-char-hex-string>
JWT_EXPIRE_MINUTES=480
```

### .env.example (safe to commit)

Add placeholder entries:
```
# JWT Authentication — generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=your-secret-key-here-generate-a-new-one-do-not-use-this
JWT_EXPIRE_MINUTES=480
```

---

## Step 6 — Database Migration

The `User` table is new. SQLModel's `create_all()` in `on_startup` will create it
automatically on next backend start — no manual migration needed.

However, add a startup check that creates a default admin user if no users exist,
so the app is not locked out on first run:

```python
# In on_startup() in main.py, after create_db():
from backend.auth import hash_password
from backend.models import User

with Session(engine) as session:
    existing_user = session.exec(select(User)).first()
    if not existing_user:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@spendsense.local")
        admin_password = os.getenv("ADMIN_PASSWORD", "changeme123")
        admin = User(
            email=admin_email,
            hashed_password=hash_password(admin_password),
            is_active=True,
            is_admin=True,
        )
        session.add(admin)
        session.commit()
        print(f"✅ Default admin created: {admin_email}")
        print(f"⚠️  Change the admin password immediately via POST /auth/register")
```

Add `ADMIN_EMAIL` and `ADMIN_PASSWORD` to both `.env` and `.env.example`.

---

## Step 7 — Update CORS for Auth Headers

The `Authorization` header must be allowed through CORS. Update `allow_headers`
in the CORSMiddleware configuration in `main.py`:

```python
allow_headers=["*", "Authorization"],
```

This ensures the browser does not strip the Bearer token header on cross-origin
requests from the Streamlit frontend.

---

## Verification Steps

After implementation, verify each of the following in order:

### 7.1 — Backend starts without errors
```bash
cd /Users/debashish/Desktop/ai-projects/expenditure-tracker
uv run uvicorn backend.main:app --port 8000 --reload
# expect: "✅ Default admin created: admin@spendsense.local" on first run
# expect: No startup errors
```

### 7.2 — Register a new user
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
# expect: {"id": 2, "email": "test@example.com", "is_active": true, ...}
# expect: NO token in response
```

### 7.3 — Duplicate registration is rejected
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "anotherpass"}'
# expect: 400 {"detail": "Email already registered"}
```

### 7.4 — Login returns a token
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
# expect: {"access_token": "eyJ...", "token_type": "bearer"}
# save the token: TOKEN=<value from access_token>
```

### 7.5 — Protected endpoint rejected without token
```bash
curl http://localhost:8000/months
# expect: 401 {"detail": "Not authenticated"}
```

### 7.6 — Protected endpoint works with token
```bash
curl http://localhost:8000/months \
  -H "Authorization: Bearer $TOKEN"
# expect: JSON array of months — same as before auth was added
```

### 7.7 — /auth/me returns current user
```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
# expect: {"id": 2, "email": "test@example.com", "last_login": "...", ...}
```

### 7.8 — Wrong password returns 401
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "wrongpassword"}'
# expect: 401 {"detail": "Invalid credentials"}
# must be same error as wrong email — no information leakage
```

### 7.9 — Expired token is rejected
```bash
# Set JWT_EXPIRE_MINUTES=0 in .env temporarily, restart, login, wait 1 min, test
curl http://localhost:8000/months \
  -H "Authorization: Bearer $EXPIRED_TOKEN"
# expect: 401 {"detail": "Token has expired"}
# restore JWT_EXPIRE_MINUTES=480 after test
```

### 7.10 — Swagger UI shows Authorize button
```
Open http://localhost:8000/docs in browser
expect: "Authorize" button visible in top right
Click it → enter credentials → all endpoints now testable via Swagger UI
```

---

## Files Modified in This Commit

| File | Change |
|---|---|
| `pyproject.toml` | `python-jose[cryptography]` and `passlib[bcrypt]` added via `uv add` |
| `backend/models.py` | `User` table added |
| `backend/auth.py` | New file — JWT logic, password hashing, `get_current_user` dependency |
| `backend/main.py` | Auth endpoints added, all existing endpoints protected |
| `.env` | `JWT_SECRET_KEY`, `JWT_EXPIRE_MINUTES`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` added |
| `.env.example` | Same keys added with placeholder values |

---

## Do Not Change in This Commit

- `frontend/app.py` — login UI is Sprint 1.4
- `backend/budget_rules.py` — no user scoping yet (Sprint 2)
- Any existing test data or the SQLite database structure beyond the new `User` table
- The nginx configs from Commit 1.2

---

## Known Limitation (Resolved in Sprint 2)

After this commit, all authenticated users share the same data — there is no
`user_id` filtering on any query. User A can read User B's expenses if they
have a valid token. This is intentional and documented — Sprint 2 adds
`user_id` to every table and every query.

This commit only establishes the authentication layer. Data isolation is the
next sprint.

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Prompt ready — awaiting execution approval*
