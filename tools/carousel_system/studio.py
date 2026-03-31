from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from carousel_system.config import ROOT_DIR, Settings
from carousel_system.image_assets import resolve_image_assets
from carousel_system.models import CarouselInput, CarouselOutput, PluginRenderPayload, PluginRenderResult
from carousel_system.payload import build_output_record, write_output_record
from carousel_system.planner import PROMPT_VERSION, generate_carousel_plan
from carousel_system.render_payload import (
    build_plugin_render_payload,
    build_render_artifact,
    infer_language,
    write_plugin_render_payload,
)


STUDIO_DIR = ROOT_DIR / ".tmp" / "studio"
STUDIO_ROUNDS_DIR = STUDIO_DIR / "rounds"
STUDIO_STATE_PATH = STUDIO_DIR / "state.json"
STUDIO_PREVIEWS_DIR = STUDIO_DIR / "previews"
STUDIO_OUTPUT_URL_PREFIX = "/studio-output"

StudioBatchMode = Literal["vary_both", "vary_style", "vary_copy"]
StudioCopyLength = Literal["tight", "balanced", "expanded", "punchy"]
StudioRating = Literal["unrated", "love", "good", "bad"]
StudioStylePool = Literal["all", "core", "local"]
StudioImageMode = Literal["auto", "none", "stock", "ai", "hybrid"]


STYLE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("auto", "Auto"),
    ("alder_forced", "Alder Portrait"),
    ("alder_split_right", "Alder Split Right"),
    ("alder_split_left", "Alder Split Left"),
    ("alder_text_only", "Alder Text Only"),
    ("typography_signal", "Typography Signal"),
    ("cp_3", "CP Minimal Split"),
    ("cp_longform", "CP Longform"),
    ("cp_gallery", "CP Gallery"),
    ("sadekov", "Sadekov Black Profile"),
    ("sadekov_light", "Sadekov White Profile"),
    ("typography_light", "Typography Editorial Light"),
    ("creator_mono", "Creator Mono Minimal"),
    ("light_glow", "Light Grain Glow"),
    ("retro_swipe", "Retro Swipe Creator"),
    ("twitter_card", "Twitter Card Soft"),
)
STYLE_LABELS = {value: label for value, label in STYLE_OPTIONS}
STYLE_POOL_VALUES: dict[StudioStylePool, tuple[str, ...]] = {
    "all": tuple(value for value, _label in STYLE_OPTIONS if value != "auto"),
    "core": (
        "alder_forced",
        "alder_split_right",
        "alder_split_left",
        "alder_text_only",
        "typography_signal",
        "cp_3",
        "cp_longform",
        "cp_gallery",
        "sadekov",
        "sadekov_light",
        "typography_light",
    ),
    "local": (
        "creator_mono",
        "light_glow",
        "retro_swipe",
        "twitter_card",
    ),
}
COPY_LENGTH_OPTIONS: tuple[tuple[StudioCopyLength, str], ...] = (
    ("tight", "Tight"),
    ("balanced", "Balanced"),
    ("expanded", "Expanded"),
    ("punchy", "Punchy"),
)
IMAGE_MODE_OPTIONS: tuple[tuple[StudioImageMode, str], ...] = (
    ("auto", "Auto"),
    ("none", "No Images"),
    ("stock", "Stock Only"),
    ("ai", "AI Only"),
    ("hybrid", "Hybrid"),
)
COPY_LENGTH_ORDER: tuple[StudioCopyLength, ...] = ("tight", "balanced", "expanded", "punchy")
COPY_LENGTH_NOTES: dict[StudioCopyLength, str] = {
    "tight": (
        "Copy profile: tight. Keep the hook extremely concise. "
        "Use short info headlines and a single crisp sentence per info slide. "
        "Keep the CTA direct and compact."
    ),
    "balanced": (
        "Copy profile: balanced. Keep the hook strong, the info slides clear, "
        "and the CTA concise. Use normal carousel-length copy."
    ),
    "expanded": (
        "Copy profile: expanded. Allow richer educational copy. "
        "Each info slide may use up to two short sentences, but stay visually usable."
    ),
    "punchy": (
        "Copy profile: punchy. Favor bold, swipe-friendly language. "
        "Use sharp headlines, shorter lines, and stronger contrast in tone."
    ),
}
RATING_SCORES: dict[StudioRating, int] = {
    "unrated": 0,
    "love": 3,
    "good": 2,
    "bad": -2,
}


