from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from carousel_system.config import Settings
from carousel_system.image_assets import ImageRequest, PexelsCandidate, _find_and_cache_pexels_asset
from carousel_system.models import (
    CarouselInput,
    CarouselPlanResponse,
    ImageAsset,
    ImageStrategy,
    PerfectLibraryEntry,
    PerfectLibraryStatus,
    SlidePlan,
)
from carousel_system.payload import build_output_record
from carousel_system.perfect_library import active_perfect_library_requested_styles, load_perfect_library_status
from carousel_system.production import ProductionJobCreateRequest, create_production_job, production_library_payload
from carousel_system.render_bridge import acquire_next_render_item
from carousel_system.render_payload import build_plugin_render_payload
from carousel_system.style_library import select_style_recipe
from carousel_system.studio import (
    REVIEW_STYLE_BUCKETS,
    StudioCreateRequest,
    StudioState,
    _build_review_variant_specs,
    _consume_review_backlog,
    _request_for_next_review_round,
    _resolve_round_request,
)


def make_plan(cta_body: str = "Follow for more English teaching materials") -> CarouselPlanResponse:
    return CarouselPlanResponse(
        slides=[
            SlidePlan(slide_number=1, slide_role="hook", headline="Low-prep writing activities", body=None, design_role="cover"),
            SlidePlan(slide_number=2, slide_role="info", headline="Quick warm-up", body="Start with one focused prompt and a visible timer.", design_role="body"),
            SlidePlan(slide_number=3, slide_role="info", headline="Model the first line", body="Give students one example so they can enter faster.", design_role="body"),
            SlidePlan(slide_number=4, slide_role="info", headline="Reduce prep", body="Reuse the same worksheet with a different writing angle.", design_role="body"),
            SlidePlan(slide_number=5, slide_role="info", headline="Raise participation", body="Let students draft first, then share with a partner.", design_role="body"),
            SlidePlan(slide_number=6, slide_role="info", headline="Keep the pace", body="Use short reflection prompts instead of long corrections.", design_role="body"),
            SlidePlan(slide_number=7, slide_role="cta", headline="Follow for more English teaching materials", body=cta_body, design_role="cta"),
        ]
    )


def make_job(reference_style: str = "auto", generation_mode: str = "standard") -> CarouselInput:
    return CarouselInput(
        job_id="test-job",
        source="manual",
        generation_mode=generation_mode,
        topic="Low-prep writing activities that help English students think faster",
        reference_style=reference_style,
        reference_file_key="test-file",
    )


def make_settings() -> Settings:
    return Settings(
        openai_api_key="test-key",
        openai_model="gpt-4.1-mini",
        pexels_api_key="test",
        google_service_account_json=None,
        google_spreadsheet_id=None,
        google_worksheet_name="queue",
        figma_access_token=None,
        figma_reference_file_key="test-file",
        render_server_host="localhost",
        render_server_port=8765,
        render_queue_priority="production_only",
    )


