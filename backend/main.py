from pathlib import Path
import json
import sqlite3
import hashlib
import hmac
import secrets
import logging
import os
import time
from collections import defaultdict, deque
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
# Load the user's AI-root configuration without logging or exposing its values.
# Existing shell environment values take precedence.
load_dotenv(ROOT.parent / '.env')

try:
    from .agent import answer
    from .models import AgentContext, ChatRequest, ChatReply, CustomerContext, PageContext, StoredChatMessage
except ImportError:  # Supports `uvicorn main:app` when run inside backend/.
    from agent import answer
    from models import AgentContext, ChatRequest, ChatReply, CustomerContext, PageContext, StoredChatMessage

logger = logging.getLogger(__name__)
DATABASE = ROOT / 'data' / 'campus_customs.db'
PRODUCTS = ROOT / 'data' / 'products'
app = FastAPI(title='Campus Customs API')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'], allow_methods=['*'], allow_headers=['*'])
app.mount('/media', StaticFiles(directory=ROOT / 'data'), name='media')

# Per-process limits protect the local API from rapid chat abuse and credential guessing.
RATE_LIMITS = {'/api/chat': (10, 60), '/api/auth/login': (5, 60), '/api/auth/register': (5, 60)}
rate_limit_events: dict[str, deque[float]] = defaultdict(deque)

@app.middleware('http')
async def rate_limit(request: Request, call_next):
    limit = RATE_LIMITS.get(request.url.path)
    if limit and request.method == 'POST':
        max_requests, window_seconds = limit
        client = request.client.host if request.client else 'unknown'
        key = f'{request.url.path}:{client}'
        now = time.monotonic()
        events = rate_limit_events[key]
        while events and now - events[0] >= window_seconds:
            events.popleft()
        if len(events) >= max_requests:
            return JSONResponse(status_code=429, content={'detail': 'Too many requests. Please wait a minute and try again.'})
        events.append(now)
    return await call_next(request)

def ensure_user_privacy_column() -> None:
    with sqlite3.connect(DATABASE) as db:
        columns = {row[1] for row in db.execute('PRAGMA table_info(users)').fetchall()}
        if 'chat_memory_enabled' not in columns:
            db.execute('ALTER TABLE users ADD COLUMN chat_memory_enabled INTEGER NOT NULL DEFAULT 1')

ensure_user_privacy_column()

PASSWORD_ITERATIONS = 310_000

class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    confirm_password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=200)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    current_password: str | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=256)

