from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from carousel_system.config import ROOT_DIR, Settings
from carousel_system.image_assets import resolve_image_assets
from carousel_system.models import (
    DEFAULT_REFERENCE_NODE_IDS,
    CarouselInput,
    CarouselOutput,
    ImageMode,
    PerfectLibraryEntry,
    PluginRenderResult,
    ProductionJobRecord,
    ProductionJobWarning,
)
from carousel_system.payload import build_output_record, write_output_record
from carousel_system.perfect_library import (
    get_perfect_library_entry,
    load_perfect_library_status,
)
from carousel_system.planner import PROMPT_VERSION, generate_carousel_plan
from carousel_system.render_payload import (
    build_plugin_render_payload,
    build_render_artifact,
    infer_language,
    write_plugin_render_payload,
)


PRODUCTION_DIR = ROOT_DIR / ".tmp" / "production"
PRODUCTION_JOBS_DIR = PRODUCTION_DIR / "jobs"
PRODUCTION_STATE_PATH = PRODUCTION_DIR / "state.json"


class ProductionState(BaseModel):
    latest_job_id: str | None = None


class ProductionJobCreateRequest(BaseModel):
    library_item_id: str
    topic: str | None = None
    script: str | None = None
    cta_text: str | None = None
    language: str | None = None
    notes: str | None = None
    image_mode: ImageMode = "auto"

    @field_validator("library_item_id", "topic", "cta_text", "language", mode="before")
    @classmethod
    def _clean_single_line_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(str(value).strip().split())
        return cleaned or None

    @field_validator("script", "notes", mode="before")
    @classmethod
    def _clean_multiline_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
        return cleaned or None

    @field_validator("language")
    @classmethod
    def _normalize_language(cls, value: str | None) -> str | None:
        return value.lower() if value else None

    @model_validator(mode="after")
    def _validate_topic_or_script(self) -> "ProductionJobCreateRequest":
        if not self.topic and not self.script:
            raise ValueError("At least one of topic or script is required.")
        return self


def production_library_payload() -> dict:
    status = load_perfect_library_status()
    entries = [entry.model_dump(mode="json") for entry in status.entries if entry.status == "active"]
    return {
        "entries": entries,
        "manifest_version": status.manifest_version,
        "updated_at": status.updated_at,
    }


def load_production_state() -> ProductionState:
    if not PRODUCTION_STATE_PATH.exists():
        return ProductionState()
    return ProductionState.model_validate_json(PRODUCTION_STATE_PATH.read_text(encoding="utf-8"))


def save_production_state(state: ProductionState) -> Path:
    PRODUCTION_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRODUCTION_STATE_PATH.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    return PRODUCTION_STATE_PATH


def load_production_job(job_id: str | None) -> ProductionJobRecord | None:
    if not job_id:
        return None
    path = PRODUCTION_JOBS_DIR / f"{job_id}.json"
    if not path.exists():
        return None
    job_record = ProductionJobRecord.model_validate_json(path.read_text(encoding="utf-8"))
    _ensure_used_script(job_record)
    return job_record


def load_latest_production_job() -> ProductionJobRecord | None:
    state = load_production_state()
    return load_production_job(state.latest_job_id)


def save_production_job(job_record: ProductionJobRecord, *, mark_latest: bool = True) -> Path:
    PRODUCTION_JOBS_DIR.mkdir(parents=True, exist_ok=True)
    path = PRODUCTION_JOBS_DIR / f"{job_record.job_id}.json"
    path.write_text(job_record.model_dump_json(indent=2), encoding="utf-8")
    state = load_production_state()
    if mark_latest:
        state.latest_job_id = job_record.job_id
    save_production_state(state)
    return path


