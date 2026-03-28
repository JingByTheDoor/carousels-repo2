# Gemini

## Canonical Data Schema
Status: `Approved and implemented`

### Input Schema
```json
{
  "job_id": "string",
  "source": "manual|google_sheets",
  "topic": "string|null",
  "script": "string|null",
  "cta_text": "string|null",
  "language": "string|null",
  "aspect_ratio": "square_1080|portrait_1080x1350",
  "output_modes": ["figma", "png"],
  "reference_style": "alder_1",
  "reference_file_key": "SsqVEXMsFxp9WPbPIy9Sww",
  "reference_node_ids": ["1:46227", "1:46232", "1:46239", "1:46288", "1:46485"],
  "notes": "string|null"
}
```

### Job Artifact Schema
```json
{
  "job_id": "string",
  "status": "queued|planning|planned|rendering|complete|error",
  "normalized_input": {
    "job_id": "string",
    "source": "manual|google_sheets",
    "topic": "string|null",
    "script": "string|null",
    "cta_text": "string|null",
    "language": "string|null",
    "aspect_ratio": "square_1080|portrait_1080x1350",
    "output_modes": ["figma", "png"],
    "reference_style": "alder_1",
    "reference_file_key": "SsqVEXMsFxp9WPbPIy9Sww",
    "reference_node_ids": ["1:46227", "1:46232", "1:46239", "1:46288", "1:46485"],
    "notes": "string|null"
  },
  "prompt_version": "baseline_v2",
  "language": "string|null",
  "style_family": "string|null",
  "style_recipe": "string|null",
  "content_plan": [
    {
      "slide_number": 1,
      "slide_role": "hook",
      "headline": "string",
      "body": "string|null",
      "design_role": "cover"
    },
    {
      "slide_number": 2,
      "slide_role": "info",
      "headline": "string",
      "body": "string",
      "design_role": "body"
    },
    {
      "slide_number": 3,
      "slide_role": "info",
      "headline": "string",
      "body": "string",
      "design_role": "body"
    },
    {
      "slide_number": 4,
      "slide_role": "info",
      "headline": "string",
      "body": "string",
      "design_role": "body"
    },
    {
      "slide_number": 5,
      "slide_role": "info",
      "headline": "string",
      "body": "string",
      "design_role": "body"
    },
    {
      "slide_number": 6,
      "slide_role": "info",
      "headline": "string",
      "body": "string",
      "design_role": "body"
    },
    {
      "slide_number": 7,
      "slide_role": "cta",
      "headline": "string",
      "body": "string|null",
      "design_role": "cta"
    }
  ],
  "design_reference_log": [
    {
      "file_key": "string",
      "node_id": "string",
      "node_name": "string",
      "usage": "cover|body|cta|palette|layout"
    }
  ],
  "render_artifact": {
    "schema_version": "figma_plugin_payload_v2",
    "backend": "figma_plugin_file_import",
    "path": "string|null",
    "page_name": "string|null",
    "style_family": "string|null",
    "style_recipe": "string|null",
    "language": "string|null",
    "result_path": "string|null"
  },
  "figma_output": {
    "file_key": "string|null",
    "file_url": "string|null",
    "page_name": "string|null",
    "slide_node_ids": ["string"]
  },
  "exports": [
    {
      "format": "png",
      "path_or_url": "string"
    }
  ],
  "source_sync": {
    "google_sheet_id": "string|null",
    "worksheet_name": "string|null",
    "row_number": "integer|null"
  },
  "error": "string|null"
}
```

