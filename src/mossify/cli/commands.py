#!/usr/bin/env python3
import argparse
import os
import sys

__author__ = "Luiz Gabriel Magalhães Trindade"
__version__ = "0.1.4"


def startproject(args):
    project_name = args.name
    target_dir = os.path.join(os.getcwd(), project_name)

    if os.path.exists(target_dir):
        print(
            f"🌿 Error: directory '{project_name}' already exists. "
            f"Please choose a different name."
        )
        sys.exit(1)

    os.makedirs(target_dir)
    os.makedirs(os.path.join(target_dir, "app"))

    files = {
        "app/__init__.py": "",
        "app/main.py": (
            '"""Mossify application entry point."""\n\n'
            "from mossify import Mossify\n"
            "from app.models import Product\n\n\n"
            "app = Mossify(\n"
            '    database_url="sqlite:///app.db",\n'
            "    database_models=[Product],\n"
            '    title="Mossify App",\n'
            "    enable_auth=True,\n"
            ")\n\n"
            "app.register_model(\n"
            "    Product,\n"
            "    async_mode=True,\n"
            "    batch_size=5_000,\n"
            "    flush_interval=5.0,\n"
            '    tags=["Products"],\n'
            "    # auth_dep=app.auth_dep,\n"
            ")\n\n\n"
            'if __name__ == "__main__":\n'
            "    app.run()\n"
        ),
        "app/models.py": (
            "from sqlmodel import SQLModel, Field\n"
            "from typing import Optional\n\n\n"
            "class Product(SQLModel, table=True):\n"
            "    id: Optional[int] = Field(default=None, primary_key=True)\n"
            "    name: str\n"
            "    price: float\n"
            "    stock: int = 0\n"
        ),
        ".gitignore": (
            "__pycache__/\n"
            "*.py[cod]\n"
            "*.db\n"
            ".mossify_cache/\n"
            ".venv/\n"
            "venv/\n"
        ),
    }

    for relpath, content in files.items():
        filepath = os.path.join(target_dir, relpath)
        with open(filepath, "w") as f:
            f.write(content)

    print(f"🌿 Mossify project '{project_name}' created successfully!")
    print(f"\n  cd {project_name}")
    print(f"  mossify run")
    print()


def run_project(args):
    """Run a Mossify project using uvicorn."""
    import uvicorn

    host = args.host
    port = args.port
    reload = args.reload

    sys.path.insert(0, os.getcwd())

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
    )


def main():
    parser = argparse.ArgumentParser(
        description=f"Mossify CLI - Command-line tools for Mossify\n"
        f"Created by: {__author__}",
        epilog="🌿 A simple, organic framework for FastAPI + SQLModel with automatic CRUD and cache.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Mossify {__version__}",
        help="Show version and exit",
    )
    parser.add_argument(
        "--about",
        action="store_true",
        help="Show creator information and exit",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    hello_parser = subparsers.add_parser("hello", help="Say hello")
    hello_parser.add_argument("--name", default="World", help="Name to greet")

    start_parser = subparsers.add_parser(
        "startproject", help="Create a new Mossify project"
    )
    start_parser.add_argument("name", help="Project name")

    run_parser = subparsers.add_parser("run", help="Run the Mossify app in the current directory")
    run_parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    run_parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    run_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    if args.about:
        print(f"""
MOSSIFY CLI
Creator: {__author__}
Version: {__version__}

🌿 A simple, organic framework for FastAPI + SQLModel
   with automatic CRUD and intelligent caching.
""")
        return

    if args.command == "hello":
        print(f"Hello, {args.name}!")
    elif args.command == "startproject":
        startproject(args)
    elif args.command == "run":
        run_project(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
