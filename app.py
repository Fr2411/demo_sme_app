import streamlit as st

from config import APP_TITLE, PAGE_ICON, PAGE_TITLE
from services.auth_service import authenticate_user
from services.client_service import ensure_db_structure, get_all_clients
from ui.add_product_tab import render_add_product_tab
from ui.admin_tab import render_admin_tab
from ui.assets_tab import render_assets_tab
from ui.dashboard_tab import render_dashboard_tab
from ui.finance_tab import render_finance_tab
from ui.sales_tab import render_sales_tab


ensure_db_structure()
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")
st.title(APP_TITLE)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = "employee"

if not st.session_state.logged_in:
    st.subheader("Login")
    client_id = st.text_input("Client ID", value="demo_client", help="Use __admin__ for platform admin accounts.")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(client_id, username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.role = user.get("role", "employee")
            st.session_state.client_id = user["client_id"]
            st.session_state.username = user["username"]
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid client, username or password")

    st.caption("Default admin credentials: __admin__ / admin / admin123")
    st.caption("Default employee credentials: demo_client / employee / employee123")
else:
    role = st.session_state.get("role", "employee")
    is_admin = role == "admin"

    if is_admin:
        all_clients = get_all_clients()
        client_options = all_clients["client_id"].tolist()
        client_filters = ["All clients", *client_options]
        selected_client_filter = st.selectbox("Client filter", client_filters, index=0, key="admin_client_filter")
        active_client_scope = "__all__" if selected_client_filter == "All clients" else selected_client_filter
        st.caption(f"Logged in as {st.session_state.get('username')} ({role})")

        tab_dashboard, tab_add, tab_assets, tab_sales, tab_finance, tab_admin = st.tabs(
            ["📊 Dashboard", "➕ Add Product", "📦 Assets Summary", "🧾 Sales Entry", "💰 Finance", "🛠️ Client Admin"]
        )

        with tab_dashboard:
            if client_options:
                render_dashboard_tab(active_client_scope, include_finance=False)
            else:
                st.info("No clients found.")

        with tab_add:
            if active_client_scope != "__all__":
                render_add_product_tab(active_client_scope)
            else:
                st.info("Select a specific client in Client filter to add products.")

        with tab_assets:
            if client_options:
                render_assets_tab(active_client_scope, include_finance=False)
            else:
                st.info("No clients found.")

        with tab_sales:
            if active_client_scope != "__all__":
                render_sales_tab(active_client_scope, include_finance=False)
            else:
                st.info("Select a specific client in Client filter to record sales.")

        with tab_finance:
            if active_client_scope != "__all__":
                render_finance_tab(active_client_scope)
            else:
                st.info("Select a specific client in Client filter to view finance details.")

        with tab_admin:
            render_admin_tab()

    else:
        active_client_id = st.session_state.get("client_id")
        st.caption(f"Logged in as {st.session_state.get('username')} ({role}) | Client: {active_client_id}")
        tab_dashboard, tab_add, tab_assets, tab_sales = st.tabs(
            ["📊 Dashboard", "➕ Add Product", "📦 Assets Summary", "🧾 Sales Entry"]
        )

        with tab_dashboard:
            render_dashboard_tab(active_client_id, include_finance=False)

        with tab_add:
            render_add_product_tab(active_client_id)

        with tab_assets:
            render_assets_tab(active_client_id, include_finance=False)

        with tab_sales:
            render_sales_tab(active_client_id, include_finance=False)

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = "employee"
        st.session_state.pop("client_id", None)
        st.session_state.pop("username", None)
        st.rerun()
