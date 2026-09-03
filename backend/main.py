from fastapi import FastAPI

from backend.config import get_settings
from backend.database.database_in import Base, engine, ensure_schema
from backend.database.seed import seed_menu
from backend.api import chat, menu, orders, dashboard

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.1.0")


@app.on_event("startup")
def startup():
    ensure_schema()
    seed_menu()


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": settings.app_name}


app.include_router(chat.router)
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(dashboard.router)
