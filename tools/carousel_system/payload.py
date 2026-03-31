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
    "1:46201": ("typography slide 1", "cta"),
    "1:46227": ("Alder_1", "cover"),
    "1:46232": ("Alder_1", "body"),
    "1:46239": ("Alder_1", "palette"),
    "1:46248": ("Alder_1", "body"),
    "1:46256": ("Alder_1", "body"),
    "1:46264": ("Alder_1", "body"),
    "1:46271": ("CP_3", "cover"),
    "1:46277": ("CP_3", "body"),
    "1:46283": ("CP_3", "layout"),
    "1:46288": ("typography slide 2", "cta"),
    "1:46485": ("1971245499", "layout"),
    "1:9052": ("1971245110", "cover"),
    "1:9064": ("1971245119", "cover"),
    "1:9076": ("1971245111", "body"),
    "1:9086": ("1971245120", "body"),
    "1:9176": ("1971245118", "cta"),
    "1:9187": ("1971245125", "cta"),
    "1:14767": ("typography light editorial", "body"),
    "1:14775": ("typography light dark-cover", "cover"),
    "1:14788": ("typography light cta", "cta"),
    "local:01-long-title": ("01 – Long Title", "cover"),
    "local:02-title": ("02 – Title", "body"),
    "local:03-copy": ("03 – Copy", "body"),
    "local:05-call-to-action": ("05 – Call to Action", "cta"),
    "local:light-1": ("Light_1", "cover"),
    "local:light-2": ("Light_2", "body"),
    "local:light-6": ("Light_6", "cta"),
    "local:title-01": ("Title (01)", "cta"),
    "local:twitter-post-default": ("Twitter Post - Default", "body"),
    "local:twitter-post-soft": ("TwitterPost_02", "cover"),
}


def build_design_reference_log(job: CarouselInput) -> list[DesignReferenceLog]:
    references: list[DesignReferenceLog] = []
    for node_id in job.reference_node_ids:
        node_name, usage = REFERENCE_NODE_DETAILS.get(node_id, ("Unknown", "palette"))
        file_key = "local_examples" if node_id.startswith("local:") else job.reference_file_key
        references.append(
            DesignReferenceLog(
                file_key=file_key,
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
