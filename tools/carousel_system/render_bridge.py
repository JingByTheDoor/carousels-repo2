from __future__ import annotations

from dataclasses import dataclass
from base64 import b64decode
from pathlib import Path

from PIL import Image

from carousel_system.config import ROOT_DIR, Settings
from carousel_system.google_sheets import GoogleSheetsQueue, QueueRow
from carousel_system.image_assets import resolve_image_assets
from carousel_system.models import (
    CarouselOutput,
    ExportArtifact,
    FigmaOutput,
    PluginRenderPayload,
    PluginRenderResult,
    SourceSync,
)
from carousel_system.payload import build_output_record, write_output_record
from carousel_system.planner import PROMPT_VERSION, generate_carousel_plan
from carousel_system.render_payload import (
    build_plugin_render_payload,
    build_render_artifact,
    infer_language,
    write_plugin_render_payload,
)
from carousel_system.studio import (
    STUDIO_PREVIEWS_DIR,
    acquire_next_studio_render_variant,
    mark_variant_rendering,
    sync_variant_render_error,
    sync_variant_render_result,
)


RENDER_RESULTS_DIR = ROOT_DIR / ".tmp" / "render-results"
EXPORTS_DIR = ROOT_DIR / ".tmp" / "exports"


@dataclass(frozen=True)
class RenderQueueItem:
    row_number: int | None
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
    resolve_image_assets(settings, record, payload)
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
            "image_asset_paths": ",".join(asset.local_path or "" for asset in record.image_assets if asset.local_path),
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
    priority = (settings.render_queue_priority or "sheets_first").strip().lower()
    if priority == "studio_only":
        return _acquire_studio_render_item()
    if priority == "sheets_only":
        return _acquire_sheet_render_item(settings, queue)
    if priority == "studio_first":
        item = _acquire_studio_render_item()
        if item:
            return item
        return _acquire_sheet_render_item(settings, queue)

    item = _acquire_sheet_render_item(settings, queue)
    if item:
        return item
    return _acquire_studio_render_item()


def _acquire_sheet_render_item(settings: Settings, queue: GoogleSheetsQueue) -> RenderQueueItem | None:
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


def _acquire_studio_render_item() -> RenderQueueItem | None:
    studio_variant = acquire_next_studio_render_variant()
    if studio_variant is None:
        return None

    job_path = Path(studio_variant.job_artifact_path)
    render_payload_path = Path(studio_variant.render_payload_path)
    record = CarouselOutput.model_validate_json(job_path.read_text(encoding="utf-8"))
    payload = PluginRenderPayload.model_validate_json(render_payload_path.read_text(encoding="utf-8"))
    mark_variant_rendering(studio_variant.job_id)
    record.status = "rendering"
    write_output_record(job_path, record)
    return RenderQueueItem(
        row_number=None,
        job_id=studio_variant.job_id,
        job_path=job_path,
        render_payload_path=render_payload_path,
        record=record,
        payload=payload,
    )


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
    resolve_image_assets(settings, record, payload)
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
            "image_asset_paths": ",".join(asset.local_path or "" for asset in record.image_assets if asset.local_path),
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
    _save_preview_images(result)
    _save_export_images(result)
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
        page_id=result.page_id,
        page_url=result.page_url,
        slide_node_ids=result.slide_node_ids,
    )
    record.render_artifact.result_path = str(result_path)
    export_artifacts = _build_export_artifacts(result)
    record.exports = export_artifacts
    write_output_record(job_path, record)

    if queue is None and settings.google_service_account_json and settings.google_spreadsheet_id:
        queue = GoogleSheetsQueue(settings)

    if queue and record.source_sync.row_number:
        queue.update_row(
            record.source_sync.row_number,
            {
                "status": "complete",
                "figma_url": result.file_url or "",
                "export_paths": ",".join(export.path_or_url for export in export_artifacts),
                "render_result_path": str(result_path),
                "error": "",
            },
        )

    preview_paths = [Path(preview.path) for preview in result.preview_images if preview.path]
    sync_variant_render_result(
        job_id,
        result,
        render_result_path=result_path,
        preview_image_paths=preview_paths,
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
    sync_variant_render_error(job_id, error_text)


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


def _save_preview_images(result: PluginRenderResult) -> None:
    preview_dir = STUDIO_PREVIEWS_DIR / result.job_id
    for preview in result.preview_images:
        if not preview.data_base64:
            continue
        preview_dir.mkdir(parents=True, exist_ok=True)
        preview_path = preview_dir / f"slide-{str(preview.slide_number).zfill(2)}.png"
        preview_path.write_bytes(b64decode(preview.data_base64))
        preview.path = str(preview_path)
        preview.url = _preview_url_from_path(preview_path)
        preview.data_base64 = None


def _save_export_images(result: PluginRenderResult) -> None:
    export_dir = EXPORTS_DIR / result.job_id
    for export_image in result.export_images:
        if not export_image.data_base64:
            continue
        export_dir.mkdir(parents=True, exist_ok=True)
        file_name = export_image.file_name or f"slide-{str(export_image.slide_number).zfill(2)}.png"
        export_path = export_dir / file_name
        export_path.write_bytes(b64decode(export_image.data_base64))
        export_image.path = str(export_path)
        export_image.url = str(export_path)
        export_image.data_base64 = None


def _build_export_artifacts(result: PluginRenderResult) -> list[ExportArtifact]:
    artifacts: list[ExportArtifact] = []
    png_paths: list[Path] = []
    for export_image in sorted(result.export_images, key=lambda item: item.slide_number):
        if not export_image.path:
            continue
        image_path = Path(export_image.path)
        png_paths.append(image_path)
        artifacts.append(
            ExportArtifact(
                format="png",
                path_or_url=str(image_path),
                slide_number=export_image.slide_number,
            )
        )

    pdf_path = _build_pdf_export(result.job_id, png_paths)
    if pdf_path:
        artifacts.append(ExportArtifact(format="pdf", path_or_url=str(pdf_path)))
    return artifacts


def _build_pdf_export(job_id: str, png_paths: list[Path]) -> Path | None:
    if not png_paths:
        return None

    rgb_images: list[Image.Image] = []
    try:
        for path in png_paths:
            image = Image.open(path)
            rgb_images.append(image.convert("RGB"))
        pdf_path = EXPORTS_DIR / job_id / "carousel.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        lead, *rest = rgb_images
        lead.save(pdf_path, "PDF", resolution=300.0, save_all=True, append_images=rest)
        return pdf_path
    finally:
        for image in rgb_images:
            image.close()


def _preview_url_from_path(path: Path) -> str:
    relative = path.resolve().relative_to(STUDIO_PREVIEWS_DIR.parent.resolve())
    return f"/studio-output/{relative.as_posix()}"
