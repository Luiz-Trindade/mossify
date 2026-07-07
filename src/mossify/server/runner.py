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
    app_str: Optional[str] = None,
    **uvicorn_kwargs,
):
    if reload:
        uvicorn.run(app, host=host, port=port, reload=True, **uvicorn_kwargs)
        return

    if workers is None:
        workers = cpu_count() or 1

    if app_str is not None:
        uvicorn.run(app_str, host=host, port=port, workers=workers, **uvicorn_kwargs)
        return

    if workers <= 1:
        uvicorn.run(app, host=host, port=port, **uvicorn_kwargs)
        return

    main_module = sys.modules.get("__main__")
    detected = None
    if main_module:
        for var_name, obj in inspect.getmembers(main_module):
            if obj is app:
                detected = f"{main_module.__name__}:{var_name}"
                break

    if detected:
        uvicorn_kwargs.setdefault("lifespan", "on")
        uvicorn.run(detected, host=host, port=port, workers=workers, **uvicorn_kwargs)
    else:
        fallback = f"{main_module.__name__}:app" if main_module else "app:app"
        uvicorn_kwargs.setdefault("lifespan", "on")
        uvicorn.run(fallback, host=host, port=port, workers=workers, **uvicorn_kwargs)
