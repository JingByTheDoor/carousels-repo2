from __future__ import annotations

import json
import re
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
REVIEW_NOTES_DIR = ROOT_DIR / "notes" / "review_feedback"

REVIEW_NICHE_PRESET = "english_teacher_materials"
REVIEW_NICHE_LABEL = "Materials helpful to English teachers"
REVIEW_DEFAULT_CTA = "Follow for more English teaching materials"
REVIEW_SAFE_STYLE_VALUES: tuple[str, ...] = (
    "alder_split_right",
    "placeholder_media",
    "light_glow",
    "device_mockup",
    "twitter_card",
)
REVIEW_COPY_SEQUENCE: tuple["StudioCopyLength", ...] = ("tight", "balanced", "expanded")
REVIEW_BRIEF_BANK: tuple[str, ...] = (
    "5 warm-up activities English teachers can use in any online class",
    "How to make speaking prompts easier for shy English learners",
    "A simple ESL worksheet format that saves prep time",
    "Classroom materials that help English students remember new vocabulary",
    "How English teachers can turn one reading text into a full lesson",
    "Pronunciation practice materials that are actually fun to use",
    "How to build better grammar handouts for English learners",
    "Low-prep writing activities that help English students think faster",
    "Visual materials that make online English classes easier to follow",
    "Listening lesson materials that keep English learners engaged",
    "How to create clear lesson slides for English teachers",
    "English teaching resources that make mixed-level classes easier",
)

StudioBatchMode = Literal["vary_both", "vary_style", "vary_copy"]
StudioCopyLength = Literal["tight", "balanced", "expanded", "punchy"]
StudioRating = Literal["unrated", "love", "good", "bad"]
StudioStylePool = Literal["all", "core", "local"]
StudioImageMode = Literal["auto", "none", "stock", "ai", "hybrid"]
StudioRoundMode = Literal["advanced", "review"]
StudioReviewStatus = Literal["drafting", "rendering", "ready_for_review", "winner_selected", "submitted", "error"]
LayoutDensityLabel = Literal["Minimal", "Mixed", "Dense"]
SLIDE_REFERENCE_PATTERN = re.compile(r"(?<![A-Za-z0-9])/slide[_-]?([1-7])\b", re.IGNORECASE)


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
    ("pastel_arrow", "Pastel Arrow Editorial"),
    ("placeholder_media", "Placeholder Media Glow"),
    ("light_glow", "Light Grain Glow"),
    ("device_mockup", "Device Mockup Gradient"),
    ("retro_swipe", "Retro Swipe Creator"),
    ("social_proof", "Social Proof LinkedIn"),
    ("profile_circle", "Profile Circle Pop"),
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
        "pastel_arrow",
        "placeholder_media",
        "light_glow",
        "device_mockup",
        "retro_swipe",
        "social_proof",
        "profile_circle",
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
    review_mode: bool = False
    niche_preset: str | None = None

    @field_validator("topic", "script", "cta_text", "language", "notes", "niche_preset", mode="before")
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
        if not self.review_mode and not self.topic and not self.script:
            raise ValueError("At least one of topic or script is required.")
        return self


class ReviewRoundCreateRequest(BaseModel):
    topic: str | None = None
    script: str | None = None
    cta_text: str | None = None
    language: str | None = None
    notes: str | None = None
    preferred_style: str = "auto"
    base_copy_length: StudioCopyLength = "balanced"
    image_mode: StudioImageMode = "hybrid"

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


