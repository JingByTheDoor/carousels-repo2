from __future__ import annotations

from base64 import b64decode, b64encode
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

from carousel_system.config import ROOT_DIR, Settings
from carousel_system.models import (
    CarouselOutput,
    ImageAsset,
    ImageStrategy,
    PerfectLibraryEntry,
    PerfectVisualTarget,
    PluginRenderPayload,
    RenderImageAssetSpec,
)
from carousel_system.perfect_library import get_perfect_library_entry


IMAGE_ASSETS_DIR = ROOT_DIR / ".tmp" / "image-assets"
IMAGE_FRIENDLY_FAMILIES = {
    "reference_alder_split_media",
    "reference_twitter_card_soft",
    "reference_light_grain_glow",
    "reference_device_mockup_gradient",
    "reference_placeholder_media_glow",
}
STANDARD_IMAGE_SLOT_BY_FAMILY = {
    "reference_alder_split_media": ("cover_media", "mask"),
    "reference_twitter_card_soft": ("cover_media", "card_embed"),
    "reference_light_grain_glow": ("cover_media", "blur_glow"),
    "reference_device_mockup_gradient": ("cover_media", "card_embed"),
    "reference_placeholder_media_glow": ("cover_media", "blur_glow"),
}
REVIEW_IMAGE_SLOT_BY_FAMILY = {
    "reference_alder_split_media": {
        1: ("cover_media", "mask"),
        2: ("body_media", "mask"),
        4: ("body_media", "mask"),
        6: ("body_media", "mask"),
    },
    "reference_light_grain_glow": {
        1: ("cover_media", "blur_glow"),
        2: ("body_media", "blur_glow"),
        4: ("body_media", "blur_glow"),
        6: ("body_media", "blur_glow"),
    },
    "reference_twitter_card_soft": {
        1: ("cover_media", "card_embed"),
        2: ("body_media", "card_embed"),
        4: ("body_media", "card_embed"),
        6: ("body_media", "card_embed"),
    },
    "reference_device_mockup_gradient": {
        1: ("cover_media", "card_embed"),
        2: ("body_media", "card_embed"),
        4: ("body_media", "card_embed"),
        6: ("body_media", "card_embed"),
    },
    "reference_placeholder_media_glow": {
        1: ("cover_media", "blur_glow"),
        2: ("body_media", "blur_glow"),
        4: ("body_media", "blur_glow"),
        6: ("body_media", "blur_glow"),
    },
}
LOCALE_BY_LANGUAGE = {
    "ru": "ru-RU",
    "en": "en-US",
}
REVIEW_VISUAL_SUFFIX_BY_SLIDE = {
    1: "teacher portrait classroom",
    2: "lesson planning desk materials",
    4: "students classroom activity",
    6: "worksheets flashcards materials",
}
DEFAULT_VISUAL_SUFFIX_BY_SLIDE = {
    1: "portrait",
    2: "workspace",
    4: "collaboration",
    6: "materials closeup",
}
PEXELS_QUERY_VARIANT_LIMIT = 4
SEMANTIC_CANDIDATE_LIMIT = 10


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


@dataclass(frozen=True)
class ImageRequest:
    slide_number: int
    role: str
    slot: str
    treatment: str
    query: str
    reason: str
    headline: str = ""
    body: str = ""
    topic: str = ""
    visual_hint: str = ""
    focus: str = ""


@dataclass(frozen=True)
class PexelsCandidate:
    photo_id: int
    width: int
    height: int
    alt_text: str
    photographer: str
    page_url: str | None
    download_url: str
    search_query: str = ""


class PexelsQueryPlan(BaseModel):
    slide_number: int = Field(ge=1, le=7)
    visual_intent: str = ""
    primary_subject: str = ""
    setting: str = ""
    action: str = ""
    avoid: list[str] = Field(default_factory=list)
    queries: list[str] = Field(default_factory=list)

    @field_validator("visual_intent", "primary_subject", "setting", "action", mode="before")
    @classmethod
    def _normalize_text_fields(cls, value: str | None) -> str:
        return _normalize_text(value)

    @field_validator("avoid", "queries", mode="before")
    @classmethod
    def _normalize_text_lists(cls, value: list[str] | str | None) -> list[str]:
        if value is None:
            return []
        items = [value] if isinstance(value, str) else value
        normalized: list[str] = []
        for item in items:
            cleaned = _normalize_text(str(item))
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized


