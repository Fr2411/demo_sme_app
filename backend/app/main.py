from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.ui_api import router as ui_router
from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.middleware.auth import AuthContextMiddleware

app = FastAPI(title=settings.app_name, version='1.0.0')
app.add_middleware(AuthContextMiddleware)

cors_origins = [origin.strip() for origin in settings.cors_origins.split(',') if origin.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(ui_router)


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}