class ReviewWinnerRequest(BaseModel):
    winner_variant_id: str
    winner_feedback: str | None = None
    loser_feedback: dict[str, str] = Field(default_factory=dict)

    @field_validator("winner_variant_id", mode="before")
    @classmethod
    def _clean_winner_id(cls, value: str) -> str:
        return " ".join(str(value).strip().split())

    @field_validator("loser_feedback", mode="before")
    @classmethod
    def _clean_feedback(cls, value: dict[str, str] | None) -> dict[str, str]:
        if not value:
            return {}
        cleaned: dict[str, str] = {}
        for key, item in value.items():
            normalized_key = " ".join(str(key).strip().split())
            normalized_value = " ".join(str(item).strip().split())
            if normalized_key and normalized_value:
                cleaned[normalized_key] = normalized_value
        return cleaned

    @field_validator("winner_feedback", mode="before")
    @classmethod
    def _clean_winner_feedback(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(str(value).strip().split())
        return cleaned or None


class StudioVariantRecord(BaseModel):
    variant_id: str
    ordinal: int
    job_id: str
    rating: StudioRating = "unrated"
    rating_note: str | None = None
    winner_feedback: str | None = None
    rejection_note: str | None = None
    copy_length: StudioCopyLength
    copy_length_label: str = ""
    layout_density_label: LayoutDensityLabel = "Mixed"
    image_count: int = 0
    requested_style: str
    requested_style_label: str = ""
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
    figma_page_name: str | None = None
    figma_page_url: str | None = None
    feedback_slide_references: list["StudioSlideReference"] = Field(default_factory=list)
    export_paths: list[str] = Field(default_factory=list)
    export_urls: list[str] = Field(default_factory=list)
    pdf_export_path: str | None = None
    pdf_export_url: str | None = None
    preview_image_paths: list[str] = Field(default_factory=list)
    preview_image_urls: list[str] = Field(default_factory=list)
    rendered_at: str | None = None
    error: str | None = None
    payload: PluginRenderPayload

    @field_validator(
        "rating_note",
        "winner_feedback",
        "rejection_note",
        "render_result_path",
        "figma_url",
        "figma_page_name",
        "figma_page_url",
        "pdf_export_path",
        "pdf_export_url",
        "rendered_at",
        "error",
        mode="before",
    )
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
    round_mode: StudioRoundMode = "advanced"
    based_on_round_id: str | None = None
    request: StudioCreateRequest
    generated_brief: str | None = None
    niche_preset: str | None = None
    review_status: StudioReviewStatus = "drafting"
    winner_variant_id: str | None = None
    figma_file_url: str | None = None
    review_note_json_path: str | None = None
    review_note_markdown_path: str | None = None
    variants: list[StudioVariantRecord]

    @field_validator(
        "generated_brief",
        "niche_preset",
        "winner_variant_id",
        "figma_file_url",
        "review_note_json_path",
        "review_note_markdown_path",
        mode="before",
    )
    @classmethod
    def _clean_round_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class StudioState(BaseModel):
    latest_round_id: str | None = None


class StudioSlideReference(BaseModel):
    token: str
    slide_number: int = Field(ge=1, le=7)
    export_path: str | None = None
    export_url: str | None = None
    preview_path: str | None = None
    preview_url: str | None = None

    @field_validator("token", "export_path", "export_url", "preview_path", "preview_url", mode="before")
    @classmethod
    def _clean_reference_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


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


StudioVariantRecord.model_rebuild()


class _VariantSpec(BaseModel):
    requested_style: str
    copy_length: StudioCopyLength
    planner_notes: str


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
        "review_defaults": {
            "niche_preset": REVIEW_NICHE_PRESET,
            "niche_label": REVIEW_NICHE_LABEL,
            "variant_count": 3,
            "image_mode": "hybrid",
            "preferred_style": "auto",
            "base_copy_length": "balanced",
        },
    }


