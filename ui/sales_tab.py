import streamlit as st

from services.analytics_service import sales_preview_metrics
from services.inventory_service import load_products
from services.sales_service import add_sale, load_sales


def render_sales_tab():
    df_products = load_products()
    df_instock = df_products[df_products["quantity"] > 0]

    if df_instock.empty:
        st.warning("No stock available.")
        return

    with st.form("sales_form", clear_on_submit=True):
        product_name = st.selectbox("Product", df_instock["product_name"])
        product_row = df_instock[df_instock["product_name"] == product_name]
        available_qty = int(product_row["quantity"].values[0])
        unit_cost = float(product_row["unit_cost"].values[0])

        st.write(f"Available Stock: {available_qty}")
        st.write(f"Purchase Cost: ${unit_cost:.2f}")

        quantity_sold = st.number_input("Quantity Sold", min_value=1, max_value=available_qty, step=1)
        unit_price = st.number_input("Selling Price", min_value=0.0, step=0.01)

        df_sales = load_sales()
        profit_per_unit, total_profit_sale, avg_margin = sales_preview_metrics(
            df_sales,
            unit_cost,
            unit_price,
            quantity_sold,
        )
        st.write(f"Profit per Unit: ${profit_per_unit:.2f}")
        st.write(f"Total Profit for this Sale: ${total_profit_sale:.2f}")
        st.write(f"Average Margin Based on Previous Sales: {avg_margin}%")

        if profit_per_unit < 0:
            st.error("⚠ Selling below cost!")

        submitted = st.form_submit_button("Record Sale")
        if submitted:
            ok, message = add_sale(product_name, quantity_sold, unit_price)
            if ok:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
