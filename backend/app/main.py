from fastapi import FastAPI

from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.middleware.auth import AuthContextMiddleware

app = FastAPI(title=settings.app_name, version='1.0.0')
app.add_middleware(AuthContextMiddleware)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}
