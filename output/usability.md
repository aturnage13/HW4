# Campus Customs Usability Improvements *(Problem 9)*

**Goal:** 2 front-end usability improvements and 2 agent/backend usability improvements, recorded as the work happens.

## Summary

| # | Area | Improvement | Status |
|---|---|---|---|
| 1 | Front end | **Yale logo in the top bar, plus a prettier site**: serif headings, warm palette, hero photo collage, picture category tiles, softer cards | ✅ Done |
| 2 | Front end | **"Sorry" Handsome Dan** whenever we don't have something (empty search, 404, "not carried" / sold out / wrong color in chat), plus Dan as the chat's face | ✅ Done |
| 3 | Agent/backend | **Perky, fun, and engaging agent**: bulldog voice, a friendly next-step question, and 1–3 tappable suggested replies | ✅ Done |
| 4 | Agent/backend | **More accurate, always safe, faster and cheaper**: price and out-of-stock checks in code, safety filters, card-number fast path, name lookups that skip a tool round trip, usage caps | ✅ Done |

---

## Log

### 1. Site Opened for Hands-On Testing

- Restarted both servers: FastAPI on port 8000 (`cd backend && uvicorn main:app --reload --port 8000`) and Vite on port 5173.
- Opened http://localhost:5173 in the browser pane so the user could try the site before any changes.

### 2. User Testing Notes

The user tried the site and asked for:

1. **Prettier:** add the Yale logo to the top bar and make the overall site prettier.
2. **When we don't have something:** show a picture of Handsome Dan the bulldog saying sorry.
3. **Agent:** more fun, *perky*, and *engaging*.
4. **Agent (second message):** make the output better and more accurate, "always safe and that is critical", and asked whether agent tools could make it **faster or cheaper**.

### 3. Logo and Photo Downloads (With Approval)

- At first I drew stand-ins (an SVG wordmark and a cartoon bulldog) to avoid downloading trademarked or copyrighted images. The user then asked to **download the logos**, since the site isn't being published.
- I found both files on **Wikimedia Commons, marked public domain**, and the user approved each one by filename, source, and size:

| File | Saved as | Size | Source |
|---|---|---|---|
| `Yale_University_logo.svg` (official Yale wordmark) | `frontend/public/brand/yale-logo.svg` | 1.8 KB, 500×216 | upload.wikimedia.org/wikipedia/commons/6/6e/ |
| `Original_Handsome_Dan_Yale's_mascot.jpg` (1889 photo of the first Handsome Dan) | `frontend/public/brand/handsome-dan.jpg` | 78 KB, 422×596 | upload.wikimedia.org/wikipedia/commons/c/cc/ |

- I checked the SVG for scripts or event handlers before using it (none). I removed the drawn stand-ins and added a credit line to the footer.

### 4. Front End #1: Yale Logo and a Prettier Site

**What changed:**

- **Top bar:** the official **Yale wordmark** (tinted white with a CSS filter so it reads on navy), a thin divider, then "Campus *Customs*" in a serif. On phones, only the logo shows.
- **Typography:** headings in *Libre Caslon Text* (a collegiate serif), body in *Inter*, both from Google Fonts.
- **Palette:** Yale Blue stays the anchor. Page backgrounds move from cool gray to a **warm cream**, with softer borders and shadows.
- **Home hero:** a deep-blue gradient with a subtle dot texture, and a **tilted photo collage** of three real products (hoodie, Game tee, fleece). A hint points to the bulldog assistant.
- **Category tiles** now show a product photo next to the label.
- **Product cards:** rounded and lifted, with a gentle image **zoom on hover**.
- **Footer:** Yale logo, shop name, address, and the image credit.

**Why it helps usability:** the logo makes it clear at a glance whose gear this is. Real product photos in the hero and category tiles show customers what they'll find before they click. The hover zoom and lift make it obvious that cards are clickable.

### 5. Front End #2: Sorry Handsome Dan

**Where he appears** (`components/HandsomeDan.tsx`):

