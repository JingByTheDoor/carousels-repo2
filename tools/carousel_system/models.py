from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


DEFAULT_REFERENCE_NODE_IDS = [
    "1:46227",
    "1:46232",
    "1:46239",
    "1:46248",
    "1:46256",
    "1:46264",
    "1:46201",
    "1:46288",
    "1:46184",
    "1:46190",
    "1:46271",
    "1:46277",
    "1:46283",
    "1:46485",
    "1:9052",
    "1:9076",
    "1:9176",
    "1:9064",
    "1:9086",
    "1:9187",
    "1:14767",
    "1:14775",
    "1:14788",
    "local:01-long-title",
    "local:02-title",
    "local:03-copy",
    "local:05-call-to-action",
    "local:light-1",
    "local:light-2",
    "local:light-6",
    "local:title-01",
    "local:twitter-post-default",
    "local:twitter-post-soft",
]
DEFAULT_PROMPT_VERSION = "baseline_v2"
DEFAULT_STYLE_FAMILY = "reference_mix_alder_portrait"
DEFAULT_STYLE_RECIPE = "alder_portrait_editorial_mix_v1"
DEFAULT_RENDER_SCHEMA_VERSION = "figma_plugin_payload_v2"
DEFAULT_RENDER_BACKEND = "figma_plugin_file_import"

JobStatus = Literal["queued", "planning", "planned", "rendering", "complete", "error"]
GenerationMode = Literal["standard", "review", "production"]
TextDensity = Literal["low", "medium", "high"]
LayoutPreference = Literal["hero", "editorial", "mask_left", "spotlight", "cta"]
VisualPriority = Literal["headline", "body", "cta"]
RenderWarningSeverity = Literal["info", "warning", "error"]
ImageMode = Literal["auto", "none", "stock", "ai", "hybrid"]
ResolvedImageMode = Literal["none", "stock", "ai", "hybrid"]
ImageProvider = Literal["pexels", "unsplash", "openai_gpt_image"]
ImageFocus = Literal["literal", "abstract", "brand_safe", "mixed"]
ImageSourceMode = Literal["stock", "ai"]
ImageSlot = Literal["none", "cover_media", "body_media", "cta_media"]
ImageTreatment = Literal["none", "crop", "mask", "duotone", "blur_glow", "card_embed", "gallery_wall"]
VisualAssetKind = Literal["photo", "infographic", "illustration", "mixed"]
PerfectLibraryEntryStatus = Literal["active", "inactive"]
ProductionVisualStatus = Literal["pending", "visual_resolved", "visual_warning"]
SafeAreaProfile = Literal[
    "cover_tall_text",
    "cover_balanced",
    "body_editorial_dense",
    "body_mask_right_column",
    "body_spotlight_dense",
    "cta_center_stack",
]


class CarouselInput(BaseModel):
    job_id: str = Field(min_length=1)
    source: Literal["manual", "google_sheets"]
    generation_mode: GenerationMode = "standard"
    library_item_id: str | None = None
    niche_preset: str | None = None
    topic: str | None = None
    script: str | None = None
    cta_text: str | None = None
    language: str | None = None
    aspect_ratio: Literal["square_1080", "portrait_1080x1350"] = "portrait_1080x1350"
    output_modes: list[Literal["figma", "png"]] = Field(default_factory=lambda: ["figma", "png"])
    reference_style: str = "auto"
    image_mode: ImageMode = "auto"
    image_source_preference: ImageProvider = "pexels"
    allow_ai_fallback: bool = True
    image_focus: ImageFocus = "brand_safe"
    reference_file_key: str
    reference_node_ids: list[str] = Field(default_factory=lambda: DEFAULT_REFERENCE_NODE_IDS.copy())
    notes: str | None = None

    @field_validator("library_item_id", "topic", "script", "cta_text", "notes", "language", mode="before")
    @classmethod
    def _strip_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("language", mode="after")
    @classmethod
    def _normalize_language(cls, value: str | None) -> str | None:
        return value.lower() if value else None

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
    page_id: str | None = None
    page_url: str | None = None
    slide_node_ids: list[str] = Field(default_factory=list)


