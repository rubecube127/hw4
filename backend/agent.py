import os
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

try:
    from .models import AgentContext, ChatReply, CustomerContext, PageContext, ProductCard, ProductDescription, ProductPrice, ProductStock
    from .tools import get_product_description, get_product_price, get_product_stock, search_products
except ImportError:  # Supports `uvicorn main:app` when run inside backend/.
    from models import AgentContext, ChatReply, CustomerContext, PageContext, ProductCard, ProductDescription, ProductPrice, ProductStock
    from tools import get_product_description, get_product_price, get_product_stock, search_products

PROMPT_PATH = Path(__file__).parent / 'prompts' / 'prompt.md'
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding='utf-8')
MODEL_NAME = os.getenv('CAMPUS_CUSTOMS_MODEL', 'openai:gpt-5.6-luna')
AUDIT_PATH = Path(__file__).resolve().parents[1] / 'output' / 'audit_trail.json'
_audit_lock = Lock()


def _short(value: object, limit: int = 240) -> str:
    text = str(value).replace('\n', ' ')
    for secret_name in ('password', 'api_key', 'token', 'hash'):
        if secret_name in text.lower():
            return '[redacted sensitive value]'
    return text[:limit] + ('…' if len(text) > limit else '')


def audit_event(tool_name: str, args: object, result: object, stop_reason: str) -> None:
    """Append one non-sensitive agent activity record without exposing secrets."""
    with _audit_lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        event = {'time': datetime.now(timezone.utc).isoformat(), 'tool_name': tool_name, 'args': _short(args), 'result': _short(result), 'stop_reason': stop_reason}
        try:
            records = json.loads(AUDIT_PATH.read_text(encoding='utf-8')) if AUDIT_PATH.exists() else []
            if not isinstance(records, list): records = []
        except (OSError, json.JSONDecodeError):
            records = []
        records.append(event)
        AUDIT_PATH.write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')


def configured_model() -> str | OpenAIResponsesModel:
    """Use a direct OpenAI key when supplied, otherwise use the AI-root Portkey gateway."""
    if os.getenv('OPENAI_API_KEY'):
        return MODEL_NAME
    portkey_key = os.getenv('PORTKEY_API_KEY')
    if not portkey_key:
        raise RuntimeError('Neither OPENAI_API_KEY nor PORTKEY_API_KEY is configured')
    return OpenAIResponsesModel(
        MODEL_NAME.removeprefix('openai:'),
        provider=OpenAIProvider(api_key=portkey_key, base_url='https://api.portkey.ai/v1'),
    )

def context_instructions(context: AgentContext) -> str:
    lines = ['Conversation context supplied by the application:']
    if context.customer:
        lines.append(f'Logged-in shopper: {context.customer.first_name} ({context.customer.email}). You may greet them by first name, but do not repeat their email unless needed.')
    else:
        lines.append('Shopper is a guest; do not imply that you know their identity.')
    if context.active_product:
        product = context.active_product
        lines.append(f'Active product page: {product.name} (product_id: {product.product_id}); description: {product.description}; colors: {", ".join(product.colors)}. Pronouns like “this” refer to this product.')
    if context.history:
        lines.append('Recent saved conversation (for continuity only):')
        lines.extend(f'{turn.role}: {turn.content}' for turn in context.history[-12:])
    return '\n'.join(lines)


async def answer(message: str, context: AgentContext) -> ChatReply:
    # Create the provider lazily so the FastAPI app can start and expose health/product
    # routes even before the developer supplies OPENAI_API_KEY.
    agent = Agent(configured_model(), output_type=ChatReply, system_prompt=SYSTEM_PROMPT, deps_type=AgentContext)

    @agent.tool
    def current_customer(ctx: RunContext[AgentContext]) -> CustomerContext | None:
        """Return the logged-in shopper's permitted name and email, if present."""
        result = ctx.deps.customer
        audit_event('current_customer', {}, 'available' if result else 'guest', 'tool_completed')
        return result

    @agent.tool
    def current_page_product(ctx: RunContext[AgentContext]) -> PageContext | None:
        """Return the product currently open in the shopper's browser, if any."""
        result = ctx.deps.active_product
        audit_event('current_page_product', {}, result.product_id if result else 'none', 'tool_completed')
        return result

    @agent.tool_plain
    def find_products(query: str, in_stock_only: bool = False) -> list[ProductCard]:
        """Find catalogue products matching a shopper's request; optionally include only available items."""
        result = search_products(query, limit=6, in_stock_only=in_stock_only)
        audit_event('find_products', {'query': query, 'in_stock_only': in_stock_only}, f'{len(result)} product cards', 'tool_completed')
        return result

    @agent.tool_plain
    def product_description(product_id: str) -> ProductDescription | None:
        """Get the exact catalogue description using a product ID from find_products."""
        result = get_product_description(product_id)
        audit_event('product_description', {'product_id': product_id}, result.name if result else 'not found', 'tool_completed')
        return result

    @agent.tool_plain
    def product_price(product_id: str) -> ProductPrice | None:
        """Get the exact database price using a product ID from find_products."""
        result = get_product_price(product_id)
        audit_event('product_price', {'product_id': product_id}, result.price if result else 'not found', 'tool_completed')
        return result

    @agent.tool_plain
    def product_stock(product_id: str, size: str | None = None) -> ProductStock | None:
        """Get total or size-specific inventory using a product ID from find_products."""
        result = get_product_stock(product_id, size)
        audit_event('product_stock', {'product_id': product_id, 'size': size}, result.sizes if result else 'not found', 'tool_completed')
        return result

    # A bounded request keeps the local FastAPI service responsive if a provider stalls.
    audit_event('agent_loop', {'message': message}, 'started', 'started')
    try:
        result = await asyncio.wait_for(agent.run(message, deps=context, instructions=context_instructions(context), usage_limits=UsageLimits(request_limit=5, tool_calls_limit=8, output_tokens_limit=1000)), timeout=45)
        audit_event('agent_loop', {'message': message}, 'reply generated', 'completed')
        return result.output
    except Exception as error:
        audit_event('agent_loop', {'message': message}, type(error).__name__, 'stopped_error')
        raise
