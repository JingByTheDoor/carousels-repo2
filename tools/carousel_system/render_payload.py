from __future__ import annotations

from pathlib import Path

from carousel_system.models import (
    DEFAULT_STYLE_FAMILY,
    DEFAULT_STYLE_RECIPE,
    CarouselOutput,
    PluginRenderPayload,
    RenderArtifact,
    RenderSlideSpec,
    StyleTokens,
    TypographyTokens,
)


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


def select_style_family(record: CarouselOutput, language: str) -> tuple[str, str]:
    dense_slide_count = sum(
        1
        for slide in record.content_plan
        if len((slide.body or "")) > 125 or len(slide.headline) > 48
    )
    if language == "ru" or dense_slide_count >= 3:
        return DEFAULT_STYLE_FAMILY, "alder_portrait_editorial_dense_v1"
    return DEFAULT_STYLE_FAMILY, DEFAULT_STYLE_RECIPE


def build_style_tokens() -> StyleTokens:
    return StyleTokens(
        light_background="#F4F6F7",
        dark_background="#020202",
        text_dark="#111111",
        text_light="#FFFFFF",
        accent_blue="#55C3EE",
        accent_magenta="#9E0E4C",
        accent_gold="#B59868",
        accent_orange="#FF9300",
        accent_purple="#6B1FD1",
        accent_navy="#07215B",
    )


def build_typography_tokens() -> TypographyTokens:
    return TypographyTokens(
        cover_family="Inter",
        cover_style="Black",
        body_heading_family="Poppins",
        body_heading_style="Bold",
        body_family="Poppins",
        body_style="Regular",
        cta_heading_family="Inter",
        cta_heading_style="Bold",
        cta_body_family="Inter",
        cta_body_style="Regular",
    )


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
    style_family, style_recipe = select_style_family(record, language)
    slides: list[RenderSlideSpec] = []
    for slide in record.content_plan:
        if slide.slide_role == "hook":
            slides.append(
                RenderSlideSpec(
                    slide_number=slide.slide_number,
                    slide_role=slide.slide_role,
                    design_role=slide.design_role,
                    layout_variant="cover_black_hero",
                    text_align="left",
                    headline=slide.headline,
                    body=slide.body,
                    accent_motif="geometric_cluster",
                )
            )
            continue

        if slide.slide_role == "cta":
            slides.append(
                RenderSlideSpec(
                    slide_number=slide.slide_number,
                    slide_role=slide.slide_role,
                    design_role=slide.design_role,
                    layout_variant="cta_dark_glow",
                    text_align="center",
                    headline=slide.headline,
                    body=slide.body or record.normalized_input.cta_text,
                    accent_motif="cta_signal_lines",
                )
            )
            continue

        slides.append(
            RenderSlideSpec(
                slide_number=slide.slide_number,
                slide_role=slide.slide_role,
                design_role=slide.design_role,
                layout_variant=_body_layout_variant(slide.slide_number, slide.body or "", style_recipe),
                text_align="left",
                headline=slide.headline,
                body=slide.body,
                accent_motif=_body_accent_motif(slide.slide_number, slide.body or "", style_recipe),
            )
        )

    return PluginRenderPayload(
        job_id=record.job_id,
        page_name=f"{record.job_id}-plugin-render",
        prompt_version=record.prompt_version,
        language=language,
        style_family=style_family,
        style_recipe=style_recipe,
        source_artifact_path=str(source_artifact_path),
        reference_file_key=record.normalized_input.reference_file_key,
        reference_node_ids=[reference.node_id for reference in record.design_reference_log],
        style_tokens=build_style_tokens(),
        typography=build_typography_tokens(),
        slides=slides,
    )


def write_plugin_render_payload(output_path: Path, payload: PluginRenderPayload) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    return output_path


def _body_layout_variant(slide_number: int, body: str, style_recipe: str) -> str:
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
    if style_recipe == "alder_portrait_editorial_dense_v1":
        return "editorial_count_markers" if slide_number in {2, 4, 6} else "mask_reference_band"
    if len(body) > 130:
        return "editorial_count_markers"
    if slide_number in {3, 6}:
        return "spotlight_band"
    if slide_number % 2 == 0:
        return "mask_reference_band"
    return "editorial_count_markers"
