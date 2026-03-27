from __future__ import annotations

import json

from carousel_system.cli import run
from carousel_system.config import load_settings
from carousel_system.google_sheets import GoogleSheetsQueue


def main() -> int:
    settings = load_settings(require_google=True)
    queue = GoogleSheetsQueue(settings)
    info = queue.get_spreadsheet_info()
    queue.ensure_queue_sheet()
    print(
        json.dumps(
            {
                "status": "ok",
                "spreadsheet_id": info.spreadsheet_id,
                "spreadsheet_title": info.title,
                "worksheet_name": settings.google_worksheet_name,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
