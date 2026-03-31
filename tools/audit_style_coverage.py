from __future__ import annotations

import argparse
import json
from pathlib import Path

from carousel_system.cli import run
from carousel_system.config import ROOT_DIR
from carousel_system.example_style_audit import (
    build_style_coverage_manifest,
    render_style_coverage_json,
    render_style_coverage_markdown,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit local example-style coverage against the current style engine."
    )
    parser.add_argument(
        "--examples-dir",
        default=str(ROOT_DIR / "Examples of carousels"),
        help="Directory containing local example exports.",
    )
    parser.add_argument(
        "--output-json",
        default=str(ROOT_DIR / ".tmp" / "style_coverage_manifest.json"),
        help="Path for the machine-readable JSON manifest.",
    )
    parser.add_argument(
        "--output-markdown",
        default=str(ROOT_DIR / "style_coverage.md"),
        help="Path for the human-readable markdown report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    examples_dir = Path(args.examples_dir)
    if not examples_dir.exists():
        raise FileNotFoundError(f"Examples directory not found: {examples_dir}")

    manifest = build_style_coverage_manifest(examples_dir)
    output_json = Path(args.output_json)
    output_markdown = Path(args.output_markdown)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(render_style_coverage_json(manifest), encoding="utf-8")
    output_markdown.write_text(render_style_coverage_markdown(manifest), encoding="utf-8")
    print(
        json.dumps(
            {
                "json_manifest": str(output_json),
                "markdown_report": str(output_markdown),
                "summary": manifest["summary"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run(main))
