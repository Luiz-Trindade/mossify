#!/usr/bin/env python3
import argparse

__author__ = "Luiz Gabriel Magalhães Trindade"
__version__ = "0.1.4"


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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
