# 🌿 mossify

[![PyPI - Version](https://img.shields.io/pypi/v/mossify)](https://pypi.org/project/mossify/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mossify)](https://pypi.org/project/mossify/)
[![PyPI - License](https://img.shields.io/pypi/l/mossify)](https://github.com/Luiz-Trindade/mossify/blob/main/LICENSE)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/mossify)](https://pypi.org/project/mossify/)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Luiz-Trindade/mossify/ci.yml?branch=main)](https://github.com/Luiz-Trindade/mossify/actions)

**Mossify** is a simple, organic framework that wraps **FastAPI** and **SQLModel** to give you automatic CRUD routes and intelligent caching – with almost zero boilerplate.

> _"Mossify your backend. Simple, organic, and fully covered."_

---

## 🚀 Quick Start

```bash
pip install mossify
```

```python
from mossify import Mossify
from sqlmodel import SQLModel, Field
from typing import Optional


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float


app = Mossify(database_url="sqlite:///database.db")
app.register_model(Product)

if __name__ == "__main__":
    app.run(workers=2)
```

That's it! You now have a fully functional API with:

| Method | Endpoint              | Description          |
|--------|-----------------------|----------------------|
| GET    | `/products`           | List (paginated)     |
| POST   | `/products`           | Create               |
| GET    | `/products/count`     | Count                |
| GET    | `/products/{id}`      | Get by ID            |
| PATCH  | `/products/{id}`      | Partial update       |
| PUT    | `/products/{id}`      | Full replacement     |
| DELETE | `/products/{id}`      | Delete               |

All read endpoints are automatically cached (configurable TTL). Cache is invalidated on any write operation.

---

## ✨ Features

- 🔌 **Zero boilerplate** – define your models, call `register_model()`, and go.
- ⚡ **FastAPI + SQLModel** – fully async, modern, and type-safe.
- 🧠 **Intelligent caching** – automatic TTL-based cache via `diskcache` for GET endpoints.
- 🔄 **Automatic invalidation** – cache cleared on POST, PUT, PATCH, DELETE.
- 📄 **Paginated listing** – built-in `page`/`size` query params with configurable limits.
- 🔢 **Auto count endpoint** – `GET /{models}/count` returns total records.
- 🗃️ **Async queue mode** – high-throughput POST with batch inserts and configurable flush interval.
- 🔧 **Multi‑worker ready** – scales with `uvicorn` workers out of the box.
- 📦 **Built‑in OpenAPI** – interactive docs at `/docs` and `/redoc`.
- 🛡️ **Auth module** – JWT authentication with register, login, protected routes, and per-model auth.
- 🖥️ **CLI tool** – `mossify --version`, `mossify --about`, `mossify hello`.
- 🎛️ **Granular control** – exclude specific endpoints, set custom prefixes, override cache TTL per route.

---

## 📦 Installation

```bash
pip install mossify
```

Or with `uv`:

```bash
uv pip install mossify
```

---

## 🧑‍💻 Usage

### Basic setup

```python
from mossify import Mossify
from sqlmodel import SQLModel, Field
from typing import Optional


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None


app = Mossify(
    database_url="sqlite:///items.db",
    title="My API",
    cache_ttl=300,       # 5 minutes default cache
)

app.register_model(Item, tags=["Items"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Configuration

`Mossify()` accepts:

| Parameter        | Default                  | Description                              |
|------------------|--------------------------|------------------------------------------|
| `database_url`   | `"sqlite:///mossify.db"` | Database connection URL                  |
| `database_models`| `None`                   | Optional list of models to create tables |
| `title`          | `"Mossify API"`          | FastAPI title                            |
| `description`    | `"..."`                  | FastAPI description                      |
| `version`        | `"0.1.4"`                | API version                              |
| `cache_dir`      | `".mossify_cache"`       | Directory for diskcache                  |
| `cache_ttl`      | `500`                    | Default cache TTL (seconds)              |
| `openapi_url`    | `"/openapi.json"`        | OpenAPI schema path                      |
| `docs_url`       | `"/docs"`                | Swagger UI path                          |
| `redoc_url`      | `"/redoc"`               | ReDoc path                               |
| `enable_auth`    | `False`                  | Enable built-in auth routes and User model |

You can also pass any additional `**fastapi_kwargs` that `FastAPI()` accepts.

### Model registration

`app.register_model()` accepts:

| Parameter                 | Default                   | Description                                                                                          |
|---------------------------|---------------------------|------------------------------------------------------------------------------------------------------|
| `prefix`                  | Auto (`/classname` + `s`) | URL prefix                                                                                           |
| `exclude`                 | `[]`                      | List of methods to skip (`"list"`, `"create"`, "read"`, `"update"`, `"put"`, `"delete"`, `"count"`) |
| `pagination_default_size` | `20`                      | Default items per page                                                                               |
| `pagination_max_size`     | `100`                     | Maximum items per page                                                                               |
| `async_mode`              | `False`                   | Enable async queue for POST                                                                          |
| `batch_size`              | `1000`                    | Batch size for queue flush                                                                           |
| `flush_interval`          | `5.0`                     | Max seconds before queue flush (seconds)                                                             |
| `auth_dep`                | `None`                    | Auth dependency to protect all routes of this model (from `app.auth_dep`)                            |
| `**route_kwargs`          | —                         | Extra args passed to FastAPI route (e.g. `tags`, `dependencies`)                                     |

### Async queue mode

For high-load write scenarios, enable `async_mode`:

```python
app.register_model(
    Product,
    async_mode=True,
    batch_size=5_000,      # flush every 5000 items
    flush_interval=5.0,    # or every 5 seconds
)
```

POST requests return `202 Accepted` immediately with a temporary ID. Items are inserted in batches by a background worker.

### Pagination

List endpoints support pagination out of the box:

```
GET /products?page=1&size=20
```

Response headers include `X-Total-Count` with the total number of records.

### Excluding endpoints

Skip specific operations:

```python
app.register_model(
    Product,
    exclude=["put", "delete"],   # disable PUT and DELETE
)
```

### Custom route prefix

```python
app.register_model(
    Product,
    prefix="/api/v1/products",
)
```

### Relationship example

Models with foreign keys and relationships work seamlessly:

```python
class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    products: List["Product"] = Relationship(back_populates="category")


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    category: Optional[Category] = Relationship(back_populates="products")


app = Mossify(database_url="sqlite:///ecommerce.db", database_models=[Category, Product])
app.register_model(Category, tags=["Categories"])
app.register_model(Product, tags=["Products"])
```

---

## 🖥️ CLI

```bash
mossify --version     # Show version
mossify --about       # Show creator info
mossify hello         # Say hello
mossify hello --name Mossify  # Custom greeting
```

---

## 🛡️ Auth Module

Mossify comes with a built-in auth module using **JWT** and **pbkdf2_sha256** (via `passlib`).

### Quick start with auth

Enable auth with a single flag:

```python
from mossify import Mossify
from sqlmodel import SQLModel, Field
from typing import Optional
from fastapi import Depends


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float


app = Mossify(
    database_url="sqlite:///app.db",
    database_models=[Product],
    enable_auth=True,                  # registers /auth/* routes + User model
)

app.register_model(
    Product,
    async_mode=True,
    batch_size=5_000,
    flush_interval=5.0,
    tags=["Products"],
    auth_dep=app.auth_dep,             # protects all Product CRUD routes
)

if __name__ == "__main__":
    app.run(workers=1)
```

### Auth endpoints

| Method | Endpoint         | Description                  |
|--------|------------------|------------------------------|
| POST   | `/auth/register` | Create a new user            |
| POST   | `/auth/login`    | Get JWT token                |
| GET    | `/auth/me`       | Get current user (protected) |

### Protecting specific models

Pass `auth_dep=app.auth_dep` to `register_model()` to require authentication on all CRUD routes of that model. Models registered without `auth_dep` remain public.

### Manual setup

If you need more control, import directly:

```python
from mossify import Mossify
from mossify.core.auth import register_auth_routes, User
from mossify.core.database import DatabaseManager

app = Mossify(database_url="sqlite:///app.db", database_models=[User])

db_manager = DatabaseManager("sqlite:///app.db")
get_current_user = register_auth_routes(app, db_manager)
```

---

## 🧑‍💻 Development

```bash
git clone https://github.com/Luiz-Trindade/mossify.git
cd mossify
uv venv
source .venv/bin/activate
uv sync
pytest tests/
```

---

## 📄 License

MIT © [Luiz Gabriel Magalhães Trindade](https://github.com/Luiz-Trindade)

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/Luiz-Trindade/mossify/issues) or open a pull request.

---

## 🙏 Acknowledgements

Built on top of the amazing [FastAPI](https://fastapi.tiangolo.com/) and [SQLModel](https://sqlmodel.tiangolo.com/).

---

**Made with 🌿 and ❤️**
