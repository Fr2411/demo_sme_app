
def summarize_dashboard(df_products, df_sales):
    total_assets = df_products["total_cost"].sum() if not df_products.empty else 0
    total_items = df_products["quantity"].sum() if not df_products.empty else 0
    total_revenue = df_sales["total_sale"].sum() if not df_sales.empty else 0
    total_profit = df_sales["profit"].sum() if not df_sales.empty else 0
    avg_margin = round((total_profit / total_revenue) * 100, 2) if total_revenue > 0 else 0

    return {
        "total_assets": total_assets,
        "total_items": total_items,
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "avg_margin": avg_margin,
    }


def sales_preview_metrics(df_sales, unit_cost, unit_price, quantity_sold):
    profit_per_unit = round(unit_price - unit_cost, 2)
    total_profit_sale = round(profit_per_unit * quantity_sold, 2)

    total_prev_revenue = df_sales["total_sale"].sum() if not df_sales.empty else 0
    total_prev_profit = df_sales["profit"].sum() if not df_sales.empty else 0
    avg_margin = round((total_prev_profit / total_prev_revenue) * 100, 2) if total_prev_revenue > 0 else 0

    return profit_per_unit, total_profit_sale, avg_margin