class PexelsQueryPlanBatch(BaseModel):
    plans: list[PexelsQueryPlan] = Field(default_factory=list)


class PexelsSemanticRanking(BaseModel):
    selected_photo_id: int | None = None
    ordered_photo_ids: list[int] = Field(default_factory=list)
    rejected_photo_ids: list[int] = Field(default_factory=list)
    reason: str | None = None

    @field_validator("ordered_photo_ids", "rejected_photo_ids", mode="before")
    @classmethod
    def _normalize_photo_lists(cls, value: list[int] | int | None) -> list[int]:
        if value is None:
            return []
        items = [value] if isinstance(value, int) else value
        normalized: list[int] = []
        for item in items:
            try:
                photo_id = int(item)
            except (TypeError, ValueError):
                continue
            if photo_id > 0 and photo_id not in normalized:
                normalized.append(photo_id)
        return normalized

    @field_validator("reason", mode="before")
    @classmethod
    def _normalize_reason(cls, value: str | None) -> str | None:
        cleaned = _normalize_text(value)
        return cleaned or None


def resolve_image_assets(settings: Settings, record: CarouselOutput, payload: PluginRenderPayload) -> None:
    library_entry = _resolve_library_entry(record)
    _apply_slot_defaults(record, payload, library_entry=library_entry)
    strategy = _resolve_image_strategy(settings, record, payload, library_entry=library_entry)
    record.image_strategy = strategy
    record.image_assets = []
    payload.image_strategy.mode = strategy.mode
    payload.image_strategy.provider = strategy.provider

    if strategy.mode == "none":
        _write_image_manifest(record)
        return

    if strategy.provider == "pexels" and not settings.pexels_api_key:
        record.image_strategy.reason = "PEXELS_API_KEY is not configured, so stock images were skipped."
        _write_image_manifest(record)
        return

    if strategy.provider == "openai_gpt_image" and not settings.openai_api_key:
        record.image_strategy.reason = "OPENAI_API_KEY is not configured, so AI image generation was skipped."
        _write_image_manifest(record)
        return

    requests = _build_image_requests(record, payload, library_entry=library_entry)
    if not requests:
        record.image_strategy.reason = "No image slots are active for the selected style family."
        _write_image_manifest(record)
        return

    query_plans = _plan_pexels_queries(settings, record, requests) if strategy.provider == "pexels" else {}
    assets: list[ImageAsset] = []
    used_photo_ids: set[int] = set()
    used_alt_signatures: set[str] = set()
    for image_request in requests:
        asset = None
        if strategy.provider == "pexels":
            asset = _find_and_cache_pexels_asset(
                settings,
                record,
                image_request,
                used_photo_ids=used_photo_ids,
                used_alt_signatures=used_alt_signatures,
                query_plan=query_plans.get(image_request.slide_number),
            )
        if asset is None and strategy.mode in {"ai", "hybrid"} and record.normalized_input.allow_ai_fallback:
            asset = _generate_ai_asset(settings, record, image_request)
        if asset:
            assets.append(asset)

    if assets:
        record.image_assets = assets
        _attach_assets_to_payload(payload, assets)
        provider_labels = sorted({asset.provider for asset in assets})
        provider_text = ", ".join(provider_labels)
        record.image_strategy.reason = (
            f"Attached {len(assets)} image asset"
            f"{'' if len(assets) == 1 else 's'} via Pexels for {payload.style_family}."
        )
        if provider_text:
            record.image_strategy.reason = (
                f"Attached {len(assets)} image asset"
                f"{'' if len(assets) == 1 else 's'} via {provider_text} for {payload.style_family}."
            )
    else:
        record.image_strategy.reason = "No acceptable image candidate was found for the active image slots."

    _write_image_manifest(record)


def _resolve_library_entry(record: CarouselOutput) -> PerfectLibraryEntry | None:
    if record.normalized_input.generation_mode != "production":
        return None
    return get_perfect_library_entry(record.normalized_input.library_item_id or "")


