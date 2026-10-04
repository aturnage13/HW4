"""Tools the Campus Customs agent can call. All of them are read-only.

Each one reads the catalogue/inventory tables directly so the agent answers
from real data instead of memory. agent.py registers these functions; their
docstrings and type hints become the tool descriptions the model sees.
"""

import json
import re
import sqlite3

from db import get_connection
from models import (
    Category,
    CurrentPage,
    PageContext,
    CategorySummary,
    ProductCard,
    ProductHit,
    ProductInfo,
    ProductSearchResult,
    ShopOverview,
    SizeStock,
    StockResult,
    StockStatus,
    ToolError,
)

SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
LOW_STOCK_MAX = 5
OUT_OF_STOCK_MESSAGE = "That item is out of stock."
MAX_SEARCH_RESULTS = 8  # matches the model reads per search (the page still gets every match)

# How customers say sizes -> the size codes stored in inventory.size.
SIZE_ALIASES = {
    "xs": "XS", "x-small": "XS", "extra small": "XS", "extra-small": "XS", "xsmall": "XS",
    "s": "S", "small": "S", "sm": "S",
    "m": "M", "medium": "M", "med": "M",
    "l": "L", "large": "L", "lg": "L",
    "xl": "XL", "x-large": "XL", "extra large": "XL", "extra-large": "XL", "xlarge": "XL",
    "xxl": "XXL", "2xl": "XXL", "2x": "XXL", "xx-large": "XXL", "xxlarge": "XXL",
    "2x-large": "XXL", "extra extra large": "XXL",
}

STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "in", "of", "with", "do", "you", "have", "any",
    "i", "me", "my", "want", "need", "looking", "show", "some", "something", "is", "are",
    "what", "that", "this", "to", "on", "please", "got", "get", "can", "find", "there",
    "your", "sell", "carry", "all", "which", "kind", "type", "item", "product", "options",
    "available", "stuff", "gear", "apparel", "clothing", "clothe", "merch", "anything", "every",
    # Price words: prices are handled by the max_price filter, not text matching.
    "under", "below", "less", "than", "cheaper", "cheap", "around", "about", "price", "priced",
    "cost", "dollar", "budget", "max", "maximum", "most", "up",
}

# Multi-word ways customers name a garment type -> one token. Applied before splitting.
PHRASES = [
    (r"\b(?:quarter|1/4|half)[\s-]?zips?\b", " quarter-zip "),
    (r"\bt[\s-]?shirts?\b|\btees?\b", " t-shirt "),
    (r"\bhoodies?\b|\bhoody\b|\bhooded sweatshirts?\b", " hoodie "),
    (r"\bcrew[\s-]?necks?\b", " crewneck "),
    (r"\bshort[\s-]sleeves?\b", " short-sleeve "),
    (r"\blong[\s-]sleeves?\b", " long-sleeve "),
    (r"\b(?:jackets?|fleeces?|coats?|bombers?)\b", " jacket "),
]

# Garment-type words become a category filter instead of free text, so
# "hoodies" means products that ARE hoodies, not ones that mention hoods.
CATEGORY_WORDS: dict[str, Category] = {
    "hoodie": "hoodie",
    "t-shirt": "t-shirt",
    "crewneck": "crewneck",
    "quarter-zip": "quarter-zip",
    "jacket": "jacket",
}

# Product types the catalogue has none of. Asking for these returns no matches
# (otherwise "hats" would match a hoodie whose graphic has a bulldog in a hat).
NOT_CARRIED = {
    "hat", "cap", "beanie", "visor", "sock", "short", "pant", "sweatpant", "jogger",
    "legging", "polo", "jersey", "scarf", "glove", "mitten", "bag", "backpack", "tote",
    "mug", "cup", "bottle", "tumbler", "glass", "sticker", "decal", "magnet", "pennant",
    "banner", "flag", "blanket", "keychain", "lanyard", "onesie", "bib", "dress", "skirt",
    "shoe", "sneaker", "slipper", "umbrella", "book", "pen", "jewelry", "necklace",
    "earring", "ornament", "poster", "frame", "towel", "pillow",
}

