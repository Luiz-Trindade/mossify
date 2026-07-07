import sys
import inspect
from os import cpu_count
from typing import Optional
from fastapi import FastAPI
import uvicorn


class Mossify:
    def __init__(
        self,
        database_url: str = "sqlite:///mossify.db",
        title: str = "Mossify API",
        version: str = "0.1.0",
        **fastapi_kwargs,
    ):
        self.database_url = database_url
        self.app = FastAPI(title=title, version=version, **fastapi_kwargs)

        @self.app.get("/")
        async def root():
            return {"message": "🌿 Welcome to Mossify!"}

    def run(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        reload: bool = False,
        workers: Optional[int] = None,
        **kwargs,
    ):
        """
        Inicia o servidor Uvicorn com suporte a múltiplos workers.

        - Se `reload=True`, usa a instância diretamente (workers é ignorado).
        - Se `workers` for None, usa o número de CPUs (padrão).
        - Se `workers > 1`, tenta detectar a variável que contém a instância
            no módulo __main__ para passar a string ao Uvicorn.
        - Caso contrário, passa a instância diretamente.
        """
        if reload:
            # reload não funciona com workers, então usa a instância diretamente
            uvicorn.run(self.app, host=host, port=port, reload=True, **kwargs)
            return

        # Define o número de workers (padrão = número de CPUs)
        if workers is None:
            workers = cpu_count() or 1

        if workers > 1:
            # Tenta descobrir o nome da variável que contém esta instância no módulo principal
            main_module = sys.modules.get("__main__")
            app_str = None
            if main_module:
                for var_name, obj in inspect.getmembers(main_module):
                    if obj is self:
                        app_str = f"{main_module.__name__}:{var_name}"
                        break

            if app_str:
                # Usa a string para o Uvicorn com múltiplos workers
                uvicorn.run(app_str, host=host, port=port, workers=workers, **kwargs)
            else:
                # Fallback: se não encontrar a variável, usa a instância (sem workers)
                print(
                    "⚠️  Mossify: Could not detect instance variable, using single worker."
                )
                uvicorn.run(self.app, host=host, port=port, **kwargs)
        else:
            # Apenas 1 worker: usa a instância diretamente
            uvicorn.run(self.app, host=host, port=port, **kwargs)
