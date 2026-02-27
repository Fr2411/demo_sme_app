import streamlit as st

from config import APP_TITLE, PAGE_ICON, PAGE_TITLE
from services.auth_service import authenticate_admin, authenticate_user
from services.client_service import ensure_db_structure, get_all_clients
from ui.add_product_tab import render_add_product_tab
from ui.admin_tab import render_admin_tab
from ui.assets_tab import render_assets_tab
from ui.dashboard_tab import render_dashboard_tab
from ui.sales_tab import render_sales_tab


ensure_db_structure()
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")
st.title(APP_TITLE)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if not st.session_state.logged_in:
    st.subheader("Login")
    login_mode = st.radio("Login type", ["Client Login", "Admin Login"], horizontal=True)

    if login_mode == "Client Login":
        client_id = st.text_input("Client ID", value="demo_client")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login as Client"):
            user = authenticate_user(client_id, username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.is_admin = False
                st.session_state.client_id = user["client_id"]
                st.session_state.username = user["username"]
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid client, username or password")
    else:
        username = st.text_input("Admin Username")
        password = st.text_input("Admin Password", type="password")
        if st.button("Login as Admin"):
            user = authenticate_admin(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.is_admin = True
                st.session_state.client_id = "__admin__"
                st.session_state.username = user["username"]
                st.success("Admin logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid admin credentials")

    st.caption("Default superadmin credentials: superadmin / superadmin123")
else:
    is_admin = st.session_state.get("is_admin", False)

    if is_admin:
        all_clients = get_all_clients()
        client_options = all_clients["client_id"].tolist()
        dashboard_filters = ["All clients", *client_options]
        selected_dashboard_filter = st.selectbox("Dashboard view", dashboard_filters, index=0, key="admin_dashboard_selector")
        selected_client = st.selectbox("View client workspace", client_options, key="admin_client_selector") if client_options else None
        st.caption(f"Logged in as {st.session_state.get('username')} (superadmin)")

        tab_dashboard, tab_add, tab_assets, tab_sales, tab_admin = st.tabs(
            ["📊 Dashboard", "➕ Add Product", "📦 Assets Summary", "💰 Sales Entry", "🛠️ Client Admin"]
        )

        with tab_dashboard:
            if client_options:
                dashboard_client_id = "__all__" if selected_dashboard_filter == "All clients" else selected_dashboard_filter
                render_dashboard_tab(dashboard_client_id)
            else:
                st.info("No clients found.")

        with tab_add:
            if selected_client:
                render_add_product_tab(selected_client)
            else:
                st.info("No clients found.")

        with tab_assets:
            if selected_client:
                render_assets_tab(selected_client)
            else:
                st.info("No clients found.")

        with tab_sales:
            if selected_client:
                render_sales_tab(selected_client)
            else:
                st.info("No clients found.")

        with tab_admin:
            render_admin_tab()

    else:
        active_client_id = st.session_state.get("client_id")
        st.caption(f"Logged in as {st.session_state.get('username')} ({active_client_id})")
        tab_dashboard, tab_add, tab_assets, tab_sales = st.tabs(
            ["📊 Dashboard", "➕ Add Product", "📦 Assets Summary", "💰 Sales Entry"]
        )

        with tab_dashboard:
            render_dashboard_tab(active_client_id)

        with tab_add:
            render_add_product_tab(active_client_id)

        with tab_assets:
            render_assets_tab(active_client_id)

        with tab_sales:
            render_sales_tab(active_client_id)

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.is_admin = False
        st.session_state.pop("client_id", None)
        st.session_state.pop("username", None)
        st.rerun()
