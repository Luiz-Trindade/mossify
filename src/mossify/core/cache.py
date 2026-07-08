from diskcache import Cache
from typing import Optional


class CacheManager:
    def __init__(self, cache_dir: str = "mossify_cache", ttl: int = 500):
        self.cache = Cache(cache_dir)
        self.default_ttl = ttl
        self._prefixes = set()
        self._async_prefixes = set()

    def get(self, key: str):
        return self.cache.get(key)

    def set(self, key: str, value, ttl: Optional[int] = None):
        if ttl is None:
            ttl = self.default_ttl
        self.cache.set(key, value, expire=ttl)

    def invalidate_prefix(self, prefix: str):
        for key in list(self.cache.iterkeys()):
            if key.startswith(prefix):
                self.cache.delete(key)

    def add_prefix(self, prefix: str):
        self._prefixes.add(prefix)

    def add_async_prefix(self, prefix: str):
        """Marcar prefixo como assíncrono: middleware não invalida, quem faz é o QueueManager."""
        self._async_prefixes.add(prefix)
        self._prefixes.add(prefix)

    @property
    def prefixes(self):
        return self._prefixes

    @property
    def async_prefixes(self):
        return self._async_prefixes
