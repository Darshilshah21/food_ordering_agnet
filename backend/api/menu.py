from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.database.database_in import get_db
from backend.database.models import MenuItem
from backend.schemas.menu import MenuItemRead

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=list[MenuItemRead])
def list_menu(db: Session = Depends(get_db)):
    return db.scalars(
        select(MenuItem).where(MenuItem.is_available.is_(True)).order_by(MenuItem.category, MenuItem.name)
    ).all()
