from __future__ import annotations

import re
from pathlib import Path

from carousel_system.models import (
    CarouselOutput,
    LayoutPreference,
    PluginRenderPayload,
    RenderArtifact,
    RenderSlideSpec,
    SafeAreaProfile,
    StyleTokens,
    TextDensity,
    TypographyTokens,
    VisualPriority,
)
from carousel_system.style_library import select_style_recipe


EN_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "your",
    "into",
    "from",
    "will",
    "about",
    "when",
    "what",
    "have",
}
RU_STOPWORDS = {
    "это",
    "как",
    "что",
    "для",
    "или",
    "при",
    "она",
    "они",
    "если",
    "чтобы",
    "когда",
    "только",
    "потому",
    "который",
    "которые",
    "кто",
    "тех",
    "про",
}


def infer_language(record: CarouselOutput) -> str:
    explicit = record.normalized_input.language
    if explicit:
        return explicit

    samples = [
        record.normalized_input.topic,
        record.normalized_input.script,
        record.normalized_input.cta_text,
    ]
    for slide in record.content_plan:
        samples.append(slide.headline)
        samples.append(slide.body)

    text = " ".join(part for part in samples if part)
    if any("\u0400" <= character <= "\u04FF" for character in text):
        return "ru"
    if any(character.isalpha() and "a" <= character.lower() <= "z" for character in text):
        return "en"
    return "unknown"


def build_render_artifact(output_path: Path, payload: PluginRenderPayload) -> RenderArtifact:
    return RenderArtifact(
        path=str(output_path),
        page_name=payload.page_name,
        style_family=payload.style_family,
        style_recipe=payload.style_recipe,
        language=payload.language,
    )


def build_plugin_render_payload(
    record: CarouselOutput,
    *,
    source_artifact_path: Path,
) -> PluginRenderPayload:
    language = infer_language(record)
    recipe = select_style_recipe(record, language)
    slides: list[RenderSlideSpec] = []

    for slide in record.content_plan:
        slides.append(_build_render_slide(record, slide, language, recipe.style_recipe))

    return PluginRenderPayload(
        job_id=record.job_id,
        page_name=f"{record.job_id}-plugin-render",
        prompt_version=record.prompt_version,
        language=language,
        style_family=recipe.style_family,
        style_recipe=recipe.style_recipe,
        source_artifact_path=str(source_artifact_path),
        reference_file_key=record.normalized_input.reference_file_key,
        reference_node_ids=list(recipe.reference_node_ids),
        style_tokens=recipe.style_tokens,
        typography=recipe.typography,
        slides=slides,
    )


def write_plugin_render_payload(output_path: Path, payload: PluginRenderPayload) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    return output_path