# Free-text words customers use -> words that appear in the catalogue.
SYNONYMS = {
    "grey": ["gray"],
    "sweater": ["sweatshirt", "crewneck"],
    "maroon": ["maroon", "burgundy"],
}


# ---------- Helpers ----------
def category_for(garment_type: str) -> Category:
    g = garment_type.lower()
    if "quarter-zip" in g:
        return "quarter-zip"
    if "jacket" in g or "fleece" in g:
        return "jacket"
    if "hood" in g:
        return "hoodie"
    if "t-shirt" in g:
        return "t-shirt"
    if "crewneck" in g:
        return "crewneck"
    if "performance shirt" in g:
        return "long-sleeve shirt"
    if "sweatshirt" in g:
        return "sweatshirt"
    return "other"


def stock_status(quantity: int) -> StockStatus:
    if quantity <= 0:
        return "out_of_stock"
    if quantity <= LOW_STOCK_MAX:
        return "low_stock"
    return "in_stock"


def short_description(description: str, limit: int = 140) -> str:
    first = description.split(". ")[0].rstrip(".") + "."
    return first if len(first) <= limit else first[: limit - 1].rsplit(" ", 1)[0] + "…"


def _card(row: sqlite3.Row) -> ProductCard:
    return ProductCard(
        product_id=row["product_id"],
        name=row["name"],
        category=category_for(row["garment_type"]),
        price=row["price"],
        colors=json.loads(row["colors"]),
        short_description=short_description(row["description"]),
        image_url=f"/{row['image_file_path']}",
        url=f"/products/{row['product_id']}",
    )


def _hit(row: sqlite3.Row) -> ProductHit:
    return ProductHit(
        product_id=row["product_id"],
        name=row["name"],
        category=category_for(row["garment_type"]),
        price=row["price"],
        colors=json.loads(row["colors"]),
        short_description=short_description(row["description"]),
    )


def _stock_rows(conn: sqlite3.Connection, product_id: str) -> list[SizeStock]:
    rows = conn.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchall()
    by_size = {r["size"]: r["quantity"] for r in rows}
    return [
        SizeStock(size=s, quantity=by_size[s], status=stock_status(by_size[s]))
        for s in SIZES
        if s in by_size
    ]


def _all_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()


def _singular(word: str) -> str:
    return word[:-1] if word.endswith("s") and len(word) > 3 and not word.endswith("ss") else word


def _parse_query(query: str) -> tuple[Category | None, list[str], list[list[str]]]:
    """Split a query into (category from a garment word, unsupported types, free-text terms).

    Each free-text term is a list of acceptable spellings; every term must match.
    """
    text = re.sub(r"\$\s?\d+(?:\.\d+)?|\b\d+(?:\.\d+)?\s?(?:dollars|bucks)\b", " ", query.lower())
    for pattern, replacement in PHRASES:
        text = re.sub(pattern, replacement, text)

    category: Category | None = None
    not_carried: list[str] = []
    terms: list[list[str]] = []
    for word in re.findall(r"[a-z0-9/'-]+", text):
        word = word.strip("'-")
        base = _singular(word)
        if not word or word in STOPWORDS or base in STOPWORDS:
            continue
        if word in CATEGORY_WORDS:
            category = category or CATEGORY_WORDS[word]
        elif base in NOT_CARRIED:
            not_carried.append(word)
        else:
            terms.append(SYNONYMS.get(base, [base]))
    return category, not_carried, terms


def _word_match(option: str, text: str) -> bool:
    return re.search(rf"\b{re.escape(option)}(?:s|es)?\b", text) is not None


def _term_weight(row: sqlite3.Row, options: list[str]) -> int:
    """Best field weight where any spelling of the term appears as a whole word (0 = no match)."""
    fields = [
        (row["name"].lower(), 3),
        (" ".join(json.loads(row["search_tags"])).lower(), 2),
        (row["garment_type"].lower(), 2),
        (" ".join(json.loads(row["colors"])).lower(), 2),
        (row["description"].lower(), 1),
    ]
    return max((w for text, w in fields if any(_word_match(o, text) for o in options)), default=0)


