import streamlit as st

from services.analytics_service import sales_preview_metrics
from services.inventory_service import load_products
from services.sales_service import load_sales


def render_finance_tab(client_id: str) -> None:
    st.subheader("Finance")
    df_products = load_products(client_id)
    df_sales = load_sales(client_id)

    if df_products.empty:
        st.info("No products available for finance analysis yet.")
        return

    total_inventory_value = float(df_products["total_cost"].sum())
    total_sales = float(df_sales["total_sale"].sum()) if not df_sales.empty else 0.0
    total_profit = float(df_sales["profit"].sum()) if not df_sales.empty else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Inventory Value", f"${total_inventory_value:,.2f}")
    c2.metric("Sales Revenue", f"${total_sales:,.2f}")
    c3.metric("Gross Profit", f"${total_profit:,.2f}")

    st.markdown("#### Inventory finance details")
    st.dataframe(df_products[["product_name", "quantity", "unit_cost", "total_cost"]], use_container_width=True, hide_index=True)

    if not df_sales.empty:
        st.markdown("#### Sales ledger")
        st.dataframe(
            df_sales[["date", "product_name", "quantity_sold", "unit_price", "total_sale", "cost_of_goods_sold", "profit"]],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("#### Quick pricing simulator")
    product_name = st.selectbox("Product", df_products["product_name"], key="finance_product_selector")
    product_row = df_products[df_products["product_name"] == product_name].iloc[0]

    qty = st.number_input("Quantity", min_value=1, max_value=max(1, int(product_row["quantity"])), value=1, key="finance_quantity")
    selling_price = st.number_input("Proposed Selling Price", min_value=0.0, step=0.01, key="finance_selling_price")
    profit_per_unit, total_profit_sale, avg_margin = sales_preview_metrics(
        df_sales,
        float(product_row["unit_cost"]),
        selling_price,
        qty,
    )
    st.write(f"Profit per unit: ${profit_per_unit:.2f}")
    st.write(f"Projected profit: ${total_profit_sale:.2f}")
    st.write(f"Average margin history: {avg_margin}%")
