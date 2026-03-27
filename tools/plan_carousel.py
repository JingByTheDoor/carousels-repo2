from __future__ import annotations

import argparse
from pathlib import Path
from uuid import uuid4

from carousel_system.cli import run
from carousel_system.config import ROOT_DIR, load_settings
from carousel_system.models import CarouselInput
from carousel_system.payload import build_output_record, write_output_record
from carousel_system.planner import generate_carousel_plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a 7-slide carousel payload.")
    parser.add_argument("--job-id", default=f"manual-{uuid4().hex[:8]}")
    parser.add_argument("--topic")
    parser.add_argument("--script")
    parser.add_argument("--script-file")
    parser.add_argument("--cta-text")
    parser.add_argument(
        "--aspect-ratio",
        default="portrait_1080x1350",
        choices=["square_1080", "portrait_1080x1350"],
    )
    parser.add_argument("--output-modes", default="figma,png")
    parser.add_argument("--reference-style", default="alder_1")
    parser.add_argument("--notes")
    parser.add_argument("--output-path")
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

    job = CarouselInput(
        job_id=args.job_id,
        source="manual",
        topic=args.topic,
        script=script_text,
        cta_text=args.cta_text,
        aspect_ratio=args.aspect_ratio,
        output_modes=[mode.strip() for mode in args.output_modes.split(",") if mode.strip()],
        reference_style=args.reference_style,
        reference_file_key=settings.figma_reference_file_key,
        notes=args.notes,
    )

    plan = generate_carousel_plan(settings, job)
    record = build_output_record(job, plan)
    write_output_record(output_path, record)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
