"""Campus Customs shop agent: PydanticAI wired to Portkey. main.py calls run_chat().

PORTKEY_API_KEY and OPENAI_MODEL come from a .env file. These are loaded in
order, with later files winning: the course folder, Homework 4, then backend/.

Each chat turn: the website's message (plus recent history) goes to the agent,
which calls the read-only tools in tools.py and returns an AgentReply. run_chat()
also hands back the agent's most recent search_products result, so main.py can
put every match on the page.
"""

import asyncio
import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import UsageLimits

import tools
from models import (
    AgentReply,
    ChatTurn,
    CurrentPage,
    CustomerProfile,
    ProductInfo,
    ProductSearchResult,
    ShopOverview,
    StockResult,
    ToolError,
)

HERE = Path(__file__).resolve().parent

for env_file in (HERE.parent.parent / ".env", HERE.parent / ".env", HERE / ".env"):
    if env_file.is_file():
        load_dotenv(env_file, override=True)

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
MODEL_NAME = os.getenv("OPENAI_MODEL") or "gpt-5.6-astra"
SYSTEM_PROMPT = (HERE / "prompts" / "prompt.md").read_text()

# ---------- Run limits (see output/harness.md "Specs") ----------
# A normal turn is 1-3 model requests at ~4.3k input tokens each (~95% cached) and
# ~100 output tokens. These stop a turn well before it gets expensive.
USAGE_LIMITS = UsageLimits(request_limit=5, tool_calls_limit=5, total_tokens_limit=24_000)
OUTPUT_RETRIES = 2  # replies that fail the accuracy/safety checks get 2 rewrites, then the fallback
TOOL_RETRIES = 1  # a tool called with bad arguments gets 1 more try
MODEL_SETTINGS = ModelSettings(max_tokens=800)  # replies are ~100 tokens; caps runaway output
TURN_TIMEOUT_SECONDS = 45


@dataclass
class ChatDeps:
    """Per-request context: who is chatting (None = guest) and what page they're on."""

    customer: CustomerProfile | None = None
    page: CurrentPage | None = None


@dataclass
class ChatOutcome:
    reply: AgentReply
    last_search: ProductSearchResult | None  # most recent search_products result this turn
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


agent = Agent(
    deps_type=ChatDeps,
    output_type=AgentReply,
    instructions=SYSTEM_PROMPT,
    retries=OUTPUT_RETRIES,
    model_settings=MODEL_SETTINGS,
)


@agent.instructions
def who_is_chatting(ctx: RunContext[ChatDeps]) -> str:
    c = ctx.deps.customer
    if c:
        return (
            f"The customer is logged in as {c.first_name} {c.last_name} ({c.email}). "
            "Earlier messages in this conversation are their saved chat history, possibly from previous visits."
        )
    return "The customer is browsing as a guest (not logged in). Guest chats are not saved."


@agent.instructions
def current_page(ctx: RunContext[ChatDeps]) -> str:
    page = ctx.deps.page
    if page is None:
        return "The customer's current page is unknown."
    if page.kind == "product" and page.product:
        p = page.product
        return (
            f"The customer is viewing the product page for {p.name} (product_id: {p.product_id}). "
            "When they say 'this', 'it', 'this one', or 'the shown product' without naming another "
            "item, they mean this product. Use this product_id with your tools."
        )
    if page.kind == "search_results":
        names = ", ".join(f"{i}. {p.name} ({p.product_id})" for i, p in enumerate(page.shown_products[:30], 1))
        return (
            f"The customer is viewing chat search results titled '{page.results_heading}' "
            f"showing {len(page.shown_products)} products: {names}. "
            "'The first one', 'the second one', etc. refer to this order."
        )
    labels = {"catalogue": "the full product catalogue", "home": "the home page", "other": f"the page {page.path}"}
    return f"The customer is viewing {labels.get(page.kind, page.path)}."


@agent.tool(retries=TOOL_RETRIES)
def get_customer_profile(ctx: RunContext[ChatDeps]) -> CustomerProfile | ToolError:
    """Get the logged-in customer's name and email on their account (only theirs)."""
    if ctx.deps.customer is None:
        return ToolError(error="The customer is a guest (not logged in).", hint="Offer that they can log in or create an account.")
    return ctx.deps.customer


@agent.tool(retries=TOOL_RETRIES)
def get_current_page(ctx: RunContext[ChatDeps]) -> CurrentPage | ToolError:
    """Get what the customer is looking at on the website right now (product page, search results, etc.)."""
    if ctx.deps.page is None:
        return ToolError(error="The current page is unknown.", hint="Ask which product they mean.")
    return ctx.deps.page


agent.tool_plain(tools.search_products, retries=TOOL_RETRIES)
agent.tool_plain(tools.get_product_info, retries=TOOL_RETRIES)
agent.tool_plain(tools.check_stock, retries=TOOL_RETRIES)
agent.tool_plain(tools.get_shop_overview, retries=TOOL_RETRIES)


# ---------- Accuracy and safety checks on every reply ----------
PRICE_RE = re.compile(r"\$\s?(\d+(?:\.\d{1,2})?)")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
CARD_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
# Words Dan never uses, even when chirping Harvard: profanity and put-downs.
# Whole words only, so "class" or "Shell" never trip it.
RUDE_RE = re.compile(
    r"\b(?:fuck\w*|shit\w*|bitch\w*|bastard\w*|ass|asses|asshole\w*|damn\w*|hell|crap\w*|piss\w*|"
    r"dick\w*|suck|sucks|sucked|loser|losers|stupid|idiot\w*|dumb\w*|moron\w*|pathetic|trash|garbage|"
    r"shut up|scum|ugly|hate)\b",
    re.IGNORECASE,
)
# Internal names that should never appear in a customer-facing reply.
INTERNAL_TERMS = ("product_ids", "show_on_page", "page_heading", "customer_message", "system prompt", "golden rule", "toolerror")


