from __future__ import annotations

from carousel_system.cli import run
from carousel_system.config import ROOT_DIR, load_settings
from carousel_system.google_sheets import GoogleSheetsQueue
from carousel_system.models import SourceSync
from carousel_system.payload import build_output_record, write_output_record
from carousel_system.planner import generate_carousel_plan


def main() -> int:
    settings = load_settings(require_openai=True, require_google=True)
    queue = GoogleSheetsQueue(settings)
    queue.ensure_queue_sheet()
    next_row = queue.find_next_pending_row()
    if not next_row:
        print("No queued jobs found.")
        return 0

    job_id = next_row.values.get("job_id") or f"sheet-row-{next_row.row_number}"
    try:
        queue.update_row(next_row.row_number, {"status": "processing", "error": ""})
        job = queue.queue_row_to_input(next_row)
        plan = generate_carousel_plan(settings, job)
        record = build_output_record(
            job,
            plan,
            source_sync=SourceSync(
                google_sheet_id=settings.google_spreadsheet_id,
                worksheet_name=settings.google_worksheet_name,
                row_number=next_row.row_number,
            ),
        )
        output_path = ROOT_DIR / ".tmp" / "jobs" / f"{job_id}.json"
        write_output_record(output_path, record)
        queue.update_row(
            next_row.row_number,
            {
                "job_id": job_id,
                "status": "planned",
                "reference_nodes_used": ",".join(job.reference_node_ids),
                "figma_url": "",
                "export_paths": str(output_path),
                "error": "",
            },
        )
        print(output_path)
        return 0
    except Exception as exc:
        queue.update_row(next_row.row_number, {"job_id": job_id, "status": "error", "error": str(exc)})
        raise


if __name__ == "__main__":
    raise SystemExit(run(main))
