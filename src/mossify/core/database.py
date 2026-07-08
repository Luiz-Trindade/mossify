from sqlmodel import create_engine, SQLModel, Session
from typing import Optional, Type


class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None

    def create_engine_if_needed(self, echo: bool = False):
        if self.engine is None:
            self.engine = create_engine(self.database_url, echo=echo)

    def create_tables(self, models: list[Type[SQLModel]]):
        self.create_engine_if_needed()
        SQLModel.metadata.create_all(self.engine)
        print(f"🌿 Mossify: tables created for {[m.__name__ for m in models]}")

    def get_session(self):
        self.create_engine_if_needed()
        with Session(self.engine) as session:
            yield session