def _categories_carried(rows: list[sqlite3.Row]) -> list[str]:
    seen: list[str] = []
    for row in rows:
        c = category_for(row["garment_type"])
        if c != "other" and c not in seen:
            seen.append(c)
    return seen


# ---------- Tools ----------
def search_products(
    query: str = "",
    category: Category | None = None,
    color: str | None = None,
    max_price: float | None = None,
    limit: int = 6,
) -> ProductSearchResult:
    """Search the Campus Customs catalogue for products matching what the customer describes.

    Use this whenever a customer asks about a type of item ("what hoodies do you have?",
    "red t-shirts", "anything for the Harvard game?"). Every matching product, not just
    the ones returned here, can be shown on the website's page as product cards.

    Args:
        query: The customer's words, e.g. "red t-shirts", "Yale baseball", "Benjamin Franklin".
            Garment words (hoodie, tee, crewneck, quarter-zip, jacket) filter by type, and
            every other word must match. May be empty to list a whole category.
        category: Optional garment category filter (overrides a garment word in query).
        color: Optional color the product must come in, e.g. "navy", "gray", "red".
        max_price: Optional highest price in US dollars.
        limit: How many matches to return to you here (1-8). The page shows all matches.
    """
    limit = max(1, min(limit, MAX_SEARCH_RESULTS))
    query_category, not_carried, terms = _parse_query(query)
    category = category or query_category
    color_terms = SYNONYMS.get(color.lower().strip(), [color.lower().strip()]) if color else []

    with get_connection() as conn:
        rows = _all_rows(conn)

    if not_carried:
        carried = ", ".join(_categories_carried(rows))
        return ProductSearchResult(
            total_matches=0,
            products=[],
            note=f"The catalogue has no {', '.join(not_carried)}. Product types carried: {carried}.",
        )

    scored = []
    for row in rows:
        if category and category_for(row["garment_type"]) != category:
            continue
        if max_price is not None and row["price"] > max_price:
            continue
        if color_terms:
            colors = " ".join(json.loads(row["colors"])).lower()
            if not any(_word_match(c, colors) for c in color_terms):
                continue
        weights = [_term_weight(row, options) for options in terms]
        if any(w == 0 for w in weights):
            continue
        scored.append((sum(weights), row))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["name"]))
    note = "" if scored else "No products matched every word. Try fewer or broader words, or drop a filter."
    return ProductSearchResult(
        total_matches=len(scored),
        products=[_hit(r) for _, r in scored[:limit]],
        note=note,
        all_product_ids=[r["product_id"] for _, r in scored],
    )


def normalize_size(size: str) -> str | None:
    return SIZE_ALIASES.get(re.sub(r"\s+", " ", size.strip().lower()))