class QualityRulesTests(unittest.TestCase):
    def test_perfect_library_manifest_loads_seed_entry(self) -> None:
        status = load_perfect_library_status()
        self.assertIsInstance(status, PerfectLibraryStatus)
        entry = next((item for item in status.entries if item.library_item_id == "placeholder-media-glow-perfect-v1"), None)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.status, "active")
        self.assertEqual(entry.style_recipe, "placeholder_media_glow_v1")
        self.assertIsNotNone(entry.visual_recipe)
        self.assertEqual(len(entry.visual_recipe.targets), 6)
        self.assertNotIn(7, {target.slide_number for target in entry.visual_recipe.targets})

    def test_production_library_payload_hides_inactive_entries(self) -> None:
        active_entry = PerfectLibraryEntry(
            library_item_id="active-entry",
            label="Active Entry",
            status="active",
            style_family="reference_placeholder_media_glow",
            style_recipe="placeholder_media_glow_v1",
        )
        inactive_entry = PerfectLibraryEntry(
            library_item_id="inactive-entry",
            label="Inactive Entry",
            status="inactive",
            style_family="reference_light_grain_glow",
            style_recipe="light_grain_glow_v1",
        )
        status = PerfectLibraryStatus(entries=[active_entry, inactive_entry])
        with patch("carousel_system.production.load_perfect_library_status", return_value=status):
            payload = production_library_payload()
        self.assertEqual([entry["library_item_id"] for entry in payload["entries"]], ["active-entry"])

    def test_create_production_job_sets_production_mode_and_requests_exports(self) -> None:
        settings = make_settings()

        def fake_resolve_images(_settings, record, payload) -> None:
            record.image_strategy = ImageStrategy(mode="stock", provider="pexels", reason="resolved")
            record.image_assets = [
                ImageAsset(
                    slide_number=1,
                    role="hook",
                    source_mode="stock",
                    provider="pexels",
                    query_or_prompt="teacher portrait classroom",
                    local_path="C:/tmp/slide-01.jpg",
                ),
                ImageAsset(
                    slide_number=2,
                    role="info",
                    source_mode="stock",
                    provider="pexels",
                    query_or_prompt="lesson planning desk materials",
                    local_path="C:/tmp/slide-02.jpg",
                ),
                ImageAsset(
                    slide_number=3,
                    role="info",
                    source_mode="stock",
                    provider="pexels",
                    query_or_prompt="english grammar workbook student notes",
                    local_path="C:/tmp/slide-03.jpg",
                ),
                ImageAsset(
                    slide_number=4,
                    role="info",
                    source_mode="stock",
                    provider="pexels",
                    query_or_prompt="students classroom activity",
                    local_path="C:/tmp/slide-04.jpg",
                ),
                ImageAsset(
                    slide_number=5,
                    role="info",
                    source_mode="stock",
                    provider="pexels",
                    query_or_prompt="online tutoring laptop lesson planning",
                    local_path="C:/tmp/slide-05.jpg",
                ),
                ImageAsset(
                    slide_number=6,
                    role="info",
                    source_mode="stock",
                    provider="pexels",
                    query_or_prompt="worksheets flashcards teaching materials",
                    local_path="C:/tmp/slide-06.jpg",
                ),
            ]

        request = ProductionJobCreateRequest(
            library_item_id="placeholder-media-glow-perfect-v1",
            topic="Low-prep writing activities that help English students think faster",
        )
        with patch("carousel_system.production.generate_carousel_plan", return_value=make_plan()), patch(
            "carousel_system.production.resolve_image_assets",
            side_effect=fake_resolve_images,
        ):
            job_record = create_production_job(settings, request)

        self.assertEqual(job_record.request.generation_mode, "production")
        self.assertEqual(job_record.request.library_item_id, "placeholder-media-glow-perfect-v1")
        self.assertEqual(job_record.request.output_modes, ["figma", "png"])
        self.assertEqual(job_record.style_recipe, "placeholder_media_glow_v1")
        self.assertEqual(job_record.visual_status, "visual_resolved")
        self.assertEqual(
            job_record.used_script,
            "\n\n".join(
                [
                    "Slide 1: Low-prep writing activities",
                    "Slide 2: Quick warm-up\nStart with one focused prompt and a visible timer.",
                    "Slide 3: Model the first line\nGive students one example so they can enter faster.",
                    "Slide 4: Reduce prep\nReuse the same worksheet with a different writing angle.",
                    "Slide 5: Raise participation\nLet students draft first, then share with a partner.",
                    "Slide 6: Keep the pace\nUse short reflection prompts instead of long corrections.",
                    "Slide 7: Follow for more English teaching materials\nFollow for more English teaching materials",
                ]
            ),
        )

    def test_production_job_warns_when_visual_recipe_is_missing(self) -> None:
        settings = make_settings()
        entry = PerfectLibraryEntry(
            library_item_id="warning-entry",
            label="Warning Entry",
            status="active",
            style_family="reference_placeholder_media_glow",
            style_recipe="placeholder_media_glow_v1",
            style_preference="placeholder_media",
            visual_recipe=None,
        )
        request = ProductionJobCreateRequest(library_item_id="warning-entry", topic="A useful classroom topic")

        with patch("carousel_system.production.get_perfect_library_entry", return_value=entry), patch(
            "carousel_system.production.generate_carousel_plan",
            return_value=make_plan(),
        ), patch("carousel_system.production.resolve_image_assets", return_value=None):
            job_record = create_production_job(settings, request)

        self.assertEqual(job_record.visual_status, "visual_warning")
        self.assertTrue(any(warning.code == "visual_recipe_missing" for warning in job_record.warnings))

    def test_production_request_preserves_multiline_script_and_notes(self) -> None:
        request = ProductionJobCreateRequest(
            library_item_id="placeholder-media-glow-perfect-v1",
            script="Hook line\r\nPoint one\r\n\r\nPoint two",
            notes="Keep it crisp.\r\nUse a classroom example.",
        )

        self.assertEqual(request.script, "Hook line\nPoint one\n\nPoint two")
        self.assertEqual(request.notes, "Keep it crisp.\nUse a classroom example.")

    def test_auto_selection_skips_specialty_manual_only_families(self) -> None:
        record = build_output_record(make_job("auto"), make_plan())
        recipe = select_style_recipe(record, "en")
        self.assertIn(recipe.selection_tier, {"review_safe", "default_auto"})

    def test_forced_specialty_family_is_still_available(self) -> None:
        record = build_output_record(make_job("social_proof"), make_plan())
        recipe = select_style_recipe(record, "en")
        self.assertEqual(recipe.style_recipe, "social_proof_linkedin_v1")
        self.assertEqual(recipe.selection_tier, "specialty_manual_only")

    def test_review_mode_explicit_non_safe_style_reaches_renderer_recipe(self) -> None:
        record = build_output_record(make_job("typography_light", generation_mode="review"), make_plan())
        recipe = select_style_recipe(record, "en")
        self.assertEqual(recipe.style_recipe, "typography_editorial_light_v1")
        self.assertEqual(recipe.selection_tier, "default_auto")

    def test_review_mode_auto_selection_prioritizes_least_safe_recipe_tier(self) -> None:
        record = build_output_record(make_job("auto", generation_mode="review"), make_plan())
        recipe = select_style_recipe(record, "en")
        self.assertEqual(recipe.selection_tier, "specialty_manual_only")

    def test_placeholder_cta_defaults_to_headline_and_button_only(self) -> None:
        record = build_output_record(make_job("placeholder_media"), make_plan())
        payload = build_plugin_render_payload(record, source_artifact_path=Path("test-job.json"))
        cta_slide = payload.slides[-1]
        self.assertEqual(cta_slide.layout_variant, "cta_dark_glow")
        self.assertIsNone(cta_slide.body_display)
        self.assertIsNone(cta_slide.supporting_text)
        self.assertTrue(cta_slide.button_label)

    def test_light_glow_hook_uses_shortened_copy_when_cover_is_dense(self) -> None:
        plan = make_plan()
        plan.slides[0].headline = "Boost English Learners' Thinking Speed with These Low-Prep Writing Activities!"
        record = build_output_record(make_job("light_glow"), plan)
        payload = build_plugin_render_payload(record, source_artifact_path=Path("test-job.json"))
        cover_slide = payload.slides[0]
        self.assertEqual(cover_slide.headline_display, cover_slide.headline_short)
        self.assertEqual(cover_slide.max_headline_lines, 3)

    def test_placeholder_media_hook_uses_shortened_copy_when_cover_is_dense(self) -> None:
        plan = make_plan()
        plan.slides[0].headline = "Boost Your English Students' Speedy Thinking with These Low-Prep Writing Activities!"
        record = build_output_record(make_job("placeholder_media"), plan)
        payload = build_plugin_render_payload(record, source_artifact_path=Path("test-job.json"))
        cover_slide = payload.slides[0]
        self.assertEqual(cover_slide.headline_display, cover_slide.headline_short)
        self.assertEqual(cover_slide.max_headline_lines, 3)

    def test_device_mockup_dense_body_uses_shortened_stack_copy(self) -> None:
        plan = make_plan()
        plan.slides[1].headline = "Quick prompts that ignite thinking in seconds"
        plan.slides[1].body = (
            "Use rapid-fire questions, timed pair talk, and visible response cues to sharpen thinking, "
            "reduce hesitation, and keep language moving without overexplaining the task."
        )
        record = build_output_record(make_job("device_mockup"), plan)
        payload = build_plugin_render_payload(record, source_artifact_path=Path("test-job.json"))
        body_slide = payload.slides[1]
        self.assertEqual(body_slide.headline_display, body_slide.headline_short)
        self.assertEqual(body_slide.body_display, body_slide.body_short)
        self.assertEqual(body_slide.max_headline_lines, 2)
        self.assertEqual(body_slide.max_body_lines, 4)

    def test_image_picker_refuses_exact_reuse_when_all_candidates_are_taken(self) -> None:
        settings = Settings(
            openai_api_key=None,
            openai_model="gpt-4.1-mini",
            pexels_api_key="test",
            google_service_account_json=None,
            google_spreadsheet_id=None,
            google_worksheet_name="queue",
            figma_access_token=None,
            figma_reference_file_key="test-file",
            render_server_host="localhost",
            render_server_port=8765,
            render_queue_priority="sheets_first",
        )
        record = build_output_record(make_job("placeholder_media"), make_plan())
        image_request = ImageRequest(
            slide_number=2,
            role="info",
            slot="body_media",
            treatment="blur_glow",
            query="lesson planning desk materials",
            reason="test",
        )
        candidate = PexelsCandidate(
            photo_id=123,
            width=1000,
            height=1500,
            alt_text="lesson planning desk materials",
            photographer="Tester",
            page_url=None,
            download_url="https://images.pexels.com/photos/123/test.jpg",
        )
        with patch("carousel_system.image_assets._search_pexels_candidates", return_value=[candidate]):
            asset = _find_and_cache_pexels_asset(
                settings,
                record,
                image_request,
                used_photo_ids={123},
                used_alt_signatures={"lesson planning desk materials"},
            )
        self.assertIsNone(asset)

    def test_review_mode_preserves_explicit_non_safe_preferred_style(self) -> None:
        request = StudioCreateRequest(review_mode=True, preferred_style="typography_light")
        resolved = _resolve_round_request(request)
        self.assertEqual(resolved.preferred_style, "typography_light")

    def test_review_variants_lock_to_explicit_style_instead_of_falling_back(self) -> None:
        request = StudioCreateRequest(review_mode=True, preferred_style="typography_light", base_copy_length="balanced")
        specs = _build_review_variant_specs(request, round_number=1, previous_round=None)
        self.assertEqual(len(specs), 3)
        self.assertTrue(all(spec.requested_style == "typography_light" for spec in specs))

    def test_review_auto_variants_prioritize_styles_outside_safe_pool(self) -> None:
        request = StudioCreateRequest(review_mode=True, preferred_style="auto", base_copy_length="balanced")
        specs = _build_review_variant_specs(request, round_number=1, previous_round=None, studio_state=StudioState())
        specialty_values = set(REVIEW_STYLE_BUCKETS["specialty_manual_only"])
        self.assertEqual(len(specs), 3)
        self.assertTrue(all(spec.requested_style in specialty_values for spec in specs))

    def test_review_auto_backlog_skips_styles_already_promoted_to_perfect_library(self) -> None:
        request = StudioCreateRequest(review_mode=True, preferred_style="auto", base_copy_length="balanced")
        specs = _build_review_variant_specs(request, round_number=1, previous_round=None, studio_state=StudioState())
        excluded = active_perfect_library_requested_styles()
        self.assertTrue(excluded)
        self.assertTrue(all(spec.requested_style not in excluded for spec in specs))

    def test_review_auto_backlog_does_not_repeat_styles_before_cycle_exhaustion(self) -> None:
        state = StudioState()
        first = _consume_review_backlog(state, count=3)
        second = _consume_review_backlog(state, count=3)
        self.assertEqual(len(first), 3)
        self.assertEqual(len(second), 3)
        self.assertTrue(set(first).isdisjoint(set(second)))

    def test_studio_only_bridge_falls_back_to_production_jobs(self) -> None:
        settings = make_settings()
        settings = Settings(
            openai_api_key=settings.openai_api_key,
            openai_model=settings.openai_model,
            pexels_api_key=settings.pexels_api_key,
            google_service_account_json=settings.google_service_account_json,
            google_spreadsheet_id=settings.google_spreadsheet_id,
            google_worksheet_name=settings.google_worksheet_name,
            figma_access_token=settings.figma_access_token,
            figma_reference_file_key=settings.figma_reference_file_key,
            render_server_host=settings.render_server_host,
            render_server_port=settings.render_server_port,
            render_queue_priority="studio_only",
        )
        with patch("carousel_system.render_bridge._acquire_studio_render_item", return_value=None), patch(
            "carousel_system.render_bridge._acquire_production_render_item",
            return_value="production-item",
        ):
            item = acquire_next_render_item(settings, queue=None)
        self.assertEqual(item, "production-item")

    def test_next_review_round_keeps_winner_style_even_when_not_review_safe(self) -> None:
        previous_round = SimpleNamespace(
            request=StudioCreateRequest(review_mode=True, preferred_style="typography_light", base_copy_length="balanced"),
            niche_preset="english_teacher_materials",
            generated_brief="How to create clear lesson slides for English teachers",
            winner_variant_id="variant-1",
            variants=[
                SimpleNamespace(
                    variant_id="variant-1",
                    ordinal=1,
                    requested_style="typography_light",
                    copy_length="expanded",
                    rating="love",
                    winner_feedback=None,
                    rejection_note=None,
                )
            ],
        )
        next_request = _request_for_next_review_round(previous_round)
        self.assertEqual(next_request.preferred_style, "typography_light")
        self.assertEqual(next_request.base_copy_length, "expanded")


if __name__ == "__main__":
    unittest.main()
