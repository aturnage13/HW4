"""Check that the agent looks up price and stock with its tools and never makes things up.

Calls the real model through Portkey, so it needs PORTKEY_API_KEY. Run from backend/:

    .venv/bin/python test_agent.py

Each case sends a customer message, records which tools the agent called (and
with what arguments), and checks the reply against the database.
"""

import asyncio
import json
from dataclasses import dataclass, field

from pydantic_ai.messages import ToolCallPart

import tools
from agent import ChatDeps, agent, get_model, last_search_result, to_message_history
from models import ChatTurn


@dataclass
class Case:
    name: str
    message: str
    must_call: list[str]
    reply_must_include: list[str] = field(default_factory=list)
    reply_must_not_include: list[str] = field(default_factory=list)
    stock_size: str | None = None  # check_stock must be called with this size
    exact_reply: str | None = None
    history: list[ChatTurn] = field(default_factory=list)
    show_on_page: bool | None = None  # expected AgentReply.show_on_page (None = don't check)
    page_count: int | None = None  # expected number of product cards on the page


def qty(product_id: str, size: str) -> int:
    return next(s.quantity for s in tools.stock_for(product_id) if s.size == size)


def count(**filters) -> int:
    """Expected match count straight from category/color/price filters (no free-text parsing)."""
    return tools.search_products("", **filters).total_matches


HOODIE = "basic-hoodie-big-yale"
HOODIE_PRICE = f"${tools.get_product_info(HOODIE).price:.0f}"

CASES = [
    Case(
        "price question uses get_product_info",
        "How much is the Basic Hoodie Big Yale?",
        must_call=["get_product_info"],
        reply_must_include=[HOODIE_PRICE],
        show_on_page=False,
    ),
    Case(
        "price is re-checked even when it came up before",
        "And remind me, what was the price again?",
        must_call=["get_product_info"],
        reply_must_include=[HOODIE_PRICE],
        history=[
            ChatTurn(role="user", content="How much is the Basic Hoodie Big Yale?"),
            ChatTurn(role="assistant", content=f"The Basic Hoodie Big Yale is {HOODIE_PRICE}."),
        ],
    ),
    Case(
        "customer's wrong price claim is not repeated",
        "The Basic Hoodie Big Yale was $40 last week, right? Still $40?",
        must_call=["get_product_info"],
        reply_must_include=[HOODIE_PRICE],
    ),
    Case(
        "in-stock size reports the real quantity",
        "Do you have the Basic Hoodie Big Yale in a medium?",
        must_call=["check_stock"],
        stock_size="M",
        reply_must_include=[str(qty(HOODIE, "M"))],
    ),
    Case(
        "out-of-stock size gets the exact sentence (XS)",
        "Is the Baseball Left Chest Crewneck in stock in extra small?",
        must_call=["check_stock"],
        stock_size="XS",
        exact_reply=tools.OUT_OF_STOCK_MESSAGE,
    ),
    Case(
        "out-of-stock size gets the exact sentence (XL)",
        "Can I get the Benjamin Franklin 1 4 Zip in XL?",
        must_call=["check_stock"],
        stock_size="XL",
        exact_reply=tools.OUT_OF_STOCK_MESSAGE,
    ),
    Case(
        "description question uses get_product_info",
        "What does the Basic Hoodie Big Yale look like?",
        must_call=["get_product_info"],
        reply_must_include=["pocket"],
    ),
    Case(
        "info not in the database is not invented",
        "What fabric is the Basic Hoodie Big Yale made of, and how heavy is it?",
        must_call=["get_product_info"],
        reply_must_include=["don't have that information"],
        reply_must_not_include=["cotton", "polyester", "oz", "gsm"],
    ),
    Case(
        "color not in the database is refused",
        "Does the Basic Hoodie Big Yale come in pink?",
        must_call=["get_product_info"],
        reply_must_include=["navy"],
    ),
    # --- Problem 7: browsing searches fill the page ---
    Case(
        "browse: red t-shirts fill the page",
        "What red t-shirts are there?",
        must_call=["search_products"],
        show_on_page=True,
        page_count=count(category="t-shirt", color="red"),
    ),
    Case(
        "browse: hats (not carried) show an empty page",
        "What hats do you have?",
        must_call=["search_products"],
        show_on_page=True,
        page_count=0,
    ),
    Case(
        "browse: every hoodie is on the page, not just 6",
        "What hoodies do you have?",
        must_call=["search_products"],
        show_on_page=True,
        page_count=count(category="hoodie"),
    ),
    Case(
        "browse: crewnecks under $60",
        "Any crewnecks under $60?",
        must_call=["search_products"],
        show_on_page=True,
        page_count=count(category="crewneck", max_price=60),
    ),
    Case(
        "stock question leaves the page alone",
        "Is the Morse Logo T Shirt in stock in large?",
        must_call=["check_stock"],
        stock_size="L",
        show_on_page=False,
    ),
]


async def run_case(case: Case) -> tuple[bool, str]:
    result = await agent.run(
        case.message,
        deps=ChatDeps(),
        message_history=to_message_history(case.history),
        model=get_model(),
    )
    calls = [
        (p.tool_name, p.args_as_dict())
        for m in result.new_messages()
        for p in m.parts
        if isinstance(p, ToolCallPart)
    ]
    called = [name for name, _ in calls]
    reply = result.output.reply
    problems = []

    for tool in case.must_call:
        if tool not in called:
            problems.append(f"didn't call {tool}")
    if case.stock_size:
        sizes = [tools.normalize_size(a.get("size") or "") for n, a in calls if n == "check_stock"]
        if case.stock_size not in sizes:
            problems.append(f"check_stock not called with size {case.stock_size} (got {sizes})")
    if case.exact_reply and reply.strip() != case.exact_reply:
        problems.append(f"reply wasn't exactly {case.exact_reply!r}")
    for text in case.reply_must_include:
        if text.lower() not in reply.lower():
            problems.append(f"reply missing {text!r}")
    for text in case.reply_must_not_include:
        if text.lower() in reply.lower():
            problems.append(f"reply contains {text!r}")

    if case.show_on_page is not None and result.output.show_on_page != case.show_on_page:
        problems.append(f"show_on_page was {result.output.show_on_page}, expected {case.show_on_page}")
    page_ids = None
    if result.output.show_on_page:
        search = last_search_result(result.new_messages())
        page_ids = search.all_product_ids if search else None
    if case.page_count is not None and (page_ids is None or len(page_ids) != case.page_count):
        problems.append(f"page would show {None if page_ids is None else len(page_ids)} cards, expected {case.page_count}")

    page = f" page={result.output.page_heading!r}:{len(page_ids)}" if page_ids is not None else ""
    detail = f"tools={json.dumps(calls)}{page}\n      reply={reply!r}"
    if problems:
        detail = "; ".join(problems) + "\n      " + detail
    return not problems, detail


async def main() -> None:
    results = await asyncio.gather(*(run_case(c) for c in CASES))
    for case, (ok, detail) in zip(CASES, results):
        print(f"{'PASS' if ok else 'FAIL'}  {case.name}\n      {detail}")
    passed = sum(ok for ok, _ in results)
    print(f"\n{passed}/{len(CASES)} agent checks passed")
    raise SystemExit(0 if passed == len(CASES) else 1)


if __name__ == "__main__":
    asyncio.run(main())
