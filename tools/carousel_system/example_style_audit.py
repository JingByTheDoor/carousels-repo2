from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CoverageMapping:
    status: str
    canonical_name: str
    style_families: tuple[str, ...]
    style_recipes: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class ExampleGroupRecord:
    group_name: str
    file_count: int
    sample_files: tuple[str, ...]
    status: str
    canonical_name: str
    style_families: tuple[str, ...]
    style_recipes: tuple[str, ...]
    notes: str


COVERED_GROUPS: dict[str, CoverageMapping] = {
    "Alder_1": CoverageMapping(
        status="covered",
        canonical_name="Alder_1",
        style_families=(
            "reference_mix_alder_portrait",
            "reference_alder_split_media",
            "reference_alder_text_only",
        ),
        style_recipes=(
            "alder_portrait_editorial_mix_v1",
            "alder_portrait_editorial_dense_v1",
            "alder_split_media_right_v1",
            "alder_split_media_left_v1",
            "alder_text_only_air_v1",
        ),
        notes="Primary upper-file family already harvested into multiple Alder-driven recipes.",
    ),
    "CP_3": CoverageMapping(
        status="covered",
        canonical_name="CP_3",
        style_families=(
            "reference_cp_minimal_split",
            "reference_cp_longform_split",
            "reference_cp_gallery_wall",
        ),
        style_recipes=(
            "cp_split_minimal_statement_v1",
            "cp_split_longform_v1",
            "cp_gallery_wall_v1",
        ),
        notes="Minimal split, longform split, and gallery variants are already implemented.",
    ),
    "typography slide 1": CoverageMapping(
        status="covered",
        canonical_name="typography slide 1",
        style_families=(
            "reference_typography_signal",
            "reference_typography_editorial_light",
        ),
        style_recipes=(
            "typography_signal_glow_v1",
            "typography_editorial_light_v1",
        ),
        notes="Dark centered-signal and light editorial directions are both mapped from this family.",
    ),
    "typography slide 2": CoverageMapping(
        status="covered",
        canonical_name="typography slide 2",
        style_families=("reference_typography_signal",),
        style_recipes=("typography_signal_glow_v1",),
        notes="Used as the current CTA/end-card reference family.",
    ),
    "01 – Long Title": CoverageMapping(
        status="covered",
        canonical_name="creator_mono_minimal",
        style_families=("reference_creator_mono_minimal",),
        style_recipes=("creator_mono_minimal_v1",),
        notes="Monochrome hook-export family now mapped into the minimal creator text recipe.",
    ),
    "02 – Title": CoverageMapping(
        status="covered",
        canonical_name="creator_mono_minimal",
        style_families=("reference_creator_mono_minimal",),
        style_recipes=("creator_mono_minimal_v1",),
        notes="Title-only exports now map to the same minimal creator family as the long-title and CTA slides.",
    ),
    "03 – Copy": CoverageMapping(
        status="covered",
        canonical_name="creator_mono_minimal",
        style_families=("reference_creator_mono_minimal",),
        style_recipes=("creator_mono_minimal_v1",),
        notes="Soft rose copy exports are now absorbed by the minimal creator family.",
    ),
    "05 – Call to Action": CoverageMapping(
        status="covered",
        canonical_name="creator_mono_minimal",
        style_families=("reference_creator_mono_minimal",),
        style_recipes=("creator_mono_minimal_v1",),
        notes="CTA exports now map to the same minimal creator family.",
    ),
    "Light_1": CoverageMapping(
        status="covered",
        canonical_name="light_grain_glow",
        style_families=("reference_light_grain_glow",),
        style_recipes=("light_grain_glow_v1",),
        notes="Primary light-grain hero set is now mapped into the light glow family.",
    ),
    "Title (01)": CoverageMapping(
        status="covered",
        canonical_name="retro_swipe_creator",
        style_families=("reference_retro_swipe_creator",),
        style_recipes=("retro_swipe_creator_v1",),
        notes="Textured retro creator CTA set is now mapped into the swipe-button family.",
    ),
    "Twitter Post - Default": CoverageMapping(
        status="covered",
        canonical_name="twitter_card_soft",
        style_families=("reference_twitter_card_soft",),
        style_recipes=("twitter_card_soft_v1",),
        notes="Flat tweet screenshot layout is now covered by the soft tweet-card renderer.",
    ),
}