def tool_results(messages: list[ModelMessage]) -> list[object]:
    """Every object a tool returned during this run (history holds text only, no tool parts)."""
    return [
        part.content
        for message in messages
        for part in message.parts
        if isinstance(part, ToolReturnPart)
    ]


def safety_problems(reply: str, customer: CustomerProfile | None) -> list[str]:
    """Things that must never reach a customer, whatever the model was asked."""
    problems = []
    own_email = customer.email.lower() if customer else None
    for email in EMAIL_RE.findall(reply):
        if email.lower() != own_email:
            problems.append(f"it contains an email address ({email}) that isn't this customer's own")
    if CARD_RE.search(reply):
        problems.append("it contains a card-like number")
    rude = RUDE_RE.search(reply)
    if rude:
        problems.append(f"it uses rude or crude language ('{rude.group(0)}'); keep chirps clean and friendly")
    lowered = reply.lower()
    for term in INTERNAL_TERMS:
        if term in lowered:
            problems.append(f"it mentions the internal term '{term}'")
    return problems


@agent.output_validator
def check_reply(ctx: RunContext[ChatDeps], output: AgentReply) -> AgentReply:
    """Reject replies that aren't backed by this turn's tool results or aren't safe; the model retries."""
    unknown = set(output.product_ids) - tools.existing_product_ids(output.product_ids)
    if unknown:
        raise ModelRetry(
            f"These product_ids don't exist: {sorted(unknown)}. "
            "Use only ids returned by search_products or get_product_info."
        )

    results = tool_results(ctx.messages)

    # Accuracy: every $ amount must come from a tool this turn (or be the customer's own number).
    known_prices = set()
    for r in results:
        if isinstance(r, ProductInfo):
            known_prices.add(r.price)
        elif isinstance(r, ProductSearchResult):
            known_prices.update(h.price for h in r.products)
        elif isinstance(r, ShopOverview):
            known_prices.update(v for c in r.categories for v in (c.min_price, c.max_price))
    customer_amounts = {float(a) for a in PRICE_RE.findall(str(ctx.prompt or ""))}
    stated = {float(a) for a in PRICE_RE.findall(output.reply)}
    unbacked = stated - known_prices - customer_amounts
    if unbacked:
        raise ModelRetry(
            f"Your reply states {', '.join(f'${a:g}' for a in sorted(unbacked))}, but no tool returned that "
            "price this turn. Look it up with get_product_info (or search_products), or remove it."
        )

    # Accuracy: out-of-stock answers use the exact required sentence.
    stock_checks = [r for r in results if isinstance(r, StockResult)]
    if stock_checks and all(r.customer_message for r in stock_checks):
        if output.reply.strip() != tools.OUT_OF_STOCK_MESSAGE:
            raise ModelRetry(f'The item is out of stock. Your reply must be exactly: "{tools.OUT_OF_STOCK_MESSAGE}"')
        output.sorry = True

    # Safety.
    problems = safety_problems(output.reply, ctx.deps.customer)
    if problems:
        raise ModelRetry("Rewrite your reply: " + "; ".join(problems) + ".")

    # Tidy suggestions: short, unique, and nothing sensitive.
    tidy: list[str] = []
    for s in output.suggestions:
        s = " ".join(s.split())
        if 0 < len(s) <= 60 and s.lower() not in {t.lower() for t in tidy} and not safety_problems(s, None):
            tidy.append(s)
    output.suggestions = tidy[:3]
    return output


_model: OpenAIResponsesModel | None = None


def get_model() -> OpenAIResponsesModel:
    """Build the Portkey-backed model once, on first use, and reuse it."""
    global _model
    if _model is None:
        api_key = os.environ.get("PORTKEY_API_KEY")
        if not api_key:
            raise RuntimeError("PORTKEY_API_KEY is not set. Add it to the course .env file.")
        client = AsyncOpenAI(
            base_url=PORTKEY_BASE_URL,
            api_key=api_key,
            default_headers={"x-portkey-api-key": api_key},
        )
        _model = OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
    return _model


def to_message_history(history: list[ChatTurn]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for turn in history:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


def last_search_result(messages: list[ModelMessage]) -> ProductSearchResult | None:
    """The actual object search_products returned most recently (tool returns keep the Python object)."""
    for message in reversed(messages):
        for part in reversed(message.parts):
            if (
                isinstance(part, ToolReturnPart)
                and part.tool_name == "search_products"
                and isinstance(part.content, ProductSearchResult)
            ):
                return part.content
    return None


async def run_chat(
    message: str,
    history: list[ChatTurn],
    customer: CustomerProfile | None = None,
    page: CurrentPage | None = None,
) -> ChatOutcome:
    result = await asyncio.wait_for(
        agent.run(
            message,
            deps=ChatDeps(customer=customer, page=page),
            message_history=to_message_history(history),
            model=get_model(),
            usage_limits=USAGE_LIMITS,
        ),
        timeout=TURN_TIMEOUT_SECONDS,
    )
    usage = result.usage
    return ChatOutcome(
        reply=result.output,
        last_search=last_search_result(result.new_messages()),
        requests=usage.requests,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
    )
