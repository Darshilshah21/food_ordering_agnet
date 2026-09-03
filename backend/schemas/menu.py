from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class MenuItemRead(BaseModel):
    id: int
    name: str
    description: str
    category: str
    price: Decimal
    is_available: bool

    model_config = ConfigDict(from_attributes=True)
