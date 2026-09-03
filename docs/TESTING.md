# Testing

Run:

    pytest -q

Tests cover the API health/menu endpoints and deterministic order persistence.
The production agent depends on Ollama, but tests avoid requiring an external
LLM process.

For manual acceptance testing:

1. Start Ollama.
2. Pull `llama3.2:3b`.
3. Initialize the database.
4. Build the FAISS index.
5. Start FastAPI.
6. Start Streamlit.
7. Ask for the menu.
8. Place an order containing multiple items.
9. Confirm the returned order ID and total.
10. Open Dashboard and verify order/sales data.

Additional checks cover legacy slug/name resolution, all-or-nothing validation, and user-wise dashboard totals/order details.
