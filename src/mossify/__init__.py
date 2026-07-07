from .core.app_factory import create_fastapi_app
from .server.runner import run_server


class Mossify:
    def __init__(
        self,
        database_url: str = "sqlite:///mossify.db",
        title: str = "Mossify API",
        version: str = "0.1.0",
        **fastapi_kwargs,
    ):
        self.database_url = database_url
        self.app = create_fastapi_app(title=title, version=version, **fastapi_kwargs)

    def run(self, **server_kwargs):
        """
        Inicia o servidor com os parâmetros fornecidos.
        """
        run_server(self.app, **server_kwargs)


__version__ = "0.1.3"
__all__ = ["Mossify"]
