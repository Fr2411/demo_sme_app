import pandas as pd
import streamlit as st

from config import PRODUCTS_FILE, SALES_FILE, USERS_FILE
from services.auth_service import create_client_user
from services.client_service import CLIENT_COLUMNS, add_client, get_all_clients, update_client


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
    st.subheader("Add or modify client")

    clients_df = get_all_clients()
    client_options = clients_df["client_id"].tolist()
    form_mode = st.radio("Form mode", ["Create new client", "Modify existing client"], horizontal=True)
    editing_existing_client = form_mode == "Modify existing client"

    selected_client_id = ""
    selected_client_data: dict[str, str] = {}
    if editing_existing_client:
        if not client_options:
            st.info("No clients available to modify yet.")
            return
        selected_client_id = st.selectbox("Client to modify", client_options)
        selected_row = clients_df[clients_df["client_id"] == selected_client_id].iloc[0].to_dict()
        selected_client_data = {col: str(selected_row.get(col, "") or "") for col in CLIENT_COLUMNS}

    with st.form("add_client_form", clear_on_submit=True):
        client_id = st.text_input("Client ID", value=selected_client_id, disabled=editing_existing_client)
        client_name = st.text_input("Client Name", value=selected_client_data.get("client_name", ""))
        business_overview = st.text_area("Business Overview", value=selected_client_data.get("business_overview", ""))

        col1, col2 = st.columns(2)
        opening_hours = col1.text_input("Opening Hours", value=selected_client_data.get("opening_hours", "09:00") or "09:00")
        closing_hours = col2.text_input("Closing Hours", value=selected_client_data.get("closing_hours", "21:00") or "21:00")

        col3, col4 = st.columns(2)
        max_discount_pct = col3.number_input(
            "Max Discount %",
            min_value=0.0,
            max_value=100.0,
            value=float(selected_client_data.get("max_discount_pct", 10.0) or 10.0),
            step=0.5,
        )
        sales_commission_pct = col4.number_input(
            "Sales Commission %",
            min_value=0.0,
            max_value=100.0,
            value=float(selected_client_data.get("sales_commission_pct", 2.0) or 2.0),
            step=0.5,
        )

        return_refund_policy = st.text_area("Return / Refund Policy", value=selected_client_data.get("return_refund_policy", ""))

        st.markdown("##### Meta channel settings")
        meta_business_manager_id = st.text_input(
            "Meta Business Manager ID", value=selected_client_data.get("meta_business_manager_id", "")
        )

        with st.expander("WhatsApp settings", expanded=False):
            whatsapp_enabled = st.checkbox(
                "WhatsApp Enabled", value=selected_client_data.get("whatsapp_enabled", "true").lower() == "true"
            )
            whatsapp_access_token = st.text_input(
                "WhatsApp Access Token", value=selected_client_data.get("whatsapp_access_token", ""), type="password"
            )
            whatsapp_phone_number_id = st.text_input(
                "WhatsApp Phone Number ID", value=selected_client_data.get("whatsapp_phone_number_id", "")
            )
            whatsapp_business_account_id = st.text_input(
                "WhatsApp Business Account ID", value=selected_client_data.get("whatsapp_business_account_id", "")
            )
            whatsapp_app_id = st.text_input("WhatsApp App ID", value=selected_client_data.get("whatsapp_app_id", ""))
            whatsapp_app_secret = st.text_input(
                "WhatsApp App Secret", value=selected_client_data.get("whatsapp_app_secret", ""), type="password"
            )
            whatsapp_webhook_verify_token = st.text_input(
                "WhatsApp Webhook Verify Token",
                value=selected_client_data.get("whatsapp_webhook_verify_token", ""),
                type="password",
            )
            whatsapp_token_expires_at = st.text_input(
                "WhatsApp Token Expires At", value=selected_client_data.get("whatsapp_token_expires_at", "")
            )

        with st.expander("Messenger settings", expanded=False):
            messenger_enabled = st.checkbox(
                "Messenger Enabled", value=selected_client_data.get("messenger_enabled", "true").lower() == "true"
            )
            messenger_page_access_token = st.text_input(
                "Messenger Page Access Token",
                value=selected_client_data.get("messenger_page_access_token", ""),
                type="password",
            )
            messenger_page_id = st.text_input("Messenger Page ID", value=selected_client_data.get("messenger_page_id", ""))
            messenger_app_id = st.text_input("Messenger App ID", value=selected_client_data.get("messenger_app_id", ""))
            messenger_app_secret = st.text_input(
                "Messenger App Secret", value=selected_client_data.get("messenger_app_secret", ""), type="password"
            )
            messenger_webhook_verify_token = st.text_input(
                "Messenger Webhook Verify Token",
                value=selected_client_data.get("messenger_webhook_verify_token", ""),
                type="password",
            )
            messenger_token_expires_at = st.text_input(
                "Messenger Token Expires At", value=selected_client_data.get("messenger_token_expires_at", "")
            )

        with st.expander("Instagram settings", expanded=False):
            instagram_enabled = st.checkbox(
                "Instagram Enabled", value=selected_client_data.get("instagram_enabled", "false").lower() == "true"
            )
            instagram_page_access_token = st.text_input(
                "Instagram Page Access Token",
                value=selected_client_data.get("instagram_page_access_token", ""),
                type="password",
            )
            instagram_business_account_id = st.text_input(
                "Instagram Business Account ID", value=selected_client_data.get("instagram_business_account_id", "")
            )
            instagram_app_id = st.text_input("Instagram App ID", value=selected_client_data.get("instagram_app_id", ""))
            instagram_app_secret = st.text_input(
                "Instagram App Secret", value=selected_client_data.get("instagram_app_secret", ""), type="password"
            )
            instagram_webhook_verify_token = st.text_input(
                "Instagram Webhook Verify Token",
                value=selected_client_data.get("instagram_webhook_verify_token", ""),
                type="password",
            )
            instagram_token_expires_at = st.text_input(
                "Instagram Token Expires At", value=selected_client_data.get("instagram_token_expires_at", "")
            )

        if not editing_existing_client:
            st.markdown("##### Initial credentials")
            user_username = st.text_input("Username", value="owner")
            user_password = st.text_input("Password", type="password")
            user_role = st.selectbox("Role", ["owner", "employee"], index=0)

        submitted = st.form_submit_button("Update Client" if editing_existing_client else "Create Client")

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
            "whatsapp_enabled": str(whatsapp_enabled).lower(),
            "whatsapp_access_token": whatsapp_access_token,
            "whatsapp_phone_number_id": whatsapp_phone_number_id,
            "whatsapp_business_account_id": whatsapp_business_account_id,
            "whatsapp_app_id": whatsapp_app_id,
            "whatsapp_app_secret": whatsapp_app_secret,
            "whatsapp_webhook_verify_token": whatsapp_webhook_verify_token,
            "whatsapp_token_expires_at": whatsapp_token_expires_at,
            "messenger_enabled": str(messenger_enabled).lower(),
            "messenger_page_access_token": messenger_page_access_token,
            "messenger_page_id": messenger_page_id,
            "messenger_app_id": messenger_app_id,
            "messenger_app_secret": messenger_app_secret,
            "messenger_webhook_verify_token": messenger_webhook_verify_token,
            "messenger_token_expires_at": messenger_token_expires_at,
            "instagram_enabled": str(instagram_enabled).lower(),
            "instagram_page_access_token": instagram_page_access_token,
            "instagram_business_account_id": instagram_business_account_id,
            "instagram_app_id": instagram_app_id,
            "instagram_app_secret": instagram_app_secret,
            "instagram_webhook_verify_token": instagram_webhook_verify_token,
            "instagram_token_expires_at": instagram_token_expires_at,
            "meta_business_manager_id": meta_business_manager_id,
        }
        payload = {col: payload.get(col, "") for col in CLIENT_COLUMNS}
        service_call = update_client if editing_existing_client else add_client
        target_client_id = selected_client_id if editing_existing_client else client_id
        ok, message = service_call(target_client_id, payload) if editing_existing_client else service_call(payload)
        if not ok:
            st.error(message)
            return

        if editing_existing_client:
            st.success(message)
        else:
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
