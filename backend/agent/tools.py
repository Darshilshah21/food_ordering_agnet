from contextvars import ContextVar
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from sqlalchemy import select
from typing import Optional
from backend.database.database_in import SessionLocal
from backend.database.models import MenuItem
from backend.services.order_service import create_order, get_order, sales_summary
from backend.rag.retriever import search_menu as rag_search


# Set by run_agent() for the current HTTP request. The model never has to guess
# or supply a customer ID.
CURRENT_USER_ID: ContextVar[str] = ContextVar("CURRENT_USER_ID", default="default-user")


class OrderLine(BaseModel):
    item: str = Field(
        min_length=1,
        description="The food/drink name exactly as expressed by the customer, e.g. 'veg burger' or 'marg pizza'.",
    )
    quantity: int = Field(gt=0, le=50)


@tool
def search_menu(query: str) -> str:
    """Search the restaurant menu for information such as names, categories, descriptions and prices."""
    docs = rag_search(query)
    if not docs:
        return "No matching menu items found."
    return "\n\n".join(d.page_content for d in docs)


@tool
def get_menu() -> str:
    """Return the complete currently available restaurant menu with canonical names and prices."""
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(MenuItem)
            .where(MenuItem.is_available.is_(True))
            .order_by(MenuItem.category, MenuItem.name)
        ).all()
        return "\n".join(
            f"{m.id}. {m.name} | {m.category} | ₹{m.price} | {m.description}"
            for m in rows
        )
    finally:
        db.close()


@tool
def create_food_order(items: list[OrderLine]) -> str:
    """Place a food order. Pass every requested item as {item: customer food name, quantity: number}. The tool deterministically resolves names to the real menu and validates availability."""
    db = SessionLocal()
    try:
        payload = [x.model_dump() if hasattr(x, "model_dump") else dict(x) for x in items]
        order = create_order(db, payload, user_id=CURRENT_USER_ID.get())
        lines = [
            f"{x.menu_item.name} x{x.quantity} = ₹{x.subtotal}"
            for x in order.items
        ]
        return (
            f"ORDER_CREATED id={order.id} total=₹{order.total_amount}\n"
            + "\n".join(f"- {line}" for line in lines)
        )
    except Exception as exc:
        db.rollback()
        # Normal validation failures are tool results, not HTTP 503 errors.
        return f"ORDER_NOT_CREATED reason={type(exc).__name__}: {exc}"
    finally:
        db.close()



@tool
# def get_order_details(order_id: int) -> str:
def get_order_details(order_id: Optional[int] = None):
    """Get details of a previously created order."""
    db = SessionLocal()
    try:
        order = get_order(db, order_id)
        if not order:
            return f"Order {order_id} was not found."
        lines = [f"Order #{order.id}: ₹{order.total_amount} ({order.status})"]
        lines += [
            f"- {x.menu_item.name} x{x.quantity} = ₹{x.subtotal}"
            for x in order.items
        ]
        return "\n".join(lines)
    finally:
        db.close()


@tool
def get_sales_summary() -> str:
    """Return overall sales and best-selling item information, including user-wise order totals."""
    db = SessionLocal()
    try:
        data = sales_summary(db)
        best = ", ".join(
            f"{x['name']} ({x['quantity']})" for x in data["best_selling_items"]
        )
        users = "; ".join(
            f"{x['user_id']}: {x['order_count']} orders, ₹{x['total']:.2f}"
            for x in data["user_wise"]
        ) or "No users/orders yet"
        return (
            f"Orders: {data['total_orders']}; Sales: ₹{data['total_sales']:.2f}; "
            f"Best sellers: {best or 'none'}; User-wise: {users}"
        )
    finally:
        db.close()


TOOLS = [
    search_menu,
    get_menu,
    create_food_order,
    get_order_details,
    get_sales_summary,
]
