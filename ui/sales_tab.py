import pandas as pd
import streamlit as st

from services.api_client import EasyEcomApiClient


api_client = EasyEcomApiClient()


def render_sales_tab(client_id: str, include_finance: bool = True):
    st.subheader('Sales Entry')

    try:
        products = api_client.get_products(client_id)
    except Exception as exc:
        st.error(f'Could not load products: {exc}')
        return

    if not products:
        st.warning('No products available. Add products first.')
        return

    product_options = {f"{p['name']} (#{p['id']})": p for p in products}
    selected_label = st.selectbox('Product', list(product_options.keys()))
    selected_product = product_options[selected_label]

    qty = st.number_input('Quantity Sold', min_value=1, step=1)
    selling_price = st.number_input('Selling Price', min_value=0.0, step=0.01, value=float(selected_product['unit_price']))

    if st.button('Record Sale'):
        try:
            api_client.create_sale(client_id, selected_product['id'], int(qty), float(selling_price))
            st.success('Sale recorded successfully')
            st.rerun()
        except Exception as exc:
            st.error(f'Failed to record sale: {exc}')

    st.markdown('---')
    st.subheader('Sales')
    try:
        sales = api_client.get_sales(client_id)
    except Exception as exc:
        st.error(f'Could not load sales: {exc}')
        return

    if not sales:
        st.info('No sales entries found yet for this client.')
        return

    st.dataframe(pd.DataFrame(sales), use_container_width=True)
