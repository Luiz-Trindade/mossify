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

- **GET /products** → list all products
- **POST /products** → create a product
- **GET /products/{id}** → get a product
- **PATCH /products/{id}** → update a product
- **DELETE /products/{id}** → delete a product

All routes are automatically cached and invalidated on write operations.

---

## ✨ Features

- 🔌 **Zero boilerplate** – just define your models and go.
- ⚡ **FastAPI + SQLModel** – fully async, modern, and type-safe.
- 🧠 **Intelligent caching** – automatic TTL-based cache for GET endpoints.
- 🔄 **Automatic invalidation** – cache is cleared on POST, PUT, PATCH, DELETE.
- 🔧 **Multi‑worker ready** – scale with `uvicorn` workers out of the box.
- 📦 **Built‑in OpenAPI** – interactive docs at `/docs` and `/redoc`.
- 🪶 **Lightweight** – only essential dependencies, no bloat.

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

## 🧑‍💻 Development

If you want to contribute or test the latest version:

```bash
git clone https://github.com/Luiz-Trindade/mossify.git
cd mossify
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
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
# mossify
