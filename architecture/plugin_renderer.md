# Plugin Renderer SOP

## Goal
Render approved carousel payloads inside Figma without relying on Codex or chat-bound MCP state.

## Renderer boundary
- The Python layer is responsible for planning, style selection metadata, and writing `PluginRenderPayload`.
- The Figma plugin is responsible for reading that payload, creating a new page, rendering seven portrait frames, and emitting a `PluginRenderResult`.
- The finalize step applies the plugin result back into the canonical job artifact and Google Sheet.

## Current handoff model
- Input to the plugin:
  - manual: `.tmp/render-jobs/<job_id>.render.json`
  - auto: localhost bridge response from `tools/render_server.py`
- Current payload schema: `figma_plugin_payload_v2`
- Each slide payload now includes render-aware fields such as:
  - `headline_display`
  - `body_display`
  - `headline_short`
  - `body_short`
  - `supporting_text`
  - `button_label`
  - `text_density`
  - `safe_area_profile`
- Output from the plugin:
  - manual: downloaded `figma_plugin_result_v1` JSON
  - auto: `POST /render-result` to the localhost bridge
- Finalization tool:
  - manual: `tools/apply_render_result.py`
  - auto: bridge-owned finalization inside `tools/render_server.py`

## Visual grounding
- Cover reference: `1:46227`
  - Black stage
  - Oversized white headline
  - Geometric accent cluster
- Minimal split references: `1:46184`, `1:46190`
  - Light neutral background
  - Large left or right text block
  - Floating device-card style object on the opposite side
- Typography signal references: `1:46201`, `1:46288`
  - Dark stage with soft magenta/gold glow quadrants
  - Centered or stacked large type
  - Footer signal lines for engagement cues
- Black profile portrait references: `1:9052`, `1:9076`, `1:9176`
  - Pure black portrait stage
  - Profile header block with avatar/name/subtitle
  - Minimal footer rail and centered handle
  - Sparse editorial text and CTA treatment
- White profile portrait references: `1:9064`, `1:9086`, `1:9187`
  - Pure white portrait stage
  - Same profile header/footer system as the black family
  - Black editorial copy and outline arrow cue
- Light typography references: `1:14767`, `1:14775`, `1:14788`
  - Dark cover with bottom tool-card cluster
  - White editorial comparison body layout
  - White CTA with black engagement footer signals
- Body references: `1:46232`, `1:46239`
  - Light editorial background
  - Poppins heading/body mix
  - Alternation between text-first and mask-band layouts
- CTA reference: `1:46288`
  - Dark backdrop
  - Centered white CTA copy
  - Warm/magenta glow treatment
- Portrait direction reference: `1:46485`
  - `1080x1350` portrait framing

## Rules
- The plugin must reject payloads that do not contain exactly seven slides.
- The plugin must create a new page rather than overwriting existing work silently.
- The plugin must render the slides in deterministic left-to-right order.
- The plugin should return file/page/node metadata in a result JSON the Python layer can apply.
- The plugin may approximate the approved references through curated style tokens and layout recipes, but it must log the approved node IDs that informed the payload.
- The plugin must branch on `style_recipe` so different payload families produce materially different layouts, not just recolored versions of the same composition.

## Local bridge contract
- Bridge endpoint: `http://localhost:8765`
- `GET /health`
  - returns server health and bind address
- `GET /next-job`
  - returns `204` when no jobs are available
  - otherwise returns `{ job_id, row_number, payload }`
  - prioritizes `planned` rows, then plans the next `queued` row on demand
- `POST /render-result`
  - accepts `figma_plugin_result_v1`
  - writes `.tmp/render-results/<job_id>.render-result.json`
  - finalizes the canonical job artifact and Google Sheet row
- `POST /render-error`
  - accepts `{ job_id, error }`
  - marks the job and sheet row as `error`

## Follow-up path
- Current implementation: manual file import plus localhost fetch/post bridge.
- Next improvement: add exported-image automation after a successful Figma render.
- Current image support: cover-slide image placement is allowed for image-friendly families when the payload contains a resolved asset URL.
- Current non-goal: body-slide image placement is deferred until the cover-image path is validated visually in Figma.
