from .core.app_factory import create_fastapi_app
from .server.runner import run_server
from .core.cache import CacheManager
from .core.middleware import CacheInvalidationMiddleware
from .core.router import RouterBuilder


class Mossify:
    def __init__(
        self,
        database_url: str = "sqlite:///mossify.db",
        title: str = "Mossify API",
        description: str = "🌿 Simple, organic API with automatic CRUD and caching.",
        version: str = "0.1.3",
        cache_dir: str = ".mossify_cache",
        cache_ttl: int = 120,
        openapi_url: str = "/openapi.json",
        docs_url: str = "/docs",
        redoc_url: str = "/redoc",
        **fastapi_kwargs,
    ):
        self.database_url = database_url

        # Cria a aplicação FastAPI
        self.app = create_fastapi_app(
            title=title,
            description=description,
            version=version,
            openapi_url=openapi_url,
            docs_url=docs_url,
            redoc_url=redoc_url,
            **fastapi_kwargs,
        )

        # Inicializa o cache
        self.cache_manager = CacheManager(cache_dir=cache_dir, ttl=cache_ttl)

        # Adiciona middleware de invalidação automática
        self.app.add_middleware(
            CacheInvalidationMiddleware,
            cache_manager=self.cache_manager,
        )

        # Construtor de rotas com cache
        self.router_builder = RouterBuilder(
            self.app,
            self.cache_manager,
            default_cache_ttl=cache_ttl,
        )

    async def __call__(self, scope, receive, send):
        """Torna a classe ASGI-compliant."""
        await self.app(scope, receive, send)

    def register_route(self, path: str, **kwargs):
        """Registra uma rota com cache inteligente."""
        return self.router_builder.register_route(path, **kwargs)

    def run(self, **server_kwargs):
        """Inicia o servidor com múltiplos workers."""
        # Passa a própria instância (que é ASGI) para o runner
        run_server(self, **server_kwargs)


__version__ = "0.1.4"
__all__ = ["Mossify"]
