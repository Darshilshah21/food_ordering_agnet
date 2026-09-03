# RAG

The restaurant menu is stored in SQLite as structured data. For retrieval,
available menu rows are converted to LangChain Documents containing the name,
category, description, price and availability.

A local Sentence Transformers embedding model converts those documents into
vectors. FAISS stores the vectors locally.

At query time, `search_menu` retrieves the top relevant menu documents. The
agent can use these retrieved documents as grounded evidence rather than
inventing menu information.

## Rebuild

    python scripts/ingest_data.py

The FAISS index is generated under `data/faiss_index/` and is intentionally
ignored by Git because it is a generated local artifact.
