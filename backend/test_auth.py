"""End-to-end check of the auth flow against the running servers.

Needs the API (port 8000) and Vite dev server (port 5173) running; requests go
through the Vite proxy just like the browser. The seed account's password is
read from the environment so it isn't written into this file:

    cd backend && SEED_PASSWORD=... .venv/bin/python test_auth.py

A brand-new account is created on every run with a random password that is
generated in memory and never printed.
"""

import http.cookiejar
import json
import os
import re
import secrets
import sqlite3
import urllib.error
import urllib.request

from auth import OUTBOX_DIR
from db import DB_PATH

BASE = os.getenv("BASE_URL", "http://localhost:5173")
SEED_EMAIL = "test@campuscustoms.yale.edu"
SEED_PASSWORD = os.environ.get("SEED_PASSWORD", "")

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((ok, label))
    print(f"{'PASS' if ok else 'FAIL'}  {label}")


def client():
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def call(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            BASE + path, data=data, method=method, headers={"Content-Type": "application/json"}
        )
        try:
            with opener.open(req) as res:
                return res.status, json.loads(res.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    return call, jar


def latest_token_for(email: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", email)
    files = sorted(OUTBOX_DIR.glob(f"*_{safe}.txt"))
    match = re.search(r"token=([A-Za-z0-9_\-]+)", files[-1].read_text())
    return match.group(1)


def main() -> None:
    # --- Seed user ---
    call, jar = client()
    status, body = call("POST", "/api/auth/login", {"email": SEED_EMAIL, "password": SEED_PASSWORD})
    check(status == 200, "seed user can log in")
    check("password_hash" not in json.dumps(body), "login response has no password hash")
    check(any(c.name == "cc_session" for c in jar), "login sets session cookie")
    cookie = next(c for c in jar if c.name == "cc_session")
    check(bool(cookie.has_nonstandard_attr("HttpOnly")), "session cookie is HttpOnly")
    status, body = call("GET", "/api/auth/me")
    check(status == 200 and body["user"]["email"] == SEED_EMAIL, "/me returns the seed user")

    bad, _ = client()
    status, body = bad("POST", "/api/auth/login", {"email": SEED_EMAIL, "password": "wrong-" + secrets.token_hex(4)})
    check(status == 401, "wrong password is rejected")
    status, body2 = bad("POST", "/api/auth/login", {"email": "nobody@example.com", "password": "whatever123"})
    check(status == 401 and body2 == body, "unknown email gets the same error as wrong password")

    # --- Brand-new account ---
    email = f"new.student.{secrets.token_hex(3)}@campuscustoms.yale.edu"
    password = secrets.token_urlsafe(16)
    call, _ = client()
    status, _ = call("POST", "/api/auth/register",
                     {"first_name": "New", "last_name": "Student", "email": email, "password": password})
    check(status == 201, f"new account created ({email})")

    status, _ = call("POST", "/api/auth/register",
                     {"first_name": "Dup", "last_name": "User", "email": email.upper(), "password": password})
    check(status == 409, "duplicate email (any case) is rejected")
    status, _ = call("POST", "/api/auth/register",
                     {"first_name": "A", "last_name": "B", "email": "short@campuscustoms.yale.edu", "password": "short"})
    check(status == 422, "password under 8 characters is rejected")
    status, _ = call("POST", "/api/auth/register",
                     {"first_name": "A", "last_name": "B", "email": "not-an-email", "password": password})
    check(status == 422, "invalid email is rejected")

    status, _ = call("POST", "/api/auth/login", {"email": email, "password": password})
    check(status == 403, "unconfirmed account can't log in yet")

    token = latest_token_for(email)
    status, _ = call("POST", "/api/auth/verify-email", {"token": token})
    check(status == 200, "confirmation link verifies the email")
    status, _ = call("POST", "/api/auth/verify-email", {"token": token})
    check(status == 400, "confirmation link can't be reused")

    status, body = call("POST", "/api/auth/login", {"email": email, "password": password})
    check(status == 200 and body["user"]["firstName"] == "New", "new account can log in after confirming")
    status, body = call("GET", "/api/auth/me")
    check(status == 200 and body["user"]["email"] == email, "/me returns the new user")
    call("POST", "/api/auth/logout")
    status, _ = call("GET", "/api/auth/me")
    check(status == 401, "logout ends the session")

    # --- What's actually stored ---
    conn = sqlite3.connect(DB_PATH)
    stored = conn.execute("SELECT password_hash FROM users WHERE email = ?", (email,)).fetchone()[0]
    seed = conn.execute("SELECT password_hash FROM users WHERE email = ?", (SEED_EMAIL,)).fetchone()[0]
    sessions_plain = conn.execute("SELECT COUNT(*) FROM sessions WHERE token_hash = ?", (cookie.value,)).fetchone()[0]
    conn.close()
    check(stored.startswith("pbkdf2_sha256$600000$") and password not in stored, "new password stored only as a 600k PBKDF2 hash")
    check(seed.startswith("pbkdf2_sha256$600000$"), "seed user's old 120k hash was upgraded on login")
    check(sessions_plain == 0, "raw session token is not stored in the database")

    passed = sum(ok for ok, _ in results)
    print(f"\n{passed}/{len(results)} checks passed")
    raise SystemExit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
