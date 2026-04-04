from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from carousel_system.config import Settings
from carousel_system.image_assets import ImageRequest, PexelsCandidate, _find_and_cache_pexels_asset
from carousel_system.models import CarouselInput, CarouselPlanResponse, SlidePlan
from carousel_system.payload import build_output_record
from carousel_system.render_payload import build_plugin_render_payload
from carousel_system.style_library import select_style_recipe


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


def make_job(reference_style: str = "auto") -> CarouselInput:
    return CarouselInput(
        job_id="test-job",
        source="manual",
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

    def test_placeholder_cta_defaults_to_headline_and_button_only(self) -> None:
        record = build_output_record(make_job("placeholder_media"), make_plan())
        payload = build_plugin_render_payload(record, source_artifact_path=Path("test-job.json"))
        cta_slide = payload.slides[-1]
        self.assertEqual(cta_slide.layout_variant, "cta_dark_glow")
        self.assertIsNone(cta_slide.body_display)
        self.assertIsNone(cta_slide.supporting_text)
        self.assertTrue(cta_slide.button_label)

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


if __name__ == "__main__":
    unittest.main()