def hash_password(password: str) -> str:
    """Return a salted PBKDF2-SHA256 password hash; never store plaintext passwords."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), PASSWORD_ITERATIONS).hex()
    return f'pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}'

def password_matches(password: str, stored_hash: str) -> bool:
    """Verify current hashes plus the seeded three-part 120k-iteration test hash."""
    try:
        parts = stored_hash.split('$')
        if len(parts) == 4 and parts[0] == 'pbkdf2_sha256':
            _, iterations, salt, expected = parts
        elif len(parts) == 3 and parts[0] == 'pbkdf2_sha256':
            _, salt, expected = parts
            iterations = '120000'
        else:
            return False
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), int(iterations)).hex()
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False

def row_to_product(row: sqlite3.Row, inventory: list[dict]) -> dict:
    stock = sum(item['quantity'] for item in inventory)
    return {**dict(row), 'colors': json.loads(row['colors']), 'search_tags': json.loads(row['search_tags']), 'inventory': inventory, 'total_stock': stock}

def fetch_products(product_id: str | None = None):
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        query = 'SELECT * FROM catalogue' + (' WHERE product_id = ?' if product_id else '') + ' ORDER BY name'
        rows = db.execute(query, (product_id,) if product_id else ()).fetchall()
        result = []
        for row in rows:
            stock = db.execute('SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY id', (row['product_id'],)).fetchall()
            result.append(row_to_product(row, [dict(item) for item in stock]))
        return result

def load_chat_history(user_id: int) -> list[StoredChatMessage]:
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute('SELECT role, content, products_json, created_at FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT 30', (user_id,)).fetchall()
    history = []
    for row in reversed(rows):
        try:
            products = json.loads(row['products_json']) if row['products_json'] else []
        except json.JSONDecodeError:
            products = []
        history.append(StoredChatMessage(role=row['role'], content=row['content'], products=products, created_at=row['created_at']))
    return history

def build_agent_context(user_id: int | None, active_product_id: str | None) -> AgentContext:
    customer = None
    if user_id is not None:
        with sqlite3.connect(DATABASE) as db:
            db.row_factory = sqlite3.Row
            user = db.execute('SELECT first_name, email, chat_memory_enabled FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            customer = CustomerContext(first_name=user['first_name'], email=user['email'])
        else:
            raise HTTPException(status_code=404, detail='Account not found')
    active_product = None
    if active_product_id:
        product = fetch_products(active_product_id)
        if product:
            active_product = PageContext(product_id=product[0]['product_id'], name=product[0]['name'], description=product[0]['description'], colors=product[0]['colors'])
    return AgentContext(customer=customer, active_product=active_product, history=load_chat_history(user_id) if customer and user['chat_memory_enabled'] else [])

def save_chat_message(user_id: int, role: str, content: str, products: list[dict] | None = None) -> None:
    with sqlite3.connect(DATABASE) as db:
        db.execute('INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)', (user_id, role, content, json.dumps(products) if products else None))

@app.get('/api/health')
def health(): return {'status': 'ok', 'chat_api_key_configured': bool(os.getenv('OPENAI_API_KEY') or os.getenv('PORTKEY_API_KEY')), 'chat_model': 'openai:gpt-5.6-luna', 'chat_provider': 'openai' if os.getenv('OPENAI_API_KEY') else 'portkey' if os.getenv('PORTKEY_API_KEY') else None}

@app.get('/api/products')
def products(): return fetch_products()

@app.get('/api/products/{product_id}')
def product(product_id: str):
    result = fetch_products(product_id)
    if not result: raise HTTPException(status_code=404, detail='Product not found')
    return result[0]

@app.get('/api/chat/history/{user_id}', response_model=list[StoredChatMessage])
def chat_history(user_id: int):
    with sqlite3.connect(DATABASE) as db:
        exists = db.execute('SELECT 1 FROM users WHERE id = ?', (user_id,)).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail='Account not found')
    return load_chat_history(user_id)

@app.get('/api/users/{user_id}/privacy')
def get_privacy(user_id: int):
    with sqlite3.connect(DATABASE) as db:
        row = db.execute('SELECT chat_memory_enabled FROM users WHERE id = ?', (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Account not found')
    return {'chat_memory_enabled': bool(row[0])}

@app.put('/api/users/{user_id}/privacy')
def update_privacy(user_id: int, payload: dict):
    enabled = bool(payload.get('chat_memory_enabled'))
    with sqlite3.connect(DATABASE) as db:
        cursor = db.execute('UPDATE users SET chat_memory_enabled = ? WHERE id = ?', (int(enabled), user_id))
    if not cursor.rowcount:
        raise HTTPException(status_code=404, detail='Account not found')
    return {'chat_memory_enabled': enabled}

@app.get('/api/users/{user_id}/chat-export', response_model=list[StoredChatMessage])
def export_chat_history(user_id: int):
    return chat_history(user_id)

@app.delete('/api/users/{user_id}/chat-history', status_code=204)
def delete_chat_history(user_id: int):
    with sqlite3.connect(DATABASE) as db:
        cursor = db.execute('DELETE FROM chat_messages WHERE user_id = ?', (user_id,))
    if cursor.rowcount == 0:
        with sqlite3.connect(DATABASE) as db:
            exists = db.execute('SELECT 1 FROM users WHERE id = ?', (user_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail='Account not found')

@app.post('/api/chat', response_model=ChatReply)
async def chat(payload: ChatRequest):
    try:
        context = build_agent_context(payload.user_id, payload.active_product_id)
        reply = await answer(payload.message, context)
        if payload.user_id is not None and context.history is not None:
            with sqlite3.connect(DATABASE) as db:
                memory_enabled = db.execute('SELECT chat_memory_enabled FROM users WHERE id = ?', (payload.user_id,)).fetchone()[0]
        else:
            memory_enabled = False
        if payload.user_id is not None and memory_enabled:
            save_chat_message(payload.user_id, 'user', payload.message)
            save_chat_message(payload.user_id, 'assistant', reply.reply, [product.model_dump() for product in reply.products])
        return reply
    except Exception as error:
        # Do not expose provider or API-key details to the browser.
        logger.exception('Campus Concierge request failed')
        print(f'Campus Concierge request failed: {type(error).__name__}: {error}', flush=True)
        raise HTTPException(status_code=503, detail='Campus Concierge is temporarily unavailable. Please try again shortly.') from error

@app.post('/api/auth/register', status_code=201)
def register(payload: RegisterRequest):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail='Passwords do not match')
    email = str(payload.email).lower()
    first_name, last_name = payload.first_name.strip(), payload.last_name.strip()
    if not first_name or not last_name:
        raise HTTPException(status_code=400, detail='First and last name are required')
    try:
        with sqlite3.connect(DATABASE) as db:
            cursor = db.execute(
                'INSERT INTO users (name, first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?, ?)',
                (f'{first_name} {last_name}', first_name, last_name, email, hash_password(payload.password)),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail='An account with that email already exists')
    return {'id': user_id, 'username': first_name, 'first_name': first_name, 'last_name': last_name, 'email': email}

@app.post('/api/auth/login')
def login(payload: LoginRequest):
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        user = db.execute('SELECT id, first_name, last_name, email, password_hash FROM users WHERE email = ?', (str(payload.email).lower(),)).fetchone()
    if not user or not password_matches(payload.password, user['password_hash']):
        raise HTTPException(status_code=401, detail='Email or password is incorrect')
    return {'id': user['id'], 'username': user['first_name'] or user['name'], 'first_name': user['first_name'], 'last_name': user['last_name'], 'email': user['email']}

@app.put('/api/users/{user_id}')
def update_profile(user_id: int, payload: ProfileUpdateRequest):
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        user = db.execute('SELECT password_hash, email FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail='Account not found')
        if payload.new_password:
            if not payload.current_password or not password_matches(payload.current_password, user['password_hash']):
                raise HTTPException(status_code=401, detail='Enter your current password to set a new password')
            db.execute('UPDATE users SET name = ?, first_name = ?, last_name = ?, password_hash = ? WHERE id = ?', (payload.username.strip(), payload.first_name.strip(), payload.last_name.strip(), hash_password(payload.new_password), user_id))
        else:
            db.execute('UPDATE users SET name = ?, first_name = ?, last_name = ? WHERE id = ?', (payload.username.strip(), payload.first_name.strip(), payload.last_name.strip(), user_id))
    return {'id': user_id, 'username': payload.username.strip(), 'first_name': payload.first_name.strip(), 'last_name': payload.last_name.strip(), 'email': user['email']}
