from pydantic import BaseModel, Field
from dataclasses import dataclass


class ProductCard(BaseModel):
    product_id: str
    name: str
    garment_type: str
    description: str
    price: float
    image_file_path: str
    total_stock: int


class ProductDescription(BaseModel):
    """Authoritative description returned from catalogue.description."""
    product_id: str
    name: str
    description: str


class ProductPrice(BaseModel):
    """Authoritative price returned from catalogue.price."""
    product_id: str
    name: str
    price: float


class StockBySize(BaseModel):
    """A single size's quantity from inventory; zero means unavailable."""
    size: str
    quantity: int
    in_stock: bool


class ProductStock(BaseModel):
    product_id: str
    name: str
    total_stock: int
    sizes: list[StockBySize]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    user_id: int | None = None
    active_product_id: str | None = None


class ChatReply(BaseModel):
    reply: str = Field(description='A concise, helpful answer for the shopper.')
    products: list[ProductCard] = Field(default_factory=list, description='Relevant catalogue products, if any.')


class StoredChatMessage(BaseModel):
    role: str
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str


class CustomerContext(BaseModel):
    first_name: str
    email: str


class PageContext(BaseModel):
    product_id: str
    name: str
    description: str
    colors: list[str]


@dataclass
class AgentContext:
    customer: CustomerContext | None = None
    active_product: PageContext | None = None
    history: list[StoredChatMessage] | None = None