def create_minimal_review_round(
    settings: Settings,
    request: ReviewRoundCreateRequest,
    *,
    based_on_round_id: str | None = None,
) -> StudioRoundRecord:
    studio_request = StudioCreateRequest(
        topic=request.topic,
        script=request.script,
        cta_text=request.cta_text,
        language=request.language,
        notes=request.notes,
        batch_mode="vary_both",
        variant_count=3,
        preferred_style=request.preferred_style,
        style_pool="all",
        base_copy_length=request.base_copy_length,
        image_mode=request.image_mode,
        review_mode=True,
        niche_preset=REVIEW_NICHE_PRESET,
    )
    return create_review_round(settings, studio_request, based_on_round_id=based_on_round_id)


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
    resolved_request = _resolve_round_request(request)
    generated_brief = _resolve_generated_brief(resolved_request, round_number, previous_round)
    resolved_topic = resolved_request.topic or generated_brief
    resolved_script = resolved_request.script
    resolved_cta = resolved_request.cta_text or (
        REVIEW_DEFAULT_CTA if resolved_request.review_mode else "Follow for more carousel breakdowns"
    )

    variants: list[StudioVariantRecord] = []
    for ordinal, spec in enumerate(
        _build_variant_specs(resolved_request, round_number=round_number, previous_round=previous_round),
        start=1,
    ):
        job_id = f"{round_id}-v{ordinal}"
        output_path = ROOT_DIR / ".tmp" / "jobs" / f"{job_id}.json"
        render_payload_path = ROOT_DIR / ".tmp" / "render-jobs" / f"{job_id}.render.json"
        job = CarouselInput(
            job_id=job_id,
            source="manual",
            generation_mode="review" if resolved_request.review_mode else "standard",
            niche_preset=resolved_request.niche_preset,
            topic=resolved_topic,
            script=resolved_script,
            cta_text=resolved_cta,
            language=resolved_request.language,
            image_mode=resolved_request.image_mode,
            aspect_ratio="portrait_1080x1350",
            output_modes=["figma", "png"],
            reference_style=spec.requested_style,
            reference_file_key=settings.figma_reference_file_key,
            notes=spec.planner_notes,
        )

        plan = generate_carousel_plan(settings, job)
        record = build_output_record(job, plan, prompt_version=PROMPT_VERSION, language=job.language)
        payload = build_plugin_render_payload(record, source_artifact_path=output_path)
        if resolved_request.review_mode:
            payload.page_name = f"Round {round_number:02d} · Variant {ordinal}"
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
                copy_length_label=_copy_length_label(spec.copy_length),
                layout_density_label=_layout_density_label(payload),
                image_count=_payload_image_count(payload),
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
                figma_page_name=payload.page_name,
                payload=payload,
            )
        )

    round_record = StudioRoundRecord(
        round_id=round_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        round_number=round_number,
        round_mode="review" if resolved_request.review_mode else "advanced",
        based_on_round_id=based_on_round_id,
        request=resolved_request,
        generated_brief=generated_brief,
        niche_preset=resolved_request.niche_preset,
        review_status="rendering" if variants else "drafting",
        winner_variant_id=None,
        figma_file_url=None,
        variants=variants,
    )
    save_round(round_record)
    return round_record


def create_next_review_round(settings: Settings, round_id: str) -> StudioRoundRecord:
    previous_round = load_round(round_id)
    if previous_round is None:
        raise FileNotFoundError(f"Unknown round_id: {round_id}")
    if not previous_round.winner_variant_id:
        raise ValueError("Select a winning variant before generating the next round.")
    updated_request = _request_for_next_review_round(previous_round)
    return create_review_round(settings, updated_request, based_on_round_id=previous_round.round_id)


def create_next_round(settings: Settings, round_id: str) -> StudioRoundRecord:
    previous_round = load_round(round_id)
    if previous_round is None:
        raise FileNotFoundError(f"Unknown round_id: {round_id}")
    if previous_round.round_mode == "review":
        return create_next_review_round(settings, round_id)
    updated_request = _request_for_next_round(previous_round)
    return create_review_round(settings, updated_request, based_on_round_id=previous_round.round_id)


