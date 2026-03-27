from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


DEFAULT_REFERENCE_NODE_IDS = ["1:46227", "1:46232", "1:46239", "1:46288", "1:46485"]


class CarouselInput(BaseModel):
    job_id: str = Field(min_length=1)
    source: Literal["manual", "google_sheets"]
    topic: str | None = None
    script: str | None = None
    cta_text: str | None = None
    aspect_ratio: Literal["square_1080", "portrait_1080x1350"] = "portrait_1080x1350"
    output_modes: list[Literal["figma", "png"]] = Field(default_factory=lambda: ["figma", "png"])
    reference_style: str = "alder_1"
    reference_file_key: str
    reference_node_ids: list[str] = Field(default_factory=lambda: DEFAULT_REFERENCE_NODE_IDS.copy())
    notes: str | None = None

    @field_validator("topic", "script", "cta_text", "notes", mode="before")
    @classmethod
    def _strip_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def _validate_input(self) -> "CarouselInput":
        if not self.topic and not self.script:
            raise ValueError("At least one of topic or script is required.")
        return self


class SlidePlan(BaseModel):
    slide_number: int
    slide_role: Literal["hook", "info", "cta"]
    headline: str = Field(min_length=1)
    body: str | None = None
    design_role: Literal["cover", "body", "cta"]

    @field_validator("headline", "body", mode="before")
    @classmethod
    def _normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class CarouselPlanResponse(BaseModel):
    slides: list[SlidePlan]

    @model_validator(mode="after")
    def _validate_slide_structure(self) -> "CarouselPlanResponse":
        if len(self.slides) != 7:
            raise ValueError("Carousel plan must contain exactly 7 slides.")

        expected_roles = ["hook", "info", "info", "info", "info", "info", "cta"]
        expected_design_roles = ["cover", "body", "body", "body", "body", "body", "cta"]

        for index, slide in enumerate(self.slides, start=1):
            if slide.slide_number != index:
                raise ValueError("Slides must be numbered 1 through 7 in order.")
            if slide.slide_role != expected_roles[index - 1]:
                raise ValueError("Slide roles must follow hook, info x5, cta.")
            if slide.design_role != expected_design_roles[index - 1]:
                raise ValueError("Design roles must follow cover, body x5, cta.")
            if slide.slide_role == "info" and not slide.body:
                raise ValueError("Informational slides must include body text.")

        return self


class DesignReferenceLog(BaseModel):
    file_key: str
    node_id: str
    node_name: str
    usage: Literal["cover", "body", "cta", "palette", "layout"]


class FigmaOutput(BaseModel):
    file_key: str | None = None
    file_url: str | None = None
    page_name: str | None = None
    slide_node_ids: list[str] = Field(default_factory=list)


class ExportArtifact(BaseModel):
    format: Literal["png"]
    path_or_url: str


class SourceSync(BaseModel):
    google_sheet_id: str | None = None
    worksheet_name: str | None = None
    row_number: int | None = None


class CarouselOutput(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "planned", "complete", "error"]
    normalized_input: CarouselInput
    content_plan: list[SlidePlan]
    design_reference_log: list[DesignReferenceLog]
    figma_output: FigmaOutput = Field(default_factory=FigmaOutput)
    exports: list[ExportArtifact] = Field(default_factory=list)
    source_sync: SourceSync = Field(default_factory=SourceSync)
    error: str | None = None


class QueueRow(BaseModel):
    row_number: int
    values: dict[str, str]
