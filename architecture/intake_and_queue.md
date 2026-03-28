# Intake And Queue SOP

## Goal
Normalize manual or Google Sheets input into the canonical schema in `gemini.md` and produce deterministic job records for the planner and renderer.

## Inputs
- Manual CLI input
- Google Sheets worksheet named `queue`

## Queue headers
- `job_id`
- `status`
- `topic`
- `script`
- `cta_text`
- `aspect_ratio`
- `output_modes`
- `reference_style`
- `notes`
- `figma_url`
- `export_paths`
- `reference_nodes_used`
- `error`
- `language`
- `style_family`
- `style_recipe`
- `prompt_version`
- `render_payload_path`
- `render_result_path`

## Status flow
- `queued`: waiting to be processed
- `planning`: content is being generated
- `planned`: canonical job artifact plus plugin render payload are ready
- `rendering`: the Figma plugin is actively drawing the carousel
- `complete`: the plugin render result has been applied back to the artifact and sheet
- `error`: a tool failed and the error was recorded

## Rules
- At least one of `topic` or `script` must be present.
- Empty status is treated as `queued`.
- `output_modes` is stored as a comma-separated string in Sheets and normalized to a list internally.
- `aspect_ratio` defaults to `portrait_1080x1350`.
- `reference_style` defaults to `auto`.
- `language` is optional; if blank, planning/render metadata may infer it.
- `process_next_job.py` must write both `.tmp/jobs/<job_id>.json` and `.tmp/render-jobs/<job_id>.render.json`.

## Edge cases
- If a row is missing both `topic` and `script`, move it to `error`.
- If `job_id` is empty, generate one before processing.
- If the sheet does not exist, create it and write the required headers.
- If a render result is applied to the wrong job ID, reject it instead of mutating the artifact.
