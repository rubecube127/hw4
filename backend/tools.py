import json
import sqlite3
from pathlib import Path

try:
    from .models import ProductCard, ProductDescription, ProductPrice, ProductStock, StockBySize
except ImportError:  # Supports `uvicorn main:app` when run inside backend/.
    from models import ProductCard, ProductDescription, ProductPrice, ProductStock, StockBySize

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / 'data' / 'campus_customs.db'


def search_products(query: str, limit: int = 6, in_stock_only: bool = False) -> list[ProductCard]:
    """Read-only catalogue search for the concierge agent."""
    terms = [term.lower() for term in query.split() if len(term) > 1]
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute('SELECT * FROM catalogue ORDER BY name').fetchall()
        results: list[ProductCard] = []
        for row in rows:
            haystack = ' '.join((row['name'], row['garment_type'], row['search_tags'])).lower()
            if not terms or any(term in haystack for term in terms):
                stock = db.execute('SELECT COALESCE(SUM(quantity), 0) FROM inventory WHERE product_id = ?', (row['product_id'],)).fetchone()[0]
                if not in_stock_only or stock > 0:
                    results.append(ProductCard(product_id=row['product_id'], name=row['name'], garment_type=row['garment_type'], description=row['description'], price=row['price'], image_file_path=row['image_file_path'], total_stock=stock))
            if len(results) >= limit:
                break
    return results


def get_product_description(product_id: str) -> ProductDescription | None:
    """Look up a product's database description by its exact product ID."""
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        row = db.execute('SELECT product_id, name, description FROM catalogue WHERE product_id = ?', (product_id,)).fetchone()
    return ProductDescription(**dict(row)) if row else None


def get_product_price(product_id: str) -> ProductPrice | None:
    """Look up a product's current database price by its exact product ID."""
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        row = db.execute('SELECT product_id, name, price FROM catalogue WHERE product_id = ?', (product_id,)).fetchone()
    return ProductPrice(**dict(row)) if row else None


def get_product_stock(product_id: str, size: str | None = None) -> ProductStock | None:
    """Look up stock by product ID, optionally for one requested size."""
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        product = db.execute('SELECT product_id, name FROM catalogue WHERE product_id = ?', (product_id,)).fetchone()
        if not product:
            return None
        total_stock = db.execute('SELECT COALESCE(SUM(quantity), 0) FROM inventory WHERE product_id = ?', (product_id,)).fetchone()[0]
        if size:
            row = db.execute('SELECT size, quantity FROM inventory WHERE product_id = ? AND lower(size) = lower(?)', (product_id, size)).fetchone()
            sizes = [StockBySize(size=row['size'], quantity=row['quantity'], in_stock=row['quantity'] > 0)] if row else [StockBySize(size=size, quantity=0, in_stock=False)]
        else:
            rows = db.execute('SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY id', (product_id,)).fetchall()
            sizes = [StockBySize(size=row['size'], quantity=row['quantity'], in_stock=row['quantity'] > 0) for row in rows]
    return ProductStock(product_id=product['product_id'], name=product['name'], total_stock=total_stock, sizes=sizes)
