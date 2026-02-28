# Easy Ecom

Easy Ecom is a Python-based commerce platform with:
- A **Streamlit operations UI** for inventory, sales, and analytics.
- A **FastAPI backend** for production-grade APIs, auth, reporting, chat/webhook integrations, and image search.
- **AI agents** for sales, stock, and discount decision support.

---

## 1) Setup Steps

### Prerequisites
- Python 3.10+
- pip
- Docker + Docker Compose (recommended for PostgreSQL/pgvector)

### Clone and install dependencies

```bash
git clone <your-repo-url>
cd Easy_Ecom
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

### Environment configuration
Create `backend/.env` (or export env vars) with at least:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/easy_ecom
SECRET_KEY=change_this
ACCESS_TOKEN_EXPIRE_MINUTES=60
ORDER_EDIT_2FA_CODE=123456
WHATSAPP_VERIFY_TOKEN=change_me_verify_token
WHATSAPP_APP_SECRET=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_API_VERSION=v20.0
OPENAI_API_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET_NAME=easy-ecom
```

### Start database

```bash
docker compose up -d db
```

### Run migrations

```bash
cd backend
alembic upgrade head
cd ..
```

### Run backend API

```bash
uvicorn backend.app.main:app --reload --port 8000
```

### Run Streamlit UI

```bash
streamlit run app.py
```

Default platform admin login:
- Client ID: `__admin__`
- Username: `admin`
- Password: `admin123`

Default client owner login:
- Client ID: `demo_client`
- Username: `owner`
- Password: `owner123`

Default client employee login:
- Client ID: `demo_client`
- Username: `employee`
- Password: `employee123`


### Optional API-backed dashboard integration

The Streamlit dashboard can enrich CSV analytics with live FastAPI signals when these env vars are set before running Streamlit:

```env
EASY_ECOM_API_BASE_URL=http://localhost:8000
EASY_ECOM_API_TOKEN=<jwt_access_token>
```

When configured, dashboard widgets pull returns, stock-aging, inventory movements, orders, and session logs from API endpoints; otherwise the UI gracefully falls back to CSV-only metrics.

The dashboard now includes an **API endpoint status table** in the operations panel so you can confirm each monitored endpoint (`/reports/profit-loss`, `/returns`, `/reports/stock-aging`, `/inventory/movements`, `/sessions/logs`, `/orders`) is displayed with a live connectivity status (`Connected` or `Unavailable`).

Dashboard inventory analytics are also empty-state safe for newly created clients: when no products/sales exist yet, the **Days of inventory remaining** table still renders with the expected columns instead of raising a pandas column-selection error.


---

## 2) Architecture Overview

### High-level components

1. **Streamlit App (`app.py`, `ui/`, `services/`)**
   - Handles day-to-day business operations (inventory updates, sales entry, dashboard analytics).
   - Uses a multi-tenant CSV storage folder `DB/` (`users.csv`, `products.csv`, `sales.csv`, `clients.csv`) where every operational row is tagged with `client_id`.

2. **AI Agent Layer (`ai_agents/`)**
   - `orchestrator.py` coordinates specialized agents.
   - Sales, stock, and discount supervisor agents return structured decisions and recommendations.

3. **FastAPI Backend (`backend/app/`)**
   - Versioned REST API under `/api/v1`.
   - JWT auth + RBAC model foundations.
   - Inventory, orders, returns, accounting, reports, sessions, and chat webhook modules.
   - Product image upload + embedding similarity search support.

4. **Persistence**
   - **Demo mode**: CSV files for Streamlit-side operations.
   - **Production API mode**: PostgreSQL (with pgvector) via SQLAlchemy + Alembic migrations.

5. **Deployment Layer (`deployment/`)**
   - Dockerfile + compose orchestration.
   - Nginx config and startup scripts for API service environments.

### Backend package map

