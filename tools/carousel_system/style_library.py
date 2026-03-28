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

ALDER_SPLIT_RIGHT_RECIPE = StyleRecipeSpec(
    style_family="reference_alder_split_media",
    style_recipe="alder_split_media_right_v1",
    reference_node_ids=("1:46227", "1:46248", "1:46485"),
    style_tokens=ALDER_RECIPE.style_tokens,
    typography=ALDER_RECIPE.typography,
)

ALDER_SPLIT_LEFT_RECIPE = StyleRecipeSpec(
    style_family="reference_alder_split_media",
    style_recipe="alder_split_media_left_v1",
    reference_node_ids=("1:46227", "1:46256", "1:46485"),
    style_tokens=ALDER_RECIPE.style_tokens,
    typography=ALDER_RECIPE.typography,
)

ALDER_TEXT_ONLY_RECIPE = StyleRecipeSpec(
    style_family="reference_alder_text_only",
    style_recipe="alder_text_only_air_v1",
    reference_node_ids=("1:46227", "1:46264", "1:46485"),
    style_tokens=ALDER_RECIPE.style_tokens,
    typography=ALDER_RECIPE.typography,
)

CP_LONGFORM_RECIPE = StyleRecipeSpec(
    style_family="reference_cp_longform_split",
    style_recipe="cp_split_longform_v1",
    reference_node_ids=("1:46190", "1:46277", "1:46485"),
    style_tokens=CP_SPLIT_RECIPE.style_tokens,
    typography=CP_SPLIT_RECIPE.typography,
)

CP_GALLERY_RECIPE = StyleRecipeSpec(
    style_family="reference_cp_gallery_wall",
    style_recipe="cp_gallery_wall_v1",
    reference_node_ids=("1:46271", "1:46283", "1:46485"),
    style_tokens=CP_SPLIT_RECIPE.style_tokens,
    typography=CP_SPLIT_RECIPE.typography,
)

SADEKOV_BLACK_PROFILE_RECIPE = StyleRecipeSpec(
    style_family="reference_sadekov_black_profile",
    style_recipe="sadekov_black_profile_minimal_v1",
    reference_node_ids=("1:9052", "1:9076", "1:9176"),
    style_tokens=StyleTokens(
        light_background="#F2F2F2",
        dark_background="#000000",
        text_dark="#111111",
        text_light="#FFFFFF",
        accent_blue="#409DFF",
        accent_magenta="#303030",
        accent_gold="#7B7B7B",
        accent_orange="#FFFFFF",
        accent_purple="#4A4A4A",
        accent_navy="#121212",
    ),
    typography=TypographyTokens(
        cover_family="Inter",
        cover_style="Black",
        body_heading_family="Inter",
        body_heading_style="Regular",
        body_family="Inter",
        body_style="Regular",
        cta_heading_family="Inter",
        cta_heading_style="Regular",
        cta_body_family="Inter",
        cta_body_style="Regular",
    ),
)

SADEKOV_WHITE_PROFILE_RECIPE = StyleRecipeSpec(
    style_family="reference_sadekov_white_profile",
    style_recipe="sadekov_white_profile_minimal_v1",
    reference_node_ids=("1:9064", "1:9086", "1:9187"),
    style_tokens=StyleTokens(
        light_background="#FFFFFF",
        dark_background="#FFFFFF",
        text_dark="#111111",
        text_light="#FFFFFF",
        accent_blue="#409DFF",
        accent_magenta="#D9D9D9",
        accent_gold="#A0A0A0",
        accent_orange="#111111",
        accent_purple="#EDEDED",
        accent_navy="#1A1A1A",
    ),
    typography=TypographyTokens(
        cover_family="Inter",
        cover_style="Black",
        body_heading_family="Inter",
        body_heading_style="Regular",
        body_family="Inter",
        body_style="Regular",
        cta_heading_family="Inter",
        cta_heading_style="Regular",
        cta_body_family="Inter",
        cta_body_style="Regular",
    ),
)

TYPOGRAPHY_EDITORIAL_LIGHT_RECIPE = StyleRecipeSpec(
    style_family="reference_typography_editorial_light",
    style_recipe="typography_editorial_light_v1",
    reference_node_ids=("1:14767", "1:14775", "1:14788"),
    style_tokens=StyleTokens(
        light_background="#FFFFFF",
        dark_background="#171717",
        text_dark="#111111",
        text_light="#FFFFFF",
        accent_blue="#79E7E2",
        accent_magenta="#2F3134",
        accent_gold="#F6D267",
        accent_orange="#FFB300",
        accent_purple="#5B5D60",
        accent_navy="#101114",
    ),
    typography=TypographyTokens(
        cover_family="Inter",
        cover_style="Black",
        body_heading_family="Inter",
        body_heading_style="Bold",
        body_family="Inter",
        body_style="Regular",
        cta_heading_family="Inter",
        cta_heading_style="Black",
        cta_body_family="Inter",
        cta_body_style="Regular",
    ),
)

