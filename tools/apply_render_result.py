from __future__ import annotations

import argparse
from pathlib import Path

from carousel_system.cli import run
from carousel_system.config import ROOT_DIR, load_settings
from carousel_system.google_sheets import GoogleSheetsQueue
from carousel_system.models import PluginRenderResult
from carousel_system.render_bridge import apply_render_result as apply_render_result_to_job


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply a Figma plugin render-result JSON to a job artifact.")
    parser.add_argument("--job-path")
    parser.add_argument("--job-id")
    parser.add_argument("--result-file", required=True)
    return parser.parse_args()


def resolve_job_path(args: argparse.Namespace) -> Path:
    if args.job_path:
        return Path(args.job_path)
    if args.job_id:
        return ROOT_DIR / ".tmp" / "jobs" / f"{args.job_id}.json"
    raise ValueError("Either --job-path or --job-id is required.")


def main() -> int:
    args = parse_args()
    job_path = resolve_job_path(args)
    result_path = Path(args.result_file)

    result = PluginRenderResult.model_validate_json(result_path.read_text(encoding="utf-8"))
    settings = load_settings(require_google=False)
    queue = None
    if (
        settings.google_service_account_json
        and settings.google_spreadsheet_id
        and settings.google_service_account_json.exists()
    ):
        queue = GoogleSheetsQueue(settings)

    apply_render_result_to_job(
        settings,
        queue,
        job_id=result.job_id,
        result=result,
        result_path=result_path,
    )

    print(job_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
