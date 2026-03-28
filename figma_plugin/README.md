# Figma Plugin

This folder contains the local renderer that replaces the chat-bound Figma MCP render step.

## Files
- `manifest.json`: local plugin manifest
- `code.js`: plugin controller and Figma rendering logic
- `ui.html`: local UI for importing payloads and downloading render results

## Local install
1. Open Figma desktop.
2. Go to `Plugins` -> `Development` -> `Import plugin from manifest...`
3. Select [manifest.json](C:/Users/User/OneDrive%20-%20Board%20of%20Education%20of%20SD%2039%20(Vancouver)/Documents/Carousels/carousels-repo2/figma_plugin/manifest.json)
4. Open the target Figma file.
5. Run `Carousel Render Importer` from the development plugins list.

## Workflow
1. Generate a planned job and render payload locally:
   - `tools/process_next_job.py`
   - or `tools/plan_carousel.py`
2. Open the plugin in Figma.
3. Upload or paste `.tmp/render-jobs/<job_id>.render.json`.
4. Click `Render Carousel`.
5. Download the resulting `*.render-result.json`.
6. Apply that result locally:
   - `tools/apply_render_result.py --job-id <job_id> --result-file <downloaded file>`

## Current scope
- Renders 7 portrait slides at `1080x1350`
- Uses curated layouts derived from the approved reference nodes:
  - `1:46227`
  - `1:46232`
  - `1:46239`
  - `1:46288`
  - `1:46485`
- Writes a result JSON with page and slide node IDs

## Known limitations
- The plugin currently uses a file-based handoff, not a localhost job server.
- PNG export is not automated yet.
- The style engine is a curated first pass, not a full reference-file harvesting system.
