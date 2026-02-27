import pandas as pd

from config import PRODUCTS_FILE
from services.client_service import PRODUCT_COLUMNS, ensure_db_structure
from services.common import normalize_product_name


def load_products(client_id):
    ensure_db_structure()
    df = pd.read_csv(PRODUCTS_FILE)

    for col in PRODUCT_COLUMNS:
        if col not in df.columns:
            df[col] = 0

    normalized_client_id = str(client_id) if client_id is not None else "__all__"
    include_all_clients = normalized_client_id == "__all__"

    df["client_id"] = df["client_id"].astype(str)
    if not include_all_clients:
        df = df[df["client_id"] == normalized_client_id].copy()

    if df.empty:
        return pd.DataFrame(columns=PRODUCT_COLUMNS)

    df["product_name"] = df["product_name"].apply(normalize_product_name)
    df = df[df["product_name"] != ""].copy()

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0).astype(int).clip(lower=0)
    df["unit_cost"] = pd.to_numeric(df["unit_cost"], errors="coerce").fillna(0.0).clip(lower=0).round(2)

    df["line_value"] = (df["quantity"] * df["unit_cost"]).round(2)

    consolidated = (
        df.groupby(["client_id", "product_name"], as_index=False)
        .agg(quantity=("quantity", "sum"), total_value=("line_value", "sum"))
    )
    consolidated["unit_cost"] = consolidated.apply(
        lambda row: round(row["total_value"] / row["quantity"], 2) if row["quantity"] > 0 else 0.0,
        axis=1,
    )
    consolidated["total_cost"] = (consolidated["quantity"] * consolidated["unit_cost"]).round(2)
    consolidated = consolidated[PRODUCT_COLUMNS].sort_values(["client_id", "product_name"]).reset_index(drop=True)

    if not include_all_clients:
        all_df = pd.read_csv(PRODUCTS_FILE)
        all_df = all_df[all_df["client_id"].astype(str) != normalized_client_id]
        updated = pd.concat([all_df, consolidated], ignore_index=True)
        updated.to_csv(PRODUCTS_FILE, index=False)
    return consolidated


def add_product(client_id, product_name, quantity, unit_cost):
    product_name = normalize_product_name(product_name)
    df = load_products(client_id)
    quantity = int(quantity)
    unit_cost = round(float(unit_cost), 2)

    if not product_name:
        return False, "Enter product name"
    if quantity <= 0:
        return False, "Quantity must be greater than zero"
    if unit_cost < 0:
        return False, "Unit cost cannot be negative"

    if product_name in df["product_name"].values:
        existing = df[df["product_name"] == product_name]
        old_qty = int(existing["quantity"].values[0])
        old_cost = float(existing["unit_cost"].values[0])

        new_total_qty = old_qty + quantity
        new_weighted_cost = round(((old_qty * old_cost) + (quantity * unit_cost)) / new_total_qty, 2)

        df.loc[df["product_name"] == product_name, "quantity"] = new_total_qty
        df.loc[df["product_name"] == product_name, "unit_cost"] = new_weighted_cost
        df.loc[df["product_name"] == product_name, "total_cost"] = round(new_total_qty * new_weighted_cost, 2)
    else:
        total_cost = round(quantity * unit_cost, 2)
        new_row = {
            "client_id": str(client_id),
            "product_name": product_name,
            "quantity": quantity,
            "unit_cost": unit_cost,
            "total_cost": total_cost,
        }
        if df.empty:
            df = pd.DataFrame([new_row], columns=PRODUCT_COLUMNS)
        else:
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    all_df = pd.read_csv(PRODUCTS_FILE)
    all_df = all_df[all_df["client_id"].astype(str) != str(client_id)]
    updated = pd.concat([all_df, df[PRODUCT_COLUMNS]], ignore_index=True)
    updated.to_csv(PRODUCTS_FILE, index=False)
    return True, "Product added / updated successfully"
