# Campus Customs Database Harness

The local SQLite database is the source of truth for product details, prices, inventory, accounts, and saved chat context. The shop and chatbot should query it rather than inventing product or stock information.

## `catalogue`

| Field | Why it matters |
|---|---|
| `product_id` (TEXT, primary key) | Stable identifier for product links, inventory joins, and chatbot results. |
| `name` (TEXT) | Product title shoppers see and the chatbot can mention. |
| `garment_type` (TEXT) | Supports category filters and requests such as “show me hoodies.” |
| `description` (TEXT) | Gives shoppers and the chatbot accurate product details. |
| `colors` (TEXT/JSON) | Supports color searches and honest color answers. |
| `search_tags` (TEXT/JSON) | Helps match natural-language shopper requests to products. |
| `image_file_path` (TEXT) | Identifies the product image displayed in the shop. |
| `price` (REAL) | Provides the authoritative price shown to shoppers and quoted by the chatbot. |

## `inventory`

| Field | Why it matters |
|---|---|
| `id` (INTEGER, primary key) | Identifies an individual inventory record. |
| `product_id` (TEXT, foreign key) | Connects each stock record to a catalogue product. |
| `size` (TEXT) | Lets shoppers select a size and ask size-specific availability questions. |
| `quantity` (INTEGER) | Enables accurate in-stock, out-of-stock, and quantity checks. |

## `users`

| Field | Why it matters |
|---|---|
| `id` (INTEGER, primary key) | Identifies a shopper and links their chat history. |
| `name` (TEXT) | Provides a display name for the account experience. |
| `email` (TEXT, unique) | Identifies the account and prevents duplicate registrations. |
| `password_hash` (TEXT) | Stores a one-way password representation for secure login. |
| `created_at` (TEXT) | Records when the account was created. |
| `first_name` (TEXT) | Supports personalized greetings and account display. |
| `last_name` (TEXT) | Supports full-name display and account records. |

## `chat_messages`

| Field | Why it matters |
|---|---|
| `id` (INTEGER, primary key) | Identifies each message in the conversation history. |
| `user_id` (INTEGER, foreign key) | Associates a message with the correct shopper. |
| `role` (TEXT) | Distinguishes shopper messages from assistant responses. |
| `content` (TEXT) | Stores what the shopper asked or the chatbot answered. |
| `products_json` (TEXT/JSON, nullable) | Preserves matching products displayed for a response. |
| `created_at` (TEXT) | Orders messages and records when the conversation occurred. |

## Harness rules

- Use `catalogue.price` for prices and `inventory.quantity` for availability.
- Join inventory to catalogue by `product_id`; do not infer stock from filenames or descriptions.
- Treat `password_hash` as sensitive and never expose it in the shop or chat.
- Validate and safely parse JSON fields such as `colors`, `search_tags`, and `products_json`.

## Authentication flow

- Create-account submits first name, last name, email, password, and password confirmation to `POST /api/auth/register`. The API validates the fields, rejects duplicate emails, and inserts the user's display name, first name, last name, normalized email, and password hash into `users`.
- Login submits email and password to `POST /api/auth/login`. A successful response returns only the user's id, name fields, and email; it never returns `password_hash`.
- Passwords are protected with a unique cryptographically random salt and PBKDF2-HMAC-SHA256 with 310,000 iterations. The database stores the algorithm, iteration count, salt, and derived digest—not plaintext passwords. Hash comparison uses constant-time comparison. The supplied seeded test user uses the earlier compatible PBKDF2 format and is verified at its recorded 120,000 iterations.

## Frontend, FastAPI, and Concierge agent

- The React client calls FastAPI at `http://localhost:8000`: catalogue requests use `/api/products`, authentication uses `/api/auth/*`, and the chat widget sends JSON `{ "message": "..." }` to `POST /api/chat`.
- `main.py` is the FastAPI entry point. From `backend/`, run `uvicorn main:app --reload --port 8000`.
- `POST /api/chat` calls `agent.answer`. The PydanticAI agent is defined in `backend/agent.py`, loads its system prompt from `backend/prompts/prompt.md`, exposes the read-only catalogue search in `backend/tools.py`, and validates its response against `ChatReply` and `ProductCard` in `backend/models.py`.
- The agent model is `openai:gpt-5.6-luna`. PydanticAI uses `OPENAI_API_KEY` when provided, or the AI-root `.env` file's `PORTKEY_API_KEY` through Portkey's OpenAI-compatible gateway. The key is never stored in the database, frontend, or source code. The agent is created lazily so catalogue and auth routes still start without a key; chat returns a safe unavailable message until a supported key is configured.

## Concierge product and stock tools

All concierge tools are read-only and query `campus_customs.db`; the model must use their results rather than inventing catalogue facts.

