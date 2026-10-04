# Campus Customs: Shop and Handsome Dan Chatbot (HW4)

A React + Vite + TypeScript storefront for Campus Customs with a FastAPI backend and a PydanticAI shopping assistant, **Handsome Dan**. Dan answers only from the shop database: exact prices, live stock by size, chat searches that fill the page with product cards, memory for logged-in shoppers, and clean Harvard chirps.

Full system documentation is in **[output/harness.md](output/harness.md)**.

## The Agent (backend/)

| File | Role |
|---|---|
| `backend/prompts/prompt.md` | System prompt: voice, database-only rule, tool rules, safety rules |
| `backend/agent.py` | Agent entry and wiring: model, tools, instructions, validator, run limits |
| `backend/tools.py` | Read-only tools the agent can call (search, product info, stock, overview) |
| `backend/models.py` | Pydantic / PydanticAI structured types |

`backend/main.py` is the FastAPI app (run with Uvicorn).

## What's Not in This Repo

These are kept out on purpose (see `.gitignore`). Add your own copies locally:

| Item | Where it goes |
|---|---|
| `.env` (secrets) | `HW4/.env`, copied from `.env.example` |
| `campus_customs.db` | `HW4/data/campus_customs.db` |
| Product photos | `HW4/data/products/*.jpg` |

## Setup

```bash
# 1. Secrets
cp .env.example .env            # then fill in PORTKEY_API_KEY and OPENAI_MODEL

# 2. Data: put campus_customs.db and the products/ photos in data/, then:
python3 scripts/export_catalogue.py   # builds frontend catalogue.json + copies photos

# 3. Backend (Python 3.12)
cd backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 4. Front end (Node.js)
cd ../frontend
npm install
```

## Run

Two terminals:

```bash
# Backend: run from backend/
cd backend && .venv/bin/uvicorn main:app --reload --port 8000
```

```bash
# Front end
cd frontend && npm run dev
```

Open http://localhost:5173. Vite proxies `/api/*` to the backend on port 8000.

## Tests (Backend and Front End Running)

```bash
cd backend
SEED_PASSWORD=... .venv/bin/python test_auth.py     # accounts and login
.venv/bin/python test_agent.py                      # tools, prices, stock, browse → page
SEED_PASSWORD=... .venv/bin/python test_memory.py   # history and page context
.venv/bin/python test_usability.py                  # voice, safety, chirps
```

## Homework Outputs

- `AI_prompts.md`: prompt log for each problem
- `output/harness.md`: how the system works (specs, models, tools, safety)
- `output/usability.md`, `output/design.md`: Problem 9 and 10 write-ups
- `output/app_check.html` + `output/app_check_images/`: site-testing screenshots
- `output/audit_trail.json`: append-only agent-loop audit trail

## Credits

The Yale wordmark, the 1889 photo of Handsome Dan, and the campus photos come from Wikimedia Commons (public domain or Creative Commons; photographers and licenses are listed in the site footer and in `frontend/src/data/campusPhotos.ts`). This is a class project and isn't affiliated with Yale University.