def _build_render_slide(record: CarouselOutput, slide, language: str, style_recipe: str) -> RenderSlideSpec:
    if slide.slide_role == "hook":
        headline_short = _shorten_headline(slide.headline, language, hard_limit=42)
        display = headline_short if len(slide.headline) > 42 else slide.headline
        safe_area = "cover_balanced" if style_recipe in {"typography_signal_glow_v1", "cp_split_minimal_statement_v1"} else "cover_tall_text"
        accent_motif = {
            "typography_signal_glow_v1": "signal_footer_lines",
            "cp_split_minimal_statement_v1": "device_card_mock",
        }.get(style_recipe, "geometric_cluster")
        return RenderSlideSpec(
            slide_number=slide.slide_number,
            slide_role=slide.slide_role,
            design_role=slide.design_role,
            layout_variant="cover_black_hero",
            layout_preference="hero",
            text_align="left",
            headline=slide.headline,
            headline_short=headline_short,
            headline_display=display,
            body=slide.body,
            body_short=None,
            body_display=None,
            supporting_text=None,
            button_label=None,
            text_density=_hook_density(slide.headline),
            visual_priority="headline",
            safe_area_profile=safe_area,
            max_headline_lines=5 if style_recipe == "cp_split_minimal_statement_v1" else 6,
            max_body_lines=0,
            can_truncate_body=False,
            emphasis_words=_extract_emphasis_words(slide.headline, language),
            accent_motif=accent_motif,
        )

    if slide.slide_role == "cta":
        cta_source = slide.body or record.normalized_input.cta_text or ""
        headline_short = _shorten_headline(slide.headline, language, hard_limit=38)
        body_display, supporting_text = _build_cta_copy_segments(cta_source, slide.headline, language)
        return RenderSlideSpec(
            slide_number=slide.slide_number,
            slide_role=slide.slide_role,
            design_role=slide.design_role,
            layout_variant="cta_dark_glow",
            layout_preference="cta",
            text_align="center",
            headline=slide.headline,
            headline_short=headline_short,
            headline_display=headline_short or slide.headline,
            body=cta_source or None,
            body_short=body_display,
            body_display=body_display,
            supporting_text=supporting_text,
            button_label=_build_cta_button_label(language),
            text_density=_cta_density(slide.headline, cta_source),
            visual_priority="cta",
            safe_area_profile="cta_center_stack",
            max_headline_lines=4,
            max_body_lines=4,
            can_truncate_body=True,
            emphasis_words=_extract_emphasis_words(slide.headline, language),
            accent_motif="cta_signal_lines" if style_recipe != "cp_split_minimal_statement_v1" else "device_card_mock",
        )

    body_text = slide.body or ""
    layout_variant = _body_layout_variant(slide.slide_number, body_text, style_recipe)
    layout_preference = _layout_preference_for_variant(layout_variant)
    text_density = _body_density(slide.headline, body_text)
    headline_short = _shorten_headline(slide.headline, language, hard_limit=30)
    body_short = _shorten_body(body_text, language, hard_limit=_body_hard_limit(layout_variant, text_density))
    headline_display = (
        headline_short
        if text_density == "high" or layout_variant == "body_mask_band_left"
        else slide.headline
    )
    body_display = body_short if text_density != "low" else body_text

    return RenderSlideSpec(
        slide_number=slide.slide_number,
        slide_role=slide.slide_role,
        design_role=slide.design_role,
        layout_variant=layout_variant,
        layout_preference=layout_preference,
        text_align="left",
        headline=slide.headline,
        headline_short=headline_short,
        headline_display=headline_display,
        body=body_text,
        body_short=body_short,
        body_display=body_display,
        supporting_text=None,
        button_label=None,
        text_density=text_density,
        visual_priority="headline" if text_density != "high" else "body",
        safe_area_profile=_safe_area_profile(layout_variant),
        max_headline_lines=3,
        max_body_lines=_max_body_lines(layout_variant, text_density),
        can_truncate_body=True,
        emphasis_words=_extract_emphasis_words(f"{slide.headline} {body_text}", language),
        accent_motif=_body_accent_motif(slide.slide_number, body_text, style_recipe),
    )


def _hook_density(headline: str) -> TextDensity:
    if len(headline) > 42:
        return "high"
    if len(headline) > 28:
        return "medium"
    return "low"


def _cta_density(headline: str, body: str) -> TextDensity:
    combined = len(headline) + len(body)
    if combined > 120:
        return "high"
    if combined > 72:
        return "medium"
    return "low"


def _body_density(headline: str, body: str) -> TextDensity:
    combined = len(headline) + len(body)
    if combined > 135 or len(body) > 100 or len(headline) > 32:
        return "high"
    if combined > 88 or len(body) > 65 or len(headline) > 24:
        return "medium"
    return "low"


def _layout_preference_for_variant(layout_variant: str) -> LayoutPreference:
    mapping: dict[str, LayoutPreference] = {
        "cover_black_hero": "hero",
        "body_editorial_bullet": "editorial",
        "body_mask_band_left": "mask_left",
        "body_spotlight_panel": "spotlight",
        "cta_dark_glow": "cta",
    }
    return mapping[layout_variant]


