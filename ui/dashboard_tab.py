import math

import pandas as pd
import plotly.express as px
import streamlit as st

from ai_agents.orchestrator import AgentOrchestrator
from services.client_service import get_client_profile
from services.dashboard_service import (
    compute_executive_kpis,
    discount_governance_snapshot,
    inventory_health_frames,
    load_api_dashboard_context,
    sales_performance_frames,
    summarize_movements,
)
from services.inventory_service import load_products
from services.sales_service import load_sales


def _fmt_days_remaining(value: float) -> str:
    if value == float("inf") or math.isinf(value):
        return "Stable (no recent sales)"
    return f"{max(value, 0):.1f} days"


def render_dashboard_tab(client_id, include_finance: bool = True):
    viewing_all_clients = str(client_id) == "__all__"
    profile = (
        {
            "client_name": "All clients",
            "business_overview": "Combined view across every client.",
            "opening_hours": "-",
            "closing_hours": "-",
            "max_discount_pct": 15,
            "sales_commission_pct": 3,
            "return_refund_policy": "Depends on client policy",
        }
        if viewing_all_clients
        else get_client_profile(client_id)
    )
    if profile:
        st.caption(
            f"Client: {profile.get('client_name')} | Hours: {profile.get('opening_hours')} - {profile.get('closing_hours')} | "
            f"Max discount: {profile.get('max_discount_pct')}%"
        )
    with st.sidebar:
        st.subheader("Client policy snapshot")
        st.write(f"**Business:** {profile.get('business_overview', 'N/A')}")
        st.write(f"**Max discount:** {profile.get('max_discount_pct', 0)}%")
        st.write(f"**Sales commission:** {profile.get('sales_commission_pct', 0)}%")
        st.write(f"**Return policy:** {profile.get('return_refund_policy', 'N/A')}")

    df_products = load_products(client_id)
    df_sales = load_sales(client_id)
    api_context = load_api_dashboard_context()

    kpis = compute_executive_kpis(df_products, df_sales, api_context["returns"])

    if include_finance:
        st.subheader("Executive KPI strip")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Revenue (Today)", f"${kpis['today_revenue']:,.2f}", delta=f"Week ${kpis['week_revenue']:,.2f}")
        c2.metric("Revenue (MTD)", f"${kpis['mtd_revenue']:,.2f}", delta=f"Week Profit ${kpis['week_profit']:,.2f}")
        c3.metric("Gross Profit / Margin", f"${kpis['gross_profit']:,.2f}", delta=f"{kpis['gross_margin']:.1f}% margin")
        c4.metric("Inventory Value", f"${kpis['inventory_value']:,.2f}", delta=f"Sell-through {kpis['sell_through']:.1f}%")
        c5.metric("Return Rate / Refunds", f"{kpis['return_rate']:.1f}%", delta=f"${kpis['refund_value']:,.2f}")

        st.markdown("---")

        st.subheader("Sales performance")
        sales_frames = sales_performance_frames(df_sales)

        left, right = st.columns(2)
        if not sales_frames["revenue_by_product"].empty:
            left.plotly_chart(
                px.bar(sales_frames["revenue_by_product"], x="product_name", y="total_sale", title="Revenue by Product"),
                use_container_width=True,
            )
        if not sales_frames["profit_by_product"].empty:
            right.plotly_chart(
                px.bar(sales_frames["profit_by_product"], x="product_name", y="profit", title="Profit by Product"),
                use_container_width=True,
            )

        m1, m2 = st.columns(2)
        m1.metric("Average Order Value", f"${sales_frames['aov']:,.2f}")
        m2.metric("Order Count", sales_frames["order_count"])

        if not sales_frames["margin_distribution"].empty:
            st.plotly_chart(
                px.histogram(sales_frames["margin_distribution"], x="margin_pct", nbins=12, title="Margin Distribution by Product"),
                use_container_width=True,
            )

        b1, b2 = st.columns(2)
        b1.write("Top 10 SKUs by Profit")
        b1.dataframe(sales_frames["top_profit"], use_container_width=True, hide_index=True)
        b2.write("Bottom 10 SKUs by Profit")
        b2.dataframe(sales_frames["bottom_profit"], use_container_width=True, hide_index=True)

        if not sales_frames["daily_orders"].empty:
            st.plotly_chart(
                px.line(
                    sales_frames["daily_orders"],
                    x="day",
                    y=["revenue", "order_count"],
                    title="Order Count and Revenue Trend",
                    markers=True,
                ),
                use_container_width=True,
            )
    else:
        st.subheader("Operational KPI strip")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total SKUs", len(df_products))
        c2.metric("Low-stock SKUs", int((df_products.get("quantity", 0) <= 5).sum()) if not df_products.empty else 0)
        c3.metric("Out-of-stock SKUs", int((df_products.get("quantity", 0) <= 0).sum()) if not df_products.empty else 0)
        c4.metric("Orders (records)", len(df_sales))

    st.markdown("---")
    st.subheader("Inventory health & risk")
    inventory = inventory_health_frames(df_products, df_sales, api_context["stock_aging_rows"])
    i1, i2, i3 = st.columns(3)
    i1.metric("Low-stock SKUs", len(inventory["low_stock"]))
    i2.metric("Out-of-stock SKUs", len(inventory["out_of_stock"]))
    imminent = inventory["days_remaining"].replace([float("inf")], pd.NA).dropna(subset=["days_remaining"]) if not inventory["days_remaining"].empty else inventory["days_remaining"]
    i3.metric("Items < 14 days cover", int((imminent["days_remaining"] < 14).sum()) if not imminent.empty else 0)

    d1, d2 = st.columns(2)
    d1.write("Days of inventory remaining")
    days_table = inventory["days_remaining"].copy()
    day_columns = ["product_name", "quantity", "daily_velocity", "days_remaining"]
    days_table = days_table.reindex(columns=day_columns)
    if not days_table.empty:
        days_table["days_remaining"] = days_table["days_remaining"].apply(_fmt_days_remaining)
    d1.dataframe(days_table, use_container_width=True, hide_index=True)

    d2.write("Stock aging (API)")
    d2.dataframe(inventory["stock_aging"], use_container_width=True, hide_index=True)

    movement_summary = summarize_movements(api_context["movements"])
    st.plotly_chart(px.bar(movement_summary, x="movement_type", y="count", title="Stock Movement Timeline Summary"), use_container_width=True)

    st.markdown("---")
    st.subheader("Returns, discount governance & AI recommendations")
    decisions, decision_counts = discount_governance_snapshot(df_products, profile)

    g1, g2, g3 = st.columns(3)
    g1.metric("Discount requests (simulated today)", len(decisions))
    g2.metric("Rejected / Escalated", decision_counts["rejected"], delta=f"Escalated {decision_counts['escalated']}")
    avg_requested = float(decisions["requested_discount_pct"].mean()) if not decisions.empty else 0.0
    g3.metric("Avg requested vs policy", f"{avg_requested:.1f}%", delta=f"Max {profile.get('max_discount_pct', 0)}%")

    if not decisions.empty:
        st.dataframe(decisions, use_container_width=True, hide_index=True)

    orchestrator = AgentOrchestrator()
    ai_response = orchestrator.route(
        {
            "product_name": (df_products.iloc[0]["product_name"] if not df_products.empty else "sample sku"),
            "current_margin_pct": float(kpis["gross_margin"] or 30),
            "requested_discount_pct": max(5.0, float(profile.get("max_discount_pct", 0)) * 0.8),
            "client_id": client_id,
        }
    )
    ai_suggestion = ai_response.get("metadata", {}).get("discount_supervisor", {})
    st.info(f"Suggested action: {ai_suggestion.get('action', 'n/a')} — {ai_suggestion.get('text', 'No recommendation available')}")

    st.markdown("---")
    st.subheader("Operations & control")
    o1, o2, o3 = st.columns(3)
    o1.metric("Session log records", len(api_context["session_logs"]))
    sensitive_edits = sum(1 for order in api_context["orders"] if order.get("status") in {"cancelled", "edited"})
    o2.metric("Order edit/delete alerts", sensitive_edits)
    failed_logins = sum(1 for log in api_context["session_logs"] if str(log.get("action", "")).lower() in {"failed_login", "login_failed"})
    o3.metric("Failed auth attempts", failed_logins)
    st.session_state["last_dashboard_sync"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    st.caption(f"Data freshness: {st.session_state['last_dashboard_sync']}")

    st.write("Conversational command center")
    with st.expander("Ask the dashboard"):
        st.write("Try prompts like: 'Why did margin drop this week?' or 'Show low stock SKUs with highest revenue impact'.")
    st.write(
        "Webhook/API health: "
        + ("Connected to FastAPI dashboard endpoints." if api_context["api_connected"] else "API disconnected; showing CSV-backed analytics.")
    )
    endpoint_statuses = pd.DataFrame(api_context.get("endpoint_statuses", []))
    if not endpoint_statuses.empty:
        endpoint_statuses["status"] = endpoint_statuses["connected"].map({True: "Connected", False: "Unavailable"})
        st.dataframe(endpoint_statuses[["label", "endpoint", "status"]], use_container_width=True, hide_index=True)
