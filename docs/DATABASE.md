# Database

SQLite is used for zero-configuration local execution.

Tables:

## menu_items

Stores item name, description, category, price and availability.

## orders

Stores order total, status and creation timestamp.

## order_items

Stores each ordered menu item, quantity, unit price and subtotal.

Relationships:

    Order 1 ---- * OrderItem * ---- 1 MenuItem

Business rules are implemented in `backend/services/order_service.py`.

## User-wise reporting

`orders.user_id` stores the chat/session customer identifier. Existing databases are migrated automatically by adding this column with a `legacy-user` default, so old orders are preserved.
