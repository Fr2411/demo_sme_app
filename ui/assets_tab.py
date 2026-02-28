import streamlit as st

from services.inventory_service import load_products


def render_assets_tab(client_id, include_finance: bool = True):
    df = load_products(client_id)
    if df.empty:
        st.info("No products available.")
        return

    if include_finance:
        st.dataframe(df.style.format({"unit_cost": "${:.2f}", "total_cost": "${:.2f}"}))
        st.write("Total Asset Value:", f"${df['total_cost'].sum():,.2f}")
        return

    st.dataframe(df[["product_name", "quantity"]], use_container_width=True, hide_index=True)
    st.caption("Employee view hides cost columns by policy.")