```text
backend/app
├── api/
│   ├── deps.py
│   └── v1/endpoints/
├── core/
├── db/
├── middleware/
├── models/
├── schemas/
└── services/
```

### Typical request flow (backend)
1. Request hits FastAPI route (`api/v1/endpoints/*`).
2. Dependencies enforce auth/context (`api/deps.py`).
3. Endpoint validates payload with Pydantic schemas.
4. Business logic executes using DB session and services.
5. Response serialized and returned to caller.

---


## 3) Multi-tenant CSV Data Layer (DB folder)

The Streamlit workflow now uses a shared multi-client CSV database under `DB/`:

- `DB/users.csv`: login users per client (`client_id`, `username`, `password`, `role`).
- `DB/user_feature_access.csv`: per-user feature toggle map (`client_id`, `username`, `feature`, `enabled`).
- `DB/products.csv`: inventory rows with `client_id`.
- `DB/sales.csv`: sales rows with `client_id`.
- `DB/finance_transactions.csv`: manual finance ledger (`transaction_type`, `category`, `amount`, `created_by`) per client.
- `DB/finance_salaries.csv`: salary setup (`employee_name`, `monthly_salary`, `payment_day`, `status`) per client.
- `DB/clients.csv`: client business profile, communication channels, and policy controls:
  - Core profile: `business_overview`, `opening_hours`, `closing_hours`, `max_discount_pct`, `return_refund_policy`, `sales_commission_pct`
  - WhatsApp integration: `whatsapp_enabled`, `whatsapp_access_token`, `whatsapp_phone_number_id`, `whatsapp_business_account_id`, `whatsapp_app_id`, `whatsapp_app_secret`, `whatsapp_webhook_verify_token`, `whatsapp_token_expires_at`
  - Messenger integration: `messenger_enabled`, `messenger_page_access_token`, `messenger_page_id`, `messenger_app_id`, `messenger_app_secret`, `messenger_webhook_verify_token`, `messenger_token_expires_at`
  - Instagram integration: `instagram_enabled`, `instagram_page_access_token`, `instagram_business_account_id`, `instagram_app_id`, `instagram_app_secret`, `instagram_webhook_verify_token`, `instagram_token_expires_at`
  - Shared Meta setup: `meta_business_manager_id`

### How isolation works
- Client login requires `client_id`, username, and password.
- Easy Ecom now supports one platform role (`admin`) and two per-client roles (`owner`, `employee`).
- Platform admin login (`client_id=__admin__`) unlocks the **Client Admin** tab, **Finance** tab, and cross-client access via **Client filter**.
- Client owners can access all tabs for their own client, including finance.
- Client employees only access their own `client_id` workspace. Finance can be granted per user by platform admin using the Role Access toggle (off by default).
- Inventory and sales services always filter by the active `client_id` workspace.
- Writes are merged back into shared CSVs while preserving records for other clients.

### AI agent integration with client policies
- `AgentOrchestrator` enriches incoming payloads with `client_context` from `DB/clients.csv` when `client_id` is provided.
- Discount decisions enforce `max_discount_pct` and include commission metadata in responses.
- Prompt context now includes client business/policy details so agents can use them as needed.


### Role-based access redesign (Platform Admin + Client Owner/Employee)
- **Admin** (`client_id=__admin__`) can access all clients, all tabs, and finance endpoints.
- **Owner** (per client) can access all tabs and finance data, but only within that client workspace.
- **Employee** (per client) can access operations tabs by default; finance can be explicitly enabled per user from Role Access when you want delegated bookkeeping.
- Legacy CSV roles are normalized automatically (`superadmin -> admin`, `manager -> owner`, `staff -> employee`).
- Platform admins now have a dedicated **Role Access** tab to enable/disable each feature per user with toggle controls.
- Feature toggle enforcement is applied at runtime; users only see tabs that are currently enabled for their login.
- **Add Product tab** now includes a **Recently Added Products Statement** table that shows full product details for the active client inventory.
- **Sales Entry tab** now includes a **Sales Entry Statement** table that shows all recorded sales details (latest first).

