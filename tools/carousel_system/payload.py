from __future__ import annotations

from pathlib import Path

from carousel_system.models import (
    DEFAULT_PROMPT_VERSION,
    CarouselInput,
    CarouselOutput,
    CarouselPlanResponse,
    DesignReferenceLog,
    SourceSync,
)


REFERENCE_NODE_DETAILS = {
    "1:46184": ("CP_3", "cover"),
    "1:46190": ("CP_3", "body"),
    "1:46227": ("Alder_1", "cover"),
    "1:46232": ("Alder_1", "body"),
    "1:46239": ("Alder_1", "palette"),
    "1:46201": ("typography slide 1", "cta"),
    "1:46288": ("typography slide 2", "cta"),
    "1:46485": ("1971245499", "layout"),
}


def build_design_reference_log(job: CarouselInput) -> list[DesignReferenceLog]:
    references: list[DesignReferenceLog] = []
    for node_id in job.reference_node_ids:
        node_name, usage = REFERENCE_NODE_DETAILS.get(node_id, ("Unknown", "palette"))
        references.append(
            DesignReferenceLog(
                file_key=job.reference_file_key,
                node_id=node_id,
                node_name=node_name,
                usage=usage,
            )
        )
    return references


def build_output_record(
    job: CarouselInput,
    plan: CarouselPlanResponse,
    *,
    source_sync: SourceSync | None = None,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    language: str | None = None,
) -> CarouselOutput:
    return CarouselOutput(
        job_id=job.job_id,
        status="planned",
        normalized_input=job,
        prompt_version=prompt_version,
        language=language,
        content_plan=plan.slides,
        design_reference_log=build_design_reference_log(job),
        source_sync=source_sync or SourceSync(),
    )


def write_output_record(output_path: Path, record: CarouselOutput) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
    return output_path
