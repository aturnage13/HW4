# Homework 4 — AI Prompts Log

**Course:** AI Foundations for Managers
**Project:** A helpful customer-service chatbot for Campus Customs

This file logs the prompts typed into the Claude Code window for Homework 4. Each problem has its own section with the problem number and title, the initial prompt, at least one follow-up prompt, and a one-sentence note on what the initial prompt lacked.

---

## Problem 1: Vibe Coder Prompts

### Initial Prompt

> We are continuing on with the Ai Foundations for Manager course. We are now working on Homework 4, so you should use that folder for everything that we do today. We are going to develop a chatbot for Campus Customs and this chatbot ought to be helpful. I'm going to give you one problem at a time, so don't work ahead. For Problem 1, create AI_prompts.md which is where you will keep stuff. This file is the log of what I type into this window. I want you to do one section for each problem. This must include a problem number and title (which I will provide), at least a prompt that I provide, and one follow on prompt from me and a sentence from you stating what it lacked.

### Follow-up Prompt

> "Problem 1: Vibe Coder Prompts," the next prompt will be for Problem 2

### What the Initial Prompt Lacked

The initial prompt asked for a section with a problem number and title but didn't give the title, so I had to leave a placeholder until the follow-up supplied "Vibe Coder Prompts."

---

## Problem 2: Analyze the database

### Initial Prompt

> "Problem 2: Analyze the database"

### Follow-up Prompt

> @"/Users/andrewturnage/Downloads/data/campus_customs.db"
> So this is the data file to rule them all Mr. Baggins. You need to read this, understand it, and pay attention to catalogue, inventory, and users. While doing that, I need you to make a file called output/harness.md. there you will record each table and its fields, then you need to use your thoughts and generate ONE short line on why each field matters for the shop or chatbot.

### What the Initial Prompt Lacked

The initial prompt didn't say where the database was or what "analyze" meant, so I couldn't start until the follow-up gave the file path, the tables to focus on, and the deliverable (`output/harness.md`).

---

## Problem 3: Build the Campus Customs website

### Initial Prompt

> "Problem 3: Build the Campus Customs website"

### Follow-up Prompt

> Alright we are going to make the front end for Campus Customs. This is React + Vite _ TypeScript scaffold. At the top, you should have a navigation bar that links to the following pages:  Home, Products, About Us, Log In, Create account.
>
> I want you to go to this website:  https://yalebulldogblue.com
>
> Read how they word their Home and About us sections to use as inspiration for outs. Do not copy these pages to what we are working on. they are meant to be helpful examples for what we are doing.
>
> For the Products page show the product images from the catalogue that you looked at (use image paths in the database) and include basic product info (name, price, short description of the product). $Each product should be on a single-item page. This single-item page should have a large item on one side, full product text on the other. This should include description, price, sizes/stock when you get them. Put the image on the left.
>
> The chatbot chat interface should be on the bottom right. It doesn't actually need to do anything yet.

### Follow-up Prompt 2

> I also need a small api made. It should be a simple FastAPI in backend/main/py which will serve products and images and we will work more on this in Problem 5.

### What the Initial Prompt Lacked

The initial prompt gave no tech stack, page list, layout, content source, chatbot scope, or backend, so the follow-ups had to specify React + Vite + TypeScript, the five nav pages, the product grid and detail layout, the reference site for tone, a placeholder chat widget, and a FastAPI server for products and images.

---

## Problem 4: Create account and login

### Initial Prompt

> "Problem 4: Create account and login"
>
> We are building a create-account and login workflow. Create Account:  required fields are first and last name, email, password. You should figure out how to confirm the email. Then, Log In will require email and password. New accounts that are made will go into the users table. Passwords need to be secured and must not be accessible by anyone. You must not share them either if you see them.
>
> A test users for the seed database is test@campuscustoms.yale.edu and the password is password.
>
> Once you make all this, I wnat you to confirm by doing that you can login as that users and that a brand-new account that you create works. Update output/harness.md with how the auth works.

### Follow-up Prompt

> _[Pending]_

### What the Initial Prompt Lacked

_[Pending — added after the follow-up prompt]_

---

## Problem 5: PydanticAI agent backend

### Initial Prompt