def _apply_slot_defaults(
    record: CarouselOutput,
    payload: PluginRenderPayload,
    *,
    library_entry: PerfectLibraryEntry | None = None,
) -> None:
    for slide in payload.slides:
        slide.image_slot = "none"
        slide.image_required = False
        slide.image_treatment = "none"
        slide.image_asset = None

    visual_recipe = library_entry.visual_recipe if library_entry else None
    if record.normalized_input.generation_mode == "production" and visual_recipe and visual_recipe.targets:
        slide_plan = {
            target.slide_number: (target.slot, target.treatment)
            for target in visual_recipe.targets
            if target.slot != "none"
        }
        effective_mode = record.normalized_input.image_mode
        if effective_mode == "auto":
            effective_mode = visual_recipe.source_mode
        require_image = effective_mode in {"auto", "stock", "ai", "hybrid"}
        for slide in payload.slides:
            slot, treatment = slide_plan.get(slide.slide_number, ("none", "none"))
            if slot == "none":
                continue
            slide.image_slot = slot
            slide.image_required = require_image
            slide.image_treatment = treatment
        return

    if payload.style_family not in IMAGE_FRIENDLY_FAMILIES:
        return

    if record.normalized_input.generation_mode == "review":
        slide_plan = REVIEW_IMAGE_SLOT_BY_FAMILY.get(payload.style_family, {})
    else:
        slot, treatment = STANDARD_IMAGE_SLOT_BY_FAMILY.get(payload.style_family, ("none", "none"))
        slide_plan = {1: (slot, treatment)}

    if not slide_plan:
        return

    require_image = record.normalized_input.image_mode in {"stock", "ai", "hybrid"}
    for slide in payload.slides:
        slot, treatment = slide_plan.get(slide.slide_number, ("none", "none"))
        if slot == "none":
            continue
        slide.image_slot = slot
        slide.image_required = require_image
        slide.image_treatment = treatment


def _resolve_image_strategy(
    settings: Settings,
    record: CarouselOutput,
    payload: PluginRenderPayload,
    *,
    library_entry: PerfectLibraryEntry | None = None,
) -> ImageStrategy:
    visual_recipe = library_entry.visual_recipe if library_entry else None
    requested_mode = record.normalized_input.image_mode
    if record.normalized_input.generation_mode == "production" and requested_mode == "auto" and visual_recipe:
        requested_mode = visual_recipe.source_mode
    preferred_provider = record.normalized_input.image_source_preference
    family_supports_images = payload.style_family in IMAGE_FRIENDLY_FAMILIES or bool(visual_recipe and visual_recipe.targets)

    if requested_mode == "none":
        return ImageStrategy(mode="none", provider=None, reason="User explicitly disabled images.")

    if not family_supports_images:
        return ImageStrategy(
            mode="none",
            provider=None,
            reason=f"{payload.style_family} is currently treated as a text-led family.",
        )

    if requested_mode == "ai":
        return ImageStrategy(
            mode="ai",
            provider="openai_gpt_image",
            reason="AI generation was requested, but only stock acquisition is implemented in this pass.",
        )

    if requested_mode == "stock":
        return ImageStrategy(mode="stock", provider="pexels", reason="Stock-only mode.")

    if requested_mode == "hybrid":
        if not settings.pexels_api_key and settings.openai_api_key:
            return ImageStrategy(
                mode="ai",
                provider="openai_gpt_image",
                reason="Hybrid requested. Pexels is unavailable, so AI image generation is active.",
            )
        provider = "pexels"
        reason = "Hybrid requested. Stock-first is implemented now; AI fallback will come later."
        if preferred_provider == "openai_gpt_image":
            reason = "Hybrid requested. AI fallback is not implemented yet, so stock-first remains active."
        return ImageStrategy(mode="hybrid", provider=provider, reason=reason)

    if requested_mode == "auto":
        if record.normalized_input.generation_mode == "review":
            if settings.pexels_api_key:
                return ImageStrategy(
                    mode="hybrid",
                    provider="pexels",
                    reason="Review mode uses stock-first images with AI fallback when needed.",
                )
            if settings.openai_api_key:
                return ImageStrategy(
                    mode="ai",
                    provider="openai_gpt_image",
                    reason="Review mode fell back to AI because Pexels is unavailable.",
                )
            return ImageStrategy(
                mode="none",
                provider=None,
                reason="Review mode needs images, but neither Pexels nor OpenAI is configured.",
            )
        if not settings.pexels_api_key:
            if settings.openai_api_key and record.normalized_input.generation_mode == "production":
                return ImageStrategy(
                    mode="ai",
                    provider="openai_gpt_image",
                    reason="Auto image mode fell back to AI because Pexels is unavailable for this production template.",
                )
            return ImageStrategy(
                mode="none",
                provider=None,
                reason="Auto image mode chose stock-first, but PEXELS_API_KEY is missing.",
            )
        return ImageStrategy(
            mode="stock",
            provider="pexels",
            reason="Auto image mode chose stock-first for an image-friendly family.",
        )

    return ImageStrategy(mode="none", provider=None, reason="No image strategy matched.")


