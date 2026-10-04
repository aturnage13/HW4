"""Campus Customs API: products, product images, auth, and the shop chatbot.

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000
"""

import asyncio
import json
import logging
import sqlite3
from contextlib import asynccontextmanager

from fastapi import Cookie, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic_ai import capture_run_messages
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded

import app_check
import audit
import history
import tools
from agent import run_chat, safety_problems
from auth import router as auth_router
from auth import session_user
from db import ROOT, get_connection, init_db
from models import ChatHistory, ChatRequest, ChatResponse, CustomerProfile, PageResults, SizeStock

IMAGES_DIR = ROOT / "data" / "products"
log = logging.getLogger("campus_customs")

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Campus Customs API", lifespan=lifespan)

# Allow the Vite dev server to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(auth_router)
app.include_router(app_check.router)  # dev-only 📸 Snap requests

# image_file_path in the database is "products/<file>.jpg", so mounting the
# image folder at /products makes each stored path a working URL.
app.mount("/products", StaticFiles(directory=IMAGES_DIR), name="images")


def row_to_product(row: sqlite3.Row) -> dict:
    return {
        "productId": row["product_id"],
        "name": row["name"],
        "garmentType": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "searchTags": json.loads(row["search_tags"]),
        "imageFilePath": row["image_file_path"],
        "imageUrl": f"/{row['image_file_path']}",
        "price": row["price"],
    }


