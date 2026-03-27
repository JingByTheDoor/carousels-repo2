from __future__ import annotations

import json

from carousel_system.cli import run
from carousel_system.config import load_settings
from carousel_system.figma_api import get_file_metadata


def main() -> int:
    settings = load_settings(require_figma=True)
    metadata = get_file_metadata(settings.figma_access_token or "", settings.figma_reference_file_key)
    file_info = metadata.get("file", {})
    print(
        json.dumps(
            {
                "status": "ok",
                "file_key": settings.figma_reference_file_key,
                "name": file_info.get("name"),
                "editor_type": file_info.get("editorType"),
                "last_touched_at": file_info.get("last_touched_at"),
                "url": file_info.get("url"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