def _build_image_requests(
    record: CarouselOutput,
    payload: PluginRenderPayload,
    *,
    library_entry: PerfectLibraryEntry | None = None,
) -> list[ImageRequest]:
    requests: list[ImageRequest] = []
    visual_targets = {
        target.slide_number: target
        for target in (library_entry.visual_recipe.targets if library_entry and library_entry.visual_recipe else [])
    }
    for slide in payload.slides:
        if slide.image_slot == "none":
            continue
        visual_target = visual_targets.get(slide.slide_number)
        content_slide = next((item for item in record.content_plan if item.slide_number == slide.slide_number), None)
        visual_hint = _visual_suffix(record, slide.slide_number, library_entry=library_entry, visual_target=visual_target)
        focus = _resolve_image_focus(record, library_entry=library_entry)
        query = _build_query(record, slide.slide_number, library_entry=library_entry, visual_target=visual_target)
        reason = (
            f"{library_entry.label} requires a resolved production visual."
            if library_entry and visual_target
            else f"{payload.style_family} exposes a hook-media slot."
        )
        requests.append(
            ImageRequest(
                slide_number=slide.slide_number,
                role=slide.slide_role,
                slot=slide.image_slot,
                treatment=slide.image_treatment,
                query=query,
                reason=reason,
                headline=content_slide.headline if content_slide else "",
                body=(content_slide.body or "") if content_slide else "",
                topic=record.normalized_input.topic or "",
                visual_hint=visual_hint,
                focus=focus,
            )
        )
    return requests


def _resolve_image_focus(
    record: CarouselOutput,
    *,
    library_entry: PerfectLibraryEntry | None = None,
) -> str:
    if library_entry and library_entry.visual_recipe:
        return library_entry.visual_recipe.default_focus
    return record.normalized_input.image_focus


def _build_query(
    record: CarouselOutput,
    slide_number: int,
    *,
    library_entry: PerfectLibraryEntry | None = None,
    visual_target: PerfectVisualTarget | None = None,
) -> str:
    slide = next((item for item in record.content_plan if item.slide_number == slide_number), None)
    topic = record.normalized_input.topic or ""
    headline = slide.headline if slide else ""
    body = slide.body if slide else ""
    role = slide.slide_role if slide else "info"
    source = " ".join(part for part in [topic, headline, body] if part) or record.content_plan[0].headline
    keywords = _compact_keywords(source)
    focus = _resolve_image_focus(record, library_entry=library_entry)
    niche = "english teacher materials" if record.normalized_input.generation_mode == "review" else "education"
    visual_suffix = _visual_suffix(record, slide_number, library_entry=library_entry, visual_target=visual_target)
    base = f"{keywords} {role} {niche} {visual_suffix}".strip()
    if focus == "brand_safe":
        return f"{base} professional clean"
    if focus == "literal":
        return f"{base} realistic"
    if focus == "abstract":
        return f"{base} conceptual"
    return f"{base} editorial"


def _visual_suffix(
    record: CarouselOutput,
    slide_number: int,
    *,
    library_entry: PerfectLibraryEntry | None = None,
    visual_target: PerfectVisualTarget | None = None,
) -> str:
    if visual_target is not None:
        suffix = visual_target.query_suffix or ""
        if visual_target.asset_kind != "photo":
            suffix = f"{visual_target.asset_kind} {suffix}".strip()
        if suffix:
            return suffix
    if library_entry and library_entry.visual_recipe and library_entry.visual_recipe.default_query_suffix:
        return library_entry.visual_recipe.default_query_suffix
    if record.normalized_input.generation_mode == "review":
        return REVIEW_VISUAL_SUFFIX_BY_SLIDE.get(slide_number, "teaching materials")
    return DEFAULT_VISUAL_SUFFIX_BY_SLIDE.get(slide_number, "editorial scene")