DUPLICATE_GROUPS: dict[str, CoverageMapping] = {
    "1971245499": CoverageMapping(
        status="duplicate",
        canonical_name="portrait_reference_1971245499",
        style_families=(
            "reference_mix_alder_portrait",
            "reference_alder_split_media",
            "reference_alder_text_only",
            "reference_typography_signal",
            "reference_cp_minimal_split",
            "reference_cp_longform_split",
            "reference_cp_gallery_wall",
        ),
        style_recipes=(),
        notes="Single exported portrait layout reference already used as a shared sizing/layout anchor.",
    ),
    "1971245110": CoverageMapping(
        status="duplicate",
        canonical_name="reference_sadekov_black_profile_cover_export",
        style_families=("reference_sadekov_black_profile",),
        style_recipes=("sadekov_black_profile_minimal_v1",),
        notes="Exported black-profile cover slide already mapped to node 1:9052.",
    ),
    "1971245111": CoverageMapping(
        status="duplicate",
        canonical_name="reference_sadekov_black_profile_body_export",
        style_families=("reference_sadekov_black_profile",),
        style_recipes=("sadekov_black_profile_minimal_v1",),
        notes="Exported black-profile body slide already mapped to node 1:9076.",
    ),
    "1971245118": CoverageMapping(
        status="duplicate",
        canonical_name="reference_sadekov_black_profile_cta_export",
        style_families=("reference_sadekov_black_profile",),
        style_recipes=("sadekov_black_profile_minimal_v1",),
        notes="Exported black-profile CTA slide already mapped to node 1:9176.",
    ),
    "1971245119": CoverageMapping(
        status="duplicate",
        canonical_name="reference_sadekov_white_profile_cover_export",
        style_families=("reference_sadekov_white_profile",),
        style_recipes=("sadekov_white_profile_minimal_v1",),
        notes="Exported white-profile cover slide already mapped to node 1:9064.",
    ),
    "1971245120": CoverageMapping(
        status="duplicate",
        canonical_name="reference_sadekov_white_profile_body_export",
        style_families=("reference_sadekov_white_profile",),
        style_recipes=("sadekov_white_profile_minimal_v1",),
        notes="Exported white-profile body slide already mapped to node 1:9086.",
    ),
    "1971245125": CoverageMapping(
        status="duplicate",
        canonical_name="reference_sadekov_white_profile_cta_export",
        style_families=("reference_sadekov_white_profile",),
        style_recipes=("sadekov_white_profile_minimal_v1",),
        notes="Exported white-profile CTA slide already mapped to node 1:9187.",
    ),
    "Light_2": CoverageMapping(
        status="duplicate",
        canonical_name="light_grain_glow",
        style_families=("reference_light_grain_glow",),
        style_recipes=("light_grain_glow_v1",),
        notes="Numbered light exports are treated as close aliases of the same grain-glow system.",
    ),
    "Light_3": CoverageMapping(
        status="duplicate",
        canonical_name="light_grain_glow",
        style_families=("reference_light_grain_glow",),
        style_recipes=("light_grain_glow_v1",),
        notes="Grouped into the same light glow family as `Light_1` pending more granular harvest work.",
    ),
    "Light_4": CoverageMapping(
        status="duplicate",
        canonical_name="light_grain_glow",
        style_families=("reference_light_grain_glow",),
        style_recipes=("light_grain_glow_v1",),
        notes="Grouped into the same light glow family as `Light_1` pending more granular harvest work.",
    ),
    "Light_6": CoverageMapping(
        status="duplicate",
        canonical_name="light_grain_glow",
        style_families=("reference_light_grain_glow",),
        style_recipes=("light_grain_glow_v1",),
        notes="Profile-heavy light export treated as a high-confidence alias of the light glow family.",
    ),
    "Tweet": CoverageMapping(
        status="duplicate",
        canonical_name="twitter_card_soft",
        style_families=("reference_twitter_card_soft",),
        style_recipes=("twitter_card_soft_v1",),
        notes="Tweet exports are treated as aliases of the tweet-card family.",
    ),
    "Twitter Post - Dim": CoverageMapping(
        status="duplicate",
        canonical_name="twitter_card_soft",
        style_families=("reference_twitter_card_soft",),
        style_recipes=("twitter_card_soft_v1",),
        notes="Theme variation of the same tweet-card structure.",
    ),
    "Twitter Post - Lights Out": CoverageMapping(
        status="duplicate",
        canonical_name="twitter_card_soft",
        style_families=("reference_twitter_card_soft",),
        style_recipes=("twitter_card_soft_v1",),
        notes="Theme variation of the same tweet-card structure.",
    ),
    "TwitterPost_02": CoverageMapping(
        status="duplicate",
        canonical_name="twitter_card_soft",
        style_families=("reference_twitter_card_soft",),
        style_recipes=("twitter_card_soft_v1",),
        notes="Soft-gradient tweet card export treated as a high-confidence alias of the covered tweet-card family.",
    ),
    "TwitterPost_08": CoverageMapping(
        status="duplicate",
        canonical_name="twitter_card_soft",
        style_families=("reference_twitter_card_soft",),
        style_recipes=("twitter_card_soft_v1",),
        notes="Repeated soft-card tweet exports grouped into the same tweet-card family for now.",
    ),
}