> "Problem 5: PydanticAI agent backend"
>
> We are now building the shop chatbot. This is in the form of a PydanticAI agent behind FastAPI. You will plug this into the front end chat widget. Put the API app in backend/main.py which I will run with Uvicorn. Keep the agent as the following four files:
>
> backend/prompts/prompt.md - this is a system prompt
> backend/agent/py - this is the agent entry/and wiring
> backend/tools.py - these are the tools that the agent can call
> backend/models.py - which is the Pydantic/PydanticAI strucutured types.
>
> I want you to expose a chat route in main.py so that a message from the website gets a reply from the agent. Use the API for this.
>
> We are going to put Campus Customs voice and safety basics into prompts/prompt.md
>
> I wnat you to start or update types in models.py for chat replies / product cards as needed.
>
> For output/harness.md, I want you to note how the front end talks to FastAPI and how the agent is loaded.
>
> We have to make sure that the backend runs from the backend/ folder like:

### Follow-up Prompt

> Ask questions if needed

### Follow-up Prompt 2

> uvicorn main:app --reload --port 8000

### What the Initial Prompt Lacked

The initial prompt was cut off before the run command, so I had to ask before building, and the follow-up supplied `uvicorn main:app --reload --port 8000` (the model, chat access, and stock questions went unanswered, so I used my recommended defaults).

---

## Problem 6: Tools: Product info and stock

### Initial Prompt

> "Problem 6: Tools: Product info and stock"
>
> I'm now going to equip the agent with tools to look up real info from campus_customs.db
>
> It will look at the product description, price, and the quantity in stock (use size requrested by customer).
>
> This agent may only use the provided database. Nothing else is acceptable. If something is out of stock, just say "That item is out of stock." Do not ever make anything up.
>
> You need to expand prompts/prompt.md so that the agent knows to use these tools for price and stock questions every time. In output/harness.md I want you to list each tool and explain which model fields you chose for lookup results and why.

### Follow-up Prompt

> _[Pending]_

### What the Initial Prompt Lacked

_[Pending — added after the follow-up prompt]_

---

## Problem 7: Chat search that updates the page

### Initial Prompt

> "Problem 7: Chat search that updates the page"
>
> For this you are going to make the agent good at something. When a customer asks about a type of item, like "what hats do you have?" or "What red t-shirts are there?" the agent shall search the catalogue and the website that is generated should show those matching items as product cards. These product cards shall show an image of that product, name, price, and a short blurb of info about it. This should be dynamic.
>
> After you do that, we need to test it. Let's make sure that the single-item page from Problem 3 still works. Each product card should open when clicked. I want you to update prompts/prompt.md and output/harness.md so that it is clear how search results reach the page.

### Follow-up Prompt

> _[Pending]_

### What the Initial Prompt Lacked

_[Pending — added after the follow-up prompt]_

---

## Problem 8: Customery Memory

### Initial Prompt

> "Problem 8: Customery Memory"
>
> Whenever a shopper logs in, save their chat history in the database in the right spot and call it when they come back. the agent has to know who they are chatting with, which should use both name and email. This should live in agent deps or tools.
>
> I also want you to work on page context. If the customer asks if the store has the shown product, on that page, in a different color, for instance, the agent shall know which item they mean.
>
> History is only for logged in users. This will not limit how guests chat, just that there will be no history. Document in output/harness.md how user chat history is stored, what customer fields the agent sees, and how page context is passed.

### Follow-up Prompt

> _[Pending]_

### What the Initial Prompt Lacked

_[Pending — added after the follow-up prompt]_

---

## Problem 9: Usability Improvements

### Initial Prompt

> "Problem 9: Usability Improvements"
>
> Onwards and upwards. Write output/usability.md as you work. We need to come up with 2 front end usability improvements and 2 agent/backend usability improvements. Lets open the site before you do anything and let me test it out.

### Follow-up Prompt

> Okay so I want to make it prettier. Add the Yale logo in the top bar. I also want you to make the overall site prettier. For front end stuff, when you don't have something, have a picture of Handsome Dan the bulldog saying sorry or something. For backend, the agent should be more fun. Have it be perky with responses. And I also want the agent to be engaging.

### Follow-up Prompt 2