def _compact_keywords(text: str, *, max_words: int = 6) -> str:
    tokens = re.findall(r"[A-Za-z\u0400-\u04FF0-9]+", text.lower())
    if not tokens:
        return "professional education"
    return " ".join(tokens[:max_words])


def _normalize_query_text(text: str | None) -> str:
    cleaned = _normalize_text(text)
    if not cleaned:
        return ""
    cleaned = re.sub(r"[\.,;:|/]+", " ", cleaned)
    return _normalize_text(cleaned)


def _openai_client(settings: Settings) -> OpenAI | None:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def _build_pexels_query_planning_prompt(record: CarouselOutput, requests: list[ImageRequest]) -> str:
    header = [
        f"carousel topic: {_normalize_text(record.normalized_input.topic) or 'n/a'}",
        f"carousel language: {record.language or record.normalized_input.language or 'unknown'}",
        f"generation mode: {record.normalized_input.generation_mode}",
        f"style family: {record.style_family or 'unknown'}",
    ]
    slides: list[str] = []
    for request in requests:
        slides.extend(
            [
                "",
                f"slide_number: {request.slide_number}",
                f"role: {request.role}",
                f"slot: {request.slot}",
                f"treatment: {request.treatment}",
                f"headline: {request.headline or 'n/a'}",
                f"body: {request.body or 'n/a'}",
                f"visual_hint: {request.visual_hint or 'n/a'}",
                f"focus: {request.focus or 'n/a'}",
                f"reason: {request.reason}",
                f"fallback_query: {request.query}",
            ]
        )
    return "\n".join(header + slides)


def _plan_pexels_queries(
    settings: Settings,
    record: CarouselOutput,
    requests: list[ImageRequest],
) -> dict[int, PexelsQueryPlan]:
    client = _openai_client(settings)
    if client is None or not requests:
        return {}

    system_prompt = """You write concise, precise Pexels stock-photo search queries for Instagram carousel slides.

Return a JSON object that matches the supplied schema.

Rules:
- Queries must be natural English search phrases for Pexels, even if the slide copy is in another language.
- Each query should be concrete and visual, usually 4 to 10 words.
- Prioritize scenes that literally support the slide meaning.
- Avoid generic business buzzwords, landmarks, castles, tourism, flags, random city scenes, and weak symbolic matches unless the slide explicitly asks for them.
- Prefer one clear subject, business-safe educational settings, and compositions that can crop vertically with text overlays.
- Give each slide 3 to 4 meaningfully different query variants, not trivial rewordings.
- Keep different slides visually varied so the carousel does not repeat the same stock setup."""
    try:
        completion = client.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": _build_pexels_query_planning_prompt(record, requests)},
            ],
            response_format=PexelsQueryPlanBatch,
        )
        message = completion.choices[0].message
        parsed = getattr(message, "parsed", None)
        if not parsed:
            return {}
    except Exception:
        return {}

    plan_map: dict[int, PexelsQueryPlan] = {}
    parsed_by_slide = {plan.slide_number: plan for plan in parsed.plans}
    for request in requests:
        parsed_plan = parsed_by_slide.get(request.slide_number)
        queries: list[str] = []
        if parsed_plan:
            for query in parsed_plan.queries:
                normalized = _normalize_query_text(query)
                if normalized and normalized not in queries:
                    queries.append(normalized)
        fallback_query = _normalize_query_text(request.query)
        if fallback_query and fallback_query not in queries:
            queries.append(fallback_query)
        if not queries:
            continue
        if parsed_plan is None:
            plan_map[request.slide_number] = PexelsQueryPlan(
                slide_number=request.slide_number,
                visual_intent=request.reason,
                primary_subject=request.visual_hint,
                setting=request.focus,
                action=request.role,
                avoid=[],
                queries=queries[:PEXELS_QUERY_VARIANT_LIMIT],
            )
            continue
        plan_map[request.slide_number] = PexelsQueryPlan(
            slide_number=request.slide_number,
            visual_intent=parsed_plan.visual_intent,
            primary_subject=parsed_plan.primary_subject,
            setting=parsed_plan.setting,
            action=parsed_plan.action,
            avoid=parsed_plan.avoid,
            queries=queries[:PEXELS_QUERY_VARIANT_LIMIT],
        )
    return plan_map