def create_production_job(settings: Settings, request: ProductionJobCreateRequest) -> ProductionJobRecord:
    library_entry = get_perfect_library_entry(request.library_item_id)
    if library_entry is None or library_entry.status != "active":
        raise FileNotFoundError(f"Unknown or inactive perfect-library item: {request.library_item_id}")

    job_id = f"production-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:6]}"
    job_path = ROOT_DIR / ".tmp" / "jobs" / f"{job_id}.json"
    render_payload_path = ROOT_DIR / ".tmp" / "render-jobs" / f"{job_id}.render.json"
    input_job = _build_input_job(job_id, request, library_entry, settings)

    plan = generate_carousel_plan(settings, input_job)
    record = build_output_record(input_job, plan, prompt_version=PROMPT_VERSION, language=input_job.language)
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

    warnings = _build_visual_warnings(library_entry, record, payload)
    job_record = ProductionJobRecord(
        job_id=job_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        status="planned",
        request=input_job,
        library_item_id=library_entry.library_item_id,
        library_label=library_entry.label,
        style_family=payload.style_family,
        style_recipe=payload.style_recipe,
        job_artifact_path=str(job_path),
        render_payload_path=str(render_payload_path),
        used_script=_format_used_script(record),
        image_assets=list(record.image_assets),
        visual_status="visual_warning" if warnings else "visual_resolved",
        warnings=warnings,
    )
    save_production_job(job_record)
    return job_record


def acquire_next_production_render_job() -> ProductionJobRecord | None:
    for job_path in _ordered_production_job_paths(load_production_state().latest_job_id):
        job_record = ProductionJobRecord.model_validate_json(job_path.read_text(encoding="utf-8"))
        artifact_path = Path(job_record.job_artifact_path)
        updated = False
        if artifact_path.exists():
            output_record = CarouselOutput.model_validate_json(artifact_path.read_text(encoding="utf-8"))
            if output_record.status == "complete" and job_record.status != "complete":
                _apply_output_snapshot(job_record, output_record)
                updated = True
            elif output_record.status == "error" and job_record.status != "error":
                job_record.status = "error"
                job_record.error = output_record.error
                updated = True
        if updated:
            save_production_job(job_record, mark_latest=False)
        if job_record.status != "planned":
            continue
        job_record.status = "rendering"
        job_record.error = None
        save_production_job(job_record, mark_latest=False)
        return job_record
    return None


def sync_production_render_result(job_id: str, result: PluginRenderResult, *, render_result_path: Path) -> None:
    job_record = load_production_job(job_id)
    if job_record is None:
        return
    artifact_path = Path(job_record.job_artifact_path)
    output_record = None
    if artifact_path.exists():
        output_record = CarouselOutput.model_validate_json(artifact_path.read_text(encoding="utf-8"))
    if output_record is not None:
        _apply_output_snapshot(job_record, output_record)
    job_record.status = "complete"
    job_record.render_result_path = str(render_result_path)
    job_record.figma_file_url = result.file_url
    job_record.figma_page_url = result.page_url or result.file_url
    job_record.figma_page_name = result.page_name
    job_record.fit_metrics = list(result.fit_metrics)
    _merge_render_warnings(job_record, result)
    save_production_job(job_record, mark_latest=False)


def sync_production_render_error(job_id: str, error_text: str) -> None:
    job_record = load_production_job(job_id)
    if job_record is None:
        return
    job_record.status = "error"
    job_record.error = error_text
    save_production_job(job_record, mark_latest=False)


def _build_input_job(
    job_id: str,
    request: ProductionJobCreateRequest,
    library_entry: PerfectLibraryEntry,
    settings: Settings,
) -> CarouselInput:
    reference_style = library_entry.style_preference or library_entry.style_recipe
    return CarouselInput(
        job_id=job_id,
        source="manual",
        generation_mode="production",
        library_item_id=library_entry.library_item_id,
        topic=request.topic,
        script=request.script,
        cta_text=request.cta_text,
        language=request.language,
        output_modes=["figma", "png"],
        reference_style=reference_style,
        image_mode=request.image_mode,
        reference_file_key=library_entry.reference_file_key or settings.figma_reference_file_key,
        reference_node_ids=list(library_entry.reference_node_ids) or DEFAULT_REFERENCE_NODE_IDS.copy(),
        notes=request.notes,
    )