def _add_group(mapping_table: dict[str, CoverageMapping], names: tuple[str, ...], mapping: CoverageMapping) -> None:
    for name in names:
        mapping_table[name] = mapping


COVERED_GROUPS.update(
    {
        "1": CoverageMapping(
            status="covered",
            canonical_name="pastel_arrow_editorial",
            style_families=("reference_pastel_arrow_editorial",),
            style_recipes=("pastel_arrow_editorial_v1",),
            notes="Big-title pastel export family now maps to the pastel arrow editorial recipe.",
        ),
        "104": CoverageMapping(
            status="covered",
            canonical_name="pastel_arrow_editorial",
            style_families=("reference_pastel_arrow_editorial",),
            style_recipes=("pastel_arrow_editorial_v1",),
            notes="Arrow-led glow title export maps into the pastel arrow editorial family.",
        ),
        "11 3": CoverageMapping(
            status="covered",
            canonical_name="pastel_arrow_editorial",
            style_families=("reference_pastel_arrow_editorial",),
            style_recipes=("pastel_arrow_editorial_v1",),
            notes="Gradient-corner editorial text slides are now harvested into the pastel arrow family.",
        ),
        "120": CoverageMapping(
            status="covered",
            canonical_name="pastel_arrow_editorial",
            style_families=("reference_pastel_arrow_editorial",),
            style_recipes=("pastel_arrow_editorial_v1",),
            notes="Follow/CTA exports from the same pastel-arrow system are covered.",
        ),
        "2": CoverageMapping(
            status="covered",
            canonical_name="placeholder_media_glow",
            style_families=("reference_placeholder_media_glow",),
            style_recipes=("placeholder_media_glow_v1",),
            notes="Image-first placeholder exports now map to the placeholder media glow family.",
        ),
        "127": CoverageMapping(
            status="covered",
            canonical_name="device_mockup_gradient",
            style_families=("reference_device_mockup_gradient",),
            style_recipes=("device_mockup_gradient_v1",),
            notes="Phone-card social exports now map to the device mockup gradient family.",
        ),
        "148": CoverageMapping(
            status="covered",
            canonical_name="device_mockup_gradient",
            style_families=("reference_device_mockup_gradient",),
            style_recipes=("device_mockup_gradient_v1",),
            notes="Rounded device-card exports are covered by the device mockup gradient family.",
        ),
        "149": CoverageMapping(
            status="covered",
            canonical_name="device_mockup_gradient",
            style_families=("reference_device_mockup_gradient",),
            style_recipes=("device_mockup_gradient_v1",),
            notes="Alternate phone-card exports map into the same device mockup family.",
        ),
        "Carousel4": CoverageMapping(
            status="covered",
            canonical_name="social_proof_linkedin",
            style_families=("reference_social_proof_linkedin",),
            style_recipes=("social_proof_linkedin_v1",),
            notes="LinkedIn/social-proof poster exports are now covered by the social proof family.",
        ),
        "Carousel6": CoverageMapping(
            status="covered",
            canonical_name="profile_circle_pop",
            style_families=("reference_profile_circle_pop",),
            style_recipes=("profile_circle_pop_v1",),
            notes="Circle-profile creator posters now map to the profile circle pop family.",
        ),
        "Frame 34034": CoverageMapping(
            status="covered",
            canonical_name="profile_circle_pop",
            style_families=("reference_profile_circle_pop",),
            style_recipes=("profile_circle_pop_v1",),
            notes="Circle-profile CTA exports are covered by the profile circle pop family.",
        ),
        "Frame 34303": CoverageMapping(
            status="covered",
            canonical_name="profile_circle_pop",
            style_families=("reference_profile_circle_pop",),
            style_recipes=("profile_circle_pop_v1",),
            notes="Blue follow/creator exports now map into the profile circle pop family.",
        ),
        "Profile Picture": CoverageMapping(
            status="covered",
            canonical_name="profile_circle_pop",
            style_families=("reference_profile_circle_pop",),
            style_recipes=("profile_circle_pop_v1",),
            notes="Minimal profile-picture exports now map into the profile circle pop family.",
        ),
    }
)

