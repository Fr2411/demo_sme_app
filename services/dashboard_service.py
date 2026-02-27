from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from urllib import error, parse, request

import pandas as pd

from ai_agents.discount_supervisor import DiscountSupervisor

MOVEMENT_TYPES = ["in", "out", "adjustment", "return_in", "return_out"]


def _coerce_sales_frame(df_sales: pd.DataFrame) -> pd.DataFrame:
    if df_sales.empty:
        return df_sales.copy()

    frame = df_sales.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["date"] = frame["date"].fillna(pd.Timestamp.now())
    for column in ["quantity_sold", "total_sale", "profit", "unit_price", "unit_cost", "cost_of_goods_sold"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0)
    frame["margin_pct"] = (frame["profit"] / frame["total_sale"].replace(0, pd.NA) * 100).fillna(0)
    return frame


def compute_executive_kpis(df_products: pd.DataFrame, df_sales: pd.DataFrame, returns_payload: list[dict]) -> dict:
    sales = _coerce_sales_frame(df_sales)
    now = pd.Timestamp.now()
    day_start = now.normalize()
    week_start = day_start - timedelta(days=day_start.weekday())
    month_start = day_start.replace(day=1)

    def _sum_between(start: pd.Timestamp, column: str) -> float:
        if sales.empty:
            return 0.0
        return float(sales.loc[sales["date"] >= start, column].sum())

    inventory_value = float(pd.to_numeric(df_products.get("total_cost", 0), errors="coerce").fillna(0).sum())
    sold_units = float(pd.to_numeric(sales.get("quantity_sold", 0), errors="coerce").fillna(0).sum())
    on_hand_units = float(pd.to_numeric(df_products.get("quantity", 0), errors="coerce").fillna(0).sum())
    available_units = sold_units + on_hand_units
    sell_through = (sold_units / available_units * 100) if available_units > 0 else 0

    refund_value = 0.0
    return_rate = 0.0
    if returns_payload:
        returned_units = 0.0
        for item in returns_payload:
            qty = float(item.get("quantity", 0) or 0)
            price = float(item.get("unit_price", 0) or 0)
            returned_units += qty
            refund_value += qty * price
        return_rate = (returned_units / sold_units * 100) if sold_units > 0 else 0

    total_revenue = float(sales["total_sale"].sum()) if not sales.empty else 0.0
    total_profit = float(sales["profit"].sum()) if not sales.empty else 0.0

    today_revenue = _sum_between(day_start, "total_sale")
    week_revenue = _sum_between(week_start, "total_sale")
    mtd_revenue = _sum_between(month_start, "total_sale")
    week_profit = _sum_between(week_start, "profit")
    month_profit = _sum_between(month_start, "profit")

    return {
        "today_revenue": today_revenue,
        "week_revenue": week_revenue,
        "mtd_revenue": mtd_revenue,
        "gross_profit": total_profit,
        "gross_margin": (total_profit / total_revenue * 100) if total_revenue > 0 else 0,
        "inventory_value": inventory_value,
        "sell_through": sell_through,
        "return_rate": return_rate,
        "refund_value": refund_value,
        "week_profit": week_profit,
        "month_profit": month_profit,
    }


def sales_performance_frames(df_sales: pd.DataFrame) -> dict[str, pd.DataFrame | float]:
    sales = _coerce_sales_frame(df_sales)
    if sales.empty:
        empty = pd.DataFrame()
        return {
            "revenue_by_product": empty,
            "profit_by_product": empty,
            "margin_distribution": empty,
            "top_profit": empty,
            "bottom_profit": empty,
            "daily_orders": empty,
            "aov": 0.0,
            "order_count": 0,
        }

    revenue_by_product = sales.groupby("product_name", as_index=False)["total_sale"].sum().sort_values("total_sale", ascending=False)
    product_profit = sales.groupby("product_name", as_index=False).agg({"profit": "sum", "total_sale": "sum"})
    product_profit["margin_pct"] = (product_profit["profit"] / product_profit["total_sale"].replace(0, pd.NA) * 100).fillna(0)
    product_profit = product_profit.sort_values("profit", ascending=False)

    daily_orders = (
        sales.assign(day=sales["date"].dt.date)
        .groupby("day", as_index=False)
        .agg(order_count=("product_name", "count"), revenue=("total_sale", "sum"))
    )
    daily_orders["aov"] = (daily_orders["revenue"] / daily_orders["order_count"].replace(0, pd.NA)).fillna(0)

    return {
        "revenue_by_product": revenue_by_product,
        "profit_by_product": product_profit,
        "margin_distribution": product_profit[["product_name", "margin_pct"]],
        "top_profit": product_profit.head(10),
        "bottom_profit": product_profit.sort_values("profit", ascending=True).head(10),
        "daily_orders": daily_orders,
        "aov": float(sales["total_sale"].mean()),
        "order_count": int(len(sales)),
    }