> For the agent, we need to make the output better and more accurate. It should always be safe and that is critical. Are there agent tools that would help it run faster or cheaper?

### Follow-up Prompt 3

> Download the logos. We aren't actually publishing the website, so we won't be sued.

### Follow-up Prompt 4

> Lets open the page when you are done.

### Follow-up Prompt 5

> We need more constrast between the banner and main page blues. Do Yale blue on top and a different shade for the webpages. Greys might be better actually? And for the handsome dan stuff, when the site doesn't have something can we have him say something like, "I'm out of breath looking, but we don't seem to have that!" I like the initial responses.

### Follow-up Prompt 6

> How about instead of the out of breath thing we have him say, "Sorry, I was busy beating Harvard and couldn't find what you needed!"

### Follow-up Prompt 7

> When he does find something, can you have him say "I love the smell of Harvard defeat in the morning!"

### Follow-up Prompt 8

> Lets add some other sayings for both can't find it and do find it scenarios. They should be funny, light hearted, and Yale specific.

### Follow-up Prompt 9

> Can you add pictures, pretty ones, of the campus to the website. In the banner, the pages themselves, wherever makes sense and will look pretty. I want to remind people how pretty the campus is while they are thinking about spending money.

### Follow-up Prompt 10

> Lets open it

### Follow-up Prompt 11

> I want the agent, handsome Dan, to chirp when people ask if we will beat Harvard or whatever. Nothing mean, offensive, or rude, but funny. He will never say any slurs, be rude, use offensive language.

### What the Initial Prompt Lacked

The initial prompt didn't name which usability improvements to make, so the follow-ups had to supply them: the Yale logo and a prettier site, a "sorry" Handsome Dan, a perky and engaging agent, and accurate, safe, cheaper agent output, plus permission to download the real logo and photo.

---

## Problem 10: Stlye the Website

### Initial Prompt

> Problem 10: Stlye the Website
>
> This one wants me to add creative design. I think that we did this on accident. Add stuff to output/design.md that shows what we changed and why it will help customers stick around on the website to buy. This should be short and sweet. Ask me if you don't know why I asked you to do something that made the website better.

### Follow-up Prompt

> _[Pending]_

### What the Initial Prompt Lacked

_[Pending — added after the follow-up prompt]_

---

## Problem 10 (continued): Site Testing (app check)

*(The user also labeled this one "Problem 10.")*

### Initial Prompt

> Problem 10: Site Testing (app check)
>
> For this, I need to check some stuff. I want you to take screenshots as I do it. Can we develop a way for you to know when I want you to take a screenshot and to save it to output/app_check.html?
>
> We need to check inventory level, dynamic search-results cards, a usability feature I had you improve in Problem 9.
>
> This html output is going to be graded by another AI bot. It should be easy to grade. It will include the check, a screenshot, and a sentence or two on what we are showing. Put the screenshot images in output/app_check_images/ and link them from app_check.html with relative paths.

### Follow-up Prompt

> I was supposed to keep an append-only output/audit_trail.json of the agent-loop activity (time, tool name, shorts arguments/results, sotp reasons). This wasn't supposed to be wiped between runs. I also need to give you saome safety rules for prompts/prompt.md

### Follow-up Prompt 2

> We now need to finish the output/harness.md which establishes how the syste works. It should ahve model fields in models.py and why you chose them
>
> Tools and abilities
> Safety rules
> Specs ( loop limits, results caps, models, how to run front and back)
>
> I think that you should stop runs after a certain amount of trying and that you should focus on conserving tokens. What rules do you want?

### What the Initial Prompt Lacked

_[Pending — added after the follow-up prompt]_

---

## Problem 13: Push to GitHub and submit the URL

### Initial Prompt

> Problem 13: Push to GitHub and submit the URL
>
> We are going to put the code in a folder named HW4 and we will push it to a public GitHub repository. I need a repo URL at the end of this to submit. Do not put the real .env, campus_customs.db, product images in the GitHub. Use .gitignore and include lenv.example with placeholders only.The agent should have four files under backend/: prompts/prompt.md, agent.py, tools.py, and models.py

### Follow-up Prompt

> _[Pending]_

### What the Initial Prompt Lacked

_[Pending — added after the follow-up prompt]_