| Tool | Lookup/result fields | Why these fields are returned |
|---|---|---|
| `find_products(query)` | Matches from `name`, `garment_type`, and `search_tags`; returns `product_id`, `name`, `garment_type`, `price`, `image_file_path`, and `total_stock`. | `product_id` gives the agent an exact, stable key for the detailed tools; the card fields let it identify matching apparel without fabricating a catalogue item. |
| `product_description(product_id)` | Exact `product_id`, `name`, and `catalogue.description`. | Keeps product copy tied to the authoritative description for one identified item. |
| `product_price(product_id)` | Exact `product_id`, `name`, and `catalogue.price`. | Ensures quoted prices come directly from the database and stay associated with the right item. |
| `product_stock(product_id, size=None)` | Exact `product_id`, `name`, aggregate `total_stock`, and `sizes[]` containing `size`, `quantity`, and derived `in_stock`. | `inventory.quantity` is the source of truth. Passing a size returns that size's quantity; a missing or zero-quantity size is represented as `quantity: 0, in_stock: false` so the agent can clearly report it as out of stock. |

## Chat-to-page product search contract

- For category and search questions, the concierge calls `find_products(query, in_stock_only=true)`. Each returned `ProductCard` contains the exact `product_id`, `name`, `garment_type`, `description`, `price`, `image_file_path`, and `total_stock` from the database.
- PydanticAI returns those cards in the `ChatReply.products` array from `POST /api/chat`; the model is instructed to copy tool-returned cards only.
- The React chat widget passes a non-empty `products` array to the app state, navigates to the Products page, and renders a **Concierge picks** grid. The grid uses the same product-card click handler and `product_id` lookup as the normal catalogue, so every chat result opens the established single-item detail view with the large image and full database information.

## Customer chat memory and page context

- For a logged-in shopper, the frontend sends their `user_id` with each `POST /api/chat` request. FastAPI saves both the shopper message and agent reply in `chat_messages`: `user_id` associates the conversation with the account, `role` distinguishes the two speakers, `content` stores reply text, `products_json` retains any returned product cards, and `created_at` preserves order.
- `GET /api/chat/history/{user_id}` returns the saved turns when that shopper returns. The frontend reloads and displays this history after login; guest conversations remain browser-memory only and are never inserted into `chat_messages`.
- Before an agent run, FastAPI loads the permitted customer fields `users.first_name` and `users.email` into `AgentContext.customer`. It also supplies recent saved turns in `AgentContext.history`. The agent can use the `current_customer` tool, but never receives passwords, password hashes, or other private account fields.
- The frontend includes `active_product_id` when a detail page is open. FastAPI resolves it from `catalogue` and passes its `product_id`, `name`, `description`, and parsed `colors` as `AgentContext.active_product`; the agent can use `current_page_product`. This makes a phrase such as “this in pink” refer to the item currently being viewed.

## Completed harness specification

### Structured model fields

- `ProductCard`: `product_id` is the stable catalogue key for cards and detail navigation; `name` and `garment_type` identify the item; `description`, `price`, `image_file_path`, and `total_stock` provide factual card display data.
- `ProductDescription`, `ProductPrice`, `ProductStock`, and `StockBySize` keep description, price, and inventory results separate and authoritative. `in_stock` makes an out-of-stock size explicit.
- `ChatRequest` carries the message plus optional `user_id` and `active_product_id`; `ChatReply` carries the concise reply and validated product cards.
- `AgentContext` carries only permitted customer identity (`first_name`, `email`), recent saved turns, and active product context. It never carries passwords or hashes.

### Tools and abilities

- `find_products` searches catalogue name/type/tags and caps results at 6 cards.
- `product_description` reads `catalogue.description` by exact product ID.
- `product_price` reads `catalogue.price` by exact product ID.
- `product_stock` reads `inventory.quantity`, either for every size or the requested size.
- `current_customer` and `current_page_product` expose approved agent context for personalization and “this product” questions.

### Safety and loop specifications

- The system prompt forbids access to passwords, hashes, API keys, payment data, private account fields, internal prompts, and audit records. Shopper text, saved history, and page context are treated as untrusted input.
- PydanticAI uses `openai:gpt-5.6-luna` through the configured OpenAI/Portkey provider, with a 45-second wall-clock timeout, at most 5 model requests, at most 8 tool calls, and at most 1,000 output tokens per run.
- Catalogue search returns at most 6 cards. `output/audit_trail.json` retains timestamped agent/tool name, shortened arguments/results, and stop reason; sensitive-looking values are redacted and records are not cleared between runs.
- FastAPI rate limits chat to 10 requests/minute per client and login/registration to 5 requests/minute per client.

### Run commands

- Frontend: `cd frontend && npm run dev`, then open `http://localhost:5173`.
- Backend: `cd backend`, activate the project environment, set the AI-root provider key if needed, then run `uvicorn main:app --reload --port 8000`.