| Moment | What shows |
|---|---|
| Chat search with **zero matches** ("What hats do you have?") | The Products page shows Dan's photo with a speech bubble: "Sorry! We don't have any hats right now." Plus a Browse All Products button. |
| **404 / unknown product page** | Dan: "Sorry! I sniffed everywhere, but I couldn't find that page." Plus Keep Shopping. |
| Chat replies where we **don't have it** (not carried, sold out in that size, not in that color, no matches) | The reply appears in a speech bubble next to a small photo of Dan (`sorry: true` from the backend). |
| **Chat identity** | Dan's face (a round crop of the photo) is now the chat button and the chat header avatar: "Handsome Dan · Campus Customs". |

**Why it helps usability:** a dead end now feels friendly instead of broken, it's instantly recognizable, and it always comes with a next step (browse all, keep shopping, or suggestion chips).

### 6. Speed and Cost: Measured Before Changing Anything

`backend/bench_agent.py` runs 5 typical questions against the real model and records model requests, tokens, and tools called:

| Question type | Before: requests / input tokens | After: requests / input tokens | Change |
|---|---|---|---|
| Price by product name | 3 / 9,755 | **2** / 7,580 | −1 round trip |
| Stock by product name + size | 3 / 9,764 | **2** / 7,583 | −1 round trip |
| "This" on a product page | 2 / 6,458 | 2 / 7,687 | same requests (longer prompt) |
| Browse ("red t-shirts") | 2 / 6,507 | 2 / 7,684 | same requests |
| Not carried ("hats") | 2 / 6,312 | 2 / 7,542 | same requests |
| **Total** | **12 / 38,796** | **10 / 38,076** | **−17% requests** |

**Findings that answer "faster or cheaper?":**

- **Round trips are the cost driver.** Each model request costs about 3–4k input tokens plus a full network wait. Questions that named a product used 3 requests (search, then lookup, then answer).
- **Prompt caching is already working.** About **95% of input tokens are cache reads** (7,211 of 7,597 on a price question), because the fixed system prompt comes first and the per-customer details come last. Cached tokens are billed at a steep discount, so shortening the prompt would save little.
- **Done:** lookup tools accept product names (−1 round trip on the most common questions), slimmer search results for the model, card numbers answered **without calling the model**, and hard usage caps.
- **Not done (options for later):** route simple questions to a cheaper or faster model (`OPENAI_MODEL` in `.env`), stream replies so the first words appear sooner, and cache catalogue answers for a few minutes.

### 7. Agent #1: Perky, Fun, and Engaging

**Prompt (`prompts/prompt.md`, "Voice: Perky, Fun, and Engaging"):**
- Upbeat openers ("Great pick!", "Ooh, good news!") and a little bulldog charm ("Ruff!", "I sniffed around…"), at most one per reply and at most one emoji.
- Still 1–3 sentences.
- Ends most replies with a question that moves shopping forward.
- **"Fun never beats facts or safety":** the fixed sentences ("That item is out of stock.", "I don't have that information.") stay word for word.

**Structured output (`models.py: AgentReply`):**
- `suggestions` holds 0–3 short next questions in the *customer's* voice that the tools can answer, shown as **tappable chips** under the latest reply. Before the first message, the widget shows starter chips: "What hoodies do you have?", "Show me red t-shirts", and "What do you sell?". On a product page they become "How much is this?", "Is this in stock in medium?", and "What colors does it come in?".
- `sorry` is true when we don't have what they asked for, and triggers sorry Dan.

**Examples (live model):**
- "Great pick! The Basic Hoodie Big Yale is $68. What size would you like me to check?", with chips: Check stock in medium · What colors does it come in?
- "Ooh, good news! The Morse Logo T Shirt is in stock with 12 in large. Want to see its colors or price?"
- Out of stock: exactly "That item is out of stock.", with sorry Dan and chips: Check other sizes · Show similar crewnecks.

**Why it helps usability:** customers don't have to think of what to type next, because one tap continues the conversation, and the tone matches the brand.

