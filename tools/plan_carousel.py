from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import uuid4

from carousel_system.cli import run
from carousel_system.config import ROOT_DIR, load_settings
from carousel_system.models import CarouselInput
from carousel_system.payload import build_output_record, write_output_record
from carousel_system.planner import PROMPT_VERSION, generate_carousel_plan
from carousel_system.render_payload import (
    build_plugin_render_payload,
    build_render_artifact,
    infer_language,
    write_plugin_render_payload,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a 7-slide carousel payload.")
    parser.add_argument("--job-id", default=f"manual-{uuid4().hex[:8]}")
    parser.add_argument("--topic")
    parser.add_argument("--script")
    parser.add_argument("--script-file")
    parser.add_argument("--cta-text")
    parser.add_argument("--language")
    parser.add_argument(
        "--aspect-ratio",
        default="portrait_1080x1350",
        choices=["square_1080", "portrait_1080x1350"],
    )
    parser.add_argument("--output-modes", default="figma,png")
    parser.add_argument("--reference-style", default="alder_1")
    parser.add_argument("--notes")
    parser.add_argument("--output-path")
    parser.add_argument("--render-payload-path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = load_settings(require_openai=True)

    script_text = args.script
    if args.script_file:
        script_text = Path(args.script_file).read_text(encoding="utf-8")

    output_path = (
        Path(args.output_path)
        if args.output_path
        else ROOT_DIR / ".tmp" / "jobs" / f"{args.job_id}.json"
    )
    render_payload_path = (
        Path(args.render_payload_path)
        if args.render_payload_path
        else ROOT_DIR / ".tmp" / "render-jobs" / f"{args.job_id}.render.json"
    )

    job = CarouselInput(
        job_id=args.job_id,
        source="manual",
        topic=args.topic,
        script=script_text,
        cta_text=args.cta_text,
        language=args.language,
        aspect_ratio=args.aspect_ratio,
        output_modes=[mode.strip() for mode in args.output_modes.split(",") if mode.strip()],
        reference_style=args.reference_style,
        reference_file_key=settings.figma_reference_file_key,
        notes=args.notes,
    )

    plan = generate_carousel_plan(settings, job)
    record = build_output_record(job, plan, prompt_version=PROMPT_VERSION, language=job.language)
    render_payload = build_plugin_render_payload(record, source_artifact_path=output_path)
    record.language = render_payload.language or infer_language(record)
    record.style_family = render_payload.style_family
    record.style_recipe = render_payload.style_recipe
    record.render_artifact = build_render_artifact(render_payload_path, render_payload)
    write_output_record(output_path, record)
    write_plugin_render_payload(render_payload_path, render_payload)
    print(
        json.dumps(
            {
                "job_artifact": str(output_path),
                "render_payload": str(render_payload_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
