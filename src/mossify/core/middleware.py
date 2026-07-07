from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from .cache import CacheManager


class CacheInvalidationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, cache_manager: CacheManager):
        super().__init__(app)
        self.cache_manager = cache_manager

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            path = request.url.path.rstrip("/")
            for prefix in self.cache_manager.prefixes:
                if path.startswith(prefix):
                    self.cache_manager.invalidate_prefix(prefix)
        return response
