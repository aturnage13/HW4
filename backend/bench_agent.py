"""Measure what typical chat questions cost: model round trips, tokens, and time.

Calls the real model. Run from backend/:  .venv/bin/python bench_agent.py [label]
"""

import asyncio
import json
import sys
import time

from pydantic_ai.messages import ToolCallPart

import tools
from agent import ChatDeps, agent, get_model
from models import CurrentPage

QUESTIONS = [
    ("price by name", "How much is the Basic Hoodie Big Yale?", None),
    ("stock by name + size", "Is the Morse Logo T Shirt in stock in a large?", None),
    ("on product page: color", "Do you have this in red?", "basic-hoodie-big-yale"),
    ("browse", "What red t-shirts are there?", None),
    ("not carried", "Do you sell hats?", None),
]


def page_for(product_id: str | None) -> CurrentPage | None:
    if not product_id:
        return None
    return CurrentPage(kind="product", path=f"/products/{product_id}", product=tools.product_cards([product_id])[0])


async def run_one(label: str, message: str, product_id: str | None) -> dict:
    start = time.perf_counter()
    result = await agent.run(message, deps=ChatDeps(page=page_for(product_id)), model=get_model())
    elapsed = time.perf_counter() - start
    usage = result.usage
    tool_calls = [
        p.tool_name
        for m in result.new_messages()
        for p in m.parts
        if isinstance(p, ToolCallPart) and p.tool_name != "final_result"
    ]
    return {
        "label": label,
        "seconds": round(elapsed, 1),
        "model_requests": usage.requests,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "tools": tool_calls,
        "reply": result.output.reply,
    }


async def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    rows = []
    for q in QUESTIONS:  # sequential so timings don't interfere
        rows.append(await run_one(*q))
    print(f"== {label} ==")
    for r in rows:
        print(
            f"{r['label']:24} {r['seconds']:5}s  requests={r['model_requests']}  "
            f"in={r['input_tokens']:6}  out={r['output_tokens']:5}  tools={r['tools']}"
        )
        print(f"{'':24} reply: {r['reply'][:150]!r}")
    tot = {k: sum(r[k] for r in rows) for k in ("seconds", "model_requests", "input_tokens", "output_tokens")}
    print(f"{'TOTAL':24} {round(tot['seconds'], 1):5}s  requests={tot['model_requests']}  "
          f"in={tot['input_tokens']:6}  out={tot['output_tokens']:5}")
    with open(f"bench_{label}.json", "w") as f:
        json.dump(rows, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