def _build_pexels_candidate_ranking_prompt(
    record: CarouselOutput,
    image_request: ImageRequest,
    candidates: list[PexelsCandidate],
    *,
    query_plan: PexelsQueryPlan | None = None,
) -> str:
    lines = [
        f"topic: {_normalize_text(image_request.topic) or _normalize_text(record.normalized_input.topic) or 'n/a'}",
        f"language: {record.language or record.normalized_input.language or 'unknown'}",
        f"slide_number: {image_request.slide_number}",
        f"role: {image_request.role}",
        f"headline: {image_request.headline or 'n/a'}",
        f"body: {image_request.body or 'n/a'}",
        f"visual_hint: {image_request.visual_hint or 'n/a'}",
        f"fallback_query: {image_request.query}",
        f"planned_intent: {query_plan.visual_intent if query_plan else 'n/a'}",
        f"planned_subject: {query_plan.primary_subject if query_plan else 'n/a'}",
        f"planned_setting: {query_plan.setting if query_plan else 'n/a'}",
        f"planned_action: {query_plan.action if query_plan else 'n/a'}",
        "avoid: " + (", ".join(query_plan.avoid) if query_plan and query_plan.avoid else "n/a"),
        "",
        "candidates:",
    ]
    for candidate in candidates:
        ratio = round(candidate.height / max(candidate.width, 1), 2) if candidate.width and candidate.height else 0
        lines.extend(
            [
                f"- photo_id: {candidate.photo_id}",
                f"  query: {candidate.search_query or image_request.query}",
                f"  alt_text: {candidate.alt_text or 'n/a'}",
                f"  photographer: {candidate.photographer or 'n/a'}",
                f"  size: {candidate.width}x{candidate.height}",
                f"  portrait_ratio: {ratio}",
            ]
        )
    return "\n".join(lines)


def _semantic_rank_pexels_candidates(
    settings: Settings,
    record: CarouselOutput,
    image_request: ImageRequest,
    candidates: list[PexelsCandidate],
    *,
    query_plan: PexelsQueryPlan | None = None,
) -> PexelsSemanticRanking | None:
    client = _openai_client(settings)
    if client is None or not candidates:
        return None

    system_prompt = """You are choosing the best Pexels photo for one educational Instagram carousel slide.

Return a JSON object that matches the supplied schema.

Rules:
- Favor candidates that literally depict the slide meaning, not candidates that only share one keyword.
- Reject tourist landmarks, castles, flags, generic office meetings, handshake-business photos, vague success imagery, and random books or objects unless the slide explicitly asks for them.
- Prefer clean, realistic, business-safe images with one clear subject and a usable portrait crop.
- If no candidate truly fits, return no selected photo and an empty ordered list."""
    candidate_subset = candidates[:SEMANTIC_CANDIDATE_LIMIT]
    valid_ids = {candidate.photo_id for candidate in candidate_subset}
    try:
        completion = client.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": _build_pexels_candidate_ranking_prompt(
                        record,
                        image_request,
                        candidate_subset,
                        query_plan=query_plan,
                    ),
                },
            ],
            response_format=PexelsSemanticRanking,
        )
        message = completion.choices[0].message
        parsed = getattr(message, "parsed", None)
        if not parsed:
            return None
    except Exception:
        return None

    ordered_photo_ids = [photo_id for photo_id in parsed.ordered_photo_ids if photo_id in valid_ids]
    if parsed.selected_photo_id in valid_ids and parsed.selected_photo_id not in ordered_photo_ids:
        ordered_photo_ids.insert(0, parsed.selected_photo_id)
    rejected_photo_ids = [
        photo_id
        for photo_id in parsed.rejected_photo_ids
        if photo_id in valid_ids and photo_id not in ordered_photo_ids
    ]
    return PexelsSemanticRanking(
        selected_photo_id=ordered_photo_ids[0] if ordered_photo_ids else None,
        ordered_photo_ids=ordered_photo_ids,
        rejected_photo_ids=rejected_photo_ids,
        reason=parsed.reason,
    )


