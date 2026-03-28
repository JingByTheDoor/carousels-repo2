from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from carousel_system.config import ROOT_DIR, Settings
from carousel_system.google_sheets import GoogleSheetsQueue, QueueRow
from carousel_system.models import CarouselOutput, FigmaOutput, PluginRenderPayload, PluginRenderResult, SourceSync
from carousel_system.payload import build_output_record, write_output_record
from carousel_system.planner import PROMPT_VERSION, generate_carousel_plan
from carousel_system.render_payload import (
    build_plugin_render_payload,
    build_render_artifact,
    infer_language,
    write_plugin_render_payload,
)


RENDER_RESULTS_DIR = ROOT_DIR / ".tmp" / "render-results"


@dataclass(frozen=True)
class RenderQueueItem:
    row_number: int
    job_id: str
    job_path: Path
    render_payload_path: Path
    record: CarouselOutput
    payload: PluginRenderPayload


def plan_row_to_render_item(settings: Settings, queue: GoogleSheetsQueue, row: QueueRow) -> RenderQueueItem:
    job_id = row.values.get("job_id") or f"sheet-row-{row.row_number}"
    queue.update_row(row.row_number, {"status": "planning", "error": ""})
    job = queue.queue_row_to_input(row)
    plan = generate_carousel_plan(settings, job)
    job_path = ROOT_DIR / ".tmp" / "jobs" / f"{job_id}.json"
    render_payload_path = ROOT_DIR / ".tmp" / "render-jobs" / f"{job_id}.render.json"
    record = build_output_record(
        job,
        plan,
        source_sync=SourceSync(
            google_sheet_id=settings.google_spreadsheet_id,
            worksheet_name=settings.google_worksheet_name,
            row_number=row.row_number,
        ),
        prompt_version=PROMPT_VERSION,
        language=job.language,
    )
    payload = build_plugin_render_payload(record, source_artifact_path=job_path)
    record.language = payload.language or infer_language(record)
    record.style_family = payload.style_family
    record.style_recipe = payload.style_recipe
    record.design_reference_log = [
        reference for reference in record.design_reference_log if reference.node_id in set(payload.reference_node_ids)
    ]
    record.render_artifact = build_render_artifact(render_payload_path, payload)
    write_output_record(job_path, record)
    write_plugin_render_payload(render_payload_path, payload)
    queue.update_row(
        row.row_number,
        {
            "job_id": job_id,
            "status": "planned",
            "reference_nodes_used": ",".join(payload.reference_node_ids),
            "figma_url": "",
            "export_paths": str(job_path),
            "error": "",
            "language": payload.language,
            "style_family": payload.style_family,
            "style_recipe": payload.style_recipe,
            "prompt_version": PROMPT_VERSION,
            "render_payload_path": str(render_payload_path),
            "render_result_path": "",
        },
    )
    return RenderQueueItem(
        row_number=row.row_number,
        job_id=job_id,
        job_path=job_path,
        render_payload_path=render_payload_path,
        record=record,
        payload=payload,
    )


def acquire_next_render_item(settings: Settings, queue: GoogleSheetsQueue) -> RenderQueueItem | None:
    queue.ensure_queue_sheet()
    row = queue.find_first_row_by_status({"planned"})
    if row:
        item = hydrate_planned_row(settings, queue, row)
        queue.update_row(row.row_number, {"status": "rendering", "error": ""})
        return item

    row = queue.find_first_row_by_status({"", "queued"})
    if not row:
        return None

    item = plan_row_to_render_item(settings, queue, row)
    queue.update_row(row.row_number, {"status": "rendering", "error": ""})
    return item