### Finance operations (Streamlit)
- Finance tab now includes a **manual transaction form** so authorized users can add income/expense rows (salary, rent, utility, logistics, etc.) to a client ledger.
- Finance tab also includes **salary setup** management for employee payroll planning (name, role, monthly salary, payment day, status).
- Net cash flow KPI is calculated as total income minus total expense from `finance_transactions.csv`.
- Access control is still centralized through `DB/user_feature_access.csv` and platform **Role Access** toggles.

## 4) API Documentation

Base URL (local): `http://localhost:8000`

Interactive docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Auth
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`

### Products
- `POST /api/v1/products`
- `GET /api/v1/products`
- `GET /api/v1/products/{product_id}`
- `PATCH /api/v1/products/{product_id}`
- `DELETE /api/v1/products/{product_id}`

### Inventory
- `POST /api/v1/inventory/adjustments`
- `GET /api/v1/inventory/movements`

### Orders
- `POST /api/v1/orders`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `PATCH /api/v1/orders/{order_id}` *(requires `X-2FA-Code` header)*
- `DELETE /api/v1/orders/{order_id}` *(requires `X-2FA-Code` header)*

### Returns
- `POST /api/v1/returns`
- `GET /api/v1/returns`

### Accounting
- `POST /api/v1/accounting/journal-entries`
- `GET /api/v1/accounting/journal-entries`

### Reports
- `GET /api/v1/reports/profit-loss`
- `GET /api/v1/reports/stock-aging`

### Chat / WhatsApp
- `GET /api/v1/chat/webhook` *(Meta verification handshake)*
- `POST /api/v1/chat/webhook` *(inbound webhook processing)*
- `POST /api/v1/chat/webhook/inbound` *(manual/dev simulation)*
- `GET /api/v1/chat/templates`

### Sessions
- `GET /api/v1/sessions/logs`

### Product Image Search
- `POST /api/v1/products/{product_id}/images`
- `POST /api/v1/products/image-search`

---

## 5) How to Deploy

### Option A: Docker Compose (recommended)

1. Build and start services:
   ```bash
   docker compose up --build -d
   ```
2. Run migrations inside API container (if not automated by your entrypoint):
   ```bash
   docker compose exec backend alembic upgrade head
   ```
3. Verify health:
   ```bash
   curl http://localhost:8000/health
   ```

### Option B: Manual VM/Server deployment

1. Provision Python, PostgreSQL (with pgvector), and Nginx.
2. Set environment variables securely.
3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Run migrations:
   ```bash
   cd backend && alembic upgrade head
   ```
5. Start with gunicorn/uvicorn (example):
   ```bash
   gunicorn -k uvicorn.workers.UvicornWorker backend.app.main:app -b 0.0.0.0:8000
   ```
6. Configure Nginx reverse proxy using `deployment/nginx/default.conf`.

### Deployment recommendations
- Use a managed PostgreSQL instance with automated backups.
- Store secrets in a secrets manager (not in repo).
- Enable TLS at ingress (Nginx/load balancer).
- Add centralized logging and metrics.

---

## 6) How to Test

### Backend tests

```bash
pytest backend/tests -q
```

### Focused test modules

```bash
pytest backend/tests/test_api_endpoints.py -q
pytest backend/tests/test_whatsapp_service.py -q
pytest backend/tests/test_image_matching.py -q
```

### Optional quality checks

```bash
python -m compileall .
```

---

## Project Structure

```text
.
├── app.py
├── config.py
├── ai_agents/
├── services/
├── ui/
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
├── deployment/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Critical Business Logic Notes

- Weighted average costing is used for stock purchase updates.
- Sales operations validate stock availability before commit.
- Profit, COGS, and revenue are recomputed to preserve accounting integrity.
- Chat webhook pipeline supports signature validation, AI routing, and response logging.
- Image recognition uses embedding similarity over pgvector-backed storage.


