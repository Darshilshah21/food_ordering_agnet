from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.database_in import get_db
from backend.services.order_service import sales_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return sales_summary(db)
