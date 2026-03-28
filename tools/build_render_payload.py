from __future__ import annotations

import argparse
from pathlib import Path

from carousel_system.cli import run
from carousel_system.config import ROOT_DIR
from carousel_system.models import CarouselOutput
from carousel_system.payload import write_output_record
from carousel_system.render_payload import (
    build_plugin_render_payload,
    build_render_artifact,
    write_plugin_render_payload,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Figma plugin render payload from a planned job.")
    parser.add_argument("--job-id")
    parser.add_argument("--job-path")
    parser.add_argument("--render-payload-path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    job_path = resolve_job_path(args.job_id, args.job_path)
    render_payload_path = (
        Path(args.render_payload_path)
        if args.render_payload_path
        else ROOT_DIR / ".tmp" / "render-jobs" / f"{job_path.stem}.render.json"
    )

    record = CarouselOutput.model_validate_json(job_path.read_text(encoding="utf-8"))
    payload = build_plugin_render_payload(record, source_artifact_path=job_path)
    record.language = payload.language
    record.style_family = payload.style_family
    record.style_recipe = payload.style_recipe
    record.design_reference_log = [
        reference for reference in record.design_reference_log if reference.node_id in set(payload.reference_node_ids)
    ]
    record.render_artifact = build_render_artifact(render_payload_path, payload)
    write_output_record(job_path, record)
    write_plugin_render_payload(render_payload_path, payload)
    print(render_payload_path)
    return 0


def resolve_job_path(job_id: str | None, job_path: str | None) -> Path:
    if job_path:
        return Path(job_path)
    if not job_id:
        raise ValueError("Either --job-id or --job-path is required.")
    return ROOT_DIR / ".tmp" / "jobs" / f"{job_id}.json"


if __name__ == "__main__":
    raise SystemExit(run(main))