## 7) Dashboard Flow (Streamlit)

The dashboard tab is now organized as a command-center layout while preserving the existing architecture (CSV-first + optional API augment):

1. **Executive KPI strip**: today/week/MTD revenue, gross profit + margin, inventory value, sell-through, and return/refund KPIs.
2. **Sales performance panel**: revenue/profit by product, margin histogram, top/bottom SKU contribution, AOV + order-count trend.
3. **Inventory health panel**: low-stock/out-of-stock counters, days-of-inventory estimate from recent velocity, stock-aging table, stock movement summary.
4. **Returns/discount/AI panel**: simulated discount-governance monitor (policy-aware), commission impact preview, and AI recommendation card from orchestrated agents.
5. **Operations & control panel**: session activity counts, sensitive order edit/delete alerts, failed auth trend, and data freshness timestamp.
6. **Sidebar policy snapshot**: business profile, operating hours, discount cap, commission rate, and return policy.

This implementation keeps the original data model intact (no schema migration required) and uses existing data sources in `DB/*.csv`, AI agents, and FastAPI endpoints.

## 6) Financial Management & Client Dashboard Module

### Double-entry design (strict accounting)
- Every expense, income, payroll accrual, and payroll payment creates a **balanced journal entry** in `journal_entries` + `journal_lines`.
- Financial business records (`expenses`, `income`, `payroll`, `cash_transactions`) always store `linked_journal_entry_id` to guarantee traceability.
- Journal entries are immutable from API perspective (no delete endpoint); corrections use `POST /api/v1/accounting/journal-entries/{entry_id}/reverse`.

### Chart of accounts (default auto-provision)
- `1000` Cash (Asset)
- `1010` Bank (Asset)
- `1100` Accounts Receivable (Asset)
- `2000` Accounts Payable (Liability)
- `2100` Payroll Liability (Liability)
- `3000` Owner Equity (Equity)
- `3100` Retained Earnings (Equity)
- `4000` Revenue (Revenue)
- `5000` Cost of Goods Sold (Expense)
- `6000` Operating Expenses (Expense)
- `6100` Salary Expense (Expense)

### Finance API
- `POST /api/v1/finance/expenses`
- `POST /api/v1/finance/income`
- `POST /api/v1/finance/employees`
- `POST /api/v1/finance/payroll`
- `POST /api/v1/finance/payroll/{payroll_id}/approve` *(requires OTP payload `654321` in this implementation)*
- `GET /api/v1/finance/reports/cashflow`
- `GET /api/v1/finance/reports/pnl`
- `GET /api/v1/finance/reports/balance-sheet`
- `GET /api/v1/finance/dashboard`

### Client dashboard API
- `GET /api/v1/client/dashboard`
- `GET /api/v1/client/orders`
- `GET /api/v1/client/invoices`
- `GET /api/v1/client/invoices/{invoice_id}/download` *(PDF stub)*
- `GET /api/v1/client/statement`
- `GET /api/v1/client/statement/download` *(PDF stub)*
- `POST /api/v1/client/payment-confirmation`
- `POST /api/v1/client/return-request`
- `POST /api/v1/client/support-message`

### RBAC matrix
- `admin`: full global access across all clients (UI + finance APIs).
- `owner`: full access within assigned client, including finance APIs.
- `employee`: non-finance workflows only; finance endpoints are blocked.

### Security and audit controls
- Financial operations generate `audit_logs` records (action, entity, actor, timestamp).
- Payroll approval enforces simple 2FA OTP validation.
- `JournalEntry` includes `created_by`, `created_at`, and reversal linkage.

### Scheduled task stubs
Located in `backend/app/services/scheduled_finance_tasks.py`:
- `monthly_payroll_generation`
- `monthly_pnl_auto_snapshot`
- `overdue_receivable_alert`
- `low_cash_warning_alert`
