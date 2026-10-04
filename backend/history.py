"""Customer chat memory: saving and loading logged-in shoppers' chats in chat_messages.

Guests are never saved. For a logged-in customer, each exchange becomes two rows
(role='user', then role='assistant' with the cards shown in products_json), keyed
by users.id. Their saved turns are the agent's memory the next time they chat.
"""

import json
import re

import tools
from db import get_connection
from models import ChatTurn, HistoryMessage, ProductCard

AGENT_MEMORY_MESSAGES = 12  # most recent saved messages (~6 exchanges) the agent gets as context
WIDGET_HISTORY_MESSAGES = 50  # most recent saved messages shown in the chat widget

# 13-19 digits, optionally split by spaces/dashes: looks like a payment card.
CARD_NUMBER_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")


def redact(text: str) -> str:
    """Keep card-like numbers out of saved chat history."""
    return CARD_NUMBER_RE.sub("[redacted number]", text)


def _recent_rows(user_id: int, limit: int):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json, created_at FROM chat_messages "
            "WHERE user_id = ? AND role IN ('user', 'assistant') ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return list(reversed(rows))  # oldest first


def _card_ids(products_json: str | None) -> list[str]:
    """Product ids from a saved products_json (seed rows use product_id, newer rows productId)."""
    if not products_json:
        return []
    try:
        items = json.loads(products_json)
    except json.JSONDecodeError:
        return []
    return [i.get("productId") or i.get("product_id") for i in items if isinstance(i, dict)]


def load_agent_memory(user_id: int) -> list[ChatTurn]:
    """The customer's recent saved turns, oldest first, as the agent's message history."""
    rows = _recent_rows(user_id, AGENT_MEMORY_MESSAGES)
    # History must start with a customer message.
    while rows and rows[0]["role"] != "user":
        rows.pop(0)
    return [ChatTurn(role=r["role"], content=r["content"]) for r in rows]


def load_widget_history(user_id: int) -> list[HistoryMessage]:
    """The customer's recent saved messages for the chat widget, with cards rebuilt from the catalogue."""
    return [
        HistoryMessage(
            role=r["role"],
            content=r["content"],
            products=tools.product_cards([i for i in _card_ids(r["products_json"]) if i]),
            created_at=r["created_at"],
        )
        for r in _recent_rows(user_id, WIDGET_HISTORY_MESSAGES)
    ]


def save_exchange(user_id: int, message: str, reply: str, cards: list[ProductCard]) -> None:
    cards_json = json.dumps([c.model_dump(by_alias=True) for c in cards])
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)",
            (user_id, redact(message)),
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) "
            "VALUES (?, 'assistant', ?, ?)",
            (user_id, redact(reply), cards_json),
        )