def _safe_area_profile(layout_variant: str) -> SafeAreaProfile:
    mapping: dict[str, SafeAreaProfile] = {
        "cover_black_hero": "cover_tall_text",
        "body_editorial_bullet": "body_editorial_dense",
        "body_mask_band_left": "body_mask_right_column",
        "body_spotlight_panel": "body_spotlight_dense",
        "cta_dark_glow": "cta_center_stack",
    }
    return mapping[layout_variant]


def _max_body_lines(layout_variant: str, text_density: TextDensity) -> int:
    if layout_variant == "body_mask_band_left":
        return 10 if text_density == "high" else 8
    if layout_variant == "body_spotlight_panel":
        return 7 if text_density == "high" else 6
    return 8 if text_density == "high" else 6


def _body_hard_limit(layout_variant: str, text_density: TextDensity) -> int:
    if layout_variant == "body_mask_band_left":
        return 72 if text_density == "high" else 84
    if layout_variant == "body_spotlight_panel":
        return 88 if text_density == "high" else 104
    return 92 if text_density == "high" else 114


def _body_layout_variant(slide_number: int, body: str, style_recipe: str) -> str:
    if style_recipe == "typography_signal_glow_v1":
        return "body_spotlight_panel" if slide_number in {3, 5} else "body_editorial_bullet"
    if style_recipe == "cp_split_minimal_statement_v1":
        return "body_editorial_bullet" if slide_number in {2, 4, 6} else "body_spotlight_panel"
    if style_recipe == "alder_portrait_editorial_dense_v1":
        return "body_editorial_bullet" if slide_number in {2, 4, 6} else "body_mask_band_left"

    if len(body) > 130:
        return "body_editorial_bullet"
    if slide_number in {3, 6}:
        return "body_spotlight_panel"
    if slide_number % 2 == 0:
        return "body_mask_band_left"
    return "body_editorial_bullet"


def _body_accent_motif(slide_number: int, body: str, style_recipe: str) -> str:
    if style_recipe == "typography_signal_glow_v1":
        return "signal_glow_panel" if slide_number in {3, 5} else "signal_footer_lines"
    if style_recipe == "cp_split_minimal_statement_v1":
        return "device_card_mock"
    if style_recipe == "alder_portrait_editorial_dense_v1":
        return "editorial_count_markers" if slide_number in {2, 4, 6} else "mask_reference_band"
    if len(body) > 130:
        return "editorial_count_markers"
    if slide_number in {3, 6}:
        return "spotlight_band"
    if slide_number % 2 == 0:
        return "mask_reference_band"
    return "editorial_count_markers"


def _shorten_headline(text: str, language: str, hard_limit: int) -> str | None:
    normalized = _normalize_text(text)
    if len(normalized) <= hard_limit:
        return normalized

    split_match = re.split(r"\s+[—\-:]\s+", normalized, maxsplit=1)
    if len(split_match) == 2:
        left, right = split_match
        right = right.strip(" .!?")
        left_words = left.split()
        while left_words:
            candidate = f"{' '.join(left_words)} — {right}".strip()
            if len(candidate) <= hard_limit:
                return candidate
            left_words.pop()

    candidate = re.split(r"[.!?]", normalized)[0].strip()
    if 0 < len(candidate) <= hard_limit:
        return candidate

    if " - " in normalized:
        candidate = normalized.split(" - ", 1)[0].strip()
        if candidate:
            normalized = candidate
    if " — " in normalized:
        candidate = normalized.split(" — ", 1)[0].strip()
        if candidate:
            normalized = candidate
    if ":" in normalized:
        candidate = normalized.split(":", 1)[0].strip()
        if candidate:
            normalized = candidate

    words = normalized.split()
    max_words = 5 if language == "ru" else 6
    trimmed = " ".join(words[:max_words]).strip()
    if len(trimmed) > hard_limit:
        trimmed = _truncate_to_limit(trimmed, hard_limit)
    return trimmed or _truncate_to_limit(normalized, hard_limit)


