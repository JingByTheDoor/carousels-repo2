# Progress

## 2026-03-27

### Completed
- Inspected the repository root and confirmed the active project folder is `carousels-repo2`.
- Initialized project memory files and scaffold directories.
- Captured the carousel product direction, Google Sheets source-of-truth plan, and approved Figma reference nodes.
- Added Python project scaffolding, environment contract, queue/planning tools, and initial architecture SOPs.
- Verified Google Sheets access and queue setup.
- Verified OpenAI planning and generated working job artifacts from sheet input.
- Rendered prior iterations into Figma via MCP while that path was still active.
- Reworked the local architecture so rendering no longer depends on chat-bound MCP state.
- Added canonical render metadata to the job artifact model:
  - `prompt_version`
  - `language`
  - `style_family`
  - `style_recipe`
  - `render_artifact`
- Added a dedicated plugin render payload model and plugin render result model.
- Expanded the Google Sheets queue headers to include:
  - `language`
  - `style_family`
  - `style_recipe`
  - `prompt_version`
  - `render_payload_path`
  - `render_result_path`
- Updated `tools/process_next_job.py` so one queue pass now writes:
  - `.tmp/jobs/<job_id>.json`
  - `.tmp/render-jobs/<job_id>.render.json`
- Added `tools/build_render_payload.py` to regenerate plugin payloads from existing job artifacts.
- Added `tools/apply_render_result.py` to finalize plugin render results back into the job artifact and Google Sheet.
- Added a local Figma plugin scaffold in `figma_plugin/`:
  - `manifest.json`
  - `code.js`
  - `ui.html`
  - `README.md`
- Added a localhost render bridge in `tools/render_server.py`.
- Added shared bridge/finalization helpers in `tools/carousel_system/render_bridge.py`.
- Extended the plugin UI with:
  - `Poll Next Job`
  - `Start Auto Mode`
  - automatic `POST /render-result`
  - automatic `POST /render-error`
- Updated the plugin manifest to allow development-time access to `http://localhost:8765`.
- Updated `README.md`, `gemini.md`, `claude.md`, and architecture SOPs for the new plugin render path.
- Upgraded the plugin render payload from `figma_plugin_payload_v1` to `figma_plugin_payload_v2`.
- Added render-aware slide fields including:
  - `headline_short`
  - `headline_display`
  - `body_short`
  - `body_display`
  - `supporting_text`
  - `button_label`
  - `text_density`
  - `safe_area_profile`
- Updated the plugin renderer to consume those display-safe fields instead of always rendering the raw headline/body text.
- Regenerated `.tmp\\render-jobs\\sheet-row-2.render.json` as a v2 payload for the Russian test case.

### Errors
- A delegated worker was interrupted during plugin scaffolding, so the final plugin implementation was completed locally.
- The first live plugin attempt failed in Figma because its runtime rejected object spread syntax in `figma_plugin/code.js`.
- The first payload contract was too thin for reliable layout decisions, which caused weak text fitting on the rendered slides.
- The first localhost bridge pass still needed explicit CORS and `OPTIONS` handling because the plugin UI uses browser-style `fetch()` requests.
- Figma Desktop rejected `devAllowedDomains` using `http://127.0.0.1:8765`, so the plugin bridge now standardizes on `http://localhost:8765`.

### Test / Verification
- `python -m compileall tools` passed.
- `node --check .\figma_plugin\code.js` passed.
- `rg -n "\.\.\." .\figma_plugin\code.js` confirmed the unsupported object spread syntax was removed after the runtime error.
- `.venv\Scripts\python tools\build_render_payload.py --job-path .tmp\jobs\sheet-row-2.verify.json --render-payload-path .tmp\render-jobs\sheet-row-2.verify.render.json` passed.
- `PluginRenderPayload.model_validate_json(...)` passed against `.tmp\render-jobs\sheet-row-2.verify.render.json`.
- `.venv\Scripts\python tools\build_render_payload.py --job-id sheet-row-2` passed after the v2 payload changes and rewrote `.tmp\render-jobs\sheet-row-2.render.json`.
- `PluginRenderPayload.model_validate_json(...)` passed against the regenerated `figma_plugin_payload_v2` file.
- `.venv\Scripts\python tools\ensure_queue_sheet.py` passed and updated the queue header row to the expanded schema.
- `Get-Content .\figma_plugin\manifest.json | ConvertFrom-Json` passed.
- `.venv\Scripts\python tools\plan_carousel.py --help` passed.
- `.venv\Scripts\python tools\apply_render_result.py --help` passed.
- `Get-Content .\figma_plugin\manifest.json | ConvertFrom-Json` passed after adding `networkAccess` and `documentAccess`.
- A temporary bridge boot on port `8766` returned `GET /health -> {"status":"ok","host":"127.0.0.1","port":8766}`.
- Live end-to-end plugin rendering inside Figma is not yet verified in this turn.

### Current Status
- Google Sheets, OpenAI planning, and plugin render-payload generation are working.
- The repo now has a local Figma plugin render path that can replace the chat-bound MCP render step.
- The local finalize step exists, but it still needs one live plugin run for end-to-end confirmation.
- The localhost bridge now exists, but it still needs one live auto-mode plugin pass for end-to-end confirmation.
- PNG export automation is still not implemented in the local toolchain.
