# Campus Customs (hw4)

Campus Customs is a Yale-themed storefront with a FastAPI/PydanticAI concierge and a Vite frontend.

## Place the data pack

Copy the provided private data pack into these paths (it is intentionally excluded from GitHub):

- `data/campus_customs.db`
- `data/products/` (the product image files)

Create a local `.env` file from `.env.example` and set your own `PORTKEY_API_KEY`. Do not commit `.env` or the data pack.

## Run the backend

From the project root, create/activate the virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start FastAPI:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API is available at `http://localhost:8000`.

## Run the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL Vite prints (normally `http://localhost:5173`). The frontend uses the FastAPI server at port 8000 for authentication, catalogue search, and chat.

For a production frontend build:

```bash
npm run build
```
