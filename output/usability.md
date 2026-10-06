# Campus Customs Usability Improvements

## Frontend improvements

| Improvement | What was added | Why it helps a Campus Customs shopper or business |
|---|---|---|
| Account menu and settings | A click-only account menu provides My Account, Settings, and Log out. Settings let shoppers update their username, name fields, password, chat-memory preference, and saved chat data. | Shoppers have a clear, compact place to manage their account and privacy without cluttering the main store navigation. |
| Scrollable minimized chat panel | The concierge panel has a bounded height, scrollable message history, and a persistent message input. | Long conversations no longer cover the storefront or hide the input, so shoppers can keep browsing and chatting comfortably. |

## Backend and agent improvements

| Improvement | What was added | Why it helps a Campus Customs shopper or business |
|---|---|---|
| Request rate limiting | FastAPI limits each client to 10 chat requests per minute and 5 login or registration attempts per minute. Requests beyond the limit receive a clear `429` response. | Helps protect shoppers from abusive behavior and protects the business from password-guessing attempts, chat spam, and unexpected model-provider costs. |
| User privacy controls | Authenticated users can turn future chat-memory saving on or off, download their saved history, or permanently delete it. The backend stores future turns only when `chat_memory_enabled` is true. | Gives shoppers meaningful control over their conversation data while preserving optional continuity for customers who want it. |

## Verification performed

- The React production build completed successfully.
- Python compilation passed for `main.py`, `agent.py`, `models.py`, and `tools.py`.
- The API privacy schema creates a default-enabled `chat_memory_enabled` column for existing users without losing existing account data.
- A focused authentication test verified that the sixth rapid login attempt receives the expected `429` rate-limit response.
