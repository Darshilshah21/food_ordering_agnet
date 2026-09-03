from backend.database.database_in import ensure_schema
from backend.database.seed import seed_menu

ensure_schema()
seed_menu()
print("SQLite database and menu are ready.")