def _row_by_id(product_id: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()


def resolve_product(product: str) -> tuple[sqlite3.Row | None, ToolError | None]:
    """Find exactly one catalogue row from a product_id OR a product name.

    Lets the agent go straight to get_product_info / check_stock with the name the
    customer used, skipping a search_products round trip. Tries, in order: exact
    product_id, exact name (any case), the name as a slug, then a search that must
    match exactly one product. Anything ambiguous comes back as a ToolError listing
    the candidates, so the agent asks instead of guessing.
    """
    key = product.strip()
    if not key:
        return None, ToolError(error="No product given.", hint="Ask which product they mean.")
    row = _row_by_id(key)
    if row is None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM catalogue WHERE lower(name) = ?", (key.lower(),)).fetchone()
    if row is None:
        row = _row_by_id(re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-"))
    if row is not None:
        return row, None

    matches = search_products(key, limit=4)
    if len(matches.all_product_ids) == 1:
        return _row_by_id(matches.all_product_ids[0]), None
    if not matches.all_product_ids:
        return None, ToolError(
            error=f"No product called '{key}' in the catalogue.",
            hint="Call search_products with broader words. If nothing matches, we don't carry it.",
        )
    options = "; ".join(f"{p.name} ({p.product_id})" for p in matches.products)
    return None, ToolError(
        error=f"'{key}' matches {matches.total_matches} products, e.g. {options}.",
        hint="Ask the customer which one they mean, or call again with the exact product_id.",
    )


def get_product_info(product: str) -> ProductInfo | ToolError:
    """Look up one product's description, price, and colors from the catalogue.

    Use this every time a customer asks what something costs or what it's like.

    Args:
        product: The product_id (e.g. "basic-hoodie-big-yale") or the product's name
            as the customer said it (e.g. "Basic Hoodie Big Yale").
    """
    row, error = resolve_product(product)
    if error:
        return error
    return ProductInfo(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        price=row["price"],
        colors=json.loads(row["colors"]),
    )


def check_stock(product: str, size: str | None = None) -> StockResult | ToolError:
    """Look up how many units are in stock for a product, in the size the customer asked for.

    Use this every time a customer asks whether something is available or in stock.

    Args:
        product: The product_id or the product's name as the customer said it.
        size: The customer's size, e.g. "M", "medium", "XL", "2XL". Leave empty only
            if the customer didn't name a size; then every size is returned.
    """
    row, error = resolve_product(product)
    if error:
        return error
    product_id = row["product_id"]
    with get_connection() as conn:
        sizes = _stock_rows(conn, product_id)

    requested = None
    if size and size.strip():
        requested = normalize_size(size)
        if requested is None:
            return ToolError(
                error=f"'{size}' isn't a size we carry.",
                hint=f"Sizes are {', '.join(SIZES)}. Ask the customer which of these they want.",
            )
        sizes = [s for s in sizes if s.size == requested]

    in_stock = any(s.quantity > 0 for s in sizes)
    return StockResult(
        product_id=product_id,
        name=row["name"],
        requested_size=requested,
        sizes=sizes,
        in_stock=in_stock,
        customer_message=None if in_stock else OUT_OF_STOCK_MESSAGE,
    )


def get_shop_overview() -> ShopOverview:
    """Get what Campus Customs sells: product categories, how many of each, price ranges, and sizes."""
    with get_connection() as conn:
        rows = _all_rows(conn)
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(category_for(row["garment_type"]), []).append(row["price"])
    return ShopOverview(
        total_products=len(rows),
        sizes_offered=SIZES,
        categories=[
            CategorySummary(category=c, product_count=len(p), min_price=min(p), max_price=max(p))
            for c, p in sorted(groups.items(), key=lambda kv: -len(kv[1]))
        ],
    )


# ---------- Used by main.py (not exposed to the agent) ----------
def product_cards(product_ids: list[str]) -> list[ProductCard]:
    """Build cards for the given ids, in order, skipping any that don't exist."""
    if not product_ids:
        return []
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM catalogue WHERE product_id IN ({','.join('?' * len(product_ids))})",
            product_ids,
        ).fetchall()
    by_id = {r["product_id"]: r for r in rows}
    seen: set[str] = set()
    cards = []
    for pid in product_ids:
        if pid in by_id and pid not in seen:
            seen.add(pid)
            cards.append(_card(by_id[pid]))
    return cards


def existing_product_ids(product_ids: list[str]) -> set[str]:
    return {c.product_id for c in product_cards(product_ids)}


def stock_for(product_id: str) -> list[SizeStock] | None:
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        return _stock_rows(conn, product_id) if exists else None


def resolve_page(page: PageContext | None) -> CurrentPage | None:
    """Check the widget's page report against the database (unknown ids are dropped)."""
    if page is None:
        return None
    path = page.path.split("?")[0] or "/"
    matches = product_cards([page.product_id]) if page.product_id else []
    product = matches[0] if matches else None
    shown = product_cards(page.shown_product_ids[:120])
    if product:
        kind = "product"
    elif page.results_heading:
        kind = "search_results"
    elif path == "/products":
        kind = "catalogue"
    elif path == "/":
        kind = "home"
    else:
        kind = "other"
    return CurrentPage(
        kind=kind,
        path=path,
        product=product,
        results_heading=page.results_heading if kind == "search_results" else None,
        shown_products=shown if kind == "search_results" else [],
    )
