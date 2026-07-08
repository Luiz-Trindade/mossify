from contextlib import asynccontextmanager
from typing import Optional, List, Type
from sqlmodel import SQLModel


from .core.app_factory import create_fastapi_app
from .server.runner import run_server
from .core.cache import CacheManager
from .core.middleware import CacheInvalidationMiddleware
from .core.router import RouterBuilder
from .core.database import DatabaseManager
from .core.model_registry import ModelRegistry
from .core.auth import register_auth_routes


class Mossify:
    def __init__(
        self,
        database_url: str = "sqlite:///mossify.db",
        database_models: Optional[List[Type[SQLModel]]] = None,
        title: str = "Mossify API",
        description: str = "🌿 Simple, organic API with automatic CRUD and caching.",
        version: str = "0.1.4",
        cache_dir: str = ".mossify_cache",
        cache_ttl: int = 500,
        openapi_url: str = "/openapi.json",
        docs_url: str = "/docs",
        redoc_url: str = "/redoc",
        enable_auth: bool = False,
        **fastapi_kwargs,
    ):
        self.database_url = database_url

        # Cache
        self.cache_manager = CacheManager(cache_dir=cache_dir, ttl=cache_ttl)

        # Database
        self.db_manager = DatabaseManager(database_url)
        if database_models:
            self.db_manager.create_tables(database_models)

        # Router builder
        self.router_builder = RouterBuilder(
            None,
            self.cache_manager,
            default_cache_ttl=cache_ttl,
        )

        # Model registry
        self.model_registry = ModelRegistry(
            router_builder=self.router_builder,
            db_manager=self.db_manager,
        )

        @asynccontextmanager
        async def lifespan(app):
            await self.model_registry.start_queue_workers()
            try:
                yield
            finally:
                await self.model_registry.stop_queue_workers()

        self.app = create_fastapi_app(
            title=title,
            description=description,
            version=version,
            openapi_url=openapi_url,
            docs_url=docs_url,
            redoc_url=redoc_url,
            lifespan=lifespan,
            **fastapi_kwargs,
        )

        self.app.add_middleware(
            CacheInvalidationMiddleware,
            cache_manager=self.cache_manager,
        )

        self.router_builder.app = self.app

        if enable_auth:
            self.auth_dep = register_auth_routes(self, self.db_manager)
        else:
            self.auth_dep = None

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)

    def register_route(self, path: str, **kwargs):
        return self.router_builder.register_route(path, **kwargs)

    def register_model(self, model_class: Type[SQLModel], **kwargs):
        return self.model_registry.register_model(model_class, **kwargs)

    def run(self, **server_kwargs):
        run_server(self, **server_kwargs)


__version__ = "0.1.5"
__all__ = ["Mossify"]
