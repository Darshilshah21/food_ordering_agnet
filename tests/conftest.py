import os
os.environ["DATABASE_URL"] = "sqlite:///./test_food_orders.db"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from backend.database.database_in import Base, get_db
from backend.database.models import MenuItem
from backend.main import app

engine = create_engine(
    "sqlite:///./test_food_orders.db",
    connect_args={"check_same_thread": False},
)
TestingSession = sessionmaker(bind=engine)


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = TestingSession()
    db.add_all([
        MenuItem(name="Test Burger", description="Test", category="Burger", price=100, is_available=True),
        MenuItem(name="Test Coke", description="Test", category="Beverage", price=50, is_available=True),
    ])
    db.commit()
    db.close()

    def override():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
