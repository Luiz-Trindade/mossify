import asyncio
import json
from typing import List, Type, Dict, Any, Literal, Optional
from sqlmodel import SQLModel, Session
from .cache import CacheManager
from .database import DatabaseManager


class QueueManager:
    def __init__(
        self,
        db_manager: DatabaseManager,
        model_class: Type[SQLModel],
        batch_size: int = 2000,
        flush_interval: float = 5.0,
        max_queue_size: int = 10000,
        cache_manager: Optional[CacheManager] = None,
        cache_prefix: Optional[str] = None,
    ):
        self.db_manager = db_manager
        self.model_class = model_class
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        self._total_processed = 0
        self._cache_manager = cache_manager
        self._cache_prefix = cache_prefix

    async def start(self):
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        print(f"🌿 Queue worker started for {self.model_class.__name__}")

    async def stop(self):
        self._running = False
        if self._worker_task:
            await self._worker_task
        print(
            f"🌿 Queue worker stopped for {self.model_class.__name__} "
            f"(total processed: {self._total_processed})"
        )

    async def enqueue(
        self, action: Literal["create", "update", "delete"], data: Dict[str, Any]
    ) -> int:
        """
        Adiciona um item à fila com uma ação específica.
        Retorna um ID temporário para rastreamento.
        """
        # Serializa para JSON para reduzir uso de memória
        serialized = json.dumps(data, default=str)
        item_id = id(data)  # ID temporário
        await self.queue.put((action, item_id, serialized))
        return item_id

    async def _worker(self):
        create_buffer: List[Dict[str, Any]] = []
        update_buffer: List[Dict[str, Any]] = []
        delete_buffer: List[int] = []

        while self._running or not self.queue.empty():
            try:
                action, _, serialized = await asyncio.wait_for(
                    self.queue.get(), timeout=self.flush_interval
                )
                data = json.loads(serialized)
                if action == "create":
                    create_buffer.append(data)
                elif action == "update":
                    update_buffer.append(data)
                elif action == "delete":
                    delete_buffer.append(data["id"])
            except asyncio.TimeoutError:
                await self._flush_buffers(create_buffer, update_buffer, delete_buffer)
                create_buffer.clear()
                update_buffer.clear()
                delete_buffer.clear()
                continue

            # Se algum buffer atingir o tamanho máximo, flush todos
            if (
                len(create_buffer) >= self.batch_size
                or len(update_buffer) >= self.batch_size
                or len(delete_buffer) >= self.batch_size
            ):
                await self._flush_buffers(create_buffer, update_buffer, delete_buffer)
                create_buffer.clear()
                update_buffer.clear()
                delete_buffer.clear()

        # Flush final
        await self._flush_buffers(create_buffer, update_buffer, delete_buffer)

    async def _flush_buffers(
        self,
        creates: List[Dict[str, Any]],
        updates: List[Dict[str, Any]],
        deletes: List[int],
    ):
        if creates:
            await self._flush_creates(creates)
        if updates:
            await self._flush_updates(updates)
        if deletes:
            await self._flush_deletes(deletes)

        # Invalida o cache após o flush real dos dados no banco
        if self._cache_manager and self._cache_prefix:
            self._cache_manager.invalidate_prefix(self._cache_prefix)

    async def _flush_creates(self, items: List[Dict[str, Any]]):
        if not items:
            return
        await asyncio.to_thread(self._sync_create, items)
        self._total_processed += len(items)

    def _sync_create(self, items: List[Dict[str, Any]]):
        with Session(self.db_manager.engine) as session:
            objects = [self.model_class(**data) for data in items]
            session.add_all(objects)
            session.commit()

    async def _flush_updates(self, items: List[Dict[str, Any]]):
        if not items:
            return
        await asyncio.to_thread(self._sync_update, items)
        self._total_processed += len(items)

    def _sync_update(self, items: List[Dict[str, Any]]):
        with Session(self.db_manager.engine) as session:
            for data in items:
                item_id = data.pop("id")
                obj = session.get(self.model_class, item_id)
                if obj:
                    for key, value in data.items():
                        setattr(obj, key, value)
                    session.add(obj)
            session.commit()

    async def _flush_deletes(self, ids: List[int]):
        if not ids:
            return
        await asyncio.to_thread(self._sync_delete, ids)
        self._total_processed += len(ids)

    def _sync_delete(self, ids: List[int]):
        with Session(self.db_manager.engine) as session:
            for id in ids:
                obj = session.get(self.model_class, id)
                if obj:
                    session.delete(obj)
            session.commit()
