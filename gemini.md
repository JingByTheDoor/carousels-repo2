# Gemini

## Canonical Data Schema
Status: `Drafted for Blueprint approval`

### Input Schema
```json
{
  "job_id": "string",
  "source": "manual|google_sheets",
  "topic": "string|null",
  "script": "string|null",
  "cta_text": "string|null",
  "aspect_ratio": "square_1080|portrait_1080x1350",
  "output_modes": ["figma", "png"],
  "reference_style": "alder_1",
  "reference_file_key": "SsqVEXMsFxp9WPbPIy9Sww",
  "reference_node_ids": ["1:46227", "1:46232", "1:46239", "1:46288", "1:46485"],
  "notes": "string|null"
}
```

### Output Schema
```json
{
  "job_id": "string",
  "status": "queued|processing|planned|complete|error",
  "normalized_input": {
    "topic": "string|null",
    "script": "string|null",
    "cta_text": "string|null",
    "aspect_ratio": "square_1080|portrait_1080x1350",
    "output_modes": ["figma", "png"]
  },
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
    "error"
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
- `planned` means the content payload exists and is waiting for the Figma render step.

## Maintenance Log

### 2026-03-27
- Initialized schema file during repository bootstrap.
- Drafted v1 schemas for manual input and Google Sheets queue input.
- Locked the 7-slide carousel contract: hook, five info slides, CTA.
- Updated the queue state model to include `planned` before Figma rendering completes.
- Switched the v1 default aspect ratio to `portrait_1080x1350`.
- Implementation remains blocked pending blueprint approval.
