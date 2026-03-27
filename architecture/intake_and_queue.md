# Intake And Queue SOP

## Goal
Normalize manual or Google Sheets input into the canonical schema in `gemini.md`.

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

## Status flow
- `queued`: waiting to be processed
- `processing`: currently being planned
- `planned`: content payload is ready and waiting for Figma rendering/export
- `complete`: Figma render plus export step finished
- `error`: a tool failed and the error was recorded

## Rules
- At least one of `topic` or `script` must be present.
- Empty status is treated as `queued`.
- `output_modes` is stored as a comma-separated string in Sheets and normalized to a list internally.
- `aspect_ratio` defaults to `portrait_1080x1350`.
- `reference_style` defaults to `alder_1`.

## Edge cases
- If a row is missing both `topic` and `script`, move it to `error`.
- If `job_id` is empty, generate one before processing.
- If the sheet does not exist, create it and write the required headers.
