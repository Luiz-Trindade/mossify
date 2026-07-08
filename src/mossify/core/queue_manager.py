import asyncio
from typing import List, Type, Dict, Any
from sqlmodel import SQLModel, Session
from .database import DatabaseManager


class QueueManager:
    def __init__(
        self,
        db_manager: DatabaseManager,
        model_class: Type[SQLModel],
        batch_size: int = 5000,  # aumentado para 5000
        flush_interval: float = 10.0,  # aumentado para 10s
    ):
        self.db_manager = db_manager
        self.model_class = model_class
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._running = False
        self._total_inserted = 0  # contador opcional

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
            f"🌿 Queue worker stopped for {self.model_class.__name__} (total inserted: {self._total_inserted})"
        )

    async def enqueue(self, data: Dict[str, Any]) -> int:
        """Adiciona um item à fila e retorna um ID temporário."""
        item_id = id(data)
        # Use put_nowait para evitar overhead de await (se a fila não estiver cheia)
        try:
            self.queue.put_nowait((item_id, data))
        except asyncio.QueueFull:
            await self.queue.put((item_id, data))  # fallback
        return item_id

    async def _worker(self):
        buffer: List[Dict[str, Any]] = []
        while self._running or not self.queue.empty():
            try:
                _, data = await asyncio.wait_for(
                    self.queue.get(), timeout=self.flush_interval
                )
                buffer.append(data)
            except asyncio.TimeoutError:
                if buffer:
                    await self._flush(buffer)
                    buffer = []
                continue

            if len(buffer) >= self.batch_size:
                await self._flush(buffer)
                buffer = []

        if buffer:
            await self._flush(buffer)

    async def _flush(self, items: List[Dict[str, Any]]):
        if not items:
            return

        # Executa a operação de banco em uma thread separada
        count = len(items)
        await asyncio.to_thread(self._sync_flush, items)
        self._total_inserted += count
        # Log opcional (remova se quiser silenciar)
        print(f"🌿 Inserted {count} {self.model_class.__name__} items")

    def _sync_flush(self, items: List[Dict[str, Any]]):
        """Método síncrono executado em thread separada."""
        with Session(self.db_manager.engine) as session:
            # Usa bulk_insert_mappings para maior performance
            session.bulk_insert_mappings(self.model_class, items)
            session.commit()
