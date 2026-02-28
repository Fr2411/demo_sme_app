import pandas as pd
import streamlit as st

from config import PRODUCTS_FILE, SALES_FILE, USERS_FILE
from services.auth_service import create_client_user
from services.client_service import CLIENT_COLUMNS, add_client, get_all_clients


def _render_data_overview() -> None:
    st.subheader("All clients data")
    st.dataframe(get_all_clients(), use_container_width=True, hide_index=True)

    st.markdown("#### Operational datasets")
    users_df = pd.read_csv(USERS_FILE)
    products_df = pd.read_csv(PRODUCTS_FILE)
    sales_df = pd.read_csv(SALES_FILE)

    c1, c2, c3 = st.columns(3)
    c1.write("Users")
    c1.dataframe(users_df, use_container_width=True, hide_index=True)
    c2.write("Products")
    c2.dataframe(products_df, use_container_width=True, hide_index=True)
    c3.write("Sales")
    c3.dataframe(sales_df, use_container_width=True, hide_index=True)


def render_admin_tab() -> None:
    st.caption("Only admin can view/manage this panel.")
    _render_data_overview()

    st.markdown("---")
    st.subheader("Add new client")

    with st.form("add_client_form", clear_on_submit=True):
        client_id = st.text_input("Client ID")
        client_name = st.text_input("Client Name")
        business_overview = st.text_area("Business Overview")

        col1, col2 = st.columns(2)
        opening_hours = col1.text_input("Opening Hours", value="09:00")
        closing_hours = col2.text_input("Closing Hours", value="21:00")

        col3, col4 = st.columns(2)
        max_discount_pct = col3.number_input("Max Discount %", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
        sales_commission_pct = col4.number_input("Sales Commission %", min_value=0.0, max_value=100.0, value=2.0, step=0.5)

        return_refund_policy = st.text_area("Return / Refund Policy")
        whatsapp_number = st.text_input("WhatsApp Number")
        messenger = st.text_input("Messenger")
        required_api_keys = st.text_area(
            "Required API Keys",
            value="WHATSAPP_ACCESS_TOKEN,WHATSAPP_PHONE_NUMBER_ID,OPENAI_API_KEY",
            help="Comma-separated keys required for this client.",
        )

        st.markdown("##### Initial credentials")
        user_username = st.text_input("Username", value="admin")
        user_password = st.text_input("Password", type="password")
        user_role = st.selectbox("Role", ["admin", "employee"], index=0)
        submitted = st.form_submit_button("Create Client")

    if submitted:
        payload = {
            "client_id": client_id,
            "client_name": client_name,
            "business_overview": business_overview,
            "opening_hours": opening_hours,
            "closing_hours": closing_hours,
            "max_discount_pct": max_discount_pct,
            "return_refund_policy": return_refund_policy,
            "sales_commission_pct": sales_commission_pct,
            "whatsapp_number": whatsapp_number,
            "messenger": messenger,
            "required_api_keys": required_api_keys,
        }
        payload = {col: payload.get(col, "") for col in CLIENT_COLUMNS}
        ok, message = add_client(payload)
        if not ok:
            st.error(message)
            return

        user_ok, user_message = create_client_user(
            client_id=client_id,
            username=user_username,
            password=user_password,
            role=user_role,
        )
        if not user_ok:
            st.warning(f"Client created but login user not created: {user_message}")
        else:
            st.success(f"{message}. {user_message}")
        st.rerun()
