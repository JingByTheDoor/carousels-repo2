from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from carousel_system.config import Settings
from carousel_system.image_assets import ImageRequest, PexelsCandidate, _find_and_cache_pexels_asset
from carousel_system.models import CarouselInput, CarouselPlanResponse, SlidePlan
from carousel_system.payload import build_output_record
from carousel_system.render_payload import build_plugin_render_payload
from carousel_system.style_library import select_style_recipe
from carousel_system.studio import (
    REVIEW_STYLE_BUCKETS,
    StudioCreateRequest,
    _build_review_variant_specs,
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


class QualityRulesTests(unittest.TestCase):
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
        specs = _build_review_variant_specs(request, round_number=1, previous_round=None)
        specialty_values = set(REVIEW_STYLE_BUCKETS["specialty_manual_only"])
        self.assertEqual(len(specs), 3)
        self.assertTrue(all(spec.requested_style in specialty_values for spec in specs))

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
