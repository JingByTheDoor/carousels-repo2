from __future__ import annotations

from carousel_system.cli import run
from carousel_system.config import ROOT_DIR, load_settings
from carousel_system.google_sheets import GoogleSheetsQueue
from carousel_system.models import SourceSync
from carousel_system.payload import build_output_record, write_output_record
from carousel_system.planner import PROMPT_VERSION, generate_carousel_plan
from carousel_system.render_payload import (
    build_plugin_render_payload,
    build_render_artifact,
    write_plugin_render_payload,
)


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
        queue.update_row(next_row.row_number, {"status": "planning", "error": ""})
        job = queue.queue_row_to_input(next_row)
        plan = generate_carousel_plan(settings, job)
        output_path = ROOT_DIR / ".tmp" / "jobs" / f"{job_id}.json"
        render_payload_path = ROOT_DIR / ".tmp" / "render-jobs" / f"{job_id}.render.json"
        record = build_output_record(
            job,
            plan,
            source_sync=SourceSync(
                google_sheet_id=settings.google_spreadsheet_id,
                worksheet_name=settings.google_worksheet_name,
                row_number=next_row.row_number,
            ),
            prompt_version=PROMPT_VERSION,
            language=job.language,
        )
        render_payload = build_plugin_render_payload(record, source_artifact_path=output_path)
        record.language = render_payload.language
        record.style_family = render_payload.style_family
        record.style_recipe = render_payload.style_recipe
        record.render_artifact = build_render_artifact(render_payload_path, render_payload)
        write_output_record(output_path, record)
        write_plugin_render_payload(render_payload_path, render_payload)
        queue.update_row(
            next_row.row_number,
            {
                "job_id": job_id,
                "status": "planned",
                "reference_nodes_used": ",".join(job.reference_node_ids),
                "figma_url": "",
                "export_paths": str(output_path),
                "error": "",
                "language": render_payload.language,
                "style_family": render_payload.style_family,
                "style_recipe": render_payload.style_recipe,
                "prompt_version": PROMPT_VERSION,
                "render_payload_path": str(render_payload_path),
                "render_result_path": "",
            },
        )
        print(render_payload_path)
        return 0
    except Exception as exc:
        queue.update_row(next_row.row_number, {"job_id": job_id, "status": "error", "error": str(exc)})
        raise


if __name__ == "__main__":
    raise SystemExit(run(main))
