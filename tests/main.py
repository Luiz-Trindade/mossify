from mossify import Mossify
from sqlmodel import SQLModel, Field
from typing import Optional


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    stock: int = 0


app = Mossify(
    database_url="sqlite:///products.db",
    database_models=[Product],
    enable_auth=True,
)

app.register_model(
    Product,
    async_mode=True,
    batch_size=5_000,
    flush_interval=5.0,
    tags=["Products"],
    # auth_dep=app.auth_dep,
)

if __name__ == "__main__":
    app.run()