def inventory_health_frames(df_products: pd.DataFrame, df_sales: pd.DataFrame, stock_aging_rows: list[dict]) -> dict:
    products = df_products.copy()
    days_remaining_columns = ["product_name", "quantity", "quantity_sold", "daily_velocity", "days_remaining"]
    if products.empty:
        return {
            "low_stock": pd.DataFrame(),
            "out_of_stock": pd.DataFrame(),
            "days_remaining": pd.DataFrame(columns=days_remaining_columns),
            "stock_aging": pd.DataFrame(stock_aging_rows),
        }

    products["quantity"] = pd.to_numeric(products["quantity"], errors="coerce").fillna(0)
    low_stock = products[(products["quantity"] > 0) & (products["quantity"] <= 5)].sort_values("quantity")
    out_of_stock = products[products["quantity"] <= 0]

    sales = _coerce_sales_frame(df_sales)
    recent_window_start = pd.Timestamp.now() - timedelta(days=30)
    recent_sales = sales[sales["date"] >= recent_window_start] if not sales.empty else pd.DataFrame()
    velocity = (
        recent_sales.groupby("product_name", as_index=False)["quantity_sold"].sum() if not recent_sales.empty else pd.DataFrame(columns=["product_name", "quantity_sold"])
    )

    days_df = products[["product_name", "quantity"]].merge(velocity, on="product_name", how="left")
    days_df["quantity_sold"] = days_df["quantity_sold"].fillna(0)
    days_df["daily_velocity"] = days_df["quantity_sold"] / 30
    days_df["days_remaining"] = days_df.apply(
        lambda row: (row["quantity"] / row["daily_velocity"]) if row["daily_velocity"] > 0 else float("inf"), axis=1
    )
    days_df = days_df.sort_values("days_remaining", ascending=True)
    days_df = days_df.reindex(columns=days_remaining_columns)

    return {
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "days_remaining": days_df,
        "stock_aging": pd.DataFrame(stock_aging_rows),
    }


def discount_governance_snapshot(df_products: pd.DataFrame, profile: dict) -> tuple[pd.DataFrame, dict]:
    products = df_products.copy()
    if products.empty:
        return pd.DataFrame(), {"approved": 0, "rejected": 0, "escalated": 0}

    supervisor = DiscountSupervisor()
    rows = []
    max_discount = float(profile.get("max_discount_pct", 0) or 0)
    commission_pct = float(profile.get("sales_commission_pct", 0) or 0)

    products["unit_cost"] = pd.to_numeric(products["unit_cost"], errors="coerce").fillna(0)
    products = products[products["unit_cost"] > 0].copy()

    scenario_discounts = [max(2.0, max_discount * 0.3), max(5.0, max_discount * 0.7), max(max_discount + 3, 20.0)]
    for _, row in products.head(8).iterrows():
        baseline_margin = 35.0
        for requested in scenario_discounts:
            decision = supervisor.evaluate(
                {
                    "product_name": row["product_name"],
                    "current_margin_pct": baseline_margin,
                    "requested_discount_pct": requested,
                    "client_context": profile,
                }
            )
            action = decision["action"]
            status = "approved"
            if action == "reject_discount":
                status = "rejected"
            elif action in {"executive_approval_required", "supervisor_review_required"}:
                status = "escalated"

            post_margin = float(decision["metadata"]["post_discount_margin"])
            commission_impact = max(0.0, requested) * commission_pct / 100
            rows.append(
                {
                    "product_name": row["product_name"],
                    "requested_discount_pct": round(requested, 2),
                    "policy_max_discount_pct": max_discount,
                    "post_discount_margin_pct": round(post_margin, 2),
                    "status": status,
                    "commission_impact_pct": round(commission_impact, 2),
                }
            )

    snapshot = pd.DataFrame(rows)
    counts = {
        "approved": int((snapshot["status"] == "approved").sum()) if not snapshot.empty else 0,
        "rejected": int((snapshot["status"] == "rejected").sum()) if not snapshot.empty else 0,
        "escalated": int((snapshot["status"] == "escalated").sum()) if not snapshot.empty else 0,
    }
    return snapshot, counts


def _request_json(path: str, params: dict | None = None) -> list[dict] | dict | None:
    base_url = os.getenv("EASY_ECOM_API_BASE_URL", "").strip().rstrip("/")
    token = os.getenv("EASY_ECOM_API_TOKEN", "").strip()
    if not base_url or not token:
        return None

    query = f"?{parse.urlencode(params)}" if params else ""
    req = request.Request(
        f"{base_url}{path}{query}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="GET",
    )
    try:
        with request.urlopen(req, timeout=5) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def load_api_dashboard_context() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    profit_loss = _request_json("/api/v1/reports/profit-loss", {"period_start": today, "period_end": today})
    returns = _request_json("/api/v1/returns")
    stock_aging = _request_json("/api/v1/reports/stock-aging", {"as_of_date": today})
    movements = _request_json("/api/v1/inventory/movements")
    session_logs = _request_json("/api/v1/sessions/logs")
    orders = _request_json("/api/v1/orders")

    stock_aging_rows = stock_aging.get("rows", []) if isinstance(stock_aging, dict) else []

    return {
        "profit_loss": profit_loss if isinstance(profit_loss, dict) else {},
        "returns": returns if isinstance(returns, list) else [],
        "stock_aging_rows": stock_aging_rows,
        "movements": movements if isinstance(movements, list) else [],
        "session_logs": session_logs if isinstance(session_logs, list) else [],
        "orders": orders if isinstance(orders, list) else [],
        "api_connected": any([profit_loss, returns, stock_aging, movements, session_logs, orders]),
    }


def summarize_movements(movements: list[dict]) -> pd.DataFrame:
    if not movements:
        return pd.DataFrame(columns=["movement_type", "count"])

    frame = pd.DataFrame(movements)
    if "movement_type" not in frame.columns:
        return pd.DataFrame(columns=["movement_type", "count"])

    summary = frame.groupby("movement_type", as_index=False).size().rename(columns={"size": "count"})
    for movement in MOVEMENT_TYPES:
        if movement not in summary["movement_type"].values:
            summary = pd.concat([summary, pd.DataFrame([{"movement_type": movement, "count": 0}])], ignore_index=True)
    return summary.sort_values("movement_type")
