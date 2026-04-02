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

CREATOR_MONO_RECIPE = StyleRecipeSpec(
    style_family="reference_creator_mono_minimal",
    style_recipe="creator_mono_minimal_v1",
    reference_node_ids=(
        "local:01-long-title",
        "local:02-title",
        "local:03-copy",
        "local:05-call-to-action",
    ),
    style_tokens=StyleTokens(
        light_background="#FFFFFF",
        dark_background="#111111",
        text_dark="#101010",
        text_light="#FFFFFF",
        accent_blue="#C8D3E1",
        accent_magenta="#D88989",
        accent_gold="#D0B089",
        accent_orange="#111111",
        accent_purple="#EDEDED",
        accent_navy="#2B2B2B",
    ),
    typography=TypographyTokens(
        cover_family="Inter",
        cover_style="Black",
        body_heading_family="Inter",
        body_heading_style="Black",
        body_family="Inter",
        body_style="Regular",
        cta_heading_family="Inter",
        cta_heading_style="Black",
        cta_body_family="Inter",
        cta_body_style="Regular",
    ),
)

LIGHT_GRAIN_GLOW_RECIPE = StyleRecipeSpec(
    style_family="reference_light_grain_glow",
    style_recipe="light_grain_glow_v1",
    reference_node_ids=("local:light-1", "local:light-2", "local:light-6"),
    style_tokens=StyleTokens(
        light_background="#F7F5FF",
        dark_background="#232742",
        text_dark="#24252C",
        text_light="#FFFFFF",
        accent_blue="#8A8DFF",
        accent_magenta="#D26BFF",
        accent_gold="#CBD6FF",
        accent_orange="#76F48A",
        accent_purple="#6A60FF",
        accent_navy="#343C72",
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

RETRO_SWIPE_RECIPE = StyleRecipeSpec(
    style_family="reference_retro_swipe_creator",
    style_recipe="retro_swipe_creator_v1",
    reference_node_ids=("local:title-01",),
    style_tokens=StyleTokens(
        light_background="#9DAF86",
        dark_background="#6B7759",
        text_dark="#1F241C",
        text_light="#FFF6E8",
        accent_blue="#DDE3CF",
        accent_magenta="#8A9670",
        accent_gold="#FFD48A",
        accent_orange="#F0C46B",
        accent_purple="#C8D2B8",
        accent_navy="#33402D",
    ),
    typography=TypographyTokens(
        cover_family="Montserrat",
        cover_style="Bold",
        body_heading_family="Montserrat",
        body_heading_style="Bold",
        body_family="Inter",
        body_style="Regular",
        cta_heading_family="Montserrat",
        cta_heading_style="Bold",
        cta_body_family="Inter",
        cta_body_style="Regular",
    ),
)

TWITTER_CARD_SOFT_RECIPE = StyleRecipeSpec(
    style_family="reference_twitter_card_soft",
    style_recipe="twitter_card_soft_v1",
    reference_node_ids=("local:twitter-post-default", "local:twitter-post-soft"),
    style_tokens=StyleTokens(
        light_background="#F7F9FC",
        dark_background="#1F2633",
        text_dark="#1E1F26",
        text_light="#FFFFFF",
        accent_blue="#3AA4FF",
        accent_magenta="#F1C0A8",
        accent_gold="#F1D58B",
        accent_orange="#FFB566",
        accent_purple="#B7D6FF",
        accent_navy="#607B9C",
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

PASTEL_ARROW_RECIPE = StyleRecipeSpec(
    style_family="reference_pastel_arrow_editorial",
    style_recipe="pastel_arrow_editorial_v1",
    reference_node_ids=("local:1", "local:104", "local:11-3", "local:frame-15"),
    style_tokens=StyleTokens(
        light_background="#F8F6FF",
        dark_background="#23263A",
        text_dark="#1F2230",
        text_light="#FFFFFF",
        accent_blue="#8CA8FF",
        accent_magenta="#E58FF5",
        accent_gold="#FFE0A8",
        accent_orange="#FF9A62",
        accent_purple="#B39CFF",
        accent_navy="#5B69D4",
    ),
    typography=TypographyTokens(
        cover_family="Inter",
        cover_style="Black",
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

PLACEHOLDER_MEDIA_RECIPE = StyleRecipeSpec(
    style_family="reference_placeholder_media_glow",
    style_recipe="placeholder_media_glow_v1",
    reference_node_ids=("local:2", "local:28", "local:32", "local:frame-16"),
    style_tokens=StyleTokens(
        light_background="#F7F8FF",
        dark_background="#1D2134",
        text_dark="#1C2030",
        text_light="#FFFFFF",
        accent_blue="#9DB7FF",
        accent_magenta="#F3B5D0",
        accent_gold="#F4E6C7",
        accent_orange="#FFAA65",
        accent_purple="#C1C8FF",
        accent_navy="#4651A5",
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

DEVICE_MOCKUP_RECIPE = StyleRecipeSpec(
    style_family="reference_device_mockup_gradient",
    style_recipe="device_mockup_gradient_v1",
    reference_node_ids=("local:127", "local:148", "local:149", "local:twitterpost-01"),
    style_tokens=StyleTokens(
        light_background="#FBFAFF",
        dark_background="#2A3044",
        text_dark="#222536",
        text_light="#FFFFFF",
        accent_blue="#77B9FF",
        accent_magenta="#F0C1A9",
        accent_gold="#F4E2A2",
        accent_orange="#FFB36D",
        accent_purple="#B0D1FF",
        accent_navy="#6F8FBA",
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

SOCIAL_PROOF_RECIPE = StyleRecipeSpec(
    style_family="reference_social_proof_linkedin",
    style_recipe="social_proof_linkedin_v1",
    reference_node_ids=("local:carousel4", "local:carousel8-9", "local:frame-34305"),
    style_tokens=StyleTokens(
        light_background="#EDF4EA",
        dark_background="#234046",
        text_dark="#1B2C30",
        text_light="#F7F8F2",
        accent_blue="#B4D6FF",
        accent_magenta="#95B36B",
        accent_gold="#FFD48A",
        accent_orange="#F3C970",
        accent_purple="#D9E8C4",
        accent_navy="#2D4A52",
    ),
    typography=TypographyTokens(
        cover_family="Montserrat",
        cover_style="Bold",
        body_heading_family="Montserrat",
        body_heading_style="Bold",
        body_family="Inter",
        body_style="Regular",
        cta_heading_family="Montserrat",
        cta_heading_style="Bold",
        cta_body_family="Inter",
        cta_body_style="Regular",
    ),
)

PROFILE_CIRCLE_RECIPE = StyleRecipeSpec(
    style_family="reference_profile_circle_pop",
    style_recipe="profile_circle_pop_v1",
    reference_node_ids=("local:150", "local:frame-34034", "local:frame-34303", "local:profile-picture"),
    style_tokens=StyleTokens(
        light_background="#F6F4FF",
        dark_background="#2B2E8E",
        text_dark="#171B2A",
        text_light="#FFFFFF",
        accent_blue="#B6C0FF",
        accent_magenta="#7B73FF",
        accent_gold="#FFFFFF",
        accent_orange="#B8BEFF",
        accent_purple="#5E5AF2",
        accent_navy="#1D1F68",
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
    CREATOR_MONO_RECIPE.style_recipe: CREATOR_MONO_RECIPE,
    LIGHT_GRAIN_GLOW_RECIPE.style_recipe: LIGHT_GRAIN_GLOW_RECIPE,
    RETRO_SWIPE_RECIPE.style_recipe: RETRO_SWIPE_RECIPE,
    TWITTER_CARD_SOFT_RECIPE.style_recipe: TWITTER_CARD_SOFT_RECIPE,
    PASTEL_ARROW_RECIPE.style_recipe: PASTEL_ARROW_RECIPE,
    PLACEHOLDER_MEDIA_RECIPE.style_recipe: PLACEHOLDER_MEDIA_RECIPE,
    DEVICE_MOCKUP_RECIPE.style_recipe: DEVICE_MOCKUP_RECIPE,
    SOCIAL_PROOF_RECIPE.style_recipe: SOCIAL_PROOF_RECIPE,
    PROFILE_CIRCLE_RECIPE.style_recipe: PROFILE_CIRCLE_RECIPE,
}


def select_style_recipe(record: CarouselOutput, language: str) -> StyleRecipeSpec:
    preference = (record.normalized_input.reference_style or "").strip().lower()
    if record.normalized_input.generation_mode == "review":
        if preference in {"alder_split_right", "alder_right"}:
            return ALDER_SPLIT_RIGHT_RECIPE
        if preference in {"light_glow", "light_grain", "soft_light", "reference_light_grain_glow"}:
            return LIGHT_GRAIN_GLOW_RECIPE
        if preference in {"twitter_card", "tweet", "twitter_post", "reference_twitter_card_soft"}:
            return TWITTER_CARD_SOFT_RECIPE
        review_candidates = [
            ALDER_SPLIT_RIGHT_RECIPE,
            LIGHT_GRAIN_GLOW_RECIPE,
            TWITTER_CARD_SOFT_RECIPE,
        ]
        return review_candidates[_content_signature(record) % len(review_candidates)]
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
    if preference in {"creator_mono", "mono_minimal", "minimal_creator", "long_title", "reference_creator_mono_minimal"}:
        return CREATOR_MONO_RECIPE
    if preference in {"pastel_arrow", "gradient_arrow", "arrow_editorial", "11_3", "reference_pastel_arrow_editorial"}:
        return PASTEL_ARROW_RECIPE
    if preference in {"placeholder_media", "image_placeholder", "glow_placeholder", "reference_placeholder_media_glow"}:
        return PLACEHOLDER_MEDIA_RECIPE
    if preference in {"light_glow", "light_grain", "soft_light", "reference_light_grain_glow"}:
        return LIGHT_GRAIN_GLOW_RECIPE
    if preference in {"device_mockup", "phone_card", "mockup_gradient", "reference_device_mockup_gradient"}:
        return DEVICE_MOCKUP_RECIPE
    if preference in {"retro_swipe", "title01", "swipe_creator", "reference_retro_swipe_creator"}:
        return RETRO_SWIPE_RECIPE
    if preference in {"social_proof", "linkedin", "linkedin_cards", "reference_social_proof_linkedin"}:
        return SOCIAL_PROOF_RECIPE
    if preference in {"profile_circle", "circle_pop", "profile_pop", "reference_profile_circle_pop"}:
        return PROFILE_CIRCLE_RECIPE
    if preference in {"twitter_card", "tweet", "twitter_post", "reference_twitter_card_soft"}:
        return TWITTER_CARD_SOFT_RECIPE

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
            CREATOR_MONO_RECIPE,
            PASTEL_ARROW_RECIPE,
            SOCIAL_PROOF_RECIPE,
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
            LIGHT_GRAIN_GLOW_RECIPE,
            CREATOR_MONO_RECIPE,
            PASTEL_ARROW_RECIPE,
            DEVICE_MOCKUP_RECIPE,
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
        CREATOR_MONO_RECIPE,
        LIGHT_GRAIN_GLOW_RECIPE,
        RETRO_SWIPE_RECIPE,
        TWITTER_CARD_SOFT_RECIPE,
        PASTEL_ARROW_RECIPE,
        PLACEHOLDER_MEDIA_RECIPE,
        DEVICE_MOCKUP_RECIPE,
        SOCIAL_PROOF_RECIPE,
        PROFILE_CIRCLE_RECIPE,
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
