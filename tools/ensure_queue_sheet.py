from __future__ import annotations

import json

from carousel_system.cli import run
from carousel_system.config import load_settings
from carousel_system.google_sheets import GoogleSheetsQueue, QUEUE_HEADERS


def main() -> int:
    settings = load_settings(require_google=True)
    queue = GoogleSheetsQueue(settings)
    queue.ensure_queue_sheet()
    print(
        json.dumps(
            {
                "status": "ok",
                "worksheet_name": settings.google_worksheet_name,
                "headers": QUEUE_HEADERS,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
