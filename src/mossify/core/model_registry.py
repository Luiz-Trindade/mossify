from typing import Optional, List, Type, Dict, Any
from fastapi import Depends, HTTPException, Body, Query, Response
from sqlmodel import SQLModel, Session, select, func
from .database import DatabaseManager
from .router import RouterBuilder
from .queue_manager import QueueManager


class ModelRegistry:
    def __init__(self, router_builder: RouterBuilder, db_manager: DatabaseManager):
        self.router_builder = router_builder
        self.db_manager = db_manager
        self._registered_models = set()
        self._queue_managers: Dict[Type[SQLModel], QueueManager] = {}

    def register_model(
        self,
        model_class: Type[SQLModel],
        prefix: Optional[str] = None,
        exclude: Optional[List[str]] = None,
        pagination_default_size: int = 20,
        pagination_max_size: int = 100,
        async_mode: bool = False,
        batch_size: int = 1000,
        flush_interval: float = 5.0,
        auth_dep: Optional[Any] = None,
        **route_kwargs,
    ):
        if prefix is None:
            prefix = f"/{model_class.__name__.lower()}s"

        exclude = exclude or []
        exclude_set = set(exclude)

        self.db_manager.create_engine_if_needed()
        if model_class not in self._registered_models:
            self.db_manager.create_tables([model_class])
            self._registered_models.add(model_class)

        # --- Schemas dinâmicos ---
        ignored_fields = {"id", "created_at", "updated_at"}
        fields_info = {}
        for name, field in model_class.model_fields.items():
            if name not in ignored_fields:
                fields_info[name] = (field.annotation, field)

        create_annotations = {k: v[0] for k, v in fields_info.items()}
        create_defaults = {
            k: v[1].default for k, v in fields_info.items() if v[1].default is not None
        }
        CreateModel = type(
            f"{model_class.__name__}Create",
            (SQLModel,),
            {
                "__annotations__": create_annotations,
                **create_defaults,
            },
        )

        from typing import Optional as OptType

        update_annotations = {k: OptType[v[0]] for k, v in fields_info.items()}
        update_defaults = {k: None for k in fields_info}
        UpdateModel = type(
            f"{model_class.__name__}Update",
            (SQLModel,),
            {
                "__annotations__": update_annotations,
                **update_defaults,
            },
        )

        def get_session():
            yield from self.db_manager.get_session()

        # Monta a lista de dependências (combina auth_dep com outras fornecidas)
        dependencies = []
        if auth_dep:
            dependencies.append(Depends(auth_dep))  # <-- envolve com Depends
        if "dependencies" in route_kwargs:
            deps = route_kwargs.pop("dependencies")
            if isinstance(deps, list):
                dependencies.extend(deps)
            else:
                dependencies.append(deps)
        if dependencies:
            route_kwargs["dependencies"] = dependencies

        # --- Rotas (todas async) ---
        # A ordem é importante: count deve vir antes de {item_id}

        # 1. Listar
        if "list" not in exclude_set:

            @self.router_builder.register_route(
                prefix,
                methods=["GET"],
                response_model=List[model_class],
                cache_prefix=prefix,
                **route_kwargs,
            )
            async def list_items(
                response: Response,
                session: Session = Depends(get_session),
                page: int = Query(1, ge=1, description="Página (começa em 1)"),
                size: int = Query(
                    pagination_default_size,
                    ge=1,
                    le=pagination_max_size,
                    description=f"Quantidade por página (máx {pagination_max_size})",
                ),
            ):
                total_count = session.exec(
                    select(func.count()).select_from(model_class)
                ).one()
                response.headers["X-Total-Count"] = str(total_count)
                offset = (page - 1) * size
                statement = select(model_class).offset(offset).limit(size)
                return session.exec(statement).all()

            list_items.__name__ = f"list_{model_class.__name__.lower()}"

        # 2. Contar (deve vir antes de /{item_id})
        if "count" not in exclude_set:

            @self.router_builder.register_route(
                f"{prefix}/count",
                methods=["GET"],
                cache_prefix=prefix,
                **route_kwargs,
            )
            async def count_items(session: Session = Depends(get_session)):
                count = session.exec(
                    select(func.count()).select_from(model_class)
                ).one()
                return {"count": count}

            count_items.__name__ = f"count_{model_class.__name__.lower()}"

        # 3. Criar (com ou sem fila)
        if "create" not in exclude_set:
            if async_mode:
                if model_class not in self._queue_managers:
                    qm = QueueManager(
                        self.db_manager,
                        model_class,
                        batch_size=batch_size,
                        flush_interval=flush_interval,
                    )
                    self._queue_managers[model_class] = qm

                @self.router_builder.register_route(
                    prefix,
                    methods=["POST"],
                    status_code=202,
                    cache_prefix=prefix,
                    **route_kwargs,
                )
                async def create_item_async(
                    data: CreateModel = Body(...),
                ):
                    qm = self._queue_managers[model_class]
                    temp_id = await qm.enqueue(data.model_dump())
                    return {"status": "accepted", "id": temp_id}

                create_item_async.__name__ = (
                    f"create_{model_class.__name__.lower()}_async"
                )
            else:

                @self.router_builder.register_route(
                    prefix,
                    methods=["POST"],
                    response_model=model_class,
                    status_code=201,
                    cache_prefix=prefix,
                    **route_kwargs,
                )
                async def create_item(
                    data: CreateModel = Body(...),
                    session: Session = Depends(get_session),
                ):
                    item = model_class(**data.model_dump())
                    session.add(item)
                    session.commit()
                    session.refresh(item)
                    return item

                create_item.__name__ = f"create_{model_class.__name__.lower()}"

        # 4. Obter (/{item_id})
        if "read" not in exclude_set:

            @self.router_builder.register_route(
                f"{prefix}/{{item_id}}",
                methods=["GET"],
                response_model=model_class,
                cache_prefix=prefix,
                **route_kwargs,
            )
            async def get_item(item_id: int, session: Session = Depends(get_session)):
                item = session.get(model_class, item_id)
                if not item:
                    raise HTTPException(status_code=404, detail="Item not found")
                return item

            get_item.__name__ = f"get_{model_class.__name__.lower()}"

        # 5. Atualização parcial (PATCH)
        if "update" not in exclude_set:

            @self.router_builder.register_route(
                f"{prefix}/{{item_id}}",
                methods=["PATCH"],
                response_model=model_class,
                cache_prefix=prefix,
                **route_kwargs,
            )
            async def update_item(
                item_id: int,
                data: UpdateModel = Body(...),
                session: Session = Depends(get_session),
            ):
                item = session.get(model_class, item_id)
                if not item:
                    raise HTTPException(status_code=404, detail="Item not found")
                for key, value in data.model_dump(exclude_unset=True).items():
                    setattr(item, key, value)
                session.add(item)
                session.commit()
                session.refresh(item)
                return item

            update_item.__name__ = f"update_{model_class.__name__.lower()}"

        # 6. Substituição completa (PUT)
        if "put" not in exclude_set:

            @self.router_builder.register_route(
                f"{prefix}/{{item_id}}",
                methods=["PUT"],
                response_model=model_class,
                cache_prefix=prefix,
                **route_kwargs,
            )
            async def put_item(
                item_id: int,
                data: CreateModel = Body(...),
                session: Session = Depends(get_session),
            ):
                item = session.get(model_class, item_id)
                if not item:
                    raise HTTPException(status_code=404, detail="Item not found")
                for key, value in data.model_dump().items():
                    setattr(item, key, value)
                session.add(item)
                session.commit()
                session.refresh(item)
                return item

            put_item.__name__ = f"put_{model_class.__name__.lower()}"

        # 7. Deletar
        if "delete" not in exclude_set:

            @self.router_builder.register_route(
                f"{prefix}/{{item_id}}",
                methods=["DELETE"],
                cache_prefix=prefix,
                **route_kwargs,
            )
            async def delete_item(
                item_id: int, session: Session = Depends(get_session)
            ):
                item = session.get(model_class, item_id)
                if not item:
                    raise HTTPException(status_code=404, detail="Item not found")
                session.delete(item)
                session.commit()
                return {"detail": "Item deleted"}

            delete_item.__name__ = f"delete_{model_class.__name__.lower()}"

        print(
            f"🌿 Mossify: CRUD routes registered for {model_class.__name__} at {prefix}"
        )

    async def start_queue_workers(self):
        for qm in self._queue_managers.values():
            await qm.start()

    async def stop_queue_workers(self):
        for qm in self._queue_managers.values():
            await qm.stop()
