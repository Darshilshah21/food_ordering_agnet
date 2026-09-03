# Agent and Custom Database Tool

The application uses a LangChain tool-calling agent.

Tools:

- `search_menu`: RAG-based menu retrieval
- `get_menu`: complete menu lookup
- `create_food_order`: creates an order through the application service
- `get_order_details`: reads an order
- `get_sales_summary`: reads aggregate dashboard information

The assignment says not to use the directly provided SQL agent. Therefore
this project does not use `create_sql_agent` or expose a SQL query tool.

The agent selects high-level business operations. SQLAlchemy remains inside
the service/database layers.


## Reliability layer

Clear purchase requests are first checked by a deterministic router. For example:

    can you order the 2 veg burger and 3 marg pizza and one coke plz

is converted to:

    [{"item": "veg burger", "quantity": 2},
     {"item": "marg pizza", "quantity": 3},
     {"item": "coke", "quantity": 1}]

The custom `create_food_order` tool then resolves those names against the live
database. The LLM is never required to invent database IDs such as
`burger-veg`.

The service supports canonical names, common aliases, numeric IDs, and legacy
slug-like identifiers. If an item cannot be matched confidently, the whole
order is rejected without creating a partial order.

## Customer-wise reporting

The chat `session_id` is treated as the customer/session identifier and is
stored on every order. The dashboard groups totals and items by customer and
also exposes individual order details.
