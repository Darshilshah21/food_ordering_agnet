import os
import uuid
import requests
import streamlit as st
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

try:
    API_URL = st.secrets["API_URL"]
except Exception:
    API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


st.set_page_config(
    page_title="Food Ordering Agent",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main page */
    .main {
        padding-top: 1rem;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;
        padding: 15px;
        background-color: rgba(128, 128, 128, 0.04);
    }

    /* User cards */
    .user-card {
        padding: 18px;
        border-radius: 14px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        margin-bottom: 12px;
        background-color: rgba(128, 128, 128, 0.04);
    }

    .user-title {
        font-size: 20px;
        font-weight: 700;
    }

    .user-id {
        font-family: monospace;
        font-size: 13px;
        opacity: 0.75;
    }

    .section-title {
        font-size: 22px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    /* Order card */
    .order-card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;
        padding: 14px;
        margin: 8px 0;
    }

    .small-text {
        font-size: 13px;
        opacity: 0.75;
    }

    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }

    /* Hide excessive Streamlit spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.title("🍔 AI Food Ordering Agent")
st.caption(
    "Local LLM + RAG + LangChain Agent + SQLite"
)


# ============================================================
# CUSTOMER / SESSION ID
# ============================================================

if "user_id" not in st.session_state:
    st.session_state.user_id = f"user-{uuid.uuid4().hex[:8]}"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("👤 Customer")

    st.code(
        st.session_state.user_id,
        language="text",
    )

    st.caption(
        "This Customer ID identifies orders created from this browser session."
    )

    st.divider()

    st.subheader("⚙️ Backend")

    st.write(API_URL)

    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.rerun()

    st.divider()

    st.subheader("Navigation")

    st.info(
        "Use the tabs to chat with the ordering agent, "
        "view the menu, or analyze customer orders."
    )


# ============================================================
# TABS
# ============================================================

tab_chat, tab_menu, tab_dashboard = st.tabs(
    [
        "💬 Chat",
        "📋 Menu",
        "📊 Dashboard",
    ]
)


# ============================================================
# CHAT
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


with tab_chat:

    st.subheader("💬 Food Ordering Assistant")

    st.caption(
        f"Customer ID: `{st.session_state.user_id}`"
    )

    # Display previous messages
    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    prompt = st.chat_input(
        "Example: order 2 veg burger, 3 marg pizza and 1 coke"
    )


    if prompt:

        # Add user message
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )


        with st.chat_message("user"):
            st.markdown(prompt)


        # Call backend
        try:

            response = requests.post(
                f"{API_URL}/chat",
                json={
                    "message": prompt,
                    "session_id": st.session_state.user_id,
                },
                timeout=180,
            )

            response.raise_for_status()

            response_data = response.json()

            answer = response_data.get(
                "response",
                "I couldn't understand the response from the backend.",
            )


        except requests.HTTPError as exc:

            try:

                detail = response.json().get(
                    "detail",
                    str(exc),
                )

            except Exception:

                detail = str(exc)


            answer = f"⚠️ {detail}"


        except Exception as exc:

            answer = (
                "⚠️ Unable to contact the backend.\n\n"
                f"`{exc}`"
            )


        # Store response
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )


        with st.chat_message("assistant"):
            st.markdown(answer)


# ============================================================
# MENU
# ============================================================

with tab_menu:

    st.subheader("📋 Restaurant Menu")

    try:

        response = requests.get(
            f"{API_URL}/menu",
            timeout=10,
        )

        response.raise_for_status()

        menu = response.json()


        if not menu:

            st.info("No menu items available.")

        else:

            # Search menu
            search = st.text_input(
                "🔎 Search menu",
                placeholder="Search burger, pizza, coke...",
            )


            filtered_menu = menu


            if search:

                search_lower = search.lower()

                filtered_menu = [
                    item
                    for item in menu
                    if search_lower in item["name"].lower()
                    or search_lower in item.get(
                        "description",
                        "",
                    ).lower()
                    or search_lower in item.get(
                        "category",
                        "",
                    ).lower()
                ]


            # Menu columns
            columns = st.columns(3)


            for index, item in enumerate(filtered_menu):

                with columns[index % 3]:

                    with st.container(border=True):

                        st.markdown(
                            f"### {item['name']}"
                        )

                        st.markdown(
                            f"**₹{item['price']}**"
                        )

                        st.caption(
                            item.get(
                                "category",
                                "Food",
                            )
                        )

                        st.write(
                            item.get(
                                "description",
                                "",
                            )
                        )


    except Exception as exc:

        st.error(
            f"Unable to load menu: {exc}"
        )


# ============================================================
# DASHBOARD
# ============================================================

with tab_dashboard:

    st.header("📊 Order Analytics Dashboard")

    st.caption(
        "Customer-wise orders, sales, repeated dishes and overall restaurant analytics."
    )


    # --------------------------------------------------------
    # LOAD DASHBOARD DATA
    # --------------------------------------------------------

    try:

        response = requests.get(
            f"{API_URL}/dashboard/summary",
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()


    except Exception as exc:

        st.error(
            f"Unable to load dashboard: {exc}"
        )

        st.stop()


    # --------------------------------------------------------
    # EXTRACT DATA SAFELY
    # --------------------------------------------------------

    total_orders = data.get(
        "total_orders",
        0,
    )

    total_sales = float(
        data.get(
            "total_sales",
            0,
        )
        or 0
    )

    user_wise = data.get(
        "user_wise",
        [],
    )

    customer_summary = []

    best_selling = data.get(
        "best_selling_items",
        [],
    )


    # ========================================================
    # TOP KPI CARDS
    # ========================================================

    st.subheader("📈 Overall Analytics")


    total_customers = len(user_wise)


    # Calculate total item quantity
    total_items_sold = 0

    for item in best_selling:

        total_items_sold += int(
            item.get(
                "quantity",
                0,
            )
            or 0
        )


    average_order_value = (
        total_sales / total_orders
        if total_orders > 0
        else 0
    )


    c1, c2, c3, c4, c5 = st.columns(5)


    c1.metric(
        "👥 Customers",
        total_customers,
    )


    c2.metric(
        "📦 Total Orders",
        total_orders,
    )


    c3.metric(
        "💰 Total Sales",
        f"₹{total_sales:,.2f}",
    )


    c4.metric(
        "🍔 Items Sold",
        total_items_sold,
    )


    c5.metric(
        "🧾 Avg. Order",
        f"₹{average_order_value:,.2f}",
    )


    st.divider()


    # ========================================================
    # USER-WISE CUSTOMER ANALYTICS
    # ========================================================

    st.subheader("👥 Customer-wise Order Breakdown")


    if not user_wise:

        st.info(
            "No customer orders have been created yet."
        )

    else:

        # ----------------------------------------------------
        # Customer summary table
        # ----------------------------------------------------

        customer_summary = []


        for index, user in enumerate(
            user_wise,
            start=1,
        ):

            customer_summary.append(
                {
                    "Customer": f"User {index}",
                    "User ID": user.get(
                        "user_id",
                        "Unknown",
                    ),
                    "Orders": user.get(
                        "order_count",
                        0,
                    ),
                    "Total Spent": float(
                        user.get(
                            "total",
                            0,
                        )
                        or 0
                    ),
                }
            )


        customer_df = pd.DataFrame(
            customer_summary
        )


        st.dataframe(
            customer_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Total Spent": st.column_config.NumberColumn(
                    "Total Spent",
                    format="₹%.2f",
                )
            },
        )


        st.markdown(
            '<div class="section-title">👤 Individual Customers</div>',
            unsafe_allow_html=True,
        )


        # ----------------------------------------------------
        # USER EXPANDERS
        # ----------------------------------------------------

        for index, user in enumerate(
            user_wise,
            start=1,
        ):

            user_id = user.get(
                "user_id",
                "Unknown",
            )

            order_count = int(
                user.get(
                    "order_count",
                    0,
                )
                or 0
            )

            user_total = float(
                user.get(
                    "total",
                    0,
                )
                or 0
            )

            user_items = user.get(
                "items",
                [],
            )

            user_orders = user.get(
                "orders",
                [],
            )


            # Customer header
            with st.expander(
                (
                    f"👤 User {index}  |  "
                    f"{user_id}  |  "
                    f"📦 {order_count} order(s)  |  "
                    f"💰 ₹{user_total:,.2f}"
                ),
                expanded=False,
            ):

                # --------------------------------------------
                # USER PROFILE
                # --------------------------------------------

                uc1, uc2, uc3 = st.columns(3)


                uc1.metric(
                    "🆔 User ID",
                    user_id,
                )


                uc2.metric(
                    "📦 Orders",
                    order_count,
                )


                uc3.metric(
                    "💰 Total Spent",
                    f"₹{user_total:,.2f}",
                )


                st.divider()


                # --------------------------------------------
                # ITEMS ORDERED BY USER
                # --------------------------------------------

                st.markdown(
                    "### 🍔 Items Ordered by This User"
                )


                if user_items:

                    user_items_df = pd.DataFrame(
                        user_items
                    )


                    # Normalize possible columns
                    if "quantity" in user_items_df.columns:

                        user_items_df["quantity"] = (
                            pd.to_numeric(
                                user_items_df[
                                    "quantity"
                                ],
                                errors="coerce",
                            )
                            .fillna(0)
                            .astype(int)
                        )


                    st.dataframe(
                        user_items_df,
                        use_container_width=True,
                        hide_index=True,
                    )


                    # Repeated dishes for this user
                    if "quantity" in user_items_df.columns:

                        repeated_user_items = (
                            user_items_df[
                                user_items_df["quantity"] > 1
                            ]
                            .sort_values(
                                "quantity",
                                ascending=False,
                            )
                        )


                        if not repeated_user_items.empty:

                            st.markdown(
                                "#### 🔁 Repeated / Multiple Quantity Dishes"
                            )

                            st.dataframe(
                                repeated_user_items,
                                use_container_width=True,
                                hide_index=True,
                            )

                else:

                    st.info(
                        "No item information available for this customer."
                    )


                st.divider()


                # --------------------------------------------
                # INDIVIDUAL ORDERS
                # --------------------------------------------

                st.markdown(
                    "### 📦 Individual Orders"
                )


                if not user_orders:

                    st.info(
                        "No individual orders found."
                    )

                else:

                    for order in user_orders:

                        order_id = order.get(
                            "order_id",
                            "N/A",
                        )

                        status = order.get(
                            "status",
                            "Unknown",
                        )

                        order_total = float(
                            order.get(
                                "total",
                                0,
                            )
                            or 0
                        )

                        created_at = order.get(
                            "created_at",
                            "Unknown",
                        )

                        order_items = order.get(
                            "items",
                            [],
                        )


                        with st.container(
                            border=True
                        ):

                            # Order header
                            oc1, oc2, oc3, oc4 = st.columns(
                                4
                            )


                            oc1.markdown(
                                f"**🧾 Order #{order_id}**"
                            )


                            oc2.markdown(
                                f"**Status:** {status}"
                            )


                            oc3.markdown(
                                f"**Total:** ₹{order_total:,.2f}"
                            )


                            oc4.markdown(
                                f"**User:** `{user_id}`"
                            )


                            st.caption(
                                f"🕐 Created: {created_at}"
                            )


                            # Order items
                            if order_items:

                                order_items_df = pd.DataFrame(
                                    order_items
                                )


                                st.dataframe(
                                    order_items_df,
                                    use_container_width=True,
                                    hide_index=True,
                                )

                            else:

                                st.info(
                                    "No item details available."
                                )


    st.divider()


    # ========================================================
    # BEST SELLING / REPEATED DISH ANALYTICS
    # ========================================================

    st.subheader("🔥 Best-Selling & Repeated Dishes")


    if not best_selling:

        st.info(
            "No dishes have been ordered yet."
        )

    else:

        best_df = pd.DataFrame(
            best_selling
        )


        # Normalize quantity
        if "quantity" in best_df.columns:

            best_df["quantity"] = (
                pd.to_numeric(
                    best_df["quantity"],
                    errors="coerce",
                )
                .fillna(0)
                .astype(int)
            )


        # ----------------------------------------------------
        # Top dishes
        # ----------------------------------------------------

        st.markdown(
            "### 🏆 Most Ordered Dishes"
        )


        if "quantity" in best_df.columns:

            top_items = (
                best_df.sort_values(
                    "quantity",
                    ascending=False,
                )
                .reset_index(drop=True)
            )


            # Top 3
            top3 = top_items.head(3)


            cols = st.columns(
                max(
                    1,
                    len(top3),
                )
            )


            for i, (_, item) in enumerate(
                top3.iterrows()
            ):

                with cols[i]:

                    st.metric(
                        f"#{i + 1} {item.get('name', 'Unknown')}",
                        f"{int(item.get('quantity', 0))} sold",
                    )


            st.bar_chart(
                top_items.set_index(
                    "name"
                )["quantity"]
            )


        st.markdown(
            "### 🔁 Repeated Dishes"
        )


        if "quantity" in best_df.columns:

            repeated_dishes = (
                best_df[
                    best_df["quantity"] > 1
                ]
                .sort_values(
                    "quantity",
                    ascending=False,
                )
                .reset_index(drop=True)
            )


            if not repeated_dishes.empty:

                st.dataframe(
                    repeated_dishes,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No dish has been ordered more than once yet."
                )


        # Full dish table
        st.markdown(
            "### 🍽️ Complete Dish Performance"
        )


        st.dataframe(
            best_df,
            use_container_width=True,
            hide_index=True,
        )


    st.divider()


    # ========================================================
    # ORDER STATUS ANALYTICS
    # ========================================================

    st.subheader("📦 Order Status Analytics")


    all_orders = []


    for user in user_wise:

        user_id = user.get(
            "user_id",
            "Unknown",
        )


        for order in user.get(
            "orders",
            [],
        ):

            all_orders.append(
                {
                    "order_id": order.get(
                        "order_id",
                        "N/A",
                    ),
                    "user_id": user_id,
                    "status": order.get(
                        "status",
                        "Unknown",
                    ),
                    "total": float(
                        order.get(
                            "total",
                            0,
                        )
                        or 0
                    ),
                    "created_at": order.get(
                        "created_at",
                        "",
                    ),
                }
            )


    if all_orders:

        all_orders_df = pd.DataFrame(
            all_orders
        )


        status_counts = (
            all_orders_df[
                "status"
            ]
            .value_counts()
        )


        sc1, sc2 = st.columns(2)


        with sc1:

            st.markdown(
                "### 📊 Orders by Status"
            )

            st.bar_chart(
                status_counts
            )


        with sc2:

            st.markdown(
                "### 📋 Status Summary"
            )

            status_df = (
                status_counts
                .reset_index()
            )

            status_df.columns = [
                "Status",
                "Orders",
            ]


            st.dataframe(
                status_df,
                use_container_width=True,
                hide_index=True,
            )


    else:

        st.info(
            "No orders available for status analytics."
        )


    # ========================================================
    # RECENT ORDERS
    # ========================================================

    st.subheader("🕐 Recent Orders")


    if all_orders:

        recent_orders = all_orders_df.copy()


        recent_orders = recent_orders.tail(
            min(
                10,
                len(recent_orders),
            )
        )


        st.dataframe(
            recent_orders,
            use_container_width=True,
            hide_index=True,
            column_config={
                "total": st.column_config.NumberColumn(
                    "Total",
                    format="₹%.2f",
                )
            },
        )

    else:

        st.info(
            "No recent orders."
        )


    # ========================================================
    # CUSTOMER SPENDING CHART
    # ========================================================

    st.subheader("💰 Customer Spending")


    if customer_summary:

        spending_df = pd.DataFrame(
            customer_summary
        )


        spending_chart = spending_df[
            [
                "User ID",
                "Total Spent",
            ]
        ].set_index(
            "User ID"
        )


        st.bar_chart(
            spending_chart
        )


    # ========================================================
    # FOOTER
    # ========================================================

    st.divider()

    st.caption(
        "🍔 Food Ordering Agent • "
        "LangChain + Ollama + RAG + FastAPI + SQLite + Streamlit"
    )