def _find_and_cache_pexels_asset(
    settings: Settings,
    record: CarouselOutput,
    image_request: ImageRequest,
    *,
    used_photo_ids: set[int],
    used_alt_signatures: set[str],
    query_plan: PexelsQueryPlan | None = None,
) -> ImageAsset | None:
    queries = [
        _normalize_query_text(query)
        for query in (query_plan.queries if query_plan and query_plan.queries else [image_request.query])
    ]
    queries = [query for query in queries if query]
    if not queries:
        return None

    candidate_map: dict[int, PexelsCandidate] = {}
    for query in queries:
        candidates = _search_pexels_candidates(
            settings,
            query,
            language=record.language or record.normalized_input.language or "en",
        )
        for candidate in candidates:
            incumbent = candidate_map.get(candidate.photo_id)
            if incumbent is None:
                candidate_map[candidate.photo_id] = candidate
                continue
            if _score_candidate(candidate, candidate.search_query or query) > _score_candidate(
                incumbent,
                incumbent.search_query or image_request.query,
            ):
                candidate_map[candidate.photo_id] = candidate
    if not candidate_map:
        return None

    ranked = sorted(
        candidate_map.values(),
        key=lambda candidate: _score_candidate(candidate, candidate.search_query or image_request.query),
        reverse=True,
    )
    semantic_ranking = _semantic_rank_pexels_candidates(
        settings,
        record,
        image_request,
        ranked,
        query_plan=query_plan,
    )
    if semantic_ranking is not None:
        candidate_lookup = {candidate.photo_id: candidate for candidate in ranked}
        ranked = [candidate_lookup[photo_id] for photo_id in semantic_ranking.ordered_photo_ids if photo_id in candidate_lookup]
        if not ranked:
            return None

    best = None
    for candidate in ranked:
        if candidate.photo_id in used_photo_ids:
            continue
        alt_signature = _compact_keywords(candidate.alt_text, max_words=8)
        if alt_signature and alt_signature in used_alt_signatures:
            continue
        best = candidate
        break
    if best is None:
        for candidate in ranked:
            if candidate.photo_id not in used_photo_ids:
                best = candidate
                break
    if best is None:
        return None

    used_photo_ids.add(best.photo_id)
    alt_signature = _compact_keywords(best.alt_text, max_words=8)
    if alt_signature:
        used_alt_signatures.add(alt_signature)

    asset_dir = IMAGE_ASSETS_DIR / record.job_id
    asset_dir.mkdir(parents=True, exist_ok=True)
    extension = _detect_extension(best.download_url)
    asset_path = asset_dir / f"slide-{image_request.slide_number:02d}-pexels-{best.photo_id}{extension}"
    if not asset_path.exists():
        _download_binary(settings, best.download_url, asset_path)

    return ImageAsset(
        slide_number=image_request.slide_number,
        role=image_request.role,
        source_mode="stock",
        provider="pexels",
        query_or_prompt=best.search_query or image_request.query,
        original_url=best.download_url,
        local_path=str(asset_path),
        credit=f"Photo by {best.photographer} on Pexels",
        width=best.width,
        height=best.height,
        alt_text=best.alt_text,
    )


def _generate_ai_asset(
    settings: Settings,
    record: CarouselOutput,
    image_request: ImageRequest,
) -> ImageAsset | None:
    if not settings.openai_api_key:
        return None

    prompt = (
        f"Create a vertical editorial image for an Instagram carousel slide about {image_request.query}. "
        "Make it useful for English teachers and teaching materials. "
        "Keep it clean, realistic, brand-safe, and suitable for an educational business account. "
        "Avoid text, watermarks, logos, or UI chrome."
    )
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1536",
        quality="medium",
        output_format="png",
    )
    if not response.data:
        return None

    image = response.data[0]
    if not image.b64_json:
        return None

    asset_dir = IMAGE_ASSETS_DIR / record.job_id
    asset_dir.mkdir(parents=True, exist_ok=True)
    asset_path = asset_dir / f"slide-{image_request.slide_number:02d}-openai.png"
    asset_path.write_bytes(b64decode(image.b64_json))
    revised_prompt = image.revised_prompt or prompt
    return ImageAsset(
        slide_number=image_request.slide_number,
        role=image_request.role,
        source_mode="ai",
        provider="openai_gpt_image",
        query_or_prompt=revised_prompt,
        original_url=None,
        local_path=str(asset_path),
        credit="Generated with OpenAI",
        alt_text=revised_prompt,
    )
