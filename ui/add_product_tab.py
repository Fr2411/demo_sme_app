import pandas as pd
import streamlit as st

from services.api_client import EasyEcomApiClient


api_client = EasyEcomApiClient()


def render_add_product_tab(client_id: str):
    st.subheader('Add Product')
    with st.form('add_product_form', clear_on_submit=True):
        product_name = st.text_input('Product Name')
        category = st.text_input('Category', value='General')
        unit_cost = st.number_input('Unit Cost', min_value=0.0, step=0.01)
        unit_price = st.number_input('Selling Price', min_value=0.0, step=0.01)
        submitted = st.form_submit_button('Add Product')

        if submitted:
            if not product_name.strip():
                st.error('Enter product name')
            else:
                try:
                    api_client.create_product(client_id, product_name.strip(), category.strip(), unit_cost, unit_price)
                    st.success('Product added successfully')
                    st.rerun()
                except Exception as exc:
                    st.error(f'Failed to add product: {exc}')

    st.markdown('---')
    st.subheader('Products')
    try:
        products = api_client.get_products(client_id)
    except Exception as exc:
        st.error(f'Could not load products: {exc}')
        return

    if not products:
        st.info('No product records found yet for this client.')
        return

    st.dataframe(pd.DataFrame(products), use_container_width=True)
