from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from backend.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def ensure_schema():
    """Create tables and apply small, backward-compatible SQLite migrations."""
    Base.metadata.create_all(engine)

    # The original project did not have a customer/user column. Keep existing
    # databases working by adding it without deleting any existing orders.
    if settings.database_url.startswith("sqlite"):
        with engine.begin() as conn:
            columns = {
                row[1] for row in conn.execute(text("PRAGMA table_info(orders)")).fetchall()
            }
            if "user_id" not in columns:
                conn.execute(text(
                    "ALTER TABLE orders ADD COLUMN user_id VARCHAR(100) NOT NULL DEFAULT 'legacy-user'"
                ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_orders_user_id ON orders (user_id)"
            ))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
