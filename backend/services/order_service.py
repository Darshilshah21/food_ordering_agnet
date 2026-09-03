import re
import unicodedata
from decimal import Decimal
from difflib import SequenceMatcher
from typing import Optional, Union

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.database.models import MenuItem, Order, OrderItem


# Common speech/typing variants. The canonical menu name always comes from DB.
ALIASES = {
    "veg burger": "Veg Burger",
    "vegetable burger": "Veg Burger",
    "veggie burger": "Veg Burger",
    "burger veg": "Veg Burger",
    "veg-burger": "Veg Burger",
    "burger-veg": "Veg Burger",
    "vegburger": "Veg Burger",

    "chicken burger": "Chicken Burger",
    "burger chicken": "Chicken Burger",
    "chicken-burger": "Chicken Burger",

    "margherita": "Margherita Pizza",
    "margherita pizza": "Margherita Pizza",
    "marg pizza": "Margherita Pizza",
    "margarita pizza": "Margherita Pizza",
    "margareta pizza": "Margherita Pizza",
    "margareta": "Margherita Pizza",
    "margherita-pizza": "Margherita Pizza",

    "farmhouse": "Farmhouse Pizza",
    "farmhouse pizza": "Farmhouse Pizza",
    "farmhouse-pizza": "Farmhouse Pizza",

    "chicken tikka": "Chicken Tikka Pizza",
    "chicken tikka pizza": "Chicken Tikka Pizza",
    "chicken-tikka-pizza": "Chicken Tikka Pizza",

    "coke": "Coke",
    "coca cola": "Coke",
    "coca-cola": "Coke",

    "fries": "French Fries",
    "french fries": "French Fries",
    "cheese fries": "Cheese Fries",

    "cold coffee": "Cold Coffee",
    "brownie": "Chocolate Brownie",
    "chocolate brownie": "Chocolate Brownie",
}


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value)).lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _alias_target(value: str) -> Optional[str]:
    n = normalize_name(value)
    if n in {normalize_name(k): v for k, v in ALIASES.items()}:
        return {normalize_name(k): v for k, v in ALIASES.items()}[n]
    return None


def resolve_menu_item(db: Session, requested: Union[str, int]) -> MenuItem:
    """Resolve a human menu name/alias/legacy slug/numeric ID to one available row.

    Exact canonical names win. IDs and old slug-like IDs are supported for
    backward compatibility, but a bad LLM-generated ID is never accepted
    silently unless it actually maps to a real menu item.
    """
    available = db.scalars(
        select(MenuItem).where(MenuItem.is_available.is_(True))
    ).all()

    if not available:
        raise ValueError("The menu is empty or no menu item is currently available.")

    raw = str(requested).strip()
    normalized = normalize_name(raw)

    # 1. Exact canonical name.
    exact = [m for m in available if normalize_name(m.name) == normalized]
    if len(exact) == 1:
        return exact[0]

    # 2. Known aliases, including the legacy "burger-veg" style identifier.
    target = _alias_target(raw)
    if target:
        matches = [m for m in available if normalize_name(m.name) == normalize_name(target)]
        if len(matches) == 1:
            return matches[0]

    # 3. Numeric database ID (only if it really exists and is available).
    if raw.isdigit():
        item = db.get(MenuItem, int(raw))
        if item and item.is_available:
            return item

    # 4. Slug form of the canonical DB name.
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    slug_matches = [
        m for m in available
        if re.sub(r"[^a-z0-9]+", "-", normalize_name(m.name)).strip("-") == slug
    ]
    if len(slug_matches) == 1:
        return slug_matches[0]

    # 5. Conservative fuzzy matching. Do not guess when two choices are close.
    scored = sorted(
        (
            (SequenceMatcher(None, normalized, normalize_name(m.name)).ratio(), m)
            for m in available
        ),
        key=lambda x: x[0],
        reverse=True,
    )
    if scored and scored[0][0] >= 0.72:
        if len(scored) == 1 or scored[0][0] - scored[1][0] >= 0.10:
            return scored[0][1]

    choices = ", ".join(m.name for m in available)
    raise ValueError(f"Could not uniquely match '{requested}' to the menu. Available: {choices}")


