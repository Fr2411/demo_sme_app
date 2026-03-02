import streamlit as st

from config import APP_TITLE, PAGE_ICON, PAGE_TITLE
from services.api_client import EasyEcomApiClient
from ui.add_product_tab import render_add_product_tab
from ui.sales_tab import render_sales_tab

api_client = EasyEcomApiClient()

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout='wide')
st.title(APP_TITLE)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader('Login')
    client_id = st.text_input('Client ID', value='demo_client')
    username = st.text_input('Username', value='owner')
    password = st.text_input('Password', type='password', value='owner123')

    if st.button('Login'):
        try:
            result = api_client.login(client_id, username, password)
            st.session_state.logged_in = True
            st.session_state.client_id = result['user']['client_id']
            st.session_state.username = result['user']['username']
            st.success('Logged in successfully!')
            st.rerun()
        except Exception as exc:
            st.error(f'Invalid credentials or API unavailable: {exc}')
else:
    st.caption(f"Logged in as {st.session_state.get('username')} | Client: {st.session_state.get('client_id')}")
    products_tab, sales_tab = st.tabs(['➕ Products', '🧾 Sales'])
    with products_tab:
        render_add_product_tab(st.session_state['client_id'])
    with sales_tab:
        render_sales_tab(st.session_state['client_id'])

    if st.button('Logout'):
        st.session_state.logged_in = False
        st.session_state.pop('client_id', None)
        st.session_state.pop('username', None)
        st.rerun()
