"""Append-only audit trail of agent-loop activity: output/audit_trail.json.

The file is one JSON array that only ever grows. New events are written over the
closing "]" (never rewriting earlier entries), under a file lock so the API and
test scripts can log at the same time. It is never wiped between runs.

Each chat turn adds:
  run_start   who (guest / logged-in customer), page, the message (short, redacted)
  tool_call   tool name + short arguments
  tool_result tool name + short summary of what it returned
  retry       why a reply was sent back to the model (accuracy/safety checks)
  run_end     stop reason, model requests, tokens, the reply (short, redacted)
"""

import fcntl
import json
import re
import uuid
from datetime import datetime, timezone

from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    RetryPromptPart,
    ToolCallPart,
    ToolReturnPart,
)

from db import ROOT
from models import (
    CurrentPage,
    CustomerProfile,
    ProductInfo,
    ProductSearchResult,
    ShopOverview,
    StockResult,
    ToolError,
)

AUDIT_FILE = ROOT / "output" / "audit_trail.json"
SHORT = 160

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
CARD_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")


def new_run_id() -> str:
    return uuid.uuid4().hex[:8]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def short(value: object, limit: int = SHORT) -> str:
    """Compact, privacy-safe text: no emails or card numbers, trimmed to `limit`."""
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    text = CARD_RE.sub("[card]", EMAIL_RE.sub("[email]", " ".join(text.split())))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def summarize_result(content: object) -> str:
    """One-line summary of a tool's return value."""
    if isinstance(content, ProductSearchResult):
        top = ", ".join(p.name for p in content.products[:3])
        return f"{content.total_matches} matches" + (f": {top}" if top else f" ({content.note})")
    if isinstance(content, ProductInfo):
        return f"{content.name}: ${content.price:g}, colors {', '.join(content.colors) or 'none listed'}"
    if isinstance(content, StockResult):
        sizes = ", ".join(f"{s.size}={s.quantity}" for s in content.sizes)
        return f"{content.name}: {sizes}" + (f" -> '{content.customer_message}'" if content.customer_message else "")
    if isinstance(content, ShopOverview):
        return f"{content.total_products} products in {len(content.categories)} categories"
    if isinstance(content, CustomerProfile):
        return "logged-in customer profile (name + email, not logged here)"
    if isinstance(content, CurrentPage):
        return f"page {content.kind}" + (f": {content.product.name}" if content.product else "")
    if isinstance(content, ToolError):
        return f"error: {content.error}"
    return short(content)


def append(events: list[dict]) -> None:
    """Append events to the JSON array without touching existing entries."""
    if not events:
        return
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    body = ",\n".join("  " + json.dumps(e, ensure_ascii=False) for e in events)
    with open(AUDIT_FILE, "a+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0, 2)
            if f.tell() == 0:
                f.write(("[\n" + body + "\n]\n").encode())
                return
            # Step back over the closing "]" (and trailing whitespace), then continue the array.
            pos = f.tell()
            while pos > 0:
                pos -= 1
                f.seek(pos)
                ch = f.read(1)
                if ch not in b" \n\r\t":
                    break
            if ch != b"]":
                raise ValueError(f"{AUDIT_FILE} is not a JSON array; refusing to modify it")
            f.seek(pos)
            f.truncate()
            empty = pos <= 2  # file was "[]"
            f.write((("\n" if empty else ",\n") + body + "\n]\n").encode())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def turn_events(
    run_id: str,
    *,
    started_at: str,
    who: str,
    page: str,
    message: str,
    messages: list[ModelMessage],
    stop_reason: str,
    reply: str,
    requests: int | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> list[dict]:
    """Build the audit events for one chat turn from the agent run's messages."""
    events = [{"time": started_at, "run": run_id, "event": "run_start", "who": who, "page": page, "message": short(message)}]
    for m in messages:
        stamp = m.timestamp.isoformat(timespec="seconds") if getattr(m, "timestamp", None) else now()
        for part in m.parts:
            if isinstance(part, ToolCallPart) and part.tool_name != "final_result":
                events.append({"time": stamp, "run": run_id, "event": "tool_call", "tool": part.tool_name,
                               "args": short(part.args_as_dict())})
            elif isinstance(part, ToolReturnPart) and part.tool_name != "final_result":
                events.append({"time": part.timestamp.isoformat(timespec="seconds"), "run": run_id,
                               "event": "tool_result", "tool": part.tool_name,
                               "result": short(summarize_result(part.content))})
            elif isinstance(part, RetryPromptPart):
                events.append({"time": part.timestamp.isoformat(timespec="seconds"), "run": run_id,
                               "event": "retry", "tool": part.tool_name or "final_result",
                               "reason": short(part.model_response() if callable(getattr(part, "model_response", None)) else part.content)})
        if isinstance(m, ModelResponse) and getattr(m, "finish_reason", None) == "length":
            events.append({"time": stamp, "run": run_id, "event": "retry", "reason": "model hit its output length limit"})
    end = {"time": now(), "run": run_id, "event": "run_end", "stop_reason": stop_reason, "reply": short(reply)}
    if requests is not None:
        end.update({"model_requests": requests, "input_tokens": input_tokens, "output_tokens": output_tokens})
    events.append(end)
    return events