STYLE_RECIPES: dict[str, StyleRecipeSpec] = {
    ALDER_RECIPE.style_recipe: ALDER_RECIPE,
    ALDER_DENSE_RECIPE.style_recipe: ALDER_DENSE_RECIPE,
    ALDER_SPLIT_RIGHT_RECIPE.style_recipe: ALDER_SPLIT_RIGHT_RECIPE,
    ALDER_SPLIT_LEFT_RECIPE.style_recipe: ALDER_SPLIT_LEFT_RECIPE,
    ALDER_TEXT_ONLY_RECIPE.style_recipe: ALDER_TEXT_ONLY_RECIPE,
    TYPOGRAPHY_SIGNAL_RECIPE.style_recipe: TYPOGRAPHY_SIGNAL_RECIPE,
    CP_SPLIT_RECIPE.style_recipe: CP_SPLIT_RECIPE,
    CP_LONGFORM_RECIPE.style_recipe: CP_LONGFORM_RECIPE,
    CP_GALLERY_RECIPE.style_recipe: CP_GALLERY_RECIPE,
    SADEKOV_BLACK_PROFILE_RECIPE.style_recipe: SADEKOV_BLACK_PROFILE_RECIPE,
    SADEKOV_WHITE_PROFILE_RECIPE.style_recipe: SADEKOV_WHITE_PROFILE_RECIPE,
    TYPOGRAPHY_EDITORIAL_LIGHT_RECIPE.style_recipe: TYPOGRAPHY_EDITORIAL_LIGHT_RECIPE,
}


def select_style_recipe(record: CarouselOutput, language: str) -> StyleRecipeSpec:
    preference = (record.normalized_input.reference_style or "").strip().lower()
    if preference in {"alder_forced", "alder_locked", "reference_mix_alder_portrait"}:
        return ALDER_DENSE_RECIPE if language == "ru" else ALDER_RECIPE
    if preference in {"alder_split_right", "alder_right"}:
        return ALDER_SPLIT_RIGHT_RECIPE
    if preference in {"alder_split_left", "alder_left"}:
        return ALDER_SPLIT_LEFT_RECIPE
    if preference in {"alder_text_only", "alder_text"}:
        return ALDER_TEXT_ONLY_RECIPE
    if preference in {"typography", "typography_signal", "signal"}:
        return TYPOGRAPHY_SIGNAL_RECIPE
    if preference in {"cp_3", "cp3", "minimal", "cp_split"}:
        return CP_SPLIT_RECIPE
    if preference in {"cp_longform", "cp_long"}:
        return CP_LONGFORM_RECIPE
    if preference in {"cp_gallery", "gallery_wall", "gallery"}:
        return CP_GALLERY_RECIPE
    if preference in {"sadekov", "black_profile", "profile_black", "reference_sadekov_black_profile"}:
        return SADEKOV_BLACK_PROFILE_RECIPE
    if preference in {"sadekov_light", "white_profile", "profile_white", "reference_sadekov_white_profile"}:
        return SADEKOV_WHITE_PROFILE_RECIPE
    if preference in {"typography_light", "typography_editorial", "reference_typography_editorial_light"}:
        return TYPOGRAPHY_EDITORIAL_LIGHT_RECIPE

    body_lengths = [len(slide.body or "") for slide in record.content_plan if slide.slide_role == "info"]
    average_body = sum(body_lengths) / len(body_lengths) if body_lengths else 0
    hook_length = len(record.content_plan[0].headline) if record.content_plan else 0
    cta_length = len(record.content_plan[-1].headline) + len(record.content_plan[-1].body or "") if record.content_plan else 0
    dense_slide_count = sum(1 for length in body_lengths if length > 110)
    signature = _content_signature(record)

    if (language == "ru" and average_body > 100) or dense_slide_count >= 4 or average_body > 126:
        candidates = [ALDER_DENSE_RECIPE, ALDER_TEXT_ONLY_RECIPE, CP_LONGFORM_RECIPE, TYPOGRAPHY_EDITORIAL_LIGHT_RECIPE]
        return candidates[signature % len(candidates)]

    if average_body > 102 or hook_length > 54:
        candidates = [
            ALDER_RECIPE,
            ALDER_SPLIT_RIGHT_RECIPE,
            ALDER_SPLIT_LEFT_RECIPE,
            CP_LONGFORM_RECIPE,
            TYPOGRAPHY_SIGNAL_RECIPE,
            TYPOGRAPHY_EDITORIAL_LIGHT_RECIPE,
        ]
        return candidates[signature % len(candidates)]

    if average_body > 82 or cta_length > 88:
        candidates = [
            TYPOGRAPHY_SIGNAL_RECIPE,
            TYPOGRAPHY_EDITORIAL_LIGHT_RECIPE,
            CP_SPLIT_RECIPE,
            ALDER_SPLIT_RIGHT_RECIPE,
            ALDER_SPLIT_LEFT_RECIPE,
            CP_LONGFORM_RECIPE,
            SADEKOV_BLACK_PROFILE_RECIPE,
        ]
        return candidates[signature % len(candidates)]

    candidates = [
        CP_SPLIT_RECIPE,
        CP_GALLERY_RECIPE,
        TYPOGRAPHY_SIGNAL_RECIPE,
        TYPOGRAPHY_EDITORIAL_LIGHT_RECIPE,
        SADEKOV_BLACK_PROFILE_RECIPE,
        SADEKOV_WHITE_PROFILE_RECIPE,
        ALDER_SPLIT_RIGHT_RECIPE,
        ALDER_SPLIT_LEFT_RECIPE,
    ]
    return candidates[signature % len(candidates)]


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
