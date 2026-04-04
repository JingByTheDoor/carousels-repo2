from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from carousel_system.config import ROOT_DIR


FEEDBACK_DIR = ROOT_DIR / "notes" / "review_feedback"
DEFAULT_JSON_OUTPUT = ROOT_DIR / ".tmp" / "review_feedback_audit.json"
DEFAULT_MD_OUTPUT = ROOT_DIR / ".tmp" / "review_feedback_audit.md"

ISSUE_PATTERNS = {
    "overlap": re.compile(r"text (?:is )?over|over each other|overlap|glitched", re.IGNORECASE),
    "whitespace": re.compile(r"too much white space|blank space|underfilled|too much whitespace", re.IGNORECASE),
    "cta_duplication": re.compile(r"cta.*repeat|repeats the same|same thing as the title|last slide.*wierd text|last slide.*doesn't mak sense|misgeneration.*last slide", re.IGNORECASE),
    "weak_images": re.compile(r"same on 2 and 4|same images|different images|image.*too thin|wonky|duplicate.*photo", re.IGNORECASE),
    "decorative_mismatch": re.compile(r"random squares|like comment save buttons|not needed|device shell|phone fram", re.IGNORECASE),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize recurring issues from saved Studio review feedback.")
    parser.add_argument("--feedback-dir", default=str(FEEDBACK_DIR))
    parser.add_argument("--output-json", default=str(DEFAULT_JSON_OUTPUT))
    parser.add_argument("--output-md", default=str(DEFAULT_MD_OUTPUT))
    return parser.parse_args()


def collect_feedback_entries(feedback_dir: Path) -> list[dict]:
    entries: list[dict] = []
    for path in sorted(feedback_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        round_id = payload.get("round_id") or path.stem
        for bucket in ("winner", "losers"):
            block = payload.get(bucket)
            if not block:
                continue
            variants = [block] if bucket == "winner" else block
            for variant in variants:
                feedback = (variant.get("feedback") or "").strip()
                if not feedback:
                    continue
                entries.append(
                    {
                        "round_id": round_id,
                        "style_family": variant.get("style_family") or "unknown",
                        "style": variant.get("style") or "unknown",
                        "feedback": feedback,
                    }
                )
    return entries


def classify_feedback(entries: list[dict]) -> dict:
    issue_counts = Counter()
    family_counts: dict[str, Counter] = defaultdict(Counter)

    for entry in entries:
        matched = False
        for issue, pattern in ISSUE_PATTERNS.items():
            if pattern.search(entry["feedback"]):
                issue_counts[issue] += 1
                family_counts[entry["style_family"]][issue] += 1
                matched = True
        if not matched:
            issue_counts["uncategorized"] += 1
            family_counts[entry["style_family"]]["uncategorized"] += 1

    return {
        "feedback_entries": len(entries),
        "issue_counts": dict(issue_counts.most_common()),
        "family_issue_counts": {
            family: dict(counter.most_common())
            for family, counter in sorted(family_counts.items())
        },
    }


def write_outputs(summary: dict, json_output: Path, md_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Review Feedback Audit",
        "",
        f"- Feedback entries: {summary['feedback_entries']}",
        "",
        "## Issue Counts",
    ]
    for issue, count in summary["issue_counts"].items():
        lines.append(f"- `{issue}`: {count}")

    lines.append("")
    lines.append("## By Style Family")
    for family, counts in summary["family_issue_counts"].items():
        counts_text = ", ".join(f"{issue}={count}" for issue, count in counts.items())
        lines.append(f"- `{family}`: {counts_text}")

    md_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    feedback_dir = Path(args.feedback_dir)
    entries = collect_feedback_entries(feedback_dir)
    summary = classify_feedback(entries)
    write_outputs(summary, Path(args.output_json), Path(args.output_md))
    print(Path(args.output_json))
    print(Path(args.output_md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
