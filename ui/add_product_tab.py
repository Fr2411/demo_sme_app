import streamlit as st

from services.inventory_service import add_product


def render_add_product_tab():
    with st.form("add_product_form", clear_on_submit=True):
        product_name = st.text_input("Product Name")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        unit_cost = st.number_input("Unit Cost", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("Add Product")
        if submitted:
            if product_name:
                ok, message = add_product(product_name, quantity, unit_cost)
                if ok:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Enter product name")