class ExportArtifact(BaseModel):
    format: Literal["png", "pdf"]
    path_or_url: str
    slide_number: int | None = None


class ImageStrategy(BaseModel):
    mode: ResolvedImageMode = "none"
    provider: ImageProvider | None = None
    reason: str | None = None

    @field_validator("reason", mode="before")
    @classmethod
    def _normalize_optional_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class ImageAsset(BaseModel):
    slide_number: int
    role: Literal["hook", "info", "cta"]
    source_mode: ImageSourceMode
    provider: ImageProvider
    query_or_prompt: str
    original_url: str | None = None
    local_path: str | None = None
    credit: str | None = None
    width: int | None = None
    height: int | None = None
    alt_text: str | None = None

    @field_validator("query_or_prompt", "original_url", "local_path", "credit", "alt_text", mode="before")
    @classmethod
    def _normalize_optional_asset_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class SourceSync(BaseModel):
    google_sheet_id: str | None = None
    worksheet_name: str | None = None
    row_number: int | None = None


class PerfectVisualTarget(BaseModel):
    slide_number: int = Field(ge=1, le=7)
    slot: ImageSlot
    treatment: ImageTreatment = "none"
    asset_kind: VisualAssetKind = "photo"
    query_suffix: str | None = None
    required: bool = True

    @field_validator("query_suffix", mode="before")
    @classmethod
    def _normalize_query_suffix(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class PerfectVisualRecipe(BaseModel):
    description: str | None = None
    source_mode: ImageMode = "hybrid"
    default_focus: ImageFocus = "brand_safe"
    default_query_suffix: str | None = None
    targets: list[PerfectVisualTarget] = Field(default_factory=list)

    @field_validator("description", "default_query_suffix", mode="before")
    @classmethod
    def _normalize_visual_recipe_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class PerfectLibraryEntry(BaseModel):
    library_item_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    status: PerfectLibraryEntryStatus = "active"
    style_family: str = Field(min_length=1)
    style_recipe: str = Field(min_length=1)
    style_preference: str | None = None
    reference_file_key: str | None = None
    reference_node_ids: list[str] = Field(default_factory=list)
    visual_recipe: PerfectVisualRecipe | None = None
    approval_notes: str | None = None
    approved_at: str | None = None
    approved_by: str | None = None
    notes: str | None = None
    exemplar_preview_path: str | None = None
    exemplar_export_path: str | None = None

    @field_validator(
        "style_preference",
        "reference_file_key",
        "approval_notes",
        "approved_at",
        "approved_by",
        "notes",
        "exemplar_preview_path",
        "exemplar_export_path",
        mode="before",
    )
    @classmethod
    def _normalize_library_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class PerfectLibraryStatus(BaseModel):
    manifest_version: str = "perfect_library_v1"
    updated_at: str | None = None
    entries: list[PerfectLibraryEntry] = Field(default_factory=list)

    @field_validator("updated_at", mode="before")
    @classmethod
    def _normalize_status_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class RenderArtifact(BaseModel):
    schema_version: str = DEFAULT_RENDER_SCHEMA_VERSION
    backend: Literal["figma_plugin_file_import"] = DEFAULT_RENDER_BACKEND
    path: str | None = None
    page_name: str | None = None
    style_family: str | None = None
    style_recipe: str | None = None
    language: str | None = None
    result_path: str | None = None


class StyleTokens(BaseModel):
    light_background: str
    dark_background: str
    text_dark: str
    text_light: str
    accent_blue: str
    accent_magenta: str
    accent_gold: str
    accent_orange: str
    accent_purple: str
    accent_navy: str


class TypographyTokens(BaseModel):
    cover_family: str
    cover_style: str
    body_heading_family: str
    body_heading_style: str
    body_family: str
    body_style: str
    cta_heading_family: str
    cta_heading_style: str
    cta_body_family: str
    cta_body_style: str


class RenderCanvasSpec(BaseModel):
    width: int = 1080
    height: int = 1350
    slide_gap: int = 120


class RenderImageAssetSpec(BaseModel):
    provider: ImageProvider | None = None
    local_path: str | None = None
    url: str | None = None
    credit: str | None = None
    data_base64: str | None = None

    @field_validator("local_path", "url", "credit", "data_base64", mode="before")
    @classmethod
    def _normalize_optional_render_asset_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class RenderImageStrategySpec(BaseModel):
    mode: ResolvedImageMode = "none"
    provider: ImageProvider | None = None


class RenderSlideSpec(BaseModel):
    slide_number: int
    slide_role: Literal["hook", "info", "cta"]
    design_role: Literal["cover", "body", "cta"]
    layout_variant: Literal[
        "cover_black_hero",
        "body_editorial_bullet",
        "body_mask_band_left",
        "body_spotlight_panel",
        "cta_dark_glow",
    ]
    layout_preference: LayoutPreference
    text_align: Literal["left", "center"] = "left"
    headline: str = Field(min_length=1)
    headline_short: str | None = None
    headline_display: str = Field(min_length=1)
    body: str | None = None
    body_short: str | None = None
    body_display: str | None = None
    supporting_text: str | None = None
    button_label: str | None = None
    text_density: TextDensity
    visual_priority: VisualPriority
    safe_area_profile: SafeAreaProfile
    max_headline_lines: int = Field(ge=1)
    max_body_lines: int = Field(ge=0)
    can_truncate_body: bool = False
    emphasis_words: list[str] = Field(default_factory=list)
    accent_motif: str | None = None
    image_slot: ImageSlot = "none"
    image_required: bool = False
    image_treatment: ImageTreatment = "none"
    image_asset: RenderImageAssetSpec | None = None

    @field_validator(
        "headline_short",
        "headline_display",
        "body",
        "body_short",
        "body_display",
        "supporting_text",
        "button_label",
        mode="before",
    )
    @classmethod
    def _normalize_optional_render_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None

    @field_validator("emphasis_words", mode="before")
    @classmethod
    def _normalize_emphasis_words(cls, value: list[str] | None) -> list[str]:
        if not value:
            return []
        return [" ".join(item.strip().split()) for item in value if item and item.strip()]


class PluginRenderPayload(BaseModel):
    schema_version: str = DEFAULT_RENDER_SCHEMA_VERSION
    backend: Literal["figma_plugin_file_import"] = DEFAULT_RENDER_BACKEND
    job_id: str
    page_name: str
    include_download_exports: bool = True
    prompt_version: str = DEFAULT_PROMPT_VERSION
    language: str = "unknown"
    style_family: str = DEFAULT_STYLE_FAMILY
    style_recipe: str = DEFAULT_STYLE_RECIPE
    save_post_icon_data_base64: str | None = None
    source_artifact_path: str
    reference_file_key: str
    reference_node_ids: list[str]
    canvas: RenderCanvasSpec = Field(default_factory=RenderCanvasSpec)
    image_strategy: RenderImageStrategySpec = Field(default_factory=RenderImageStrategySpec)
    style_tokens: StyleTokens
    typography: TypographyTokens
    slides: list[RenderSlideSpec]

    @field_validator("save_post_icon_data_base64", mode="before")
    @classmethod
    def _normalize_optional_icon_data(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = "".join(value.strip().split())
        return cleaned or None

    @model_validator(mode="after")
    def _validate_slide_count(self) -> "PluginRenderPayload":
        if len(self.slides) != 7:
            raise ValueError("Plugin render payload must contain exactly 7 slides.")
        return self


class PluginPreviewImage(BaseModel):
    slide_number: int
    mime_type: Literal["image/png"] = "image/png"
    data_base64: str | None = None
    path: str | None = None
    url: str | None = None

    @field_validator("data_base64", "path", "url", mode="before")
    @classmethod
    def _normalize_optional_preview_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class PluginExportImage(BaseModel):
    slide_number: int
    file_name: str | None = None
    mime_type: Literal["image/png"] = "image/png"
    data_base64: str | None = None
    path: str | None = None
    url: str | None = None

    @field_validator("file_name", "data_base64", "path", "url", mode="before")
    @classmethod
    def _normalize_optional_export_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class PluginRenderWarning(BaseModel):
    slide_number: int
    code: str = Field(min_length=1)
    severity: RenderWarningSeverity = "warning"
    message: str = Field(min_length=1)


class PluginFitMetric(BaseModel):
    slide_number: int
    role: Literal["cover", "body", "cta"]
    headline_font_size: int | None = None
    body_font_size: int | None = None
    headline_lines: int | None = None
    body_lines: int | None = None
    content_top: int | None = None
    content_bottom: int | None = None
    occupied_height_ratio: float | None = None
    truncated: bool = False
    image_rendered: bool = False


class PluginRenderResult(BaseModel):
    schema_version: Literal["figma_plugin_result_v1"] = "figma_plugin_result_v1"
    job_id: str
    page_name: str
    page_id: str
    file_key: str | None = None
    file_url: str | None = None
    page_url: str | None = None
    slide_node_ids: list[str] = Field(default_factory=list)
    preview_images: list[PluginPreviewImage] = Field(default_factory=list)
    export_images: list[PluginExportImage] = Field(default_factory=list)
    render_warnings: list[PluginRenderWarning] = Field(default_factory=list)
    fit_metrics: list[PluginFitMetric] = Field(default_factory=list)
    rendered_at: str


class ProductionJobWarning(BaseModel):
    code: str = Field(min_length=1)
    severity: RenderWarningSeverity = "warning"
    message: str = Field(min_length=1)
    slide_number: int | None = None

    @field_validator("code", "message", mode="before")
    @classmethod
    def _normalize_warning_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class ProductionJobRecord(BaseModel):
    job_id: str
    created_at: str
    status: JobStatus
    request: CarouselInput
    library_item_id: str
    library_label: str
    style_family: str | None = None
    style_recipe: str | None = None
    job_artifact_path: str
    render_payload_path: str
    render_result_path: str | None = None
    figma_file_url: str | None = None
    figma_page_url: str | None = None
    figma_page_name: str | None = None
    export_paths: list[str] = Field(default_factory=list)
    export_urls: list[str] = Field(default_factory=list)
    pdf_export_path: str | None = None
    pdf_export_url: str | None = None
    used_script: str | None = None
    visual_status: ProductionVisualStatus = "pending"
    warnings: list[ProductionJobWarning] = Field(default_factory=list)
    fit_metrics: list[PluginFitMetric] = Field(default_factory=list)
    error: str | None = None

    @field_validator(
        "render_result_path",
        "figma_file_url",
        "figma_page_url",
        "figma_page_name",
        "pdf_export_path",
        "pdf_export_url",
        "error",
        mode="before",
    )
    @classmethod
    def _normalize_production_job_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None

    @field_validator("used_script", mode="before")
    @classmethod
    def _normalize_used_script(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
        return cleaned or None


class CarouselOutput(BaseModel):
    job_id: str
    status: JobStatus
    normalized_input: CarouselInput
    prompt_version: str = DEFAULT_PROMPT_VERSION
    language: str | None = None
    style_family: str | None = None
    style_recipe: str | None = None
    content_plan: list[SlidePlan]
    design_reference_log: list[DesignReferenceLog]
    render_artifact: RenderArtifact = Field(default_factory=RenderArtifact)
    figma_output: FigmaOutput = Field(default_factory=FigmaOutput)
    image_strategy: ImageStrategy = Field(default_factory=ImageStrategy)
    image_assets: list[ImageAsset] = Field(default_factory=list)
    exports: list[ExportArtifact] = Field(default_factory=list)
    source_sync: SourceSync = Field(default_factory=SourceSync)
    error: str | None = None


class QueueRow(BaseModel):
    row_number: int
    values: dict[str, str]
