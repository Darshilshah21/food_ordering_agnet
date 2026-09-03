from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.database_in import get_db
from backend.schemas.order import OrderCreate, OrderRead, OrderItemRead
from backend.services.order_service import create_order, get_order

router = APIRouter(prefix="/orders", tags=["orders"])


def serialize(order):
    return OrderRead(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
        items=[
            OrderItemRead(
                menu_item_id=x.menu_item_id,
                name=x.menu_item.name,
                quantity=x.quantity,
                unit_price=x.unit_price,
                subtotal=x.subtotal,
            )
            for x in order.items
        ],
    )


@router.post("", response_model=OrderRead)
def create(order: OrderCreate, db: Session = Depends(get_db)):
    try:
        return serialize(
            create_order(
                db,
                [x.model_dump() for x in order.items],
                user_id=order.user_id or "api-user",
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{order_id}", response_model=OrderRead)
def read(order_id: int, db: Session = Depends(get_db)):
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return serialize(order)
