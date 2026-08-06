#!/usr/bin/env python
"""Small EpiSphere management wrapper.

This project is FastAPI/Next.js, not Django. The wrapper exists so the common
`python manage.py runserver` command starts the local FastAPI API server.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
VENV_PYTHON = BACKEND / "venv" / "Scripts" / "python.exe"


def backend_python() -> str:
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable


def run_backend(args: list[str], *, env: dict[str, str] | None = None) -> int:
    command_env = os.environ.copy()
    command_env["PYTHONPATH"] = str(BACKEND)
    if env:
        command_env.update(env)
    return subprocess.call([backend_python(), *args], cwd=BACKEND, env=command_env)


def runserver(host: str, port: int, reload: bool) -> int:
    args = ["-m", "uvicorn", "app.main:app", "--host", host, "--port", str(port)]
    if reload:
        args.append("--reload")
    return run_backend(args)


def migrate() -> int:
    return run_backend(["-m", "alembic", "upgrade", "head"])


def seed() -> int:
    return run_backend(["scripts/init_db.py"])


def main() -> int:
    parser = argparse.ArgumentParser(description="EpiSphere local management commands")
    subparsers = parser.add_subparsers(dest="command")

    runserver_parser = subparsers.add_parser("runserver", help="Start the FastAPI backend")
    runserver_parser.add_argument("--host", default="127.0.0.1")
    runserver_parser.add_argument("--port", type=int, default=8000)
    runserver_parser.add_argument("--no-reload", action="store_true")

    subparsers.add_parser("migrate", help="Run backend Alembic migrations")
    subparsers.add_parser("seed", help="Seed backend reference data")

    args = parser.parse_args()
    if args.command == "runserver":
        return runserver(args.host, args.port, not args.no_reload)
    if args.command == "migrate":
        return migrate()
    if args.command == "seed":
        return seed()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
