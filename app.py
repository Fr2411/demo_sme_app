import streamlit as st

from config import APP_TITLE, PAGE_ICON, PAGE_TITLE
from services.access_service import get_user_feature_access
from services.auth_service import authenticate_user
from services.client_service import ensure_db_structure, get_all_clients
from ui.add_product_tab import render_add_product_tab
from ui.admin_tab import render_admin_tab
from ui.assets_tab import render_assets_tab
from ui.dashboard_tab import render_dashboard_tab
from ui.finance_tab import render_finance_tab
from ui.role_access_tab import render_role_access_tab
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

    st.caption("Default platform admin: __admin__ / admin / admin123")
    st.caption("Default client owner: demo_client / owner / owner123")
    st.caption("Default client employee: demo_client / employee / employee123")
else:
    role = str(st.session_state.get("role", "employee")).lower()
    active_client_id = str(st.session_state.get("client_id"))
    active_username = str(st.session_state.get("username"))
    user_access = get_user_feature_access(active_client_id, active_username, role)

    is_platform_admin = role == "admin" and active_client_id == "__admin__"
    is_owner = role == "owner"

    if is_platform_admin:
        all_clients = get_all_clients()
        client_options = all_clients["client_id"].tolist()
        client_filters = ["All clients", *client_options]
        selected_client_filter = st.selectbox("Client filter", client_filters, index=0, key="admin_client_filter")
        active_client_scope = "__all__" if selected_client_filter == "All clients" else selected_client_filter
        st.caption(f"Logged in as {st.session_state.get('username')} (platform admin)")

        admin_tabs = []
        if user_access.get("dashboard", False):
            admin_tabs.append(("📊 Dashboard", "dashboard"))
        if user_access.get("add_product", False):
            admin_tabs.append(("➕ Add Product", "add_product"))
        if user_access.get("assets", False):
            admin_tabs.append(("📦 Assets Summary", "assets"))
        if user_access.get("sales", False):
            admin_tabs.append(("🧾 Sales Entry", "sales"))
        if user_access.get("finance", False):
            admin_tabs.append(("💰 Finance", "finance"))
        if user_access.get("client_admin", False):
            admin_tabs.append(("🛠️ Client Admin", "client_admin"))
        admin_tabs.append(("🔐 Role Access", "role_access"))

        tab_containers = st.tabs([tab_name for tab_name, _ in admin_tabs])

        for tab_container, (_, tab_key) in zip(tab_containers, admin_tabs):
            with tab_container:
                if tab_key == "dashboard":
                    if client_options:
                        render_dashboard_tab(active_client_scope, include_finance=user_access.get("finance", False))
                    else:
                        st.info("No clients found.")
                elif tab_key == "add_product":
                    if active_client_scope != "__all__":
                        render_add_product_tab(active_client_scope)
                    else:
                        st.info("Select a specific client in Client filter to add products.")
                elif tab_key == "assets":
                    if client_options:
                        render_assets_tab(active_client_scope, include_finance=user_access.get("finance", False))
                    else:
                        st.info("No clients found.")
                elif tab_key == "sales":
                    if active_client_scope != "__all__":
                        render_sales_tab(active_client_scope, include_finance=user_access.get("finance", False))
                    else:
                        st.info("Select a specific client in Client filter to record sales.")
                elif tab_key == "finance":
                    if active_client_scope != "__all__":
                        render_finance_tab(active_client_scope, active_username)
                    else:
                        st.info("Select a specific client in Client filter to view finance details.")
                elif tab_key == "client_admin":
                    render_admin_tab()
                elif tab_key == "role_access":
                    render_role_access_tab()

    else:
        st.caption(f"Logged in as {active_username} ({role}) | Client: {active_client_id}")

        user_tabs = []
        if user_access.get("dashboard", False):
            user_tabs.append(("📊 Dashboard", "dashboard"))
        if user_access.get("add_product", False):
            user_tabs.append(("➕ Add Product", "add_product"))
        if user_access.get("assets", False):
            user_tabs.append(("📦 Assets Summary", "assets"))
        if user_access.get("sales", False):
            user_tabs.append(("🧾 Sales Entry", "sales"))
        if user_access.get("finance", False):
            user_tabs.append(("💰 Finance", "finance"))

        if not user_tabs:
            st.warning("No features are enabled for this user. Contact platform admin.")
        else:
            tab_containers = st.tabs([tab_name for tab_name, _ in user_tabs])
            for tab_container, (_, tab_key) in zip(tab_containers, user_tabs):
                with tab_container:
                    if tab_key == "dashboard":
                        render_dashboard_tab(active_client_id, include_finance=user_access.get("finance", False))
                    elif tab_key == "add_product":
                        render_add_product_tab(active_client_id)
                    elif tab_key == "assets":
                        render_assets_tab(active_client_id, include_finance=user_access.get("finance", False))
                    elif tab_key == "sales":
                        render_sales_tab(active_client_id, include_finance=user_access.get("finance", False))
                    elif tab_key == "finance":
                        render_finance_tab(active_client_id, active_username)

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = "employee"
        st.session_state.pop("client_id", None)
        st.session_state.pop("username", None)
        st.rerun()
