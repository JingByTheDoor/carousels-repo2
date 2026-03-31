from __future__ import annotations

import argparse

import uvicorn

from carousel_system.cli import run
from carousel_system.studio_web import create_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local carousel review studio.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--reload", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
