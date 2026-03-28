from __future__ import annotations

import argparse
from pathlib import Path

from carousel_system.cli import run
from carousel_system.config import ROOT_DIR, load_settings
from carousel_system.google_sheets import GoogleSheetsQueue
from carousel_system.models import CarouselOutput, FigmaOutput, PluginRenderResult
from carousel_system.payload import write_output_record


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

    record = CarouselOutput.model_validate_json(job_path.read_text(encoding="utf-8"))
    result = PluginRenderResult.model_validate_json(result_path.read_text(encoding="utf-8"))
    if result.job_id != record.job_id:
        raise ValueError(
            f"Render result job_id {result.job_id!r} does not match artifact job_id {record.job_id!r}."
        )

    record.status = "complete"
    record.figma_output = FigmaOutput(
        file_key=result.file_key,
        file_url=result.file_url,
        page_name=result.page_name,
        slide_node_ids=result.slide_node_ids,
    )
    record.render_artifact.result_path = str(result_path)
    write_output_record(job_path, record)

    settings = load_settings(require_google=False)
    row_number = record.source_sync.row_number
    if (
        row_number
        and settings.google_service_account_json
        and settings.google_spreadsheet_id
        and settings.google_service_account_json.exists()
    ):
        queue = GoogleSheetsQueue(settings)
        queue.update_row(
            row_number,
            {
                "status": "complete",
                "figma_url": result.file_url or "",
                "export_paths": str(job_path),
                "render_result_path": str(result_path),
                "error": "",
            },
        )

    print(job_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
