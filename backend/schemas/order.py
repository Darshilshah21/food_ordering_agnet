from datetime import datetime
from decimal import Decimal
from typing import Optional, Union

from pydantic import BaseModel, Field, model_validator


class OrderItemInput(BaseModel):
    # Backward compatible: the original API used menu_item_id. We also accept
    # a human name/legacy slug so clients do not have to know database IDs.
    menu_item_id: Optional[Union[int, str]] = None
    item: Optional[str] = None
    quantity: int = Field(gt=0, le=50)

    @model_validator(mode="after")
    def require_item_reference(self):
        if self.menu_item_id is None and not self.item:
            raise ValueError("Provide menu_item_id or item.")
        return self


class OrderCreate(BaseModel):
    items: list[OrderItemInput] = Field(min_length=1)
    user_id: Optional[str] = Field(default="api-user", max_length=100)


class OrderItemRead(BaseModel):
    menu_item_id: int
    name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class OrderRead(BaseModel):
    id: int
    user_id: str
    total_amount: Decimal
    status: str
    created_at: datetime
    items: list[OrderItemRead]
