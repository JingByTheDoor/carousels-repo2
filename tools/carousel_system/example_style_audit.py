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
