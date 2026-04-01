from __future__ import annotations

import argparse
import atexit
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn

from carousel_system.cli import run
from carousel_system.config import ROOT_DIR, load_settings
from carousel_system.studio_web import create_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the review studio and optional render bridge.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--no-render-bridge", action="store_true")
    parser.add_argument("--bridge-host")
    parser.add_argument("--bridge-port", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = create_app()
    render_process: subprocess.Popen | None = None

    if not args.no_render_bridge:
        settings = load_settings(require_openai=True, require_google=True)
        bridge_host = args.bridge_host or settings.render_server_host
        bridge_port = args.bridge_port or settings.render_server_port
        render_process = subprocess.Popen(
            [
                str(Path(sys.executable)),
                str(ROOT_DIR / "tools" / "render_server.py"),
                "--host",
                bridge_host,
                "--port",
                str(bridge_port),
                "--queue-mode",
                "studio_only",
            ],
            cwd=ROOT_DIR,
        )

        def _cleanup_render_process() -> None:
            if render_process and render_process.poll() is None:
                render_process.terminate()

        atexit.register(_cleanup_render_process)

    if not args.no_browser:
        studio_url = f"http://{args.host}:{args.port}"

        def _open_browser() -> None:
            time.sleep(1.2)
            webbrowser.open(studio_url)

        threading.Thread(target=_open_browser, daemon=True).start()

    try:
        uvicorn.run(app, host=args.host, port=args.port)
    finally:
        if render_process and render_process.poll() is None:
            render_process.terminate()

    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