_add_group(
    DUPLICATE_GROUPS,
    (
        "1971245112",
        "1971245113",
        "1971245114",
        "1971245115",
    ),
    CoverageMapping(
        status="duplicate",
        canonical_name="reference_sadekov_black_profile_export",
        style_families=("reference_sadekov_black_profile",),
        style_recipes=("sadekov_black_profile_minimal_v1",),
        notes="Additional black-profile exports are aliases of the covered Sadekov black profile family.",
    ),
)
_add_group(
    DUPLICATE_GROUPS,
    (
        "1971245121",
        "1971245122",
        "1971245123",
        "1971245124",
    ),
    CoverageMapping(
        status="duplicate",
        canonical_name="reference_sadekov_white_profile_export",
        style_families=("reference_sadekov_white_profile",),
        style_recipes=("sadekov_white_profile_minimal_v1",),
        notes="Additional white-profile exports are aliases of the covered Sadekov white profile family.",
    ),
)
_add_group(
    DUPLICATE_GROUPS,
    (
        "105",
        "106",
        "108",
        "109",
        "112",
        "113",
        "116",
        "117",
        "121",
        "123",
        "124",
        "150",
        "151",
        "154",
        "158",
        "159",
        "5",
        "Frame 6",
        "Frame 1",
        "Frame 15",
        "Frame 16",
        "Frame 17",
        "Frame 20",
        "Frame 21",
        "Frame 34304",
        "Frame 34306",
        "Frame 34307",
        "Frame 34308",
    ),
    CoverageMapping(
        status="duplicate",
        canonical_name="pastel_arrow_editorial",
        style_families=("reference_pastel_arrow_editorial",),
        style_recipes=("pastel_arrow_editorial_v1",),
        notes="Pastel glow titles, numbered cards, and follow/thank-you exports are aliases of the pastel arrow family.",
    ),
)
_add_group(
    DUPLICATE_GROUPS,
    (
        "28",
        "29",
        "32",
        "33",
        "36",
        "37",
        "40",
        "41",
        "44",
        "45",
    ),
    CoverageMapping(
        status="duplicate",
        canonical_name="placeholder_media_glow",
        style_families=("reference_placeholder_media_glow",),
        style_recipes=("placeholder_media_glow_v1",),
        notes="Image placeholder exports are aliases of the placeholder media glow family.",
    ),
)
_add_group(
    DUPLICATE_GROUPS,
    (
        "128",
        "131",
        "132",
        "135",
        "136",
        "139",
        "140",
        "142",
        "143",
        "146",
        "147",
        "Carousel5",
        "TwitterPost_01",
        "TwitterPost_03",
        "TwitterPost_04",
        "TwitterPost_05",
        "TwitterPost_06",
        "TwitterPost_07",
        "TwitterPost_09",
    ),
    CoverageMapping(
        status="duplicate",
        canonical_name="device_mockup_gradient",
        style_families=("reference_device_mockup_gradient",),
        style_recipes=("device_mockup_gradient_v1",),
        notes="Phone-card and gradient social-card exports are aliases of the device mockup gradient family.",
    ),
)
_add_group(
    DUPLICATE_GROUPS,
    (
        "155",
        "Carousel8",
        "Carousel8-9",
        "Carousel8-9bis",
        "Frame 19",
        "Frame 34305",
    ),
    CoverageMapping(
        status="duplicate",
        canonical_name="social_proof_linkedin",
        style_families=("reference_social_proof_linkedin",),
        style_recipes=("social_proof_linkedin_v1",),
        notes="Social-proof and LinkedIn poster exports are aliases of the social proof family.",
    ),
)
_add_group(
    DUPLICATE_GROUPS,
    (
        "Carousel6-1",
        "Carousel6-2",
        "Carousel6-3",
        "Carousel6-4",
        "Carousel6-5",
        "Carousel6-6",
        "Carousel6-7",
        "Carousel6-8",
        "Frame 18",
        "Frame 34309",
    ),
    CoverageMapping(
        status="duplicate",
        canonical_name="profile_circle_pop",
        style_families=("reference_profile_circle_pop",),
        style_recipes=("profile_circle_pop_v1",),
        notes="Circle-profile follow and creator exports are aliases of the profile circle pop family.",
    ),
)
_add_group(
    DUPLICATE_GROUPS,
    ("Figma vs Sketch_", "Figma vs Sketch_ "),
    CoverageMapping(
        status="duplicate",
        canonical_name="cp_gallery_wall",
        style_families=("reference_cp_gallery_wall",),
        style_recipes=("cp_gallery_wall_v1",),
        notes="Comparison-style infographic export is treated as an alias of the CP gallery wall family.",
    ),
)


