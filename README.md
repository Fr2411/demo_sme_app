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

Default client login:
- Client ID: `demo_client`
- Username: `admin`
- Password: `admin123`

Default superadmin login (separate admin portal):
- Username: `superadmin`
- Password: `superadmin123`


### Optional API-backed dashboard integration

The Streamlit dashboard can enrich CSV analytics with live FastAPI signals when these env vars are set before running Streamlit:

```env
EASY_ECOM_API_BASE_URL=http://localhost:8000
EASY_ECOM_API_TOKEN=<jwt_access_token>
```

When configured, dashboard widgets pull returns, stock-aging, inventory movements, orders, and session logs from API endpoints; otherwise the UI gracefully falls back to CSV-only metrics.

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
- `DB/products.csv`: inventory rows with `client_id`.
- `DB/sales.csv`: sales rows with `client_id`.
- `DB/clients.csv`: client business profile, communication channels, and policy controls:
  - `business_overview`
  - `opening_hours` / `closing_hours`
  - `max_discount_pct`
  - `return_refund_policy`
  - `sales_commission_pct`
  - `whatsapp_number`
  - `messenger`
  - `required_api_keys`

### How isolation works
- Client login requires `client_id`, username, and password.
- Admin login is separate (`superadmin` role) and unlocks a dedicated **Client Admin** tab.
- The Client Admin tab can view all client/user/product/sales rows and create a new client + initial owner credentials in one flow.
- Non-admin users never see the admin panel and only access their own `client_id` data.
- Inventory and sales services always filter by the active `client_id` workspace, while superadmin controls now use a single **Client filter** across the dashboard and workspace tabs: default is **All clients** for rolled-up visibility, and selecting a client scopes analytics plus client-specific actions to that workspace.
- Writes are merged back into shared CSVs while preserving records for other clients.

### AI agent integration with client policies
- `AgentOrchestrator` enriches incoming payloads with `client_context` from `DB/clients.csv` when `client_id` is provided.
- Discount decisions enforce `max_discount_pct` and include commission metadata in responses.
- Prompt context now includes client business/policy details so agents can use them as needed.

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
