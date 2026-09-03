from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from sqlalchemy import select

from backend.config import get_settings
from backend.database.database_in import SessionLocal
from backend.database.models import MenuItem
from backend.rag.embeddings import get_embeddings


def menu_documents() -> list[Document]:
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(MenuItem).where(MenuItem.is_available.is_(True))
        ).all()
        return [
            Document(
                page_content=(
                    f"Name: {m.name}\nCategory: {m.category}\n"
                    f"Description: {m.description}\nPrice: ₹{m.price}\n"
                    f"Available: {m.is_available}"
                ),
                metadata={"menu_item_id": m.id, "name": m.name},
            )
            for m in rows
        ]
    finally:
        db.close()


def _index_path() -> Path:
    path = Path(get_settings().faiss_index_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_index():
    docs = menu_documents()
    if not docs:
        raise RuntimeError("No menu items found. Initialize the database first.")
    vectorstore = FAISS.from_documents(docs, get_embeddings())
    vectorstore.save_local(str(_index_path()))


def _index_is_current() -> bool:
    """Detect stale FAISS indexes after menu/database changes."""
    path = _index_path()
    if not (path / "index.faiss").exists() or not (path / "index.pkl").exists():
        return False

    try:
        vectorstore = FAISS.load_local(
            str(path),
            get_embeddings(),
            allow_dangerous_deserialization=True,
        )
        indexed_names = {
            str(doc.metadata.get("name", "")).strip().lower()
            for doc in vectorstore.docstore._dict.values()
        }
        current_names = {
            str(doc.metadata.get("name", "")).strip().lower()
            for doc in menu_documents()
        }
        return indexed_names == current_names
    except Exception:
        return False


def get_retriever():
    if not _index_is_current():
        build_index()

    vectorstore = FAISS.load_local(
        str(_index_path()),
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )
    return vectorstore.as_retriever(search_kwargs={"k": 5})


def search_menu(query: str) -> list[Document]:
    return get_retriever().invoke(query)
