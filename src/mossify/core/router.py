import inspect
import json
from functools import wraps
from typing import Callable
from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session
from .cache import CacheManager


class RouterBuilder:
    def __init__(self, app, cache_manager: CacheManager, default_cache_ttl: int = 120):
        self.app = app
        self.cache = cache_manager
        self.default_cache_ttl = default_cache_ttl

    def register_route(self, path: str, **kwargs):
        cache_ttl = kwargs.pop("cache_ttl", self.default_cache_ttl)
        cache_enabled = kwargs.pop("cache", True)
        cache_prefix = kwargs.pop("cache_prefix", path.rstrip("/"))
        methods = kwargs.get("methods", ["GET"])
        is_write = any(m in ["POST", "PUT", "DELETE", "PATCH"] for m in methods)

        def decorator(endpoint: Callable):
            if is_write or not cache_enabled:
                if "methods" not in kwargs:
                    kwargs["methods"] = ["GET"]
                self.app.add_api_route(path, endpoint, **kwargs)
                if is_write:
                    self.cache.add_prefix(cache_prefix)
                return endpoint

            @wraps(endpoint)
            async def cached_endpoint(*args, **kwargs):
                sig = inspect.signature(endpoint)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()

                # Remove argumentos não serializáveis
                for name, value in list(bound.arguments.items()):
                    if isinstance(value, (Request, Session, Response)):
                        del bound.arguments[name]

                items = sorted(bound.arguments.items())
                key_data = f"{endpoint.__name__}:{json.dumps(items, sort_keys=True)}"
                full_key = f"{cache_prefix}:{key_data}"

                cached = self.cache.get(full_key)
                if cached is not None:
                    return cached

                if inspect.iscoroutinefunction(endpoint):
                    result = await endpoint(*args, **kwargs)
                else:
                    result = endpoint(*args, **kwargs)

                # Converte o resultado para JSON antes de armazenar no cache
                serializable_result = jsonable_encoder(result)
                self.cache.set(full_key, serializable_result, ttl=cache_ttl)
                return result

            if "methods" not in kwargs:
                kwargs["methods"] = ["GET"]
            self.app.add_api_route(path, cached_endpoint, **kwargs)
            return endpoint

        return decorator