GROUP_SUFFIX_PATTERN = re.compile(r"(.+?)(?:-\d+-\d+|-\d+)$")


def build_style_coverage_manifest(examples_dir: Path) -> dict[str, Any]:
    rows = collect_example_group_records(examples_dir)
    summary = {
        "total_groups": len(rows),
        "covered_groups": sum(1 for row in rows if row.status == "covered"),
        "duplicate_groups": sum(1 for row in rows if row.status == "duplicate"),
        "missing_groups": sum(1 for row in rows if row.status == "missing"),
    }
    return {
        "examples_dir": str(examples_dir),
        "summary": summary,
        "groups": [asdict(row) for row in rows],
    }


def collect_example_group_records(examples_dir: Path) -> list[ExampleGroupRecord]:
    grouped_files: dict[str, list[str]] = {}
    for file_path in sorted(examples_dir.iterdir()):
        if not file_path.is_file():
            continue
        group_name = normalize_example_group_name(file_path.stem)
        grouped_files.setdefault(group_name, []).append(file_path.name)

    rows: list[ExampleGroupRecord] = []
    for group_name in sorted(grouped_files):
        mapping = COVERED_GROUPS.get(group_name) or DUPLICATE_GROUPS.get(group_name)
        status = mapping.status if mapping else "missing"
        canonical_name = mapping.canonical_name if mapping else group_name
        style_families = mapping.style_families if mapping else ()
        style_recipes = mapping.style_recipes if mapping else ()
        notes = mapping.notes if mapping else "Present in local examples folder but not mapped into the current style engine."
        sample_files = tuple(grouped_files[group_name][:3])
        rows.append(
            ExampleGroupRecord(
                group_name=group_name,
                file_count=len(grouped_files[group_name]),
                sample_files=sample_files,
                status=status,
                canonical_name=canonical_name,
                style_families=style_families,
                style_recipes=style_recipes,
                notes=notes,
            )
        )
    return rows


def normalize_example_group_name(name: str) -> str:
    match = GROUP_SUFFIX_PATTERN.fullmatch(name)
    return match.group(1) if match else name


def render_style_coverage_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Style Coverage",
        "",
        "This report is generated from the local `Examples of carousels` folder and the current style-engine mappings in `tools/carousel_system/example_style_audit.py`.",
        "",
        "## Summary",
        f"- Total grouped example families: {manifest['summary']['total_groups']}",
        f"- Covered groups: {manifest['summary']['covered_groups']}",
        f"- Duplicate/alias groups: {manifest['summary']['duplicate_groups']}",
        f"- Missing or unmapped groups: {manifest['summary']['missing_groups']}",
        "",
    ]

    grouped_rows: dict[str, list[dict[str, Any]]] = {
        "covered": [],
        "duplicate": [],
        "missing": [],
    }
    for row in manifest["groups"]:
        grouped_rows[row["status"]].append(row)

    for section_name, section_title in (
        ("covered", "Covered"),
        ("duplicate", "Duplicate Or Alias"),
        ("missing", "Missing Or Unmapped"),
    ):
        lines.append(f"## {section_title}")
        if not grouped_rows[section_name]:
            lines.append("- None")
            lines.append("")
            continue
        for row in grouped_rows[section_name]:
            family_text = ", ".join(row["style_families"]) if row["style_families"] else "None"
            recipe_text = ", ".join(row["style_recipes"]) if row["style_recipes"] else "None"
            sample_text = ", ".join(row["sample_files"])
            lines.append(f"- `{row['group_name']}` ({row['file_count']} files)")
            lines.append(f"  Canonical: `{row['canonical_name']}`")
            lines.append(f"  Style families: {family_text}")
            lines.append(f"  Recipes: {recipe_text}")
            lines.append(f"  Samples: {sample_text}")
            lines.append(f"  Notes: {row['notes']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_style_coverage_json(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
