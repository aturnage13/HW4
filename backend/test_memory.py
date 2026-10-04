"""End-to-end check of customer memory and page context (Problem 8).

Needs both servers running (requests go through the Vite proxy like the
browser) and calls the real model. A brand-new account is created each run, so
its history starts empty; its random password is generated in memory and never
printed. The seed account's password comes from the environment:

    cd backend && SEED_PASSWORD=... .venv/bin/python test_memory.py
"""

import os
import secrets
import sqlite3

from db import DB_PATH
from test_auth import BASE, SEED_EMAIL, client, latest_token_for

SEED_PASSWORD = os.environ["SEED_PASSWORD"]
results: list[tuple[bool, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((ok, label))
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"\n      {detail}" if detail else ""))


def page(path: str, product_id: str | None = None) -> dict:
    return {"path": path, "productId": product_id, "resultsHeading": None, "shownProductIds": []}


def chat(call, message: str, page_ctx: dict, history: list | None = None) -> str:
    status, body = call("POST", "/api/chat", {"message": message, "history": history or [], "page": page_ctx})
    return body.get("reply", f"<HTTP {status}: {body}>")


def rows_for(user_id: int) -> list[sqlite3.Row]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT role, content FROM chat_messages WHERE user_id = ? ORDER BY id", (user_id,)
    ).fetchall()
    conn.close()
    return rows


def total_rows() -> int:
    conn = sqlite3.connect(DB_PATH)
    n = conn.execute("SELECT COUNT(*) FROM chat_messages").fetchone()[0]
    conn.close()
    return n


def main() -> None:
    print(f"Testing against {BASE}\n")

    # --- A brand-new customer ---
    email = f"memory.test.{secrets.token_hex(3)}@campuscustoms.yale.edu"
    password = secrets.token_urlsafe(16)
    a, _ = client()
    a("POST", "/api/auth/register", {"first_name": "Morgan", "last_name": "Memory", "email": email, "password": password})
    a("POST", "/api/auth/verify-email", {"token": latest_token_for(email)})
    status, body = a("POST", "/api/auth/login", {"email": email, "password": password})
    user_id = body["user"]["id"]
    check(status == 200, f"new customer logged in ({email})")

    status, body = a("GET", "/api/chat/history")
    check(status == 200 and body["messages"] == [], "new customer starts with empty history")

    # --- The agent knows who it's talking to (name + email) ---
    reply = chat(a, "Who am I logged in as? Tell me my name and my account email.", page("/"))
    check("morgan" in reply.lower() and email in reply.lower(), "agent knows the customer's name and email", reply)

    # --- Page context: "this" = the product on screen ---
    reply = chat(a, "Do you have this in red?", page("/products/basic-hoodie-big-yale", "basic-hoodie-big-yale"))
    check(
        "basic hoodie big yale" in reply.lower() and "navy" in reply.lower(),
        "on a product page, 'this' means that product (Basic Hoodie: navy/white, no red)",
        reply,
    )
    reply = chat(a, "Is it available in a medium?", page("/products/morse-logo-t-shirt", "morse-logo-t-shirt"))
    check("morse" in reply.lower(), "page context follows the customer to a new product page", reply)

    reply = chat(a, "Heads up: I'm shopping for my roommate, who wears a size XL.", page("/"))
    check(bool(reply), "customer shares a detail to remember")

    # --- Saved in chat_messages under this user ---
    rows = rows_for(user_id)
    check(len(rows) == 8, "4 exchanges saved as 8 rows (user + assistant) under this user_id", f"{len(rows)} rows")
    check([r["role"] for r in rows] == ["user", "assistant"] * 4, "rows alternate user/assistant in order")

    # --- They come back later: new login session, widget sends no history ---
    b, _ = client()
    b("POST", "/api/auth/login", {"email": email, "password": password})
    status, body = b("GET", "/api/chat/history")
    msgs = body.get("messages", [])
    check(status == 200 and len(msgs) == 8, "history is returned when the customer comes back", f"{len(msgs)} messages")
    check(
        any("roommate" in m["content"] for m in msgs if m["role"] == "user"),
        "returned history contains what they said last time",
    )
    check(
        any(m["products"] for m in msgs if m["role"] == "assistant"),
        "returned history rebuilds the product cards that were shown",
    )
    reply = chat(b, "What size did I tell you my roommate wears?", page("/"), history=[])
    check("xl" in reply.lower(), "agent remembers from saved history (not from the browser)", reply)

    # --- Another customer can't see it ---
    c, _ = client()
    c("POST", "/api/auth/login", {"email": SEED_EMAIL, "password": SEED_PASSWORD})
    status, body = c("GET", "/api/chat/history")
    check(
        status == 200 and not any("roommate" in m["content"] for m in body["messages"]),
        "another customer's history doesn't include this customer's chat",
    )

    # --- Guests: chat works, nothing saved ---
    g, _ = client()
    before = total_rows()
    reply = chat(g, "Does this come in a different color?", page("/products/morse-logo-t-shirt", "morse-logo-t-shirt"))
    check("morse" in reply.lower() and "gray" in reply.lower(), "guest: page context works", reply)
    reply = chat(
        g,
        "What colors does it come in?",
        page("/"),
        history=[
            {"role": "user", "content": "Tell me about the Benjamin Franklin 1 4 Zip"},
            {"role": "assistant", "content": "The Benjamin Franklin 1 4 Zip is a quarter-zip pullover for $72."},
        ],
    )
    check("heather gray" in reply.lower() and "blue" in reply.lower(),
          "guest: follow-ups work from the browser's history (1/4 zip colors)", reply)
    check(total_rows() == before, "guest chats are not saved")
    status, _ = g("GET", "/api/chat/history")
    check(status == 401, "guest has no history endpoint access")

    status, body = g("POST", "/api/chat", {"message": "Do you have this in blue?", "page": page("/products/fake", "not-a-real-product")})
    check(status == 200 and bool(body.get("reply")), "a fake product id in page context is ignored safely")

    passed = sum(ok for ok, _ in results)
    print(f"\n{passed}/{len(results)} memory checks passed")
    raise SystemExit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