### Plugin Render Payload Schema
```json
{
  "schema_version": "figma_plugin_payload_v2",
  "backend": "figma_plugin_file_import",
  "job_id": "string",
  "page_name": "string",
  "prompt_version": "baseline_v2",
  "language": "string",
  "style_family": "reference_mix_alder_portrait",
  "style_recipe": "string",
  "source_artifact_path": "string",
  "reference_file_key": "SsqVEXMsFxp9WPbPIy9Sww",
  "reference_node_ids": ["1:46227", "1:46232", "1:46239", "1:46288", "1:46485"],
  "canvas": {
    "width": 1080,
    "height": 1350,
    "slide_gap": 120
  },
  "style_tokens": {
    "light_background": "#F4F6F7",
    "dark_background": "#020202",
    "text_dark": "#111111",
    "text_light": "#FFFFFF",
    "accent_blue": "#55C3EE",
    "accent_magenta": "#9E0E4C",
    "accent_gold": "#B59868",
    "accent_orange": "#FF9300",
    "accent_purple": "#6B1FD1",
    "accent_navy": "#07215B"
  },
  "typography": {
    "cover_family": "Inter",
    "cover_style": "Black",
    "body_heading_family": "Poppins",
    "body_heading_style": "Bold",
    "body_family": "Poppins",
    "body_style": "Regular",
    "cta_heading_family": "Inter",
    "cta_heading_style": "Bold",
    "cta_body_family": "Inter",
    "cta_body_style": "Regular"
  },
  "slides": [
    {
      "slide_number": 1,
      "slide_role": "hook|info|cta",
      "design_role": "cover|body|cta",
      "layout_variant": "cover_black_hero|body_editorial_bullet|body_mask_band_left|body_spotlight_panel|cta_dark_glow",
      "layout_preference": "hero|editorial|mask_left|spotlight|cta",
      "text_align": "left|center",
      "headline": "string",
      "headline_short": "string|null",
      "headline_display": "string",
      "body": "string|null",
      "body_short": "string|null",
      "body_display": "string|null",
      "supporting_text": "string|null",
      "button_label": "string|null",
      "text_density": "low|medium|high",
      "visual_priority": "headline|body|cta",
      "safe_area_profile": "cover_tall_text|cover_balanced|body_editorial_dense|body_mask_right_column|body_spotlight_dense|cta_center_stack",
      "max_headline_lines": "integer",
      "max_body_lines": "integer",
      "can_truncate_body": "boolean",
      "emphasis_words": ["string"],
      "accent_motif": "string|null"
    }
  ]
}
```

### Plugin Render Result Schema
```json
{
  "schema_version": "figma_plugin_result_v1",
  "job_id": "string",
  "page_name": "string",
  "page_id": "string",
  "file_key": "string|null",
  "file_url": "string|null",
  "slide_node_ids": ["string"],
  "rendered_at": "ISO-8601 string"
}
```

### Google Sheets Queue Schema
```json
{
  "worksheet_name": "queue",
  "columns": [
    "job_id",
    "status",
    "topic",
    "script",
    "cta_text",
    "aspect_ratio",
    "output_modes",
    "reference_style",
    "notes",
    "figma_url",
    "export_paths",
    "reference_nodes_used",
    "error",
    "language",
    "style_family",
    "style_recipe",
    "prompt_version",
    "render_payload_path",
    "render_result_path"
  ]
}
```

## Rules
- Schema definitions here are canonical.
- Any schema change requires updating this file before implementation changes proceed.
- At least one of `topic` or `script` is required.
- V1 default reference style is `alder_1`.
- V1 default aspect ratio is `portrait_1080x1350` unless explicitly overridden.
- The system must always record the exact Figma reference nodes it used.
- If only `topic` is provided, the system is expected to generate a complete 7-slide content plan before layout.
- If `script` is provided, the system restructures it into the 7-slide format instead of discarding it.
- `planned` means the content payload and plugin render payload exist and are waiting for the Figma plugin render step.
- The plugin render path supports both manual file handoff and a localhost bridge handoff in the current implementation.
- Input language should be preserved when possible; if no language is supplied, the system infers one for rendering metadata.
- The plugin payload must carry render-aware display text and truncation metadata so the renderer does not infer layout-critical text decisions from raw copy alone.

## Maintenance Log

### 2026-03-27
- Initialized schema file during repository bootstrap.
- Drafted v1 schemas for manual input and Google Sheets queue input.
- Locked the 7-slide carousel contract: hook, five info slides, CTA.
- Updated the queue state model to include `planned` before Figma rendering completes.
- Switched the v1 default aspect ratio to `portrait_1080x1350`.
- Reworked the render architecture so the local Python layer now emits a dedicated Figma plugin payload.
- Added canonical schema for plugin render payloads and plugin render results.
- Expanded the Google Sheets queue columns to track language, style selection, prompt version, and plugin handoff files.
- Upgraded the plugin payload contract to `figma_plugin_payload_v2` with render-aware slide metadata such as short/display variants, density, safe-area profile, and CTA button/support text.
- Added a localhost bridge path so the Figma plugin can fetch the next job and post back render results without manual file transfer.
