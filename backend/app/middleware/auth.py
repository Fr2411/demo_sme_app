from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class AuthContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = request.headers.get('X-Request-ID')
        return await call_next(request)
