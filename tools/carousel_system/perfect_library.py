from __future__ import annotations

from pathlib import Path

from carousel_system.config import DEFAULT_REFERENCE_FILE_KEY, ROOT_DIR
from carousel_system.models import (
    PerfectLibraryEntry,
    PerfectLibraryStatus,
    PerfectVisualRecipe,
    PerfectVisualTarget,
)


PERFECT_LIBRARY_DIR = ROOT_DIR / "notes" / "perfect_library"
PERFECT_LIBRARY_PATH = PERFECT_LIBRARY_DIR / "perfect_library.json"


def _default_status() -> PerfectLibraryStatus:
    return PerfectLibraryStatus(
        updated_at="2026-04-05T00:00:00Z",
        entries=[
            PerfectLibraryEntry(
                library_item_id="placeholder-media-glow-perfect-v1",
                label="Placeholder Media Glow",
                status="active",
                style_family="reference_placeholder_media_glow",
                style_recipe="placeholder_media_glow_v1",
                style_preference="placeholder_media",
                reference_file_key=DEFAULT_REFERENCE_FILE_KEY,
                reference_node_ids=["local:light-1", "local:light-2", "local:light-6"],
                visual_recipe=PerfectVisualRecipe(
                    description=(
                        "Bright editorial teaching-materials photography with one strong cover image "
                        "and supporting inline classroom/materials visuals."
                    ),
                    source_mode="hybrid",
                    default_focus="brand_safe",
                    default_query_suffix="editorial education photography professional clean",
                    targets=[
                        PerfectVisualTarget(
                            slide_number=1,
                            slot="cover_media",
                            treatment="blur_glow",
                            asset_kind="photo",
                            query_suffix="teacher portrait classroom whiteboard",
                        ),
                        PerfectVisualTarget(
                            slide_number=2,
                            slot="body_media",
                            treatment="blur_glow",
                            asset_kind="photo",
                            query_suffix="lesson planning desk materials",
                        ),
                        PerfectVisualTarget(
                            slide_number=3,
                            slot="body_media",
                            treatment="blur_glow",
                            asset_kind="photo",
                            query_suffix="english grammar workbook student notes",
                        ),
                        PerfectVisualTarget(
                            slide_number=4,
                            slot="body_media",
                            treatment="blur_glow",
                            asset_kind="photo",
                            query_suffix="students classroom activity",
                        ),
                        PerfectVisualTarget(
                            slide_number=5,
                            slot="body_media",
                            treatment="blur_glow",
                            asset_kind="photo",
                            query_suffix="online tutoring laptop lesson planning",
                        ),
                        PerfectVisualTarget(
                            slide_number=6,
                            slot="body_media",
                            treatment="blur_glow",
                            asset_kind="photo",
                            query_suffix="worksheets flashcards teaching materials",
                        ),
                    ],
                ),
                approval_notes="First manually promoted production-safe template.",
                approved_at="2026-04-05",
                approved_by="manual_curation",
                notes="Seed entry for the new perfect library production workflow.",
            )
        ],
    )


def ensure_perfect_library_manifest() -> Path:
    if PERFECT_LIBRARY_PATH.exists():
        return PERFECT_LIBRARY_PATH
    PERFECT_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    PERFECT_LIBRARY_PATH.write_text(_default_status().model_dump_json(indent=2), encoding="utf-8")
    return PERFECT_LIBRARY_PATH


def load_perfect_library_status() -> PerfectLibraryStatus:
    ensure_perfect_library_manifest()
    return PerfectLibraryStatus.model_validate_json(PERFECT_LIBRARY_PATH.read_text(encoding="utf-8"))


def save_perfect_library_status(status: PerfectLibraryStatus) -> Path:
    PERFECT_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    PERFECT_LIBRARY_PATH.write_text(status.model_dump_json(indent=2), encoding="utf-8")
    return PERFECT_LIBRARY_PATH


def list_perfect_library_entries(*, active_only: bool = False) -> list[PerfectLibraryEntry]:
    entries = load_perfect_library_status().entries
    if active_only:
        return [entry for entry in entries if entry.status == "active"]
    return entries


def get_perfect_library_entry(library_item_id: str) -> PerfectLibraryEntry | None:
    normalized = (library_item_id or "").strip()
    if not normalized:
        return None
    for entry in list_perfect_library_entries(active_only=False):
        if entry.library_item_id == normalized:
            return entry
    return None


def active_perfect_library_requested_styles() -> set[str]:
    styles: set[str] = set()
    for entry in list_perfect_library_entries(active_only=True):
        if entry.style_preference:
            styles.add(entry.style_preference)
    return styles


def active_perfect_library_style_recipes() -> set[str]:
    return {entry.style_recipe for entry in list_perfect_library_entries(active_only=True)}