def create_order(
    db: Session,
    items: list[dict],
    user_id: str = "default-user",
) -> Order:
    """Create an order after resolving and validating ALL items first.

    Accepts both the original API shape (menu_item_id) and the new agent shape
    (item/menu_item_name). This keeps existing clients and tests working.
    """
    if not items:
        raise ValueError("Order must contain at least one item.")

    resolved: list[tuple[MenuItem, int]] = []
    merged: dict[int, int] = {}

    # Validate everything before creating/flushing the Order. This prevents
    # half-created orders when one requested item is invalid.
    for entry in items:
        raw_item = entry.get("item") or entry.get("menu_item_name")
        if raw_item is None:
            raw_item = entry.get("menu_item_id")

        if raw_item is None:
            raise ValueError("Each order item must contain a menu item name or ID.")

        try:
            qty = int(entry["quantity"])
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"Invalid quantity for '{raw_item}'.")
        if qty <= 0 or qty > 50:
            raise ValueError(f"Quantity for '{raw_item}' must be between 1 and 50.")

        menu = resolve_menu_item(db, raw_item)
        merged[menu.id] = merged.get(menu.id, 0) + qty

    for menu_id, qty in merged.items():
        menu = db.get(MenuItem, menu_id)
        if not menu or not menu.is_available:
            raise ValueError(f"Menu item {menu_id} is unavailable.")
        resolved.append((menu, qty))

    order = Order(
        user_id=(str(user_id).strip()[:100] or "default-user"),
        total_amount=Decimal("0.00"),
        status="confirmed",
    )
    db.add(order)
    db.flush()

    total = Decimal("0.00")
    for menu, qty in resolved:
        unit_price = Decimal(str(menu.price))
        subtotal = unit_price * qty
        db.add(OrderItem(
            order_id=order.id,
            menu_item_id=menu.id,
            quantity=qty,
            unit_price=menu.price,
            subtotal=subtotal,
        ))
        total += subtotal

    order.total_amount = total
    db.commit()
    db.refresh(order)
    return get_order(db, order.id)


def get_order(db: Session, order_id: int) -> Optional[Order]:
    stmt = (
        select(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.menu_item))
        .where(Order.id == order_id)
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def sales_summary(db: Session) -> dict:
    total_orders = db.scalar(select(func.count(Order.id))) or 0
    total_sales = db.scalar(select(func.coalesce(func.sum(Order.total_amount), 0))) or 0

    stmt = (
        select(MenuItem.name, func.sum(OrderItem.quantity).label("quantity"))
        .join(OrderItem, MenuItem.id == OrderItem.menu_item_id)
        .group_by(MenuItem.id)
        .order_by(func.sum(OrderItem.quantity).desc())
    )
    best = [{"name": name, "quantity": int(qty)} for name, qty in db.execute(stmt).all()]

    user_stmt = (
        select(
            Order.user_id,
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.total_amount), 0).label("total"),
        )
        .group_by(Order.user_id)
        .order_by(func.sum(Order.total_amount).desc())
    )

    # Aggregate items per customer.
    user_wise = []
    for user_id, order_count, total in db.execute(user_stmt).all():
        item_stmt = (
            select(
                MenuItem.name,
                func.sum(OrderItem.quantity).label("quantity"),
                func.sum(OrderItem.subtotal).label("subtotal"),
            )
            .join(OrderItem, MenuItem.id == OrderItem.menu_item_id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.user_id == user_id)
            .group_by(MenuItem.id, MenuItem.name)
            .order_by(func.sum(OrderItem.quantity).desc())
        )
        items = [
            {
                "name": name,
                "quantity": int(quantity),
                "subtotal": float(subtotal or 0),
            }
            for name, quantity, subtotal in db.execute(item_stmt).all()
        ]

        order_stmt = (
            select(Order)
            .options(joinedload(Order.items).joinedload(OrderItem.menu_item))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc(), Order.id.desc())
        )
        customer_orders = db.execute(order_stmt).unique().scalars().all()

        order_details = [
            {
                "order_id": order.id,
                "status": order.status,
                "created_at": order.created_at.isoformat(),
                "total": float(order.total_amount or 0),
                "items": [
                    {
                        "name": line.menu_item.name,
                        "quantity": line.quantity,
                        "unit_price": float(line.unit_price),
                        "subtotal": float(line.subtotal),
                    }
                    for line in order.items
                ],
            }
            for order in customer_orders
        ]

        user_wise.append({
            "user_id": user_id,
            "order_count": int(order_count),
            "total": float(total or 0),
            "items": items,
            "orders": order_details,
        })

    return {
        "total_orders": int(total_orders),
        "total_sales": float(total_sales),
        "best_selling_items": best,
        "user_wise": user_wise,
    }
