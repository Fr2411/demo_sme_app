# Easy Ecom

Easy Ecom now runs with a **stateless Streamlit UI** and a **FastAPI + PostgreSQL backend** as the single source of truth.

## Architecture (AWS-ready)

- `streamlit` service: UI only, no CSV persistence.
- `backend` service: CRUD APIs + SQLAlchemy + Alembic migrations.
- `db` service: PostgreSQL (swap to AWS RDS in cloud).
- `nginx` service:
  - `/` -> Streamlit UI
  - `/api/*` -> FastAPI
  - `/health` -> FastAPI health

`DB/` CSV files are legacy artifacts and are not used at runtime.

## Key environment variables

From `.env.example`:

- `DATABASE_URL` (backend SQLAlchemy connection)
- `CORS_ORIGINS` (comma-separated backend CORS origins)
- `API_BASE_URL` (Streamlit -> API base URL, e.g. `http://nginx/api` in compose)

## Local run

```bash
cp .env.example .env
docker compose up -d --build
```

Access:

- UI: `http://localhost`
- Health via nginx: `http://localhost/api/health`

## Core API endpoints used by Streamlit

- `POST /auth/login`
- `GET /products?client_id=...`
- `POST /products`
- `GET /sales?client_id=...`
- `POST /sales`
- `GET /clients`
- `GET /health`

## Project flow

1. User logs into Streamlit.
2. Streamlit calls backend via `services/api_client.py`.
3. Backend writes/reads PostgreSQL tables (`users`, `products`, `sales`).
4. Nginx fronts both services for single-entry deployment.

## Deployment recommendation (ECS/Fargate)

Build two images and push to ECR:

- API image from `Dockerfile.api`
- UI image from `Dockerfile.streamlit`

Use one RDS PostgreSQL instance and configure `DATABASE_URL` per environment.

