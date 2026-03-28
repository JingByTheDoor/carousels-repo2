from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from carousel_system.cli import run
from carousel_system.config import load_settings
from carousel_system.google_sheets import GoogleSheetsQueue
from carousel_system.models import PluginRenderResult
from carousel_system.render_bridge import (
    acquire_next_render_item,
    apply_render_result,
    record_render_error,
    save_render_result,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve render jobs to the local Figma plugin.")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = load_settings(require_openai=True, require_google=True)
    host = args.host or settings.render_server_host
    port = args.port or settings.render_server_port
    queue = GoogleSheetsQueue(settings)
    queue.ensure_queue_sheet()

    class RenderBridgeHandler(BaseHTTPRequestHandler):
        server_version = "CarouselRenderBridge/0.1"

        def do_OPTIONS(self) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self._write_cors_headers()
            self.end_headers()

        def do_GET(self) -> None:
            try:
                path = urlparse(self.path).path
                if path == "/health":
                    self._write_json(HTTPStatus.OK, {"status": "ok", "host": host, "port": port})
                    return

                if path == "/next-job":
                    item = acquire_next_render_item(settings, queue)
                    if item is None:
                        self._write_no_content()
                        return
                    self._write_json(
                        HTTPStatus.OK,
                        {
                            "job_id": item.job_id,
                            "row_number": item.row_number,
                            "payload": item.payload.model_dump(),
                        },
                    )
                    return

                self._write_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            except Exception as exc:  # noqa: BLE001
                self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            try:
                if path == "/render-result":
                    payload = self._read_json_body()
                    result = PluginRenderResult.model_validate(payload)
                    result_path = save_render_result(result)
                    job_path = apply_render_result(
                        settings,
                        queue,
                        job_id=result.job_id,
                        result=result,
                        result_path=result_path,
                    )
                    self._write_json(
                        HTTPStatus.OK,
                        {
                            "status": "ok",
                            "job_id": result.job_id,
                            "job_path": str(job_path),
                            "result_path": str(result_path),
                        },
                    )
                    return

                if path == "/render-error":
                    payload = self._read_json_body()
                    job_id = str(payload.get("job_id", "")).strip()
                    error_text = str(payload.get("error", "")).strip() or "Unknown render error."
                    if not job_id:
                        self._write_json(HTTPStatus.BAD_REQUEST, {"error": "job_id is required"})
                        return
                    record_render_error(settings, queue, job_id=job_id, error_text=error_text)
                    self._write_json(HTTPStatus.OK, {"status": "ok", "job_id": job_id})
                    return
            except json.JSONDecodeError as exc:
                self._write_json(HTTPStatus.BAD_REQUEST, {"error": f"Invalid JSON body: {exc}"})
                return
            except Exception as exc:  # noqa: BLE001
                self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return

            self._write_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def _read_json_body(self) -> dict:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw or "{}")

        def _write_json(self, status: HTTPStatus, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self._write_cors_headers()
            self.end_headers()
            self.wfile.write(body)

        def _write_no_content(self) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self._write_cors_headers()
            self.end_headers()

        def _write_cors_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Private-Network", "true")

    httpd = ThreadingHTTPServer((host, port), RenderBridgeHandler)
    print(json.dumps({"status": "listening", "host": host, "port": port}, indent=2))
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