def _shorten_body(text: str, language: str, hard_limit: int) -> str | None:
    normalized = _normalize_text(text)
    if not normalized:
        return None
    if len(normalized) <= hard_limit:
        return normalized

    sentences = re.split(r"(?<=[.!?])\s+", normalized)
    first_sentence = sentences[0].strip()
    if first_sentence and len(first_sentence) <= hard_limit:
        return first_sentence

    clauses = re.split(r"[,:;]", normalized)
    for clause in clauses:
        cleaned = clause.strip()
        if cleaned and len(cleaned) <= hard_limit:
            return cleaned

    max_words = 14 if language == "ru" else 16
    trimmed = " ".join(normalized.split()[:max_words])
    if len(trimmed) <= hard_limit:
        return trimmed
    return _truncate_to_limit(trimmed, hard_limit)


def _truncate_to_limit(text: str, hard_limit: int) -> str:
    if len(text) <= hard_limit:
        return text
    cutoff = text[:hard_limit].rsplit(" ", 1)[0].strip()
    return cutoff or text[:hard_limit].strip()


def _extract_emphasis_words(text: str, language: str) -> list[str]:
    stopwords = RU_STOPWORDS if language == "ru" else EN_STOPWORDS
    candidates = re.findall(r"[A-Za-zА-Яа-яЁё-]{4,}", text)
    unique: list[str] = []
    for word in candidates:
        normalized = word.lower()
        if normalized in stopwords:
            continue
        if normalized not in {item.lower() for item in unique}:
            unique.append(word)
    unique.sort(key=len, reverse=True)
    return unique[:3]


def _build_cta_copy_segments(cta_text: str, headline: str, language: str) -> tuple[str | None, str | None]:
    normalized = _normalize_text(cta_text)
    if not normalized:
        return None, None

    shared_prefix_stripped = _strip_shared_prefix(normalized, headline)
    audience_text = shared_prefix_stripped or normalized
    primary_seed, secondary_seed = _split_cta_audience(audience_text)
    body_display = _truncate_to_limit(primary_seed, 40)
    supporting_text = _truncate_to_limit(secondary_seed, 32) if secondary_seed else None

    if body_display == audience_text and len(body_display) > 40:
        body_display = _shorten_body(audience_text, language, hard_limit=40)
    return body_display, supporting_text


def _build_cta_button_label(language: str) -> str:
    if language == "ru":
        return "Забрать доступ"
    return "Get access"


def _normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def _strip_shared_prefix(source_text: str, headline: str) -> str:
    source_words = source_text.split()
    headline_words = headline.split()
    index = 0
    while (
        index < len(source_words)
        and index < len(headline_words)
        and source_words[index].strip("!?,.:;").lower() == headline_words[index].strip("!?,.:;").lower()
    ):
        index += 1

    stripped = " ".join(source_words[index:]).strip()
    if stripped:
        return stripped

    for marker in (" для ", " for ", " чтобы ", " who "):
        lowered = source_text.lower()
        marker_index = lowered.find(marker)
        if marker_index >= 0:
            return source_text[marker_index + 1 :].strip()

    return source_text


def _split_cta_audience(audience_text: str) -> tuple[str, str | None]:
    lowered = audience_text.lower()
    for marker in (" и тех", " and those", " and anyone", " and people", " who "):
        marker_index = lowered.find(marker)
        if marker_index > 0:
            primary = audience_text[:marker_index].strip(" ,.;:-")
            secondary = audience_text[marker_index + 1 :].strip(" ,.;:-")
            if primary:
                return primary, secondary or None

    if "," in audience_text:
        primary, secondary = audience_text.split(",", 1)
        primary = primary.strip(" ,.;:-")
        secondary = secondary.strip(" ,.;:-")
        if primary:
            return primary, secondary or None

    return audience_text, None
