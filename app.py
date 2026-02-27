import streamlit as st

from config import APP_TITLE, PAGE_ICON, PAGE_TITLE
from services.auth_service import check_login
from ui.add_product_tab import render_add_product_tab
from ui.assets_tab import render_assets_tab
from ui.dashboard_tab import render_dashboard_tab
from ui.sales_tab import render_sales_tab


st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")
st.title(APP_TITLE)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_login(username, password):
            st.session_state.logged_in = True
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid username or password")
else:
    tab_dashboard, tab_add, tab_assets, tab_sales = st.tabs(
        ["📊 Dashboard", "➕ Add Product", "📦 Assets Summary", "💰 Sales Entry"]
    )

    with tab_dashboard:
        render_dashboard_tab()

    with tab_add:
        render_add_product_tab()

    with tab_assets:
        render_assets_tab()

    with tab_sales:
        render_sales_tab()

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
