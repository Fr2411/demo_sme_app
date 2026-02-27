import plotly.express as px
import streamlit as st

from services.analytics_service import summarize_dashboard
from services.inventory_service import load_products
from services.sales_service import load_sales


def render_dashboard_tab():
    df_products = load_products()
    df_sales = load_sales()
    summary = summarize_dashboard(df_products, df_sales)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Asset Value", f"${summary['total_assets']:,.2f}")
    col2.metric("Stock Units", summary["total_items"])
    col3.metric("Sales Revenue", f"${summary['total_revenue']:,.2f}")
    col4.metric("Total Profit", f"${summary['total_profit']:,.2f}")
    col5.metric("Average Margin", f"{summary['avg_margin']}%")

    st.markdown("---")
    st.info("⚠ Demo system limitations: Single-user, CSV-based, no FIFO, not tax-compliant, not multi-user safe.")

    if not df_products.empty:
        fig_assets = px.bar(df_products, x="product_name", y="total_cost", title="Asset Value per Product")
        st.plotly_chart(fig_assets, use_container_width=True)

    if not df_sales.empty:
        fig_sales = px.bar(
            df_sales.groupby("product_name")["total_sale"].sum().reset_index(),
            x="product_name",
            y="total_sale",
            title="Sales Revenue per Product",
        )
        st.plotly_chart(fig_sales, use_container_width=True)

        fig_profit = px.bar(
            df_sales.groupby("product_name")["profit"].sum().reset_index(),
            x="product_name",
            y="profit",
            title="Profit per Product",
        )
        st.plotly_chart(fig_profit, use_container_width=True)