def _search_pexels_candidates(settings: Settings, query: str, *, language: str) -> list[PexelsCandidate]:
    locale = "en-US" if re.search(r"[A-Za-z]", query) and not re.search(r"[\u0400-\u04FF]", query) else LOCALE_BY_LANGUAGE.get(language.lower(), "en-US")
    params = urlencode(
        {
            "query": query,
            "per_page": 8,
            "orientation": "portrait",
            "page": 1,
            "locale": locale,
        }
    )
    url = f"https://api.pexels.com/v1/search?{params}"
    response = _read_json(settings, url)
    photos = response.get("photos", [])
    candidates: list[PexelsCandidate] = []
    for photo in photos:
        src = photo.get("src") or {}
        download_url = src.get("portrait") or src.get("large2x") or src.get("large") or src.get("original")
        if not download_url:
            continue
        candidates.append(
            PexelsCandidate(
                photo_id=int(photo.get("id", 0)),
                width=int(photo.get("width", 0) or 0),
                height=int(photo.get("height", 0) or 0),
                alt_text=(photo.get("alt") or "").strip(),
                photographer=(photo.get("photographer") or "Unknown").strip(),
                page_url=(photo.get("url") or "").strip() or None,
                download_url=download_url,
                search_query=query,
            )
        )
    return candidates


def _score_candidate(candidate: PexelsCandidate, query: str) -> float:
    score = 0.0
    if candidate.height >= candidate.width:
        score += 4.0
    if candidate.width and candidate.height:
        score += min(candidate.height / max(candidate.width, 1), 2.0)
    alt_words = set(_compact_keywords(candidate.alt_text, max_words=12).split())
    query_words = set(_compact_keywords(query, max_words=12).split())
    score += float(len(alt_words & query_words)) * 1.5
    if candidate.alt_text:
        score += 1.0
    return score


def _read_json(settings: Settings, url: str) -> dict:
    headers = {"User-Agent": "carousel-automation/0.1"}
    if settings.pexels_api_key:
        headers["Authorization"] = settings.pexels_api_key
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Pexels API error {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Pexels API: {exc.reason}") from exc


def _download_binary(settings: Settings, url: str, destination: Path) -> None:
    headers = {"User-Agent": "carousel-automation/0.1"}
    if settings.pexels_api_key:
        headers["Authorization"] = settings.pexels_api_key
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            destination.write_bytes(response.read())
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Pexels download error {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not download stock image: {exc.reason}") from exc


def _detect_extension(url: str) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return suffix
    query = parse_qs(parsed.query)
    if "fm" in query:
        fmt = query["fm"][0].lower()
        if fmt in {"jpg", "jpeg", "png", "webp"}:
            return f".{fmt}"
    return ".jpg"


def _attach_assets_to_payload(payload: PluginRenderPayload, assets: list[ImageAsset]) -> None:
    asset_map = {asset.slide_number: asset for asset in assets}
    for slide in payload.slides:
        asset = asset_map.get(slide.slide_number)
        if not asset:
            continue
        data_base64 = None
        if asset.provider == "openai_gpt_image" and asset.local_path:
            data_base64 = b64encode(Path(asset.local_path).read_bytes()).decode("utf-8")
        slide.image_asset = RenderImageAssetSpec(
            provider=asset.provider,
            local_path=asset.local_path,
            url=asset.original_url,
            credit=asset.credit,
            data_base64=data_base64,
        )


def _write_image_manifest(record: CarouselOutput) -> None:
    manifest_path = IMAGE_ASSETS_DIR / record.job_id / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "job_id": record.job_id,
                "image_strategy": record.image_strategy.model_dump(mode="json"),
                "image_assets": [asset.model_dump(mode="json") for asset in record.image_assets],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
