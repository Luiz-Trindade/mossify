import sys
import inspect
from os import cpu_count
from typing import Optional
import uvicorn


def run_server(
    app,
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: Optional[int] = None,
    **uvicorn_kwargs,
):
    """
    Executa o servidor Uvicorn com suporte a múltiplos workers.

    - Se `reload=True`, usa a instância diretamente (workers é ignorado).
    - Se `workers` for None, usa o número de CPUs (padrão).
    - Se `workers > 1`, tenta detectar a variável que contém a instância
        no módulo __main__ para passar a string ao Uvicorn.
    - Caso contrário, passa a instância diretamente.
    """
    if reload:
        uvicorn.run(app, host=host, port=port, reload=True, **uvicorn_kwargs)
        return

    if workers is None:
        workers = cpu_count() or 1

    if workers > 1:
        main_module = sys.modules.get("__main__")
        app_str = None
        if main_module:
            for var_name, obj in inspect.getmembers(main_module):
                if obj is app:
                    app_str = f"{main_module.__name__}:{var_name}"
                    break

        if app_str:
            uvicorn.run(
                app_str, host=host, port=port, workers=workers, **uvicorn_kwargs
            )
        else:
            print("⚠️  Could not detect instance variable, using single worker.")
            uvicorn.run(app, host=host, port=port, **uvicorn_kwargs)
    else:
        uvicorn.run(app, host=host, port=port, **uvicorn_kwargs)
