# Plugin Renderer SOP

## Goal
Render approved carousel payloads inside Figma without relying on Codex or chat-bound MCP state.

## Renderer boundary
- The Python layer is responsible for planning, style selection metadata, and writing `PluginRenderPayload`.
- The Figma plugin is responsible for reading that payload, creating a new page, rendering seven portrait frames, and emitting a `PluginRenderResult`.
- The finalize step applies the plugin result back into the canonical job artifact and Google Sheet.

## Current handoff model
- Input to the plugin: `.tmp/render-jobs/<job_id>.render.json`
- Output from the plugin: downloaded `figma_plugin_result_v1` JSON
- Finalization tool: `tools/apply_render_result.py`

## Visual grounding
- Cover reference: `1:46227`
  - Black stage
  - Oversized white headline
  - Geometric accent cluster
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

## Follow-up path
- Current implementation: file upload or paste into a local plugin UI.
- Next improvement: replace file upload with a localhost fetch/post bridge so the plugin can pull the next job automatically.
