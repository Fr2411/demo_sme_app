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
├── ai_agents/
│   ├── orchestrator.py         # Multi-agent coordinator + OpenAI function-calling setup
│   ├── sales_agent.py          # Sales push agent (margin-safe campaign actions)
│   ├── stock_agent.py          # Stock urgency and replenishment agent
│   ├── discount_supervisor.py  # Discount approval policy agent
│   └── prompt_utils.py         # Shared prompt template/rule builders
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
   - Product selection immediately refreshes stock, purchase cost, and profit preview values in the Sales tab.
   - Sales are validated against available stock.
   - Revenue, COGS, and profit are computed and persisted.
   - Inventory quantity and value are reduced automatically.
5. **Dashboard analytics**
   - KPIs and product-level visualizations are rendered from cleaned data.
6. **AI agent orchestration (new)**
   - Structured event payloads (`dict`) are evaluated by specialized agents.
   - Every agent returns strict JSON-style output (`action`, `text`, optional `metadata`).
   - Prompt templates consistently enforce sales push, margin, stock urgency, and discount approval rules.
   - OpenAI function-calling tools are defined with JSON Schema contracts that mirror TypeScript-style interfaces.

## Critical Logic

- **Weighted Average Cost Formula**
  ```text
  new_unit_cost = ((old_qty * old_cost) + (purchased_qty * purchase_cost)) / (old_qty + purchased_qty)
  ```
- **Sale Calculations (live preview in Sales tab)**
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
- `openai`

---

## Enterprise Backend Scaffold (FastAPI + PostgreSQL)

A production-oriented backend scaffold now exists under `backend/` with:

- API versioning via `/api/v1`
- JWT authentication and bcrypt password hashing
- RBAC primitives (`users`, `roles`, `permissions`)
- SQLAlchemy session/config setup
- Alembic migration environment
- Dockerized API runtime + pgvector-ready PostgreSQL compose service

### Quickstart (Backend)

1. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Start PostgreSQL (pgvector image):
   ```bash
   docker compose up -d db
   ```
3. Run migrations (after creating your first revision):
   ```bash
   cd backend && alembic upgrade head
   ```
4. Start API:
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```

### Implemented Section C Components

- `backend/app/main.py` – FastAPI app bootstrap and middleware.
- `backend/app/api/v1/router.py` – versioned API router.
- `backend/app/api/v1/endpoints/auth.py` – auth endpoints (`/register`, `/login`).
- `backend/app/api/deps.py` – JWT dependency and current-user resolver.
- `backend/app/core/security.py` – password hashing + JWT token creation.
- `backend/app/core/config.py` – environment-driven settings.
- `backend/app/db/session.py` – SQLAlchemy engine/session.
- `backend/alembic/*` – migration scaffolding.


### Implemented Section D Endpoints

The API now includes versioned REST endpoints with Pydantic contracts:

- `GET/POST/GET{id}/PATCH/DELETE /api/v1/products`
- `POST /api/v1/inventory/adjustments`, `GET /api/v1/inventory/movements`
- `POST/GET/PATCH/DELETE /api/v1/orders` with `X-2FA-Code` required for edits
- `POST/GET /api/v1/returns`
- `POST/GET /api/v1/accounting/journal-entries` with debit-credit validation
- `GET /api/v1/reports/profit-loss`, `GET /api/v1/reports/stock-aging`
- `POST /api/v1/chat/webhook/inbound`
- `GET /api/v1/sessions/logs`

Notes:
- Order edits require `ORDER_EDIT_2FA_CODE` configured in env.
- Profit/loss report computes from journal lines grouped by account type (`revenue`, `expense`).
- Inventory is movement-ledger based (in/out/returns/adjustments), not static balances.