def save_review_winner(round_id: str, request: ReviewWinnerRequest) -> StudioRoundRecord:
    round_record = load_round(round_id)
    if round_record is None:
        raise FileNotFoundError(f"Unknown round_id: {round_id}")

    variant_ids = {variant.variant_id for variant in round_record.variants}
    if request.winner_variant_id not in variant_ids:
        raise FileNotFoundError(f"Unknown winner_variant_id: {request.winner_variant_id}")

    round_record.winner_variant_id = request.winner_variant_id
    for variant in round_record.variants:
        if variant.variant_id == request.winner_variant_id:
            cleaned_winner_feedback = _strip_slide_reference_tokens(request.winner_feedback)
            variant.rating = "love"
            variant.rating_note = cleaned_winner_feedback
            variant.winner_feedback = cleaned_winner_feedback
            variant.rejection_note = None
            variant.feedback_slide_references = _extract_slide_references(request.winner_feedback, variant)
        else:
            note = request.loser_feedback.get(variant.variant_id)
            cleaned_note = _strip_slide_reference_tokens(note)
            variant.rating = "bad"
            variant.rating_note = cleaned_note
            variant.winner_feedback = None
            variant.rejection_note = cleaned_note
            variant.feedback_slide_references = _extract_slide_references(note, variant)

    save_round(round_record)
    _write_review_feedback_notes(round_record)
    return round_record


def submit_review_round(round_id: str, request: ReviewWinnerRequest) -> StudioRoundRecord:
    round_record = save_review_winner(round_id, request)
    round_record.review_status = "submitted"
    save_round(round_record)
    _clear_active_round(round_record.round_id)
    return round_record


def load_round(round_id: str | None) -> StudioRoundRecord | None:
    if not round_id:
        return None
    path = STUDIO_ROUNDS_DIR / f"{round_id}.json"
    if not path.exists():
        return None
    round_record = StudioRoundRecord.model_validate_json(path.read_text(encoding="utf-8"))
    _rehydrate_round_variants(round_record)
    return round_record


def load_latest_round() -> StudioRoundRecord | None:
    state = load_state()
    return load_round(state.latest_round_id)


def load_latest_review_round() -> StudioRoundRecord | None:
    latest_round = load_latest_round()
    if latest_round and latest_round.round_mode == "review" and latest_round.review_status != "submitted":
        return latest_round

    for round_path in _iter_round_paths():
        round_record = StudioRoundRecord.model_validate_json(round_path.read_text(encoding="utf-8"))
        _rehydrate_round_variants(round_record)
        if round_record.round_mode == "review" and round_record.review_status != "submitted":
            return round_record
    return None


def rate_variant(round_id: str, variant_id: str, rating: StudioRating, note: str | None = None) -> StudioRoundRecord:
    round_record = load_round(round_id)
    if round_record is None:
        raise FileNotFoundError(f"Unknown round_id: {round_id}")

    updated = False
    for variant in round_record.variants:
        if variant.variant_id == variant_id:
            variant.rating = rating
            variant.rating_note = note
            if rating == "bad":
                variant.rejection_note = note
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
    _refresh_round_summary(round_record)
    STUDIO_ROUNDS_DIR.mkdir(parents=True, exist_ok=True)
    path = STUDIO_ROUNDS_DIR / f"{round_record.round_id}.json"
    path.write_text(round_record.model_dump_json(indent=2), encoding="utf-8")
    state = StudioState(latest_round_id=round_record.round_id)
    STUDIO_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STUDIO_STATE_PATH.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    return path


def _rehydrate_round_variants(round_record: StudioRoundRecord) -> None:
    updated = False
    for variant in round_record.variants:
        if variant.render_status != "complete":
            continue
        artifact_path = Path(variant.job_artifact_path)
        if not artifact_path.exists():
            continue
        job_record = CarouselOutput.model_validate_json(artifact_path.read_text(encoding="utf-8"))
        expected_export_paths = [export.path_or_url for export in job_record.exports if export.format == "png"]
        expected_pdf_path = next((export.path_or_url for export in job_record.exports if export.format == "pdf"), None)
        if variant.export_paths == expected_export_paths and variant.pdf_export_path == expected_pdf_path:
            continue
        _apply_render_snapshot_to_variant(
            variant,
            job_record=job_record,
            render_result_path=variant.render_result_path,
            preview_image_paths=variant.preview_image_paths,
        )
        updated = True
    if updated:
        save_round(round_record)


