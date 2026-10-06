# Campus Customs Database

Readable inspection of `data/campus_customs.db`.

## Tables and row counts

| Table | Rows | Purpose |
|---|---:|---|
| `catalogue` | 102 | Product descriptions, search metadata, images, and prices |
| `inventory` | 612 | Stock quantities by product and size |
| `users` | 3 | Shopper account records |
| `chat_messages` | 22 | Chat history and products shown by the chatbot |

## Relationships

- `inventory.product_id` references `catalogue.product_id`.
- `chat_messages.user_id` references `users.id`.
- `inventory` allows one row per product and size through its unique `(product_id, size)` constraint.

## Example catalogue rows

| Product | Type | Price | Colors | Image |
|---|---|---:|---|---|
| 2025 Yale Vs Harvard T Shirt | short-sleeve T-shirt | $32.00 | heather gray, white, red, navy blue | `products/2025-yale-vs-harvard-t-shirt.jpg` |
| Baseball Left Chest Crewneck | crewneck sweatshirt | $58.00 | navy, white | `products/baseball-left-chest-crewneck.jpg` |
| Basic Hoodie Big Yale | pullover hoodie | $68.00 | navy blue, white | `products/basic-hoodie-big-yale.jpg` |
| Benjamin Franklin 1 4 Zip | quarter-zip pullover sweatshirt | $72.00 | heather gray, blue, red, white | `products/benjamin-franklin-1-4-zip.jpg` |
| Benjamin Franklin Fleece Jacket | full-zip fleece jacket | $98.00 | gray, blue, red, white | `products/benjamin-franklin-fleece-jacket.jpg` |

## Example inventory rows

| Product | Size | Quantity |
|---|---|---:|
| 2025 Yale Vs Harvard T Shirt | XS | 25 |
| 2025 Yale Vs Harvard T Shirt | S | 25 |
| 2025 Yale Vs Harvard T Shirt | M | 20 |
| 2025 Yale Vs Harvard T Shirt | L | 2 |
| Baseball Left Chest Crewneck | XS | 0 |
| Baseball Left Chest Crewneck | S | 15 |

## Example account and chat data

The database contains three user accounts. The chat table stores user and assistant messages, timestamps, and optional JSON product results attached to a conversation. Passwords are stored as hashes rather than plain text.