class StudioCreateRequest(BaseModel):
    topic: str | None = None
    script: str | None = None
    cta_text: str | None = None
    language: str | None = None
    notes: str | None = None
    batch_mode: StudioBatchMode = "vary_both"
    variant_count: int = Field(default=4, ge=3, le=6)
    preferred_style: str = "auto"
    style_pool: StudioStylePool = "all"
    base_copy_length: StudioCopyLength = "balanced"
    image_mode: StudioImageMode = "auto"

    @field_validator("topic", "script", "cta_text", "language", "notes", mode="before")
    @classmethod
    def _clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None

    @field_validator("preferred_style")
    @classmethod
    def _validate_preferred_style(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in STYLE_LABELS:
            raise ValueError(f"Unknown preferred style: {value}")
        return normalized

    @field_validator("language")
    @classmethod
    def _normalize_language(cls, value: str | None) -> str | None:
        return value.lower() if value else None

    @model_validator(mode="after")
    def _validate_topic_or_script(self) -> "StudioCreateRequest":
        if not self.topic and not self.script:
            raise ValueError("At least one of topic or script is required.")
        return self


class StudioVariantRecord(BaseModel):
    variant_id: str
    ordinal: int
    job_id: str
    rating: StudioRating = "unrated"
    rating_note: str | None = None
    copy_length: StudioCopyLength
    requested_style: str
    requested_style_label: str
    planner_notes: str
    prompt_version: str
    language: str
    style_family: str
    style_recipe: str
    job_artifact_path: str
    render_payload_path: str
    render_status: Literal["planned", "rendering", "complete", "error"] = "planned"
    render_result_path: str | None = None
    figma_url: str | None = None
    preview_image_paths: list[str] = Field(default_factory=list)
    preview_image_urls: list[str] = Field(default_factory=list)
    rendered_at: str | None = None
    error: str | None = None
    payload: PluginRenderPayload

    @field_validator("rating_note", "render_result_path", "figma_url", "rendered_at", "error", mode="before")
    @classmethod
    def _clean_variant_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class StudioRoundRecord(BaseModel):
    round_id: str
    created_at: str
    round_number: int
    based_on_round_id: str | None = None
    request: StudioCreateRequest
    variants: list[StudioVariantRecord]


class StudioState(BaseModel):
    latest_round_id: str | None = None


class StudioRateRequest(BaseModel):
    rating: StudioRating
    note: str | None = None

    @field_validator("note", mode="before")
    @classmethod
    def _clean_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


def studio_bootstrap_payload() -> dict:
    state = load_state()
    return {
        "style_options": [{"value": value, "label": label} for value, label in STYLE_OPTIONS],
        "copy_length_options": [{"value": value, "label": label} for value, label in COPY_LENGTH_OPTIONS],
        "image_mode_options": [{"value": value, "label": label} for value, label in IMAGE_MODE_OPTIONS],
        "batch_modes": [
            {"value": "vary_both", "label": "Vary Style + Copy"},
            {"value": "vary_style", "label": "Vary Style"},
            {"value": "vary_copy", "label": "Vary Copy Length"},
        ],
        "style_pools": [
            {"value": "all", "label": "All Styles"},
            {"value": "core", "label": "Core Families"},
            {"value": "local", "label": "Local Example Families"},
        ],
        "latest_round_id": state.latest_round_id,
    }


def create_review_round(
    settings: Settings,
    request: StudioCreateRequest,
    *,
    based_on_round_id: str | None = None,
) -> StudioRoundRecord:
    STUDIO_ROUNDS_DIR.mkdir(parents=True, exist_ok=True)
    previous_round = load_round(based_on_round_id) if based_on_round_id else None
    round_number = 1 if previous_round is None else previous_round.round_number + 1
    round_id = f"studio-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:6]}"

    variants: list[StudioVariantRecord] = []
    for ordinal, spec in enumerate(
        _build_variant_specs(request, round_number=round_number, previous_round=previous_round),
        start=1,
    ):
        job_id = f"{round_id}-v{ordinal}"
        output_path = ROOT_DIR / ".tmp" / "jobs" / f"{job_id}.json"
        render_payload_path = ROOT_DIR / ".tmp" / "render-jobs" / f"{job_id}.render.json"
        job = CarouselInput(
            job_id=job_id,
            source="manual",
            topic=request.topic,
            script=request.script,
            cta_text=request.cta_text,
            language=request.language,
            image_mode=request.image_mode,
            aspect_ratio="portrait_1080x1350",
            output_modes=["figma", "png"],
            reference_style=spec.requested_style,
            reference_file_key=settings.figma_reference_file_key,
            notes=spec.planner_notes,
        )

        plan = generate_carousel_plan(settings, job)
        record = build_output_record(job, plan, prompt_version=PROMPT_VERSION, language=job.language)
        payload = build_plugin_render_payload(record, source_artifact_path=output_path)
        record.language = payload.language or infer_language(record)
        record.style_family = payload.style_family
        record.style_recipe = payload.style_recipe
        resolve_image_assets(settings, record, payload)
        record.design_reference_log = [
            reference for reference in record.design_reference_log if reference.node_id in set(payload.reference_node_ids)
        ]
        record.render_artifact = build_render_artifact(render_payload_path, payload)
        write_output_record(output_path, record)
        write_plugin_render_payload(render_payload_path, payload)

        variants.append(
            StudioVariantRecord(
                variant_id=f"{round_id}-variant-{ordinal}",
                ordinal=ordinal,
                job_id=job_id,
                copy_length=spec.copy_length,
                requested_style=spec.requested_style,
                requested_style_label=STYLE_LABELS.get(spec.requested_style, spec.requested_style),
                planner_notes=spec.planner_notes,
                prompt_version=PROMPT_VERSION,
                language=payload.language,
                style_family=payload.style_family,
                style_recipe=payload.style_recipe,
                job_artifact_path=str(output_path),
                render_payload_path=str(render_payload_path),
                render_status="planned",
                payload=payload,
            )
        )

    round_record = StudioRoundRecord(
        round_id=round_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        round_number=round_number,
        based_on_round_id=based_on_round_id,
        request=request,
        variants=variants,
    )
    save_round(round_record)
    return round_record


def create_next_round(settings: Settings, round_id: str) -> StudioRoundRecord:
    previous_round = load_round(round_id)
    if previous_round is None:
        raise FileNotFoundError(f"Unknown round_id: {round_id}")
    updated_request = _request_for_next_round(previous_round)
    return create_review_round(settings, updated_request, based_on_round_id=previous_round.round_id)


def load_round(round_id: str | None) -> StudioRoundRecord | None:
    if not round_id:
        return None
    path = STUDIO_ROUNDS_DIR / f"{round_id}.json"
    if not path.exists():
        return None
    return StudioRoundRecord.model_validate_json(path.read_text(encoding="utf-8"))


def load_latest_round() -> StudioRoundRecord | None:
    state = load_state()
    return load_round(state.latest_round_id)


def rate_variant(round_id: str, variant_id: str, rating: StudioRating, note: str | None = None) -> StudioRoundRecord:
    round_record = load_round(round_id)
    if round_record is None:
        raise FileNotFoundError(f"Unknown round_id: {round_id}")

    updated = False
    for variant in round_record.variants:
        if variant.variant_id == variant_id:
            variant.rating = rating
            variant.rating_note = note
            updated = True
            break

    if not updated:
        raise FileNotFoundError(f"Unknown variant_id: {variant_id}")

    save_round(round_record)
    return round_record


def load_state() -> StudioState:
    if not STUDIO_STATE_PATH.exists():
        return StudioState()
    return StudioState.model_validate_json(STUDIO_STATE_PATH.read_text(encoding="utf-8"))


def save_round(round_record: StudioRoundRecord) -> Path:
    STUDIO_ROUNDS_DIR.mkdir(parents=True, exist_ok=True)
    path = STUDIO_ROUNDS_DIR / f"{round_record.round_id}.json"
    path.write_text(round_record.model_dump_json(indent=2), encoding="utf-8")
    state = StudioState(latest_round_id=round_record.round_id)
    STUDIO_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STUDIO_STATE_PATH.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    return path


def acquire_next_studio_render_variant() -> StudioVariantRecord | None:
    for round_path in _iter_round_paths():
        round_record = StudioRoundRecord.model_validate_json(round_path.read_text(encoding="utf-8"))
        updated = False
        for variant in round_record.variants:
            job_path = Path(variant.job_artifact_path)
            if not job_path.exists():
                continue
            job_record = CarouselOutput.model_validate_json(job_path.read_text(encoding="utf-8"))
            if job_record.status == "complete" and variant.render_status != "complete":
                _apply_render_snapshot_to_variant(
                    variant,
                    job_record=job_record,
                    render_result_path=job_record.render_artifact.result_path,
                    preview_image_paths=variant.preview_image_paths,
                )
                updated = True
                continue
            if job_record.status == "error" and variant.render_status != "error":
                variant.render_status = "error"
                variant.error = job_record.error
                updated = True
                continue
            if job_record.status in {"planned", "rendering"} and variant.render_status == "planned":
                if updated:
                    save_round(round_record)
                return variant
        if updated:
            save_round(round_record)
    return None


def mark_variant_rendering(job_id: str) -> None:
    _update_variant(job_id, _set_variant_rendering)


def sync_variant_render_result(
    job_id: str,
    result: PluginRenderResult,
    *,
    render_result_path: Path,
    preview_image_paths: list[Path],
) -> None:
    def _apply(variant: StudioVariantRecord) -> None:
        preview_paths = [str(path) for path in preview_image_paths]
        _apply_render_snapshot_to_variant(
            variant,
            job_record=None,
            render_result_path=str(render_result_path),
            preview_image_paths=preview_paths,
            result=result,
        )

    _update_variant(job_id, _apply)


def sync_variant_render_error(job_id: str, error_text: str) -> None:
    def _apply(variant: StudioVariantRecord) -> None:
        variant.render_status = "error"
        variant.error = error_text

    _update_variant(job_id, _apply)


class _VariantSpec(BaseModel):
    requested_style: str
    copy_length: StudioCopyLength
    planner_notes: str


def _build_variant_specs(
    request: StudioCreateRequest,
    *,
    round_number: int,
    previous_round: StudioRoundRecord | None,
) -> list[_VariantSpec]:
    pool = _resolve_style_pool(request)
    signature = _signature(request, round_number)
    rated_bad_styles = (
        {variant.requested_style for variant in previous_round.variants if variant.rating == "bad"}
        if previous_round
        else set()
    )
    available_pool = [style for style in pool if style not in rated_bad_styles] or list(pool)
    styles = _pick_styles(
        request=request,
        available_pool=available_pool,
        signature=signature,
        previous_round=previous_round,
    )
    copy_lengths = _pick_copy_lengths(
        request=request,
        signature=signature,
        previous_round=previous_round,
    )

    specs: list[_VariantSpec] = []
    for index in range(request.variant_count):
        style_value = styles[index % len(styles)]
        copy_length = copy_lengths[index % len(copy_lengths)]
        specs.append(
            _VariantSpec(
                requested_style=style_value,
                copy_length=copy_length,
                planner_notes=_compose_planner_notes(request, copy_length, style_value, previous_round),
            )
        )
    return specs


def _pick_styles(
    *,
    request: StudioCreateRequest,
    available_pool: list[str],
    signature: int,
    previous_round: StudioRoundRecord | None,
) -> list[str]:
    if request.batch_mode == "vary_copy":
        anchor_style = _preferred_style_for_round(request, previous_round)
        return [anchor_style]

    ordered_pool = _rotated_values(available_pool, signature)
    if request.preferred_style != "auto":
        ordered_pool = [request.preferred_style] + [value for value in ordered_pool if value != request.preferred_style]
    elif previous_round:
        best_variant = _best_rated_variant(previous_round)
        if best_variant and best_variant.rating in {"love", "good"} and best_variant.requested_style != "auto":
            ordered_pool = [best_variant.requested_style] + [
                value for value in ordered_pool if value != best_variant.requested_style
            ]

    if request.batch_mode == "vary_style":
        return ordered_pool[: request.variant_count]

    if request.batch_mode == "vary_both":
        return ordered_pool[: request.variant_count]

    return [ordered_pool[0]]


def _pick_copy_lengths(
    *,
    request: StudioCreateRequest,
    signature: int,
    previous_round: StudioRoundRecord | None,
) -> list[StudioCopyLength]:
    anchor = request.base_copy_length
    best_variant = _best_rated_variant(previous_round) if previous_round else None
    if best_variant and best_variant.rating in {"love", "good"}:
        anchor = best_variant.copy_length

    ordered = _rotated_values(list(COPY_LENGTH_ORDER), COPY_LENGTH_ORDER.index(anchor))
    if request.batch_mode == "vary_style":
        return [anchor]
    if request.batch_mode == "vary_copy":
        return ordered[: request.variant_count]

    rotated = _rotated_values(ordered, signature % len(ordered))
    return rotated[: request.variant_count]


def _preferred_style_for_round(request: StudioCreateRequest, previous_round: StudioRoundRecord | None) -> str:
    if request.preferred_style != "auto":
        return request.preferred_style
    best_variant = _best_rated_variant(previous_round) if previous_round else None
    if best_variant and best_variant.rating in {"love", "good"}:
        return best_variant.requested_style
    return "auto"


def _compose_planner_notes(
    request: StudioCreateRequest,
    copy_length: StudioCopyLength,
    style_value: str,
    previous_round: StudioRoundRecord | None,
) -> str:
    notes = [COPY_LENGTH_NOTES[copy_length]]
    if request.notes:
        notes.append(f"User note: {request.notes}")

    best_variant = _best_rated_variant(previous_round) if previous_round else None
    if best_variant and best_variant.rating_note:
        notes.append(f"Previous review note: {best_variant.rating_note}")

    if style_value != "auto":
        notes.append(f"Target style family: {STYLE_LABELS.get(style_value, style_value)}.")
    else:
        notes.append("Target style family: let the style engine choose automatically.")
    return " ".join(notes)


def _request_for_next_round(previous_round: StudioRoundRecord) -> StudioCreateRequest:
    request = previous_round.request.model_copy(deep=True)
    best_variant = _best_rated_variant(previous_round)
    if best_variant and best_variant.rating in {"love", "good"}:
        request.base_copy_length = best_variant.copy_length
        if previous_round.request.batch_mode != "vary_copy":
            request.preferred_style = best_variant.requested_style
    else:
        request.preferred_style = previous_round.request.preferred_style
    return request


def _best_rated_variant(previous_round: StudioRoundRecord | None) -> StudioVariantRecord | None:
    if previous_round is None:
        return None
    rated = sorted(
        previous_round.variants,
        key=lambda variant: (-RATING_SCORES[variant.rating], variant.ordinal),
    )
    return rated[0] if rated else None


def _resolve_style_pool(request: StudioCreateRequest) -> tuple[str, ...]:
    pool = STYLE_POOL_VALUES[request.style_pool]
    if request.preferred_style != "auto" and request.preferred_style not in pool:
        return (request.preferred_style,) + pool
    return pool


def _signature(request: StudioCreateRequest, round_number: int) -> int:
    payload = "||".join(
        [
            request.topic or "",
            request.script or "",
            request.cta_text or "",
            request.notes or "",
            request.preferred_style,
            request.batch_mode,
            request.base_copy_length,
            str(round_number),
        ]
    )
    digest = sha256(payload.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _rotated_values(values: list[str] | list[StudioCopyLength] | tuple[str, ...], offset: int) -> list:
    if not values:
        return []
    offset = offset % len(values)
    return list(values[offset:]) + list(values[:offset])


def _iter_round_paths() -> list[Path]:
    if not STUDIO_ROUNDS_DIR.exists():
        return []
    return sorted(STUDIO_ROUNDS_DIR.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)


def _update_variant(job_id: str, callback) -> None:
    for round_path in _iter_round_paths():
        round_record = StudioRoundRecord.model_validate_json(round_path.read_text(encoding="utf-8"))
        updated = False
        for variant in round_record.variants:
            if variant.job_id == job_id:
                callback(variant)
                updated = True
        if updated:
            save_round(round_record)


def _set_variant_rendering(variant: StudioVariantRecord) -> None:
    variant.render_status = "rendering"
    variant.error = None


def _apply_render_snapshot_to_variant(
    variant: StudioVariantRecord,
    *,
    job_record: CarouselOutput | None,
    render_result_path: str | None,
    preview_image_paths: list[str],
    result: PluginRenderResult | None = None,
) -> None:
    source_result = result
    if source_result is None and job_record:
        source_result = PluginRenderResult(
            job_id=job_record.job_id,
            page_name=job_record.figma_output.page_name or "",
            page_id="",
            file_key=job_record.figma_output.file_key,
            file_url=job_record.figma_output.file_url,
            slide_node_ids=job_record.figma_output.slide_node_ids,
            rendered_at="",
        )

    variant.render_status = "complete"
    variant.error = None
    variant.render_result_path = render_result_path
    variant.figma_url = source_result.file_url if source_result else None
    variant.preview_image_paths = preview_image_paths
    variant.preview_image_urls = [_preview_url_from_path(path) for path in preview_image_paths]
    variant.rendered_at = source_result.rendered_at if source_result else None


def _preview_url_from_path(path: str) -> str:
    resolved = Path(path).resolve()
    relative = resolved.relative_to(STUDIO_DIR.resolve())
    return f"{STUDIO_OUTPUT_URL_PREFIX}/{relative.as_posix()}"