PRODUCT_COLUMNS = (
    "product_id, name, garment_type, description, colors, "
    "search_tags, image_file_path, price"
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/products")
def list_products() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT {PRODUCT_COLUMNS} FROM catalogue ORDER BY name"
        ).fetchall()
    return [row_to_product(r) for r in rows]


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {PRODUCT_COLUMNS} FROM catalogue WHERE product_id = ?",
            (product_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return row_to_product(row)


@app.get("/api/products/{product_id}/stock", response_model=list[SizeStock])
def get_product_stock(product_id: str) -> list[SizeStock]:
    stock = tools.stock_for(product_id)
    if stock is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return stock


def page_results(outcome) -> PageResults | None:
    """Turn the agent's last catalogue search into product cards for the main page.

    Only when the agent asked for it (show_on_page) and actually searched. Cards are
    built from the database for every match, not just the few the model saw.
    """
    search = outcome.last_search
    if not outcome.reply.show_on_page or search is None:
        return None
    return PageResults(
        heading=outcome.reply.page_heading.strip() or "Search Results",
        total_matches=search.total_matches,
        products=tools.product_cards(search.all_product_ids),
        note=search.note,
    )


def customer_profile(user) -> CustomerProfile:
    """Only these account fields reach the agent (never the password hash or user id)."""
    return CustomerProfile(
        first_name=user["first_name"] or "",
        last_name=user["last_name"] or "",
        email=user["email"],
    )


CARD_WARNING = (
    "Whoa, hold on! For your safety, please don't share card numbers in chat. "
    "I can't take payments or place orders, but I'm happy to help you find the perfect gear!"
)
OFF_LIMITS_REPLY = (
    "Ruff, that's not something I can help with! I'm all about Campus Customs gear, "
    "so ask me about hoodies, tees, sizes, or what's in stock."
)
RETRY_FALLBACK = (
    "Ruff, I couldn't get that answer quite right. Could you ask me again, maybe naming the product?"
)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, cc_session: str | None = Cookie(default=None)) -> ChatResponse:
    """Send one message from the website's chat widget to the agent and return its reply.

    Logged in: the agent's memory is the customer's saved history from chat_messages,
    and this exchange is saved. Guest: memory is the history the widget sends; nothing is saved.
    """
    user = session_user(cc_session)
    customer = customer_profile(user) if user else None
    run_id = audit.new_run_id()
    started_at = audit.now()
    run_messages: list = []
    outcome = None
    stop_reason = "error"
    response = None

    try:
        # Safety + cost: a pasted card number never goes to the model at all.
        if history.CARD_NUMBER_RE.search(body.message):
            stop_reason = "card_number_blocked_before_model"
            response = ChatResponse(reply=CARD_WARNING, suggestions=["Show me hoodies", "What's in my size?"])
        else:
            memory = history.load_agent_memory(user["id"]) if user else body.history
            with capture_run_messages() as run_messages:
                try:
                    outcome = await run_chat(body.message, memory, customer=customer, page=tools.resolve_page(body.page))
                    output = outcome.reply
                    page = page_results(outcome)
                    response = ChatResponse(
                        reply=output.reply,
                        products=tools.product_cards(output.product_ids),
                        page=page,
                        suggestions=output.suggestions,
                        sorry=output.sorry or (page is not None and page.total_matches == 0),
                    )
                    stop_reason = "final_result"
                except ModelHTTPError as err:
                    # The model provider's own safety filter blocked the message (e.g. a jailbreak attempt).
                    if "content_filter" not in str(err.body):
                        log.exception("Chat model request failed")
                        stop_reason = f"error: model HTTP {err.status_code}"
                        raise HTTPException(
                            status_code=502,
                            detail="Our assistant is having trouble right now. Please try again in a moment.",
                        )
                    log.warning("Provider content filter blocked a chat message")
                    stop_reason = "provider_content_filter"
                    response = ChatResponse(reply=OFF_LIMITS_REPLY, suggestions=["Show me hoodies", "What t-shirts do you have?"])
                except asyncio.TimeoutError:
                    log.warning("Chat agent timed out")
                    stop_reason = "timeout"
                    response = ChatResponse(reply=RETRY_FALLBACK, sorry=True)
                except UsageLimitExceeded:
                    log.warning("Chat agent hit its usage limit", exc_info=True)
                    stop_reason = "usage_limit_exceeded"
                    response = ChatResponse(reply=RETRY_FALLBACK, sorry=True)
                except UnexpectedModelBehavior:
                    # The model kept failing the accuracy/safety checks: say so, don't guess.
                    log.warning("Chat agent gave up on a reply", exc_info=True)
                    stop_reason = "gave_up_after_failed_checks"
                    response = ChatResponse(reply=RETRY_FALLBACK, sorry=True)
                except HTTPException:
                    raise
                except Exception as err:
                    log.exception("Chat agent failed")
                    stop_reason = f"error: {type(err).__name__}"
                    raise HTTPException(
                        status_code=502,
                        detail="Our assistant is having trouble right now. Please try again in a moment.",
                    )

        # Last line of defense: nothing unsafe leaves the server, even if a check above missed it.
        if safety_problems(response.reply, customer):
            log.warning("Blocked an unsafe reply")
            stop_reason = "unsafe_reply_blocked"
            response = ChatResponse(reply=RETRY_FALLBACK, sorry=True)

        if user:
            history.save_exchange(user["id"], body.message, response.reply, response.products)
        return response
    finally:
        # Append-only audit trail of this turn (output/audit_trail.json), whatever happened.
        try:
            audit.append(audit.turn_events(
                run_id,
                started_at=started_at,
                who="logged-in customer" if user else "guest",
                page=(body.page.path if body.page else "unknown"),
                message=body.message,
                messages=list(run_messages),
                stop_reason=stop_reason,
                reply=response.reply if response else "(no reply sent)",
                requests=outcome.requests if outcome else None,
                input_tokens=outcome.input_tokens if outcome else None,
                output_tokens=outcome.output_tokens if outcome else None,
            ))
        except Exception:
            log.exception("Could not write the audit trail")


@app.get("/api/chat/history", response_model=ChatHistory)
def chat_history(cc_session: str | None = Cookie(default=None)) -> ChatHistory:
    """The logged-in customer's saved chat, for the widget to show when they come back."""
    user = session_user(cc_session)
    if user is None:
        raise HTTPException(status_code=401, detail="Log in to see your chat history.")
    return ChatHistory(messages=history.load_widget_history(user["id"]))
