# SME Asset Manager Demo

A lightweight Streamlit app for small-business inventory and sales tracking with **weighted-average costing**.

## How to Run

1. Install Python 3.8+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run Streamlit app:
   ```bash
   streamlit run app.py
   ```
4. Login with:
   - Username: `admin`
   - Password: `admin123`

## Project Structure

```text
.
├── app.py                     # Main Streamlit entry point (routing + session flow)
├── config.py                  # Global constants (file paths, app title/icon)
├── services/
│   ├── auth_service.py        # Authentication logic
│   ├── common.py              # Shared helpers (name normalization)
│   ├── inventory_service.py   # Inventory load/repair + weighted average updates
│   ├── sales_service.py       # Sales load/repair + stock deduction
│   └── analytics_service.py   # KPI and sale-preview calculations
└── ui/
    ├── dashboard_tab.py       # Dashboard tab rendering
    ├── add_product_tab.py     # Add-product form tab rendering
    ├── assets_tab.py          # Assets summary table tab rendering
    └── sales_tab.py           # Sales entry tab rendering
```

## Project Flow

1. **Authentication**
   - Credentials are loaded from `users.csv` via `services/auth_service.py`.
2. **Data loading and normalization**
   - Products and sales CSV files are auto-repaired for missing columns and invalid values.
   - Product names are normalized (trimmed + lowercase) to avoid duplicate keys.
3. **Stock updates (purchases)**
   - New purchases are merged into existing stock using weighted-average unit cost.
4. **Sales recording**
   - Sales are validated against available stock.
   - Revenue, COGS, and profit are computed and persisted.
   - Inventory quantity and value are reduced automatically.
5. **Dashboard analytics**
   - KPIs and product-level visualizations are rendered from cleaned data.

## Critical Logic

- **Weighted Average Cost Formula**
  ```text
  new_unit_cost = ((old_qty * old_cost) + (purchased_qty * purchase_cost)) / (old_qty + purchased_qty)
  ```
- **Sale Calculations**
  ```text
  total_sale = quantity_sold * unit_price
  cogs       = quantity_sold * unit_cost
  profit     = total_sale - cogs
  ```
- **Data Integrity Repairs**
  - Product names are normalized to lowercase/trimmed form.
  - Negative/invalid numeric values are sanitized.
  - Sales derived fields are recalculated on load to fix historical miscalculations.

## Dependencies

From `requirements.txt`:

- `streamlit`
- `pandas`
- `plotly`
