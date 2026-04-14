from __future__ import annotations

import unittest

from carousel_system.models import CarouselInput
from carousel_system.models import DEFAULT_PROMPT_VERSION
from carousel_system.planner import PROMPT_VERSION, SYSTEM_PROMPT, build_user_prompt


class PlannerPromptTests(unittest.TestCase):
    def test_prompt_versions_stay_in_sync(self) -> None:
        self.assertEqual(PROMPT_VERSION, "baseline_v6")
        self.assertEqual(DEFAULT_PROMPT_VERSION, PROMPT_VERSION)

    def test_system_prompt_includes_translated_script_writer_rules(self) -> None:
        self.assertIn("polarizing, curiosity-driven, surprising, or provocative", SYSTEM_PROMPT)
        self.assertIn("40 characters or fewer", SYSTEM_PROMPT)
        self.assertIn("Stay within 160 characters whenever possible", SYSTEM_PROMPT)
        self.assertIn('Avoid banal rhetorical prompts such as "are you with us or against us?"', SYSTEM_PROMPT)
        self.assertIn("Slide 6 must land the final substantive point", SYSTEM_PROMPT)
        self.assertIn("Treat the notes field as high-priority planner guidance", SYSTEM_PROMPT)
        self.assertIn("Keep the original custom-prompt style intact. Only the output container changes.", SYSTEM_PROMPT)
        self.assertIn("TITLE -> headline and TEXT -> body", SYSTEM_PROMPT)
        self.assertIn("It changes the planning constraints, not the core voice.", SYSTEM_PROMPT)

    def test_user_prompt_exposes_automation_context(self) -> None:
        job = CarouselInput(
            job_id="test-job",
            source="manual",
            generation_mode="review",
            library_item_id="placeholder-media-glow-perfect-v1",
            niche_preset="english_teacher_materials",
            topic="Useful materials for shy English learners",
            cta_text="Follow for more English teaching materials",
            language="en",
            reference_style="placeholder_media",
            reference_file_key="test-file",
            notes="Copy profile: tight. Audience: English teachers.",
        )
        prompt = build_user_prompt(job)
        self.assertIn("generation_mode: review", prompt)
        self.assertIn("library_item_id: placeholder-media-glow-perfect-v1", prompt)
        self.assertIn("niche_preset: english_teacher_materials", prompt)
        self.assertIn("Only the response shape changes from TITLE/TEXT blocks to headline/body fields.", prompt)
        self.assertIn("Slide 6 should complete the argument before the CTA placeholder.", prompt)
        self.assertIn("Follow notes as planner instructions", prompt)


if __name__ == "__main__":
    unittest.main()
