from __future__ import annotations

import hashlib
from dataclasses import dataclass

from carousel_system.models import CarouselOutput, StyleTokens, TypographyTokens


@dataclass(frozen=True)
class StyleRecipeSpec:
    style_family: str
    style_recipe: str
    reference_node_ids: tuple[str, ...]
    style_tokens: StyleTokens
    typography: TypographyTokens


ALDER_RECIPE = StyleRecipeSpec(
    style_family="reference_mix_alder_portrait",
    style_recipe="alder_portrait_editorial_mix_v1",
    reference_node_ids=("1:46227", "1:46232", "1:46239", "1:46288", "1:46485"),
    style_tokens=StyleTokens(
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
    ),
    typography=TypographyTokens(
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
    ),
)

ALDER_DENSE_RECIPE = StyleRecipeSpec(
    style_family="reference_mix_alder_portrait",
    style_recipe="alder_portrait_editorial_dense_v1",
    reference_node_ids=("1:46227", "1:46232", "1:46239", "1:46288", "1:46485"),
    style_tokens=StyleTokens(
        light_background="#F4F6F7",
        dark_background="#020202",
        text_dark="#111111",
        text_light="#FFFFFF",
        accent_blue="#55C3EE",
        accent_magenta="#B0105A",
        accent_gold="#B59868",
        accent_orange="#FF9300",
        accent_purple="#6B1FD1",
        accent_navy="#07215B",
    ),
    typography=ALDER_RECIPE.typography,
)

TYPOGRAPHY_SIGNAL_RECIPE = StyleRecipeSpec(
    style_family="reference_typography_signal",
    style_recipe="typography_signal_glow_v1",
    reference_node_ids=("1:46201", "1:46288", "1:46485"),
    style_tokens=StyleTokens(
        light_background="#F4F6F7",
        dark_background="#030103",
        text_dark="#111111",
        text_light="#FFFFFF",
        accent_blue="#55C3EE",
        accent_magenta="#9E0E4C",
        accent_gold="#B59868",
        accent_orange="#FF9300",
        accent_purple="#6B1FD1",
        accent_navy="#120313",
    ),
    typography=TypographyTokens(
        cover_family="Inter",
        cover_style="Bold",
        body_heading_family="Inter",
        body_heading_style="Bold",
        body_family="Inter",
        body_style="Regular",
        cta_heading_family="Inter",
        cta_heading_style="Bold",
        cta_body_family="Inter",
        cta_body_style="Regular",
    ),
)

CP_SPLIT_RECIPE = StyleRecipeSpec(
    style_family="reference_cp_minimal_split",
    style_recipe="cp_split_minimal_statement_v1",
    reference_node_ids=("1:46184", "1:46190", "1:46485"),
    style_tokens=StyleTokens(
        light_background="#F4F6F7",
        dark_background="#111111",
        text_dark="#111111",
        text_light="#FFFFFF",
        accent_blue="#7BB8FF",
        accent_magenta="#C54D7B",
        accent_gold="#D5B37A",
        accent_orange="#FF9300",
        accent_purple="#7047E8",
        accent_navy="#1D2C53",
    ),
    typography=TypographyTokens(
        cover_family="Poppins",
        cover_style="Bold",
        body_heading_family="Poppins",
        body_heading_style="Bold",
        body_family="Poppins",
        body_style="Medium",
        cta_heading_family="Poppins",
        cta_heading_style="Bold",
        cta_body_family="Poppins",
        cta_body_style="Regular",
    ),
)

STYLE_RECIPES: dict[str, StyleRecipeSpec] = {
    ALDER_RECIPE.style_recipe: ALDER_RECIPE,
    ALDER_DENSE_RECIPE.style_recipe: ALDER_DENSE_RECIPE,
    TYPOGRAPHY_SIGNAL_RECIPE.style_recipe: TYPOGRAPHY_SIGNAL_RECIPE,
    CP_SPLIT_RECIPE.style_recipe: CP_SPLIT_RECIPE,
}


def select_style_recipe(record: CarouselOutput, language: str) -> StyleRecipeSpec:
    preference = (record.normalized_input.reference_style or "").strip().lower()
    if preference in {"typography", "typography_signal", "signal"}:
        return TYPOGRAPHY_SIGNAL_RECIPE
    if preference in {"cp_3", "cp3", "minimal", "cp_split"}:
        return CP_SPLIT_RECIPE

    body_lengths = [len(slide.body or "") for slide in record.content_plan if slide.slide_role == "info"]
    average_body = sum(body_lengths) / len(body_lengths) if body_lengths else 0
    hook_length = len(record.content_plan[0].headline) if record.content_plan else 0
    cta_length = len(record.content_plan[-1].headline) + len(record.content_plan[-1].body or "") if record.content_plan else 0
    dense_slide_count = sum(1 for length in body_lengths if length > 110)
    signature = _content_signature(record)

    if (language == "ru" and average_body > 100) or dense_slide_count >= 4 or average_body > 126:
        return ALDER_DENSE_RECIPE

    if hook_length <= 34 and average_body <= 116:
        return CP_SPLIT_RECIPE if signature % 2 == 0 else TYPOGRAPHY_SIGNAL_RECIPE

    if cta_length <= 96 and average_body <= 118 and signature % 3 == 0:
        return TYPOGRAPHY_SIGNAL_RECIPE

    if average_body <= 118 and signature % 5 in {0, 1}:
        return CP_SPLIT_RECIPE

    return ALDER_RECIPE


def _content_signature(record: CarouselOutput) -> int:
    parts = [
        record.job_id,
        record.normalized_input.topic or "",
        record.normalized_input.script or "",
        record.content_plan[0].headline if record.content_plan else "",
        record.content_plan[-1].headline if record.content_plan else "",
    ]
    digest = hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:12], 16)
