"""
backend/auth.py
───────────────
JWT token generation, verification, password hashing, and the
get_current_user FastAPI dependency used to protect all endpoints.

Sprint 1, Commit 1.3 — FastAPI Backend Authentication

Security decisions:
- JWT_SECRET_KEY must be set explicitly — no insecure default allowed
- Passwords hashed with bcrypt (intentionally slow, brute-force resistant)
- Wrong email and wrong password return identical 401 (no information leakage)
- last_login written at most once every 5 minutes (avoids DB write on every call)
- Disabled accounts (is_active=False) return 403, not 401 (distinct from unauthenticated)
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from dotenv import load_dotenv
import os

from backend.models import User, get_session

# ── Load .env ─────────────────────────────────────────────────────────────────
load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 hours default

# Fail loudly at import time if the secret key is missing.
# A missing secret must be an explicit startup failure — never a silent
# fallback to an insecure default value.
if not SECRET_KEY:
    raise RuntimeError(
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  JWT_SECRET_KEY environment variable is not set.\n"
        "\n"
        "  Add it to your .env file:\n"
        "    JWT_SECRET_KEY=<random-64-char-string>\n"
        "\n"
        "  Generate one with:\n"
        "    python3 -c \"import secrets; print(secrets.token_hex(32))\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )

# ── Password Hashing ──────────────────────────────────────────────────────────
# bcrypt is used directly (not via passlib) — passlib has compatibility issues
# with bcrypt >= 4.x on Python 3.13.
# bcrypt is intentionally slow — makes offline brute-force attacks impractical.


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plaintext password. Never store the input."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Return True if the plaintext matches the bcrypt hash, False otherwise.
    Constant-time comparison — safe against timing attacks.
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT Token Creation ────────────────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    """
    Create a signed JWT containing the provided data payload.

    The token payload includes:
    - All keys from `data` (typically {"sub": email})
    - "exp": expiry timestamp (utcnow + ACCESS_TOKEN_EXPIRE_MINUTES)

    Returns the encoded JWT string.
    """
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ── JWT Token Verification ────────────────────────────────────────────────────

def decode_token(token: str) -> dict:
    """
    Decode a JWT token and return the raw payload.
    Used by the rate limiter to extract user email as the rate limit key.
    Does NOT raise HTTPException - raises JWTError on invalid token.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Raises HTTPException 401 if the token is:
    - Expired
    - Malformed or tampered with
    - Missing the "sub" (subject / email) claim

    Returns the decoded payload dict on success.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


# ── OAuth2 Scheme ─────────────────────────────────────────────────────────────
# tokenUrl="/auth/login" makes Swagger UI show an "Authorize" button that
# calls /auth/login and stores the returned token for subsequent requests.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── FastAPI Dependency: get_current_user ──────────────────────────────────────

# Minimum interval between last_login DB writes (avoids a write on every API call)
_LAST_LOGIN_UPDATE_INTERVAL = timedelta(minutes=5)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """
    FastAPI dependency — validates the Bearer JWT and returns the authenticated User.

    Usage:
        @app.get("/some-endpoint")
        def my_endpoint(current_user: User = Depends(get_current_user)):
            ...

    Raises:
        401 Unauthorized — token is missing, invalid, or expired
        403 Forbidden    — account exists but is_active=False (disabled by admin)

    Side effect:
        Updates user.last_login at most once every 5 minutes to avoid a DB
        write on every single API call while keeping the audit trail accurate.
    """
    # Step 1 — Decode and verify the JWT
    payload = decode_access_token(token)
    email: str = payload.get("sub")

    # Step 2 — Look up the user in the database
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Step 3 — Reject disabled accounts with a distinct 403 (not 401)
    # 401 = unauthenticated, 403 = authenticated but not permitted
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled — contact administrator",
        )

    # Step 4 — Update last_login at most once every 5 minutes
    # Avoids a DB write on every API call while keeping the audit trail useful.
    now = datetime.utcnow()
    if (
        user.last_login is None
        or (now - user.last_login) > _LAST_LOGIN_UPDATE_INTERVAL
    ):
        user.last_login = now
        session.add(user)
        session.commit()
        session.refresh(user)

    return user
