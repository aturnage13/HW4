"""Create-account, email verification, and login.

Passwords are never stored or logged in plain text: only salted PBKDF2-SHA256
hashes go in users.password_hash, and the API never returns that column.
Session and verification tokens are random secrets; only their SHA-256 hashes
are stored, so a copy of the database can't be used to log in.
"""

import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Cookie, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator

from db import get_connection

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ---------- Settings ----------
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
SESSION_COOKIE = "cc_session"
SESSION_TTL = timedelta(days=7)
VERIFY_TTL = timedelta(hours=24)
OUTBOX_DIR = Path(__file__).resolve().parent / "outbox"

PBKDF2_ITERATIONS = 600_000  # OWASP 2023+ recommendation for PBKDF2-SHA256
LEGACY_ITERATIONS = 120_000  # seed accounts use pbkdf2_sha256$salt$hash at 120k
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- Password hashing ----------
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) == 4:  # pbkdf2_sha256$iterations$salt$hash
        algo, iterations, salt, digest = parts
        iterations = int(iterations)
    elif len(parts) == 3:  # legacy seed format: pbkdf2_sha256$salt$hash
        algo, salt, digest = parts
        iterations = LEGACY_ITERATIONS
    else:
        return False
    if algo != "pbkdf2_sha256":
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), iterations
    ).hex()
    return hmac.compare_digest(candidate, digest)


def needs_rehash(stored: str) -> bool:
    parts = stored.split("$")
    return len(parts) != 4 or int(parts[1]) < PBKDF2_ITERATIONS


# Used when the email isn't found so a failed login takes the same time
# whether or not the account exists.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


# ---------- Tokens ----------
def new_token() -> tuple[str, str]:
    """Return (raw token for the user, hash to store)."""
    raw = secrets.token_urlsafe(32)
    return raw, hashlib.sha256(raw.encode()).hexdigest()


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_db_time(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ---------- Email (dev mailer) ----------
def send_verification_email(email: str, first_name: str, raw_token: str) -> None:
    """Dev stand-in for an email provider: writes the message to backend/outbox/.

    Swap this for a real provider (SendGrid, SES, etc.) in production.
    """
    link = f"{FRONTEND_URL}/verify-email?token={raw_token}"
    body = (
        f"To: {email}\n"
        f"Subject: Confirm your Campus Customs account\n\n"
        f"Hi {first_name},\n\n"
        f"Thanks for signing up! Confirm your email by opening this link:\n\n"
        f"{link}\n\n"
        f"This link expires in 24 hours. If you didn't create an account, "
        f"you can ignore this email.\n"
    )
    OUTBOX_DIR.mkdir(exist_ok=True)
    stamp = utc_now().strftime("%Y%m%d-%H%M%S-%f")
    safe_email = re.sub(r"[^A-Za-z0-9._-]", "_", email)
    (OUTBOX_DIR / f"{stamp}_{safe_email}.txt").write_text(body)
    print(f"[dev mailer] Verification email for {email} written to backend/outbox/")


def issue_verification(conn, user_id: int, email: str, first_name: str) -> None:
    raw, token_hash = new_token()
    conn.execute(
        "INSERT INTO email_verification_tokens (user_id, token_hash, expires_at) "
        "VALUES (?, ?, ?)",
        (user_id, token_hash, to_db_time(utc_now() + VERIFY_TTL)),
    )
    send_verification_email(email, first_name, raw)


# ---------- Request models ----------
class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("is required")
        return v

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("must be a valid email address")
        return v


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class VerifyRequest(BaseModel):
    token: str = Field(max_length=200)


class ResendRequest(BaseModel):
    email: str = Field(max_length=254)


def public_user(row) -> dict:
    """The only user fields the API ever returns (never password_hash)."""
    return {
        "id": row["id"],
        "firstName": row["first_name"],
        "lastName": row["last_name"],
        "email": row["email"],
    }


# ---------- Routes ----------
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest) -> dict:
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE lower(email) = ?", (body.email,)
        ).fetchone()
        if exists:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "An account with that email already exists."
            )
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                f"{body.first_name} {body.last_name}",
                body.email,
                hash_password(body.password),
                body.first_name,
                body.last_name,
            ),
        )
        issue_verification(conn, cur.lastrowid, body.email, body.first_name)
    return {"message": "Account created. Check your email to confirm your address."}


@router.post("/verify-email")
def verify_email(body: VerifyRequest) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, user_id, expires_at, used_at FROM email_verification_tokens "
            "WHERE token_hash = ?",
            (hash_token(body.token),),
        ).fetchone()
        if row is None or row["used_at"] is not None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "This confirmation link is invalid or was already used."
            )
        if row["expires_at"] < to_db_time(utc_now()):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "This confirmation link has expired. Request a new one."
            )
        now = to_db_time(utc_now())
        conn.execute(
            "UPDATE email_verification_tokens SET used_at = ? WHERE id = ?", (now, row["id"])
        )
        conn.execute(
            "UPDATE users SET email_verified_at = ? WHERE id = ? AND email_verified_at IS NULL",
            (now, row["user_id"]),
        )
    return {"message": "Email confirmed. You can now log in."}


@router.post("/resend-verification")
def resend_verification(body: ResendRequest) -> dict:
    email = body.email.strip().lower()
    with get_connection() as conn:
        user = conn.execute(
            "SELECT id, first_name, email_verified_at FROM users WHERE lower(email) = ?",
            (email,),
        ).fetchone()
        if user and user["email_verified_at"] is None:
            issue_verification(conn, user["id"], email, user["first_name"] or "there")
    # Same answer either way so this can't be used to probe which emails exist.
    return {"message": "If that account needs confirming, we've sent a new link."}


@router.post("/login")
def login(body: LoginRequest, response: Response) -> dict:
    email = body.email.strip().lower()
    with get_connection() as conn:
        user = conn.execute(
            "SELECT id, email, first_name, last_name, password_hash, email_verified_at "
            "FROM users WHERE lower(email) = ?",
            (email,),
        ).fetchone()

        if user is None:
            verify_password(body.password, _DUMMY_HASH)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")
        if not verify_password(body.password, user["password_hash"]):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")
        if user["email_verified_at"] is None:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Please confirm your email before logging in.",
            )

        # Upgrade older/weaker hashes now that we know the password is right.
        if needs_rehash(user["password_hash"]):
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(body.password), user["id"]),
            )

        raw, token_hash = new_token()
        conn.execute(
            "INSERT INTO sessions (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
            (user["id"], token_hash, to_db_time(utc_now() + SESSION_TTL)),
        )

    response.set_cookie(
        SESSION_COOKIE,
        raw,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return {"user": public_user(user)}


@router.post("/logout")
def logout(response: Response, cc_session: str | None = Cookie(default=None)) -> dict:
    if cc_session:
        with get_connection() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (hash_token(cc_session),))
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"message": "Logged out."}


def session_user(raw_token: str | None):
    """Return the logged-in user's row for a session cookie, or None."""
    if not raw_token:
        return None
    with get_connection() as conn:
        return conn.execute(
            "SELECT u.id, u.email, u.first_name, u.last_name FROM sessions s "
            "JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash = ? AND s.expires_at > ?",
            (hash_token(raw_token), to_db_time(utc_now())),
        ).fetchone()


@router.get("/me")
def me(cc_session: str | None = Cookie(default=None)) -> dict:
    user = session_user(cc_session)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in.")
    return {"user": public_user(user)}
