from backend.database.seed import seed_menu
from backend.rag.retriever import build_index

seed_menu()
build_index()
print("FAISS menu index created.")
print("hello Darshil")
print("hi")
print("meet")