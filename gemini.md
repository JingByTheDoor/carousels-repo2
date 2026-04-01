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
  "image_mode": "auto|none|stock|ai|hybrid",
  "image_source_preference": "pexels|unsplash|openai_gpt_image",
  "allow_ai_fallback": "boolean",
  "image_focus": "literal|abstract|brand_safe|mixed",
  "language": "string|null",
  "aspect_ratio": "square_1080|portrait_1080x1350",
  "output_modes": ["figma", "png"],
  "reference_style": "auto",
  "reference_file_key": "SsqVEXMsFxp9WPbPIy9Sww",
  "reference_node_ids": ["1:46227", "1:46232", "1:46239", "1:46248", "1:46256", "1:46264", "1:46201", "1:46288", "1:46184", "1:46190", "1:46271", "1:46277", "1:46283", "1:46485", "1:9052", "1:9064", "1:9076", "1:9086", "1:9176", "1:9187", "1:14767", "1:14775", "1:14788", "local:01-long-title", "local:02-title", "local:03-copy", "local:05-call-to-action", "local:light-1", "local:light-2", "local:light-6", "local:title-01", "local:twitter-post-default", "local:twitter-post-soft"],
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
    "reference_style": "auto",
    "reference_file_key": "SsqVEXMsFxp9WPbPIy9Sww",
    "reference_node_ids": ["1:46227", "1:46232", "1:46239", "1:46248", "1:46256", "1:46264", "1:46201", "1:46288", "1:46184", "1:46190", "1:46271", "1:46277", "1:46283", "1:46485", "1:9052", "1:9064", "1:9076", "1:9086", "1:9176", "1:9187", "1:14767", "1:14775", "1:14788", "local:01-long-title", "local:02-title", "local:03-copy", "local:05-call-to-action", "local:light-1", "local:light-2", "local:light-6", "local:title-01", "local:twitter-post-default", "local:twitter-post-soft"],
    "notes": "string|null"
  },
  "prompt_version": "baseline_v2",
  "language": "string|null",
  "style_family": "string|null",
  "style_recipe": "string|null",
  "image_strategy": {
    "mode": "none|stock|ai|hybrid",
    "provider": "pexels|unsplash|openai_gpt_image|null",
    "reason": "string|null"
  },
  "image_assets": [
    {
      "slide_number": "integer",
      "role": "hook|info|cta",
      "source_mode": "stock|ai",
      "provider": "pexels|unsplash|openai_gpt_image",
      "query_or_prompt": "string",
      "original_url": "string|null",
      "local_path": "string|null",
      "credit": "string|null",
      "width": "integer|null",
      "height": "integer|null",
      "alt_text": "string|null"
    }
  ],
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
  "style_family": "reference_mix_alder_portrait|reference_alder_split_media|reference_alder_text_only|reference_typography_signal|reference_cp_minimal_split|reference_cp_longform_split|reference_cp_gallery_wall|reference_sadekov_black_profile|reference_sadekov_white_profile|reference_typography_editorial_light|reference_creator_mono_minimal|reference_light_grain_glow|reference_retro_swipe_creator|reference_twitter_card_soft",
  "style_recipe": "alder_portrait_editorial_mix_v1|alder_portrait_editorial_dense_v1|alder_split_media_right_v1|alder_split_media_left_v1|alder_text_only_air_v1|typography_signal_glow_v1|cp_split_minimal_statement_v1|cp_split_longform_v1|cp_gallery_wall_v1|sadekov_black_profile_minimal_v1|sadekov_white_profile_minimal_v1|typography_editorial_light_v1|creator_mono_minimal_v1|light_grain_glow_v1|retro_swipe_creator_v1|twitter_card_soft_v1",
  "source_artifact_path": "string",
  "reference_file_key": "SsqVEXMsFxp9WPbPIy9Sww",
  "reference_node_ids": ["1:46227", "1:46232", "1:46239", "1:46288", "1:46485"],
  "canvas": {
    "width": 1080,
    "height": 1350,
    "slide_gap": 120
  },
  "image_strategy": {
    "mode": "none|stock|ai|hybrid",
    "provider": "pexels|unsplash|openai_gpt_image|null"
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
      "accent_motif": "string|null",
      "image_slot": "none|cover_media|body_media|cta_media",
      "image_required": "boolean",
      "image_treatment": "none|crop|mask|duotone|blur_glow|card_embed|gallery_wall",
      "image_asset": {
        "provider": "pexels|unsplash|openai_gpt_image|null",
        "local_path": "string|null",
        "url": "string|null",
        "credit": "string|null"
      }
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
  "preview_images": [
    {
      "slide_number": "integer",
      "mime_type": "image/png",
      "data_base64": "string|null",
      "path": "string|null",
      "url": "string|null"
    }
  ],
  "rendered_at": "ISO-8601 string"
}
```

### Studio Review Round Schema
```json
{
  "round_id": "string",
  "created_at": "ISO-8601 string",
  "round_number": "integer",
  "based_on_round_id": "string|null",
  "request": {
    "topic": "string|null",
    "script": "string|null",
    "cta_text": "string|null",
    "image_mode": "auto|none|stock|ai|hybrid",
    "language": "string|null",
    "notes": "string|null",
    "batch_mode": "vary_both|vary_style|vary_copy",
    "variant_count": "integer",
    "preferred_style": "string",
    "style_pool": "all|core|local",
    "base_copy_length": "tight|balanced|expanded|punchy"
  },
  "variants": [
    {
      "variant_id": "string",
      "ordinal": "integer",
      "job_id": "string",
      "rating": "unrated|love|good|bad",
      "rating_note": "string|null",
      "winner_feedback": "string|null",
      "rejection_note": "string|null",
      "copy_length": "tight|balanced|expanded|punchy",
      "copy_length_label": "string",
      "layout_density_label": "Minimal|Mixed|Dense",
      "image_count": "integer",
      "requested_style": "string",
      "requested_style_label": "string",
      "planner_notes": "string",
      "prompt_version": "baseline_v2",
      "language": "string",
      "style_family": "string",
      "style_recipe": "string",
      "job_artifact_path": "string",
      "render_payload_path": "string",
      "render_status": "planned|rendering|complete|error",
      "render_result_path": "string|null",
      "figma_url": "string|null",
      "figma_page_name": "string|null",
      "figma_page_url": "string|null",
      "preview_image_paths": ["string"],
      "preview_image_urls": ["string"],
      "rendered_at": "ISO-8601 string|null",
      "error": "string|null",
      "payload": "Plugin Render Payload Schema"
    }
  ]
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
    "image_mode",
    "image_source_preference",
    "allow_ai_fallback",
    "image_focus",
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
    "render_result_path",
    "image_asset_paths"
  ]
}
```

## Rules
- Schema definitions here are canonical.
- Any schema change requires updating this file before implementation changes proceed.
- At least one of `topic` or `script` is required.
- V1 default reference style is `auto`.
- V1 default aspect ratio is `portrait_1080x1350` unless explicitly overridden.
- The system must always record the exact Figma reference nodes it used.
- The system may also record approved `local:` reference IDs when a style family is grounded in local exported examples instead of live Figma nodes.
- If only `topic` is provided, the system is expected to generate a complete 7-slide content plan before layout.
- If `script` is provided, the system restructures it into the 7-slide format instead of discarding it.
- `planned` means the content payload and plugin render payload exist and are waiting for the Figma plugin render step.
- The plugin render path supports both manual file handoff and a localhost bridge handoff in the current implementation.
- The plugin render result may include thumbnail previews for each slide; the bridge is responsible for moving those thumbnails out of inline base64 and into `.tmp/studio/previews/`.
- Input language should be preserved when possible; if no language is supplied, the system infers one for rendering metadata.
- The plugin payload must carry render-aware display text and truncation metadata so the renderer does not infer layout-critical text decisions from raw copy alone.
- The style engine may choose among the approved families `reference_mix_alder_portrait`, `reference_alder_split_media`, `reference_alder_text_only`, `reference_typography_signal`, `reference_cp_minimal_split`, `reference_cp_longform_split`, `reference_cp_gallery_wall`, `reference_sadekov_black_profile`, `reference_sadekov_white_profile`, `reference_typography_editorial_light`, `reference_creator_mono_minimal`, `reference_light_grain_glow`, `reference_retro_swipe_creator`, and `reference_twitter_card_soft` based on content density and a deterministic content signature.
- The local review studio is allowed to generate review rounds outside Google Sheets, but each variant must still emit the canonical job artifact and render payload.
- Studio ratings may influence the next round, but they must not overwrite prior round artifacts.
- Studio variants may also track their render lifecycle and rendered outputs independently of Google Sheets.
- Review mode may omit both `topic` and `script`; when that happens the system must auto-generate the brief inside the fixed niche preset `english_teacher_materials`.
- Default review mode must create exactly 3 variants.
- Default review mode must use only review-safe, image-capable families.
- Default review mode must not show payload-only fake previews in the browser UI; it may show a waiting state until real rendered previews exist.
- The saved review decision must support both:
  - winner feedback
  - loser rejection notes
- Review feedback summaries must be written to `notes/review_feedback/` as human-readable markdown plus structured JSON.
- The planned image layer should default to stock-first with AI fallback, not AI-first.
- `pexels` is the preferred first stock provider for the local renderer workflow; `unsplash` is a weaker default because its API guidelines require hotlinking returned URLs and attribution handling that does not fit Figma import as cleanly.
- The currently implemented image acquisition path is stock-first with `Pexels`, plus OpenAI image fallback for `ai` and `hybrid` modes when stock cannot satisfy review-mode image slots.
- The render bridge now defaults to `sheets_first` queue priority so pending studio rounds do not silently override Google Sheets rows during auto-rendering.
- The studio launcher must override render queue priority to `studio_only` so the minimal review lane is isolated from Google Sheets jobs.

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
- Approved additional reference nodes for the style engine: `1:46201`, `1:46184`, and `1:46190`.
- Implemented a multi-family style library with deterministic recipe selection and exact per-recipe reference-node logging.
- Expanded the approved reference pool to include the lower portrait black-profile family: `1:9052`, `1:9076`, and `1:9176`.
- Added `reference_sadekov_black_profile / sadekov_black_profile_minimal_v1` so the selector now covers the distinct portrait family in the source file instead of only the square families plus the single portrait layout reference.
- Expanded the approved reference pool to include the lower white-profile family (`1:9064`, `1:9086`, `1:9187`) and the alternate light typography family (`1:14767`, `1:14775`, `1:14788`).
- Added `reference_sadekov_white_profile / sadekov_white_profile_minimal_v1` and `reference_typography_editorial_light / typography_editorial_light_v1` so the selector now covers the remaining distinct archetypes in the provided file.
- Approved local exported example assets as a second reference source using `local:` IDs so new families can be harvested from `Examples of carousels/` without pretending they are Figma nodes.

### 2026-03-30
- Added the local review studio schema for multi-variant rounds, per-variant ratings, and rating-driven next-round generation.
- Approved review-specific fields:
  - `batch_mode`
  - `variant_count`
  - `preferred_style`
  - `style_pool`
  - `base_copy_length`
  - per-variant `rating`
  - per-variant `rating_note`
- Approved the local ideation path where the studio sits above the canonical job/payload artifacts rather than replacing them.

### 2026-03-31
- Reworked the studio into a minimal review-first lane:
  - default action is `Generate 3`
  - default niche is `english_teacher_materials`
  - advanced fields are hidden behind an `Advanced` drawer
- Added review-mode fields for:
  - `generated_brief`
  - `review_status`
  - `winner_variant_id`
  - `figma_file_url`
  - per-variant `rejection_note`
  - per-variant `copy_length_label`
  - per-variant `layout_density_label`
  - per-variant `image_count`
  - per-variant `figma_page_name`
  - per-variant `figma_page_url`
- Added review endpoints:
  - `POST /api/review-rounds`
  - `GET /api/review-rounds/{round_id}`
  - `POST /api/review-rounds/{round_id}/winner`
  - `POST /api/review-rounds/{round_id}/next`
- Locked review-mode rules:
  - 3 variants only
  - real rendered Figma previews only
  - image on slide 1 plus at least 3 info-slide images
  - CTA slide image omitted by default
- Added winner-feedback support and persistent review-note exports under `notes/review_feedback/`.
- Added review-round compatibility handling so older stored rounds do not break the new studio UI.