def _clear_active_round(round_id: str) -> None:
    state = load_state()
    if state.latest_round_id != round_id:
        return
    STUDIO_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STUDIO_STATE_PATH.write_text(StudioState(latest_round_id=None).model_dump_json(indent=2), encoding="utf-8")


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
        job_record = None
        artifact_path = Path(variant.job_artifact_path)
        if artifact_path.exists():
            job_record = CarouselOutput.model_validate_json(artifact_path.read_text(encoding="utf-8"))
        _apply_render_snapshot_to_variant(
            variant,
            job_record=job_record,
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


def _resolve_round_request(request: StudioCreateRequest) -> StudioCreateRequest:
    resolved = request.model_copy(deep=True)
    if resolved.review_mode:
        resolved.batch_mode = "vary_both"
        resolved.variant_count = 3
        resolved.niche_preset = resolved.niche_preset or REVIEW_NICHE_PRESET
        if resolved.image_mode == "auto":
            resolved.image_mode = "hybrid"
        if resolved.preferred_style not in {"auto", *REVIEW_SAFE_STYLE_VALUES}:
            resolved.preferred_style = "auto"
    return resolved


def _resolve_generated_brief(
    request: StudioCreateRequest,
    round_number: int,
    previous_round: StudioRoundRecord | None,
) -> str:
    if request.topic:
        return request.topic
    if request.script:
        first_line = request.script.splitlines()[0].strip()
        return first_line[:120] or "Custom script"
    if request.review_mode and previous_round and previous_round.generated_brief:
        return previous_round.generated_brief
    if request.review_mode:
        signature = _signature(request, round_number)
        return REVIEW_BRIEF_BANK[signature % len(REVIEW_BRIEF_BANK)]
    return ""


def _build_variant_specs(
    request: StudioCreateRequest,
    *,
    round_number: int,
    previous_round: StudioRoundRecord | None,
) -> list[_VariantSpec]:
    if request.review_mode:
        return _build_review_variant_specs(request, round_number=round_number, previous_round=previous_round)

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


def _build_review_variant_specs(
    request: StudioCreateRequest,
    *,
    round_number: int,
    previous_round: StudioRoundRecord | None,
) -> list[_VariantSpec]:
    signature = _signature(request, round_number)
    anchor_variant = _winner_variant(previous_round) or _best_rated_variant(previous_round)
    anchor_style = request.preferred_style if request.preferred_style != "auto" else None
    if anchor_variant and anchor_variant.rating in {"love", "good"} and anchor_variant.requested_style in REVIEW_SAFE_STYLE_VALUES:
        anchor_style = anchor_style or anchor_variant.requested_style
    style_pool = list(_rotated_values(list(REVIEW_SAFE_STYLE_VALUES), signature))
    if anchor_style in style_pool:
        styles = [anchor_style] + [value for value in style_pool if value != anchor_style]
    else:
        styles = style_pool
    styles = styles[:3]

    anchor_copy = request.base_copy_length
    if anchor_variant and anchor_variant.rating in {"love", "good"}:
        anchor_copy = anchor_variant.copy_length
    if anchor_copy not in REVIEW_COPY_SEQUENCE:
        anchor_copy = "balanced"
    copy_lengths = list(
        _rotated_values(list(REVIEW_COPY_SEQUENCE), REVIEW_COPY_SEQUENCE.index(anchor_copy))
    )
    if anchor_variant and anchor_variant.copy_length in copy_lengths:
        copy_lengths = [anchor_variant.copy_length] + [value for value in copy_lengths if value != anchor_variant.copy_length]
    copy_lengths = copy_lengths[:3]

    specs: list[_VariantSpec] = []
    for index in range(3):
        style_value = styles[index % len(styles)]
        copy_length = copy_lengths[index % len(copy_lengths)]
        specs.append(
            _VariantSpec(
                requested_style=style_value,
                copy_length=copy_length,
                planner_notes=_compose_review_planner_notes(request, copy_length, style_value, previous_round),
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


def _compose_review_planner_notes(
    request: StudioCreateRequest,
    copy_length: StudioCopyLength,
    style_value: str,
    previous_round: StudioRoundRecord | None,
) -> str:
    notes = [
        COPY_LENGTH_NOTES[copy_length],
        "Audience: English teachers looking for useful classroom or online-teaching materials.",
        "Keep the carousel practical, concrete, and directly useful to teachers.",
        "Use a strong hook, 5 clear teaching-resource points, and a direct CTA.",
    ]
    if request.notes:
        notes.append(f"User note: {request.notes}")
    if style_value != "auto":
        notes.append(f"Target style family: {STYLE_LABELS.get(style_value, style_value)}.")

    winner = _winner_variant(previous_round)
    if winner:
        notes.append(
            f"Keep what worked from the previous winner: {winner.requested_style_label}, {winner.copy_length_label} copy."
        )
    winner_feedback = _winner_feedback(previous_round)
    if winner_feedback:
        notes.append(f"Winner feedback to preserve or refine: {winner_feedback}")
    loser_notes = _rejection_notes(previous_round)
    if loser_notes:
        notes.append(f"Avoid these previous problems: {' | '.join(loser_notes)}")
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


def _request_for_next_review_round(previous_round: StudioRoundRecord) -> StudioCreateRequest:
    request = previous_round.request.model_copy(deep=True)
    request.review_mode = True
    request.niche_preset = previous_round.niche_preset or REVIEW_NICHE_PRESET
    request.topic = previous_round.generated_brief
    request.script = None
    winner = _winner_variant(previous_round) or _best_rated_variant(previous_round)
    if winner:
        request.preferred_style = winner.requested_style if winner.requested_style in REVIEW_SAFE_STYLE_VALUES else "auto"
        request.base_copy_length = winner.copy_length
    if previous_round.generated_brief:
        request.notes = _compose_next_review_note(previous_round)
    return _resolve_round_request(request)


def _compose_next_review_note(previous_round: StudioRoundRecord) -> str | None:
    notes = []
    if previous_round.request.notes:
        notes.append(previous_round.request.notes)
    winner = _winner_variant(previous_round)
    if winner:
        notes.append(f"Anchor on Variant {winner.ordinal}.")
    winner_feedback = _winner_feedback(previous_round)
    if winner_feedback:
        notes.append(f"Keep or refine these winner traits: {winner_feedback}")
    loser_notes = _rejection_notes(previous_round)
    if loser_notes:
        notes.append(f"Fix these problems: {' | '.join(loser_notes)}")
    return " ".join(notes) if notes else None


def _winner_variant(previous_round: StudioRoundRecord | None) -> StudioVariantRecord | None:
    if previous_round is None or not previous_round.winner_variant_id:
        return None
    for variant in previous_round.variants:
        if variant.variant_id == previous_round.winner_variant_id:
            return variant
    return None


def _winner_feedback(previous_round: StudioRoundRecord | None) -> str | None:
    winner = _winner_variant(previous_round)
    if winner and winner.winner_feedback:
        return winner.winner_feedback
    return None


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
            request.niche_preset or "",
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
            page_id=job_record.figma_output.page_id or "",
            file_key=job_record.figma_output.file_key,
            file_url=job_record.figma_output.file_url,
            page_url=job_record.figma_output.page_url,
            slide_node_ids=job_record.figma_output.slide_node_ids,
            rendered_at="",
        )

    variant.render_status = "complete"
    variant.error = None
    variant.render_result_path = render_result_path
    variant.figma_url = source_result.file_url if source_result else None
    variant.figma_page_name = source_result.page_name if source_result else variant.figma_page_name
    variant.figma_page_url = (
        source_result.page_url
        if source_result and source_result.page_url
        else source_result.file_url if source_result else None
    )
    variant.preview_image_paths = preview_image_paths
    variant.preview_image_urls = [_preview_url_from_path(path) for path in preview_image_paths]
    export_paths: list[str] = []
    pdf_path: str | None = None
    if job_record:
        for export in job_record.exports:
            if export.format == "png":
                export_paths.append(export.path_or_url)
            elif export.format == "pdf":
                pdf_path = export.path_or_url
    variant.export_paths = export_paths
    variant.export_urls = [_tmp_url_from_path(path) for path in export_paths]
    variant.pdf_export_path = pdf_path
    variant.pdf_export_url = _tmp_url_from_path(pdf_path) if pdf_path else None
    variant.rendered_at = source_result.rendered_at if source_result else None


def _refresh_round_summary(round_record: StudioRoundRecord) -> None:
    round_record.figma_file_url = next((variant.figma_url for variant in round_record.variants if variant.figma_url), None)
    if round_record.review_status == "submitted":
        return
    has_error = any(variant.render_status == "error" for variant in round_record.variants)
    all_complete = bool(round_record.variants) and all(variant.render_status == "complete" for variant in round_record.variants)
    if has_error:
        round_record.review_status = "error"
        return
    if round_record.winner_variant_id:
        round_record.review_status = "winner_selected"
        return
    if all_complete:
        round_record.review_status = "ready_for_review"
        return
    if round_record.variants:
        round_record.review_status = "rendering"
        return
    round_record.review_status = "drafting"


def _copy_length_label(value: StudioCopyLength) -> str:
    return value.capitalize()


def _layout_density_label(payload: PluginRenderPayload) -> LayoutDensityLabel:
    densities = [slide.text_density for slide in payload.slides if slide.slide_role == "info"]
    if not densities:
        return "Mixed"
    high_count = sum(1 for density in densities if density == "high")
    low_count = sum(1 for density in densities if density == "low")
    if high_count >= 2:
        return "Dense"
    if low_count >= 4:
        return "Minimal"
    return "Mixed"


def _payload_image_count(payload: PluginRenderPayload) -> int:
    return sum(1 for slide in payload.slides if slide.image_slot != "none")


def _extract_slide_references(note: str | None, variant: StudioVariantRecord) -> list[StudioSlideReference]:
    if not note:
        return []

    references: list[StudioSlideReference] = []
    seen: set[int] = set()
    for match in SLIDE_REFERENCE_PATTERN.finditer(note):
        slide_number = int(match.group(1))
        if slide_number in seen:
            continue
        seen.add(slide_number)
        export_path = variant.export_paths[slide_number - 1] if len(variant.export_paths) >= slide_number else None
        export_url = variant.export_urls[slide_number - 1] if len(variant.export_urls) >= slide_number else None
        preview_path = variant.preview_image_paths[slide_number - 1] if len(variant.preview_image_paths) >= slide_number else None
        preview_url = variant.preview_image_urls[slide_number - 1] if len(variant.preview_image_urls) >= slide_number else None
        references.append(
            StudioSlideReference(
                token=f"/slide_{slide_number}",
                slide_number=slide_number,
                export_path=export_path,
                export_url=export_url,
                preview_path=preview_path,
                preview_url=preview_url,
            )
        )
    return references


def _strip_slide_reference_tokens(note: str | None) -> str | None:
    if not note:
        return None
    stripped = SLIDE_REFERENCE_PATTERN.sub(" ", note)
    cleaned = " ".join(stripped.strip().split())
    return cleaned or None


def _rejection_notes(previous_round: StudioRoundRecord | None) -> list[str]:
    if previous_round is None:
        return []
    notes: list[str] = []
    for variant in previous_round.variants:
        if variant.rejection_note:
            notes.append(variant.rejection_note)
    return notes


def _write_review_feedback_notes(round_record: StudioRoundRecord) -> None:
    if round_record.round_mode != "review":
        return

    REVIEW_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    winner = _winner_variant(round_record)
    losers = [variant for variant in round_record.variants if variant.variant_id != round_record.winner_variant_id]
    payload = {
        "round_id": round_record.round_id,
        "created_at": round_record.created_at,
        "round_number": round_record.round_number,
        "generated_brief": round_record.generated_brief,
        "winner": {
            "variant_id": winner.variant_id if winner else None,
            "ordinal": winner.ordinal if winner else None,
            "style": winner.requested_style_label if winner else None,
            "style_family": winner.style_family if winner else None,
            "copy_length": winner.copy_length_label if winner else None,
            "feedback": winner.winner_feedback if winner else None,
            "figma_url": winner.figma_url if winner else None,
            "figma_page_url": winner.figma_page_url if winner else None,
            "slide_references": [reference.model_dump(mode="json") for reference in winner.feedback_slide_references]
            if winner
            else [],
        },
        "losers": [
            {
                "variant_id": variant.variant_id,
                "ordinal": variant.ordinal,
                "style": variant.requested_style_label,
                "style_family": variant.style_family,
                "copy_length": variant.copy_length_label,
                "feedback": variant.rejection_note,
                "figma_url": variant.figma_url,
                "figma_page_url": variant.figma_page_url,
                "slide_references": [reference.model_dump(mode="json") for reference in variant.feedback_slide_references],
            }
            for variant in losers
        ],
    }

    json_path = REVIEW_NOTES_DIR / f"{round_record.round_id}.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    markdown_lines = [
        f"# Review Feedback {round_record.round_id}",
        "",
        f"- Round: {round_record.round_number}",
        f"- Brief: {round_record.generated_brief or 'n/a'}",
    ]

    if winner:
        markdown_lines.extend(
            [
                "",
                "## Winner",
                f"- Variant: {winner.ordinal}",
                f"- Style: {winner.requested_style_label}",
                f"- Copy: {winner.copy_length_label}",
                f"- Figma: {winner.figma_page_url or winner.figma_url or 'n/a'}",
                f"- Winner note: {winner.winner_feedback or 'n/a'}",
            ]
        )
        if winner.feedback_slide_references:
            markdown_lines.append("- Slide refs:")
            for reference in winner.feedback_slide_references:
                target = reference.export_url or reference.preview_url or reference.export_path or reference.preview_path or "n/a"
                markdown_lines.append(f"  - {reference.token}: {target}")

    markdown_lines.extend(["", "## Rejected Variants"])
    for variant in losers:
        markdown_lines.extend(
            [
                f"- Variant {variant.ordinal}: {variant.requested_style_label} / {variant.copy_length_label}",
                f"  Feedback: {variant.rejection_note or 'n/a'}",
            ]
        )
        if variant.feedback_slide_references:
            markdown_lines.append("  Slide refs:")
            for reference in variant.feedback_slide_references:
                target = reference.export_url or reference.preview_url or reference.export_path or reference.preview_path or "n/a"
                markdown_lines.append(f"    - {reference.token}: {target}")

    markdown_lines.extend(
        [
            "",
            "## Action Notes",
            f"- Keep/refine from winner: {winner.winner_feedback if winner and winner.winner_feedback else 'n/a'}",
            f"- Problems to avoid: {' | '.join(_rejection_notes(round_record)) if _rejection_notes(round_record) else 'n/a'}",
        ]
    )

    markdown_path = REVIEW_NOTES_DIR / f"{round_record.round_id}.md"
    markdown_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")
    round_record.review_note_json_path = str(json_path)
    round_record.review_note_markdown_path = str(markdown_path)


def _preview_url_from_path(path: str) -> str:
    resolved = Path(path).resolve()
    relative = resolved.relative_to(STUDIO_DIR.resolve())
    return f"{STUDIO_OUTPUT_URL_PREFIX}/{relative.as_posix()}"


def _tmp_url_from_path(path: str | None) -> str | None:
    if not path:
        return None
    resolved = Path(path).resolve()
    relative = resolved.relative_to((ROOT_DIR / ".tmp").resolve())
    return f"/tmp-output/{relative.as_posix()}"
