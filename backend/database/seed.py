import json
from pathlib import Path
from sqlalchemy import select

from backend.database.database_in import Base, SessionLocal, engine
from backend.database.models import MenuItem


def seed_menu():
    Base.metadata.create_all(engine)

    # Resolve relative to the project root instead of the current working
    # directory. This prevents startup failures when uvicorn is launched elsewhere.
    project_root = Path(__file__).resolve().parents[2]
    menu_path = project_root / "data" / "menu.json"
    data = json.loads(menu_path.read_text(encoding="utf-8"))

    db = SessionLocal()
    try:
        for item in data:
            existing = db.scalar(
                select(MenuItem).where(MenuItem.name == item["name"])
            )
            if not existing:
                db.add(MenuItem(**item))
            else:
                # Keep the DB menu synchronized with menu.json without
                # destroying order history.
                existing.description = item["description"]
                existing.category = item["category"]
                existing.price = item["price"]
                existing.is_available = item["is_available"]
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_menu()
    print("Database initialized and menu seeded.")
