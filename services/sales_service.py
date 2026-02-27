import os
from datetime import datetime

import pandas as pd

from config import PRODUCTS_FILE, SALES_FILE
from services.common import normalize_product_name
from services.inventory_service import load_products

SALES_COLUMNS = [
    "date",
    "product_name",
    "quantity_sold",
    "unit_price",
    "unit_cost",
    "total_sale",
    "cost_of_goods_sold",
    "profit",
]


def load_sales():
    if os.path.exists(SALES_FILE):
        df = pd.read_csv(SALES_FILE)
        for col in SALES_COLUMNS:
            if col not in df.columns:
                df[col] = 0

        df["product_name"] = df["product_name"].apply(normalize_product_name)
        df["quantity_sold"] = pd.to_numeric(df["quantity_sold"], errors="coerce").fillna(0).astype(int).clip(lower=0)
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0.0).clip(lower=0).round(2)
        df["unit_cost"] = pd.to_numeric(df["unit_cost"], errors="coerce").fillna(0.0).clip(lower=0).round(2)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["date"] = df["date"].fillna(datetime.now()).dt.strftime("%Y-%m-%d %H:%M:%S")

        df["total_sale"] = (df["quantity_sold"] * df["unit_price"]).round(2)
        df["cost_of_goods_sold"] = (df["quantity_sold"] * df["unit_cost"]).round(2)
        df["profit"] = (df["total_sale"] - df["cost_of_goods_sold"]).round(2)

        df = df[SALES_COLUMNS]
        df.to_csv(SALES_FILE, index=False)
        return df

    df = pd.DataFrame(columns=SALES_COLUMNS)
    df.to_csv(SALES_FILE, index=False)
    return df


def add_sale(product_name, quantity_sold, unit_price):
    product_name = normalize_product_name(product_name)
    df_products = load_products()
    df_sales = load_sales()

    product_row = df_products[df_products["product_name"] == product_name]
    if product_row.empty:
        return False, "Product not found"

    available_qty = int(product_row["quantity"].values[0])
    unit_cost = float(product_row["unit_cost"].values[0])
    quantity_sold = int(quantity_sold)
    unit_price = round(float(unit_price), 2)

    if quantity_sold <= 0:
        return False, "Quantity sold must be greater than zero"
    if unit_price < 0:
        return False, "Selling price cannot be negative"
    if quantity_sold > available_qty:
        return False, "Cannot sell more than available stock"

    total_sale = round(quantity_sold * unit_price, 2)
    cogs = round(quantity_sold * unit_cost, 2)
    profit = round(total_sale - cogs, 2)

    new_row = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "product_name": product_name,
        "quantity_sold": quantity_sold,
        "unit_price": unit_price,
        "unit_cost": unit_cost,
        "total_sale": total_sale,
        "cost_of_goods_sold": cogs,
        "profit": profit,
    }
    df_sales = pd.concat([df_sales, pd.DataFrame([new_row])], ignore_index=True)
    df_sales.to_csv(SALES_FILE, index=False)

    new_qty = available_qty - quantity_sold
    df_products.loc[df_products["product_name"] == product_name, "quantity"] = new_qty
    df_products.loc[df_products["product_name"] == product_name, "total_cost"] = round(new_qty * unit_cost, 2)
    df_products.to_csv(PRODUCTS_FILE, index=False)
    return True, "Sale recorded successfully"
