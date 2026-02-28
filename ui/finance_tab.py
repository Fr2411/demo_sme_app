from __future__ import annotations

import streamlit as st

from services.analytics_service import sales_preview_metrics
from services.finance_ops_service import (
    DEFAULT_EXPENSE_CATEGORIES,
    DEFAULT_INCOME_CATEGORIES,
    add_transaction,
    get_salary_setup,
    get_transactions,
    upsert_salary_setup,
)
from services.inventory_service import load_products
from services.sales_service import load_sales


def render_finance_tab(client_id: str, actor_username: str) -> None:
    st.subheader("Finance")
    df_products = load_products(client_id)
    df_sales = load_sales(client_id)
    df_transactions = get_transactions(client_id)
    df_salaries = get_salary_setup(client_id)

    total_inventory_value = float(df_products["total_cost"].sum()) if not df_products.empty else 0.0
    total_sales = float(df_sales["total_sale"].sum()) if not df_sales.empty else 0.0
    gross_profit = float(df_sales["profit"].sum()) if not df_sales.empty else 0.0

    total_income = float(df_transactions[df_transactions["transaction_type"] == "income"]["amount"].sum()) if not df_transactions.empty else 0.0
    total_expense = float(df_transactions[df_transactions["transaction_type"] == "expense"]["amount"].sum()) if not df_transactions.empty else 0.0
    net_cash_flow = total_income - total_expense

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Inventory Value", f"${total_inventory_value:,.2f}")
    c2.metric("Sales Revenue", f"${total_sales:,.2f}")
    c3.metric("Gross Profit", f"${gross_profit:,.2f}")
    c4.metric("Net Cash Flow", f"${net_cash_flow:,.2f}")

    st.markdown("#### Add financial transaction")
    with st.form("finance_transaction_form"):
        tc1, tc2, tc3 = st.columns(3)
        transaction_date = tc1.date_input("Date")
        transaction_type = tc2.selectbox("Type", ["expense", "income"])
        category_options = DEFAULT_EXPENSE_CATEGORIES if transaction_type == "expense" else DEFAULT_INCOME_CATEGORIES
        category = tc3.selectbox("Category", category_options)

        title = st.text_input("Title", placeholder="e.g., February rent / Salary payout")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        notes = st.text_area("Notes", placeholder="Optional details")

        submitted_transaction = st.form_submit_button("Save transaction")

    if submitted_transaction:
        ok, message = add_transaction(
            client_id,
            {
                "transaction_date": transaction_date.strftime("%Y-%m-%d"),
                "transaction_type": transaction_type,
                "category": category,
                "title": title,
                "notes": notes,
                "amount": amount,
            },
            actor_username=actor_username,
        )
        if ok:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    st.markdown("#### Salary setup")
    with st.form("salary_setup_form"):
        sc1, sc2, sc3 = st.columns(3)
        employee_name = sc1.text_input("Employee name")
        role_title = sc2.text_input("Role title", placeholder="Cashier / Manager")
        monthly_salary = sc3.number_input("Monthly salary", min_value=0.0, step=0.01)

        sc4, sc5 = st.columns(2)
        payment_day = sc4.number_input("Payment day (1-31)", min_value=1, max_value=31, value=1, step=1)
        status = sc5.selectbox("Status", ["active", "inactive"])

        submitted_salary = st.form_submit_button("Save salary setup")

    if submitted_salary:
        ok, message = upsert_salary_setup(
            client_id,
            {
                "employee_name": employee_name,
                "role_title": role_title,
                "monthly_salary": monthly_salary,
                "payment_day": payment_day,
                "status": status,
            },
        )
        if ok:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    st.markdown("#### Salary profiles")
    if df_salaries.empty:
        st.info("No salary profiles set up yet.")
    else:
        st.dataframe(
            df_salaries[["employee_name", "role_title", "monthly_salary", "payment_day", "status", "updated_at"]],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("#### Transaction ledger")
    if df_transactions.empty:
        st.info("No financial transactions recorded yet.")
    else:
        st.dataframe(
            df_transactions[["transaction_date", "transaction_type", "category", "title", "amount", "created_by"]],
            use_container_width=True,
            hide_index=True,
        )

    if not df_products.empty:
        st.markdown("#### Inventory finance details")
        st.dataframe(df_products[["product_name", "quantity", "unit_cost", "total_cost"]], use_container_width=True, hide_index=True)

    if not df_sales.empty:
        st.markdown("#### Sales ledger")
        st.dataframe(
            df_sales[["date", "product_name", "quantity_sold", "unit_price", "total_sale", "cost_of_goods_sold", "profit"]],
            use_container_width=True,
            hide_index=True,
        )

    if not df_products.empty:
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
