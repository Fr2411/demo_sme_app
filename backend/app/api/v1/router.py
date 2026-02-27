from fastapi import APIRouter

from backend.app.api.v1.endpoints.accounting import router as accounting_router
from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.chat import router as chat_router
from backend.app.api.v1.endpoints.inventory import router as inventory_router
from backend.app.api.v1.endpoints.orders import router as orders_router
from backend.app.api.v1.endpoints.products import router as products_router
from backend.app.api.v1.endpoints.reports import router as reports_router
from backend.app.api.v1.endpoints.returns import router as returns_router
from backend.app.api.v1.endpoints.sessions import router as sessions_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(products_router)
api_router.include_router(inventory_router)
api_router.include_router(orders_router)
api_router.include_router(returns_router)
api_router.include_router(accounting_router)
api_router.include_router(reports_router)
api_router.include_router(chat_router)
api_router.include_router(sessions_router)