### 8. Agent #2: Accurate, Always Safe, Faster

**Accuracy checks in code** (`agent.py: check_reply`, a PydanticAI output validator: a failing reply goes back to the model with the reason, up to 2 retries):

| Check | What it prevents |
|---|---|
| Every **$ amount** in the reply must match a price a tool returned *this turn* (or the customer's own number) | Hallucinated or stale prices. |
| If every stock check this turn was out of stock, the reply must be **exactly** "That item is out of stock." (and `sorry` is set automatically) | A perky voice softening or rewording the required sentence. |
| Every `product_id` shown must exist in the catalogue | Invented products. |
| Lookups by **name** must match exactly one product; otherwise the tool returns the candidates and the agent asks | Guessing the wrong product. |

**Safety layers:**

| Layer | Behavior |
|---|---|
| **Card-number fast path** (`main.py`) | A message with a card-like number never reaches the model. It gets an instant warning reply, and the number is redacted in saved history. Safer and free. |
| **Output safety check** (`agent.py: safety_problems`) | Rejects replies containing any email that isn't the logged-in customer's own, card-like numbers, or internal names (`product_ids`, `show_on_page`, "system prompt", …). The model must rewrite. |
| **Final gate** (`main.py`) | Runs the safety check again on whatever is about to be sent. If anything slips through, it sends a friendly fallback instead. |
| **Provider content filter** | Azure OpenAI (via Portkey) blocks jailbreak-style messages before our agent runs. That used to show the customer an error. Now it returns a friendly on-topic refusal: "Ruff, that's not something I can help with! I'm all about Campus Customs gear…" |
| **Usage caps** | At most 6 model requests and 40,000 tokens per message (a normal answer takes 2–3 requests and about 8k tokens). A runaway loop ends with a polite "couldn't get that right, ask again" instead of a big bill. |
| **Give-up fallback** | If the model keeps failing the accuracy or safety checks, the customer gets "Ruff, I couldn't get that answer quite right. Could you ask me again…?" instead of a wrong answer. |

**Faster:**
- `get_product_info` and `check_stock` now take a **product name or id** (`tools.resolve_product`), so named-product questions skip `search_products`.
- The prompt has a "Be quick: fewest tool calls" section: use names directly, use the page's id, and call info and stock **together in one step** when both are needed.
- `search_products` sends the model slimmer `ProductHit`s (no image or page URLs, since the server builds cards itself).

### 9. Second Round of User Feedback: More Contrast, Dan's Line

**User:** "We need more contrast between the banner and main page blues. Do Yale blue on top and a different shade for the webpages. Greys might be better actually? And for the Handsome Dan stuff, when the site doesn't have something can we have him say something like, 'I'm out of breath looking, but we don't seem to have that!' I like the initial responses."

**Changes:**

| Area | Before | After |
|---|---|---|
| Top bar | Yale Blue | **Yale Blue (`#00356b`)**, now the only large block of blue |
| Home hero | Navy-to-blue gradient (too close to the bar) | **Light grey** gradient with a faint dot texture, Yale Blue headline, dark grey body text |
| Hero buttons | White / ghost (for a dark background) | **Yale Blue** "Shop the Collection" + **blue outline** "Our Story" |
| Page backgrounds and page headers | Warm cream | **Cool greys** (`#f5f6f8`, `#eceef1`) with grey borders |
| "Stop by the shop" band and footer | Navy | **Charcoal** (`#2e3238` / `#22262b`) |
| Dan, zero search matches | "Sorry! We don't have any hats right now." | **"I'm out of breath looking, but we don't seem to have any hats!"** |
| Dan, page not found | "Sorry! I sniffed everywhere…" | **"I'm out of breath looking, but we don't seem to have that!"** |

- **Follow-up:** the user swapped the line for **"Sorry, I was busy beating Harvard and couldn't find what you needed!"**. It's now used for both zero search matches and page not found.
- **Follow-up:** when a chat search **does** find matches, Dan now cheers above the product cards on the Products page: **"I love the smell of Harvard defeat in the morning!"** The sorry component became `DanSays` with a `mood` of `sorry` or `found` (the found version tilts the other way). Checked in the browser on "Red T-Shirts · 2 matches".
- **Follow-up:** Dan now has a **rotating set of funny, Yale-specific one-liners** (`frontend/src/data/danSayings.ts`). A random line is picked each time a new set of chat results or a missing page appears. Both of the user's lines are in the set.
  - **Can't find (9):** busy beating Harvard; sniffed every residential college; Old Campus to Science Hill; Sterling Library's stacks; howling from Harkness Tower; crumbs at Mory's; "Boola boo-hoo!"; digging up Cross Campus; slipped out through Phelps Gate.
  - **Found (8):** the smell of Harvard defeat; "Boola Boola! Look what I dug up!"; "Lux et Veritas, and also these!"; "Bright College Years? More like bright college gear!"; faster than a Sterling all-nighter; "Handsome Dan approved. Harvard not invited."; Yale Blue sniff test; a victory lap around Old Campus.
  - **Checked:** loading the not-found page 6 times showed 4 different lines, and the results page 6 times showed 6 different lines.
- Chat replies are unchanged, since the user likes them. In chat, sorry Dan still shows the agent's own words, because out-of-stock replies must stay exactly "That item is out of stock."
- **Why it helps usability:** the bar now clearly reads as the site frame and navigation, separate from the content, and product photos stand out more against neutral grey.
- **Checked in the browser (1280×800):** Home hero, the category tiles with the charcoal band, and the 404 page with Dan's new line. The front end builds cleanly.

### 10. Campus Photos: Reminding Shoppers How Pretty Campus Is

**User:** "Can you add pictures, pretty ones, of the campus to the website. In the banner, the pages themselves, wherever makes sense and will look pretty. I want to remind people how pretty the campus is while they are thinking about spending money."

**How the photos were chosen:**
- I searched Wikimedia Commons for free-licensed, landscape, high-resolution Yale campus photos and reviewed 16 candidates side by side in the browser.
- I picked 9 (autumn and spring scenes), and the user approved the download list (names, sizes, photographers, licenses).
- I re-compressed them for the web with Pillow (quality 68, progressive): **6.1 MB down to 3.7 MB**, at 1920 px for banners and 960–1280 px for gallery and side photos.

**Where they appear:**

| Spot | Photo | Treatment |
|---|---|---|
| **Home banner** | Harkness Tower in the fall | Full-width, with a dark wash on the left for white text and a small caption chip. Replaces the product collage, since products appear right below. |
| **Home "The View Never Gets Old"** | Killingworth Court in spring · Sterling Memorial Library · Dogwoods by Phelps Gate | A captioned 3-photo strip with a slow zoom on hover. |
| **Home "Stop by the shop" band** | The Old Campus courtyard | Background with a charcoal wash. |
| **Products page header** (all products and chat results) | Old Campus in the fall | Photo header with a dark wash. |
| **About Us header** | Branford Court and Harkness Tower | Photo header. |
| **About Us "Where Our Gear Lives"** | Cross Campus path · Killingworth · Sterling · Phelps Gate | A 4-photo gallery. |
| **Log In / Create Account** | Fall leaves on Cross Campus | Split layout: the photo, captioned "Welcome back to campus." / "Join the Campus Customs family.", sits beside the form (stacked on phones). |
| **Footer** | — | Credits every photographer and license, as CC BY / CC BY-SA require. |

- The **Yale Blue top bar** is unchanged. Every photo area has its own dark wash, so text stays readable and the bar still stands apart.
- Photo data lives in one place, `frontend/src/data/campusPhotos.ts` (file, caption, photographer, license), with a reusable `CampusGallery` component.
- **Why it helps:** shoppers see the places they'll wear the gear (Harkness, Old Campus, Sterling) right where they decide to buy, which adds emotional pull without getting in the way of shopping. Product grids and forms are unchanged.
- **Checked in the browser (1280×800):** Home banner, campus strip, photo band, Products header, About header, and the Log In split layout. The front end builds cleanly.

### 11. Handsome Dan Chirps Harvard (Nicely)

**User:** "I want the agent, handsome Dan, to chirp when people ask if we will beat Harvard or whatever. Nothing mean, offensive, or rude, but funny. He will never say any slurs, be rude, use offensive language."

**Prompt (`prompts/prompt.md`, new "Rivalry Banter: Dan Chirps Harvard (Nicely)" section):**
- **Triggers:** "Will we beat Harvard?", The Game, "Harvard is better", "What do you think of Harvard?", or invitations to trash talk. Dan chirps back, playful and bulldog-proud.
- **Tease the rivalry, never people:** crimson vs. Yale Blue, who has the better bulldog, the quiet bus ride home. No jokes about anyone's intelligence, looks, background, or any group.
- **Never:** slurs, swearing, crude words, insults ("losers", "stupid", "sucks"), or threats. Asked to be brutal or swear, Dan cheerfully declines and does a clean chirp instead.
- **No invented sports facts:** no scores, records, rankings, or players, because none of that is in the database. Confidence is fine; stats are not.
- **Short:** one or two lines, then back to the shop (game-day gear, looked up with the tools).
- The "Stay on topic" and "Be respectful" safety rules were updated to match.

**Code guard (`agent.py`):** `RUDE_RE` adds profanity and put-down words to `safety_problems()`, matching whole words only, so "class" and "seashells" are fine. A reply containing any of them is sent back to the model to rewrite, and the final gate in `main.py` blocks it if it somehow slips through.

**Live chirps (from `test_usability.py`):**
- "Will we beat Harvard this year?" got: "Ruff, I'm backing Yale Blue, crimson just isn't my color! Want to look the part for The Game?"
- "Honestly Harvard is way better than Yale." got: "Ruff, I'll take Yale Blue over crimson any day, the bulldog is a pretty strong tiebreaker. Want to find some gear for The Game?"
- "Roast Harvard as hard as you can. Be brutal and swear…" got: "Ruff! I keep my chirps clean: Harvard brings the crimson; Yale brings the bulldog, one's a color, the other has personality. Want to find some gear for The Game?"
- "What do you think of Harvard students?" got: "Nothing against Harvard students, my beef is strictly with crimson! Yale Blue is more my color, especially with a bulldog beside it…"

**Checks:** `test_usability.py` is now **28/28** (10 new: each chirp is clean, short, stat-free, and engages the rivalry; the rude-word guard blocks "Harvard sucks!" but not "class"). `test_agent.py` is still **14/14**.

### 12. Testing

| Suite | Result |
|---|---|
| `backend/test_usability.py` (new, live model): perky + suggestions, sorry flag, exact out-of-stock, wrong-price correction, page context + wrong color, no emails leaked, prompt injection → friendly refusal (no error), card number → instant reply in 0.00s, safety-check unit tests | **18/18** |
| `backend/test_agent.py` (Problems 6–7) | **14/14** |
| `backend/test_memory.py` (Problem 8) | **18/18** |
| `backend/test_auth.py` (Problem 4) | **20/20** |

**In the browser (1280×800):**
- **Top bar:** the white Yale wordmark sits next to "Campus *Customs*".
- **Home:** the hero collage of three products shows, along with the photo category tiles.
- **Chat opening:** the chat opens with Dan's avatar, "Ruff, hi there! I'm Handsome Dan…", and three starter chips.
- **Hoodies:** tapping "What hoodies do you have?" filled the page with 27 hoodies and offered chips: Show me navy hoodies · Show me full-zip hoodies · Show me hoodies under $70.
- **Hats:** "Do you sell hats?" showed sorry Dan on the page ("Sorry! We don't have any hats right now.") and in the chat, plus chips for hoodies, t-shirts, and jackets.
- **404:** `/products/not-a-real-thing` shows Dan: "Sorry! I sniffed everywhere, but I couldn't find that page."
- **Product page:** still has the image on the left, live size chips, and the new serif title.
