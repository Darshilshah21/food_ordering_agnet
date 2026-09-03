# Architecture

## Request flow

1. Streamlit collects a natural-language message.
2. Streamlit sends it to FastAPI `/chat`.
3. FastAPI invokes the LangChain tool-calling agent.
4. The agent chooses application-owned tools.
5. Menu questions use local RAG over FAISS.
6. Order creation uses a custom `create_food_order` tool.
7. The tool calls the service layer.
8. SQLAlchemy persists the order in SQLite.
9. The response is returned to Streamlit.

## Separation of concerns

- `api/`: HTTP layer
- `agent/`: LLM orchestration and custom tools
- `rag/`: local retrieval
- `database/`: SQLAlchemy models/session/seed
- `services/`: deterministic business logic
- `schemas/`: Pydantic request/response validation
- `frontend/`: Streamlit presentation

The LLM does not construct SQL and cannot access the database directly.
