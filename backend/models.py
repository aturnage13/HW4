"""Pydantic / PydanticAI structured types for the Campus Customs chatbot.

- Tool results (what tools.py hands the agent): ProductSearchResult,
  ProductInfo, StockResult, ShopOverview, ToolError. ProductCard is both a
  search result and the card shown in the chat.
- Agent output (what the model must return): AgentReply.
- Agent deps (who is chatting and what page they're on): CustomerProfile,
  CurrentPage.
- API contract (what main.py's /api/chat accepts and returns): ChatRequest,
  PageContext, ChatResponse, ChatHistory. These serialize as camelCase for the
  React front end.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

StockStatus = Literal["in_stock", "low_stock", "out_of_stock"]
Category = Literal[
    "hoodie", "crewneck", "t-shirt", "quarter-zip", "jacket", "long-sleeve shirt", "sweatshirt", "other"
]


class CamelModel(BaseModel):
    """Base for anything sent to the front end: snake_case in Python, camelCase in JSON."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ---------- Tool results ----------
class ProductCard(CamelModel):
    """A compact product summary, used in search results and shown as a card in the chat."""

    product_id: str
    name: str
    category: Category
    price: float
    colors: list[str]
    short_description: str
    image_url: str = Field(description="Site path to the product photo, e.g. /products/<id>.jpg")
    url: str = Field(description="Site path to the product page, e.g. /products/<id>")


class SizeStock(CamelModel):
    size: str
    quantity: int
    status: StockStatus


class ProductHit(BaseModel):
    """One search match as the model sees it: just what's needed to choose and talk about it.

    (No image or page URLs: cards are built from the database by the server, so
    sending those to the model would only cost tokens.)
    """

    product_id: str
    name: str
    category: Category
    price: float
    colors: list[str]
    short_description: str


class ProductSearchResult(BaseModel):
    """Lookup result for search_products: which catalogue products match, with their ids."""

    total_matches: int = Field(description="How many products matched before the limit was applied.")
    products: list[ProductHit] = Field(description="Best matches first.")
    note: str = Field(default="", description="Set when nothing matched, with advice on what to try.")
    # Every match, best first. Not sent to the model (exclude=True); main.py reads it
    # from the tool result to fill the page with product cards.
    all_product_ids: list[str] = Field(default_factory=list, exclude=True)


class ProductInfo(BaseModel):
    """Lookup result for get_product_info: the facts a customer asks about, straight from catalogue."""

    product_id: str = Field(description="Catalogue id; put it in product_ids to show this product's card.")
    name: str = Field(description="Product name, so the agent can confirm it found the right item.")
    garment_type: str = Field(description="What kind of garment it is, e.g. 'pullover hoodie'.")
    description: str = Field(description="Full catalogue description. The only source for fit, design, or features.")
    price: float = Field(description="Price in US dollars, exactly as stored. Quote it as-is.")
    colors: list[str] = Field(description="Every color this product comes in. No other colors exist.")


class StockResult(BaseModel):
    """Lookup result for check_stock: quantity on hand for the size the customer asked about."""

    product_id: str
    name: str
    requested_size: str | None = Field(
        description="The size that was checked (XS, S, M, L, XL, XXL), or null if all sizes were checked."
    )
    sizes: list[SizeStock] = Field(description="Quantity and status for the requested size, or for every size.")
    in_stock: bool = Field(description="True if at least one unit is available for the size(s) checked.")
    customer_message: str | None = Field(
        default=None,
        description="If set, say exactly this to the customer (used for out-of-stock).",
    )
    note: str = "Stock is tracked by size only, not by color."


class ToolError(BaseModel):
    """Returned instead of a result when a lookup can't be answered from the database."""

    error: str = Field(description="What went wrong, e.g. unknown product_id or size.")
    hint: str = Field(description="What to do next, e.g. call search_products or ask which size.")


class CategorySummary(BaseModel):
    category: Category
    product_count: int
    min_price: float
    max_price: float


class ShopOverview(BaseModel):
    total_products: int
    sizes_offered: list[str]
    categories: list[CategorySummary]


# ---------- Agent deps ----------
class CustomerProfile(BaseModel):
    """The logged-in shopper, from the users table. The only customer fields the agent sees."""

    first_name: str = Field(description="Customer's first name, for greeting them.")
    last_name: str = Field(description="Customer's last name.")
    email: str = Field(description="Email on the account. Share it only with this customer, only if they ask.")


class CurrentPage(BaseModel):
    """What the shopper is looking at on the website right now, checked against the database."""

    kind: Literal["product", "search_results", "catalogue", "home", "other"]
    path: str
    product: ProductCard | None = Field(
        default=None, description="The product whose page they're on. 'This' / 'it' means this product."
    )
    results_heading: str | None = Field(default=None, description="Heading of chat search results on the page.")
    shown_products: list[ProductCard] = Field(
        default_factory=list, description="Products currently shown as cards on the page, in order."
    )


# ---------- Agent output ----------
class AgentReply(BaseModel):
    """The agent's final answer to the customer."""

    reply: str = Field(
        description="What to say to the customer, in Campus Customs voice. Plain text; '- ' bullets allowed."
    )
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=6,
        description=(
            "product_id values (from tool results only) to show as small cards in the chat, "
            "most relevant first. Leave empty if no specific products are being recommended."
        ),
    )
    show_on_page: bool = Field(
        default=False,
        description=(
            "True when the customer is browsing a type of item and you called search_products "
            "for it. The website then shows EVERY match from your most recent search_products "
            "call as product cards on the main page (even when there are zero matches)."
        ),
    )
    page_heading: str = Field(
        default="",
        max_length=60,
        description="Short title for those page results in Title Case, e.g. 'Red T-Shirts', 'Hoodies Under $70', 'Hats'.",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        max_length=3,
        description=(
            "0-3 short next questions the customer can tap, written in THEIR voice, that your tools "
            "can answer, e.g. 'Check my size', 'Show me crewnecks', 'What colors does it come in?'. "
            "Max 40 characters each."
        ),
    )
    sorry: bool = Field(
        default=False,
        description="True when you're telling the customer we don't have what they asked for "
        "(not carried, sold out in their size, not in that color, no matches).",
    )


# ---------- API contract ----------
class ChatTurn(CamelModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class PageContext(CamelModel):
    """What the widget reports about the current page. main.py checks it against the database."""

    path: str = Field(default="/", max_length=300)
    product_id: str | None = Field(default=None, max_length=200)
    results_heading: str | None = Field(default=None, max_length=60)
    shown_product_ids: list[str] = Field(default_factory=list, max_length=120)


class ChatRequest(CamelModel):
    message: str = Field(min_length=1, max_length=1000)
    # Guests only: logged-in history is loaded from chat_messages instead.
    history: list[ChatTurn] = Field(default_factory=list, max_length=12)
    page: PageContext | None = None


class PageResults(CamelModel):
    """Search results for the website's main page, built from the database by main.py."""

    heading: str
    total_matches: int
    products: list[ProductCard]
    note: str = ""


class ChatResponse(CamelModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list, description="Tappable follow-up questions.")
    sorry: bool = Field(default=False, description="Show the 'sorry' Handsome Dan with this reply.")
    page: PageResults | None = Field(
        default=None, description="Set when the chat search should update the page; null otherwise."
    )


class HistoryMessage(CamelModel):
    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str


class ChatHistory(CamelModel):
    messages: list[HistoryMessage]