def _build_visual_warnings(
    library_entry: PerfectLibraryEntry,
    record: CarouselOutput,
    payload,
) -> list[ProductionJobWarning]:
    warnings: list[ProductionJobWarning] = []
    visual_recipe = library_entry.visual_recipe
    if visual_recipe is None or not visual_recipe.targets:
        warnings.append(
            ProductionJobWarning(
                code="visual_recipe_missing",
                severity="warning",
                message="This perfect-library item has no explicit visual recipe yet. Family defaults were used instead.",
            )
        )

    required_slides = {
        target.slide_number
        for target in (visual_recipe.targets if visual_recipe else [])
        if target.required
    }
    if not required_slides:
        required_slides = {slide.slide_number for slide in payload.slides if slide.image_required}
    resolved_slides = {asset.slide_number for asset in record.image_assets}
    missing_slides = sorted(required_slides - resolved_slides)
    if missing_slides:
        detail = record.image_strategy.reason or "The image resolver did not attach all required visuals."
        warnings.append(
            ProductionJobWarning(
                code="visual_asset_missing",
                severity="warning",
                message=f"Missing resolved visuals for slides {', '.join(str(number) for number in missing_slides)}. {detail}",
            )
        )
    return warnings


def _merge_render_warnings(job_record: ProductionJobRecord, result: PluginRenderResult) -> None:
    existing = {(warning.code, warning.slide_number, warning.message) for warning in job_record.warnings}
    for warning in result.render_warnings:
        key = (warning.code, warning.slide_number, warning.message)
        if key in existing:
            continue
        job_record.warnings.append(
            ProductionJobWarning(
                code=warning.code,
                severity=warning.severity,
                message=warning.message,
                slide_number=warning.slide_number,
            )
        )
        existing.add(key)


def _apply_output_snapshot(job_record: ProductionJobRecord, output_record: CarouselOutput) -> None:
    job_record.status = output_record.status
    job_record.error = output_record.error
    job_record.style_family = output_record.style_family
    job_record.style_recipe = output_record.style_recipe
    job_record.used_script = _format_used_script(output_record)
    job_record.image_assets = list(output_record.image_assets)
    job_record.export_paths = [export.path_or_url for export in output_record.exports if export.format == "png"]
    job_record.export_urls = [_tmp_url_from_path(path) for path in job_record.export_paths if _tmp_url_from_path(path)]
    job_record.pdf_export_path = next((export.path_or_url for export in output_record.exports if export.format == "pdf"), None)
    job_record.pdf_export_url = _tmp_url_from_path(job_record.pdf_export_path)
    job_record.figma_file_url = output_record.figma_output.file_url
    job_record.figma_page_url = output_record.figma_output.page_url or output_record.figma_output.file_url
    job_record.figma_page_name = output_record.figma_output.page_name


def _iter_production_job_paths() -> list[Path]:
    if not PRODUCTION_JOBS_DIR.exists():
        return []
    # Sort by the stable job id timestamp so render-result sync writes do not
    # make older jobs appear newer than freshly created ones.
    return sorted(PRODUCTION_JOBS_DIR.glob("*.json"), key=lambda path: path.stem, reverse=True)


def _ordered_production_job_paths(preferred_job_id: str | None = None) -> list[Path]:
    job_paths = _iter_production_job_paths()
    if not preferred_job_id:
        return job_paths
    preferred_path = PRODUCTION_JOBS_DIR / f"{preferred_job_id}.json"
    ordered: list[Path] = []
    if preferred_path.exists():
        ordered.append(preferred_path)
    ordered.extend(path for path in job_paths if path != preferred_path)
    return ordered


def _tmp_url_from_path(path: str | None) -> str | None:
    if not path:
        return None
    resolved = Path(path).resolve()
    relative = resolved.relative_to((ROOT_DIR / ".tmp").resolve())
    return f"/tmp-output/{relative.as_posix()}"


def _ensure_used_script(job_record: ProductionJobRecord) -> None:
    if job_record.used_script and job_record.image_assets:
        return
    artifact_path = Path(job_record.job_artifact_path)
    if not artifact_path.exists():
        return
    output_record = CarouselOutput.model_validate_json(artifact_path.read_text(encoding="utf-8"))
    if not job_record.used_script:
        job_record.used_script = _format_used_script(output_record)
    if not job_record.image_assets:
        job_record.image_assets = list(output_record.image_assets)


def _format_used_script(output_record: CarouselOutput) -> str | None:
    sections: list[str] = []
    for slide in output_record.content_plan:
        section_lines = [f"Slide {slide.slide_number}: {slide.headline}"]
        if slide.body:
            section_lines.append(slide.body)
        sections.append("\n".join(section_lines))
    script = "\n\n".join(section for section in sections if section.strip()).strip()
    return script or None