def hydrate_planned_row(settings: Settings, queue: GoogleSheetsQueue, row: QueueRow) -> RenderQueueItem:
    job_id = row.values.get("job_id") or f"sheet-row-{row.row_number}"
    job_path = _resolve_job_path(job_id, row.values.get("export_paths"))
    render_payload_path = _resolve_render_payload_path(job_id, row.values.get("render_payload_path"))

    if not job_path.exists():
        return plan_row_to_render_item(settings, queue, row)

    record = CarouselOutput.model_validate_json(job_path.read_text(encoding="utf-8"))
    payload = build_plugin_render_payload(record, source_artifact_path=job_path)
    record.language = payload.language or infer_language(record)
    record.style_family = payload.style_family
    record.style_recipe = payload.style_recipe
    record.design_reference_log = [
        reference for reference in record.design_reference_log if reference.node_id in set(payload.reference_node_ids)
    ]
    record.render_artifact = build_render_artifact(render_payload_path, payload)
    write_output_record(job_path, record)
    write_plugin_render_payload(render_payload_path, payload)
    queue.update_row(
        row.row_number,
        {
            "language": payload.language,
            "style_family": payload.style_family,
            "style_recipe": payload.style_recipe,
            "prompt_version": record.prompt_version,
            "reference_nodes_used": ",".join(payload.reference_node_ids),
            "render_payload_path": str(render_payload_path),
        },
    )

    return RenderQueueItem(
        row_number=row.row_number,
        job_id=job_id,
        job_path=job_path,
        render_payload_path=render_payload_path,
        record=record,
        payload=payload,
    )


def save_render_result(result: PluginRenderResult) -> Path:
    result_path = RENDER_RESULTS_DIR / f"{result.job_id}.render-result.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return result_path


def apply_render_result(
    settings: Settings,
    queue: GoogleSheetsQueue | None,
    *,
    job_id: str,
    result: PluginRenderResult,
    result_path: Path,
) -> Path:
    job_path = ROOT_DIR / ".tmp" / "jobs" / f"{job_id}.json"
    record = CarouselOutput.model_validate_json(job_path.read_text(encoding="utf-8"))
    if result.job_id != record.job_id:
        raise ValueError(
            f"Render result job_id {result.job_id!r} does not match artifact job_id {record.job_id!r}."
        )

    record.status = "complete"
    record.error = None
    record.figma_output = FigmaOutput(
        file_key=result.file_key,
        file_url=result.file_url,
        page_name=result.page_name,
        slide_node_ids=result.slide_node_ids,
    )
    record.render_artifact.result_path = str(result_path)
    write_output_record(job_path, record)

    if queue is None and settings.google_service_account_json and settings.google_spreadsheet_id:
        queue = GoogleSheetsQueue(settings)

    if queue and record.source_sync.row_number:
        queue.update_row(
            record.source_sync.row_number,
            {
                "status": "complete",
                "figma_url": result.file_url or "",
                "export_paths": str(job_path),
                "render_result_path": str(result_path),
                "error": "",
            },
        )

    return job_path


def record_render_error(settings: Settings, queue: GoogleSheetsQueue | None, *, job_id: str, error_text: str) -> None:
    job_path = ROOT_DIR / ".tmp" / "jobs" / f"{job_id}.json"
    if job_path.exists():
        record = CarouselOutput.model_validate_json(job_path.read_text(encoding="utf-8"))
        record.status = "error"
        record.error = error_text
        write_output_record(job_path, record)
        row_number = record.source_sync.row_number
    else:
        row_number = None

    if queue is None and settings.google_service_account_json and settings.google_spreadsheet_id:
        queue = GoogleSheetsQueue(settings)

    if queue and row_number:
        queue.update_row(row_number, {"status": "error", "error": error_text})
        return

    if queue:
        row = queue.find_row_by_job_id(job_id)
        if row:
            queue.update_row(row.row_number, {"status": "error", "error": error_text})


def _resolve_job_path(job_id: str, raw_path: str | None) -> Path:
    if raw_path:
        path = Path(raw_path)
        if path.exists():
            return path
    return ROOT_DIR / ".tmp" / "jobs" / f"{job_id}.json"


def _resolve_render_payload_path(job_id: str, raw_path: str | None) -> Path:
    if raw_path:
        path = Path(raw_path)
        if path.exists():
            return path
    return ROOT_DIR / ".tmp" / "render-jobs" / f"{job_id}.render.json"
