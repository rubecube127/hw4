# AI Prompts

This file records each problem’s number and name, the initial prompt exactly as entered, and any follow-up prompts needed, with a brief explanation of why each follow-up was needed.

## Setup — Create AI Prompts Log

### Initial prompt (verbatim)

> Create AI\_prompts.md, which will log my prompts as usual. Do you remember the guidelines for AI\_prompts.md?

### Follow-up prompts

> _None needed._

**Why a follow-up was needed:** No follow-up was needed because the logging format was clear from the existing homework prompt logs.

## Problem 2 — Analyze the Database

### Initial prompt (verbatim)

> Problem 2: Analyze the Database
> Can you open the campus customs database in a format that I can view it?  
> Also create output/harness.md. In it, write down each table and its fields, and one short line on why each field matters for the shop or the chatbot that we will be building.

### Follow-up prompts

> _None needed._

**Why a follow-up was needed:** No follow-up was needed because the requested database view and harness documentation were specified clearly.

## Problem 3 — Build the Campus Customs Website

### Initial prompt (verbatim)

> **Problem 3: Build the Campus Customs Website**
> 
> Scaffold a React + Vice + TypeScript front end for Campus Customs. Put a nav bar at the top that links to the following main pages:
> 
> - Home
> - Products
> - About Us
> - Login
> - Create Account
> 
> For Home, the website we want to mimic says something along the lines of the screenshots I attached. It should not use the same words verbatim, but should communicate a similar message differently. In the About Us tab, include information about the website from [yalebulldogblue.com](http://yalebulldogblue.com).
> 
> On the Products page, show product images from the catalogue in the homework 4 folder using the image paths in the database. Include basic product information about each item as well, including name, price, and a short description. Make each product open a single-item page (large image on the right side, full product text on the left side including description, price, and size/stock if you have them. Do not fabricate these values or this information.) Clicking a card on the Products page should take a user to the single-item page for that product.
> 
> Add a chat interface in the bottom right of the site (a floating chat panel). It does not need to talk to an agent yet — we will call back to this in a later problem.
> 
> Start a simple FastAPI app in backend/main.py to serve products and images. We will grow this into the agent backend later in Problem 5.

### Follow-up prompts

> _None needed._

**Why a follow-up was needed:** No follow-up was needed because the frontend pages, product-detail behavior, floating chat placeholder, and backend starting point were specified clearly.

### Follow-up prompt — visual references

> Here are the screenshots I forgot to attach in the initial prompt. Make changes as needed

**Why a follow-up was needed:** The screenshots clarified the intended visual direction: category navigation with a dropdown, a dark collection header, sidebar filters, sorting controls, denser product cards, and a lower-left chat affordance. The implementation was updated to reflect those patterns while retaining Campus Customs branding and original copy.

### Follow-up prompt — frontend visual redesign

> The existing frontend is super ugly. Can you make it look less plain and nicely laid out? Use Yale blue and white as the main color scheme. Text should be spaced out, and it should be a nice interface to look at. See the attached screenshot for a similar format that I want you to use. Obviously don't use images of models, but use campus-esque photos.
> 
> Also, the hyperlinked headings are ugly as plain text as they are right now. Space them out and make them look cute.

**Why a follow-up was needed:** The visual reference called for a more editorial storefront treatment, so the interface was restyled around Yale blue and white with wider spacing, stronger navigation hierarchy, and catalogue imagery used in place of model photography.

## Problem 4 — Create Account and Login

### Initial prompt (verbatim)

> **Problem 4: Create Account and Login**
> Build a create-account/login flow. Create account should entail a first name, last name, email, password, and confirm password field. Log in should require an email and password.
>
> New accounts should go in the users table. Passwords should be hashed or something to store them safely in case a hacker tries to access them.
>
> The database has an example test user whose email is [test@campuscustoms.yale.edu](mailto:test@campuscustoms.yale.edu) and password is password. Once you have created the account login page, give me the URL so I can open the page and test the user login.
>
> Update output/harness.md with how auth works (what you store for a user and how passwords are protected).

### Follow-up prompts

> It should not show this once I hit "login" after enter the username and password: null is not an object (evaluating 'e.currentTarget.reset')
>
> Also, once the username and password are entered, the user should be logged in, their username should appear in the top right corner of the screen, and "login" should go away from the headings. Once the user is logged in, you should also direct them back to the home page automatically.

> Remove the wizard from the tab when loading the website in a browser. Also update AI_prompts.md as specified for this problem.

> If I hover my cursor over my username after I've logged in ("Hi, Test") there should be a dropdown menu that has options to view my account, settings, and to log out. If I select log out, it should log me out of the website and return to the home page. The log in and create account headings should reappear in this case.
>
> My account should have an order history and settings should have fields to change my username, first name, last name, and password.

**Why follow-up prompts were needed:** The first follow-up identified an async React event-lifecycle error and specified the completed signed-in experience. The second requested replacement of the default browser-tab icon and completion of this prompt log. The final follow-up defined the account dropdown, logout behavior, profile controls, and account-history view.

## Problem 5 — PydanticsAI agent backend

### Initial prompt (verbatim)

> **Problem 5: PydanticsAI agent backend**
>
> Build the chatbot as a PydanticAI agent behind FastAPI. It should plug into the frontend chat widget. Put the API app in backend.main.py, as this is the file that will be ran with Uvicorn. Keep the agent as the following four files next to it:
>
> - Backend/prompts/prompt.md (system prompt, will grow this later)
> - Backend/agent.py (agent entry/writing)
> - Backend/tools.py (tools the agent can call)
> - Backend/models.py (Pydantic/PydanticAI structured types)
>
> In main.py, expose a chat route so a message from the website returns a reply from the agent (and whatever else you need for products/auth). Use my AI model API key for the agent.
>
> Put Campus Customs voice and safety basics into prompts/prompt.md. Tools and safety will be further explained later. Start or update types in models.py for chat replies and product cards as needed.
>
> In output/harness.md, note how the front end talks to FastAPI and how the agent is loaded (prompt file and model).
>
> The backend should be able to run from the backend/ folder with the following terminal command: uvicorn main:app --reload --port 8000

### Follow-up prompts

> Use GPT-5.6-Luna through PydanticAI

> I tried setting my key in the backend terminal session and got this error: ERROR:    [Errno 48] Address already in use

> zsh: no such file or directory: ../.venv/bin/uvicorn

> I tried prompting it to find shirts, and the chatbot gave me this error: Campus Concierge is temporarily unavailable. Please try again shortly.

> ERROR:    [Errno 48] Address already in use

**Why follow-up prompts were needed:** The initial request did not specify a model, so the first follow-up selected the exact PydanticAI model identifier. The later follow-ups addressed local backend startup, virtual-environment path, safe agent-error logging, API-key configuration, and release of a stale Uvicorn process occupying port 8000.

## Problem 6 — Tools: Product Info and Stock

### Initial prompt (verbatim)

> **Problem 6: Tools: Product Info and Stock**
>
> Give the agent tools that look up real info from campus_customs.db:
>
> - Product description
> - Price
> - How many are in stock (by size when the customer asks)
>
> The agent must use the database and should not fabricate any prices or quantities. If a size is out of stock, say so clearly.
>
> Expand prompts/prompt.md so the agent knows to call these tools for price and stock questions. Add or update return types in models.py. In output/harness.md, list each tool and explain which model fields you chose for lookup results and why.

### Follow-up prompts

> The chatbot is still telling me: Campus Concierge is temporarily unavailable. Please try again shortly. when I ask it to find me grey tshirts in size small.

> How do i view that error

> ERROR:    [Errno 48] Address already in use

> INFO:     127.0.0.1:64336 - "POST /api/chat HTTP/1.1" 503 Service Unavailable

> The key should be in my AI folder root. Are you able to read it, but not copy it?

> Update AI_prompts.md for this problem.

**Why follow-up prompts were needed:** The agent initially could not reach the model provider. The follow-ups diagnosed the local Uvicorn port conflict, made the server error visible, and identified the AI-root `PORTKEY_API_KEY` configuration. The backend was updated to load that key without exposing it and to use Portkey's OpenAI-compatible provider; the database-backed grey T-shirt stock question then returned successfully.

## Problem 7 — Chat Search That Updates the Page

### Initial prompt (verbatim)

> **Problem 7: Chat Search That Updates the Page**
> When a customer asks the chatbot about a type of item, the agent should search the catalogue and the website should dynamically show those matching items as product cards, including image, name, price, and short info. This is an API contract: the agent return structure product matches and then the front end renders them on the website. For example, if the user asks “what hoodies do you have?” The page should dynamically show the hoodies in stock.
>
> After the dynamic product cards are loaded, make sure the same single0item page behavior still works: each product card (including the ones the chat just put on the page) should still open that detail view of a large image and full information when clicked.
>
> Update prompts/prompt.md and output/harness.md so it is clear how search results reach the page.

### Follow-up prompts

> Update AI_prompts.md for this problem

**Why a follow-up was needed:** The implementation requirements were clear; the follow-up requested that this prompt log be updated for Problem 7.

## Problem 8 — Customer Memory

### Initial prompt (verbatim)

> **Problem 8: Customer Memory**
> When a shopper is logged in, save their chat history in the database in an appropriate table and reload it when they return. The agent should know who is chatting (name and email). Put that info in agent deps and/or tools the agent can call.
>
> Also pass enough page context that if someone is on a product page and asks “do you have this in pink?” The agent knows which item they mean. Code can be put into the agent context.
>
> Guests can still chat, but history only needs to persist for logged-in users. Document output/harness.md: how user chat history is stored, what customer fields the agent sees, and how page context is passed.

### Follow-up prompts

> _None needed._

**Why a follow-up was needed:** No follow-up was needed because the memory, identity, page-context, and documentation requirements were specified clearly.

## Problem 9 — Usability Improvements

### Initial prompt (verbatim)

> **Problem 9: Usability Improvements**
> I have already asked you to fix a few frontend usability improvements and backend/agent usability improvements. Can you remind me what those have been?
>
> Write output.usability.md with the improvements that have been made, with at least 2 from the frontend and 2 of the backend/agent. For each improvement, say what you added and why it helps a Campus Customs shopper or the business.
>
> Make sure that all the features I’ve asked you to add work.

### Follow-up prompts

> Let's implement rate limiting and privacy controls for the user. Replace the existing "Backend and agent improvements" in usability.md with just these 2 improvements.
>
> Also replace the existing "Frontend improvements" in usability.md with just 2 improvements that we implemented: account menu/settings and scrollable minimized chat panel.

**Why a follow-up was needed:** The initial request asked for a report. The follow-up expanded the work to add rate limiting and user privacy controls, then narrowed the report to the specified two frontend and two backend improvements.

## Problem 10 — Style the Website

### Initial prompt (verbatim)

> **Problem 10: Style the Website**
> Add some blue frilly borders and an image of Handsome Dan the bulldog to the website homepage. Include more Yale-color-themed decor to the site. Make the chatbot look cuter, maybe make its logo handsome dan.
>
> Write output/design.md listing what we changed and why it should help customers stick around and buy. Keep it concrete and short. I also specified visual details earlier, so make note of those in this file as well.

### Follow-up prompts

> _None needed._

**Why a follow-up was needed:** No follow-up was needed because the requested visual elements and design documentation were specified clearly.

## Problem 11 — Site Testing (App Check)

### Initial prompt (verbatim)

> **Problem 11: Site Testing (App Check)**
> I’ll give you screenshots and details about how the website is functioning. You should populate this information in a document called output/app_check.html (a page I can double-click and open). The HTML file should have a heading for each check that I specify, a screenshot, and one or two sentences on what the screenshot proves. The screenshot image files should be put in output/app_check_images/ and link them from app_check.html with relative paths.
>
> Check #1: Inventory Level (Stock and Price)
> The chatbot returned the quantity and prices for the products I asked for. It also loaded the page dynamically to show me hoodies that fit my description.
>
> Check #2: Dynamic Search-Result Cards
> After I searched for navy shirts, the website automatically pulled the search-result cards for navy blue catalog items.
>
> Check #3: Account Menu and Settings - Usability
> When a user clicks on the dropdown arrow under their username, they have the option to access their account, change their settings, or to log out easily.

### Follow-up prompts

> Update AI_prompts.md for Problem 11

**Why a follow-up was needed:** The follow-up requested that the completed app-check documentation be recorded in this prompt log.

## Problem 12 — Audit Trail, Safety, Finish Harness

### Initial prompt (verbatim)

> **Problem 12: Audit Trail, Safety, Finish Harness**
> Keep an append-only output/audit_trail.json of agent-loop activity (time, tool name, short args/result, stop reason). Do not wipe it between runs. Also, add some safety rules for the agent and put them in prompts/promt.md to make sure the agent is not accessing secure information like passwords and to make sure it isn’t burning up tokens.
>
> Finish output/harness.md so it’s clear how the system works, including:
> - Model fields in models.py and why you chose them
> - Tools and abilities
> - Safety rules
> - Specs (loop limits, result caps, models, how to run front and back)

### Follow-up prompts

> _None needed._

**Why a follow-up was needed:** No follow-up was needed because the audit, safety, and harness requirements were specified clearly.
