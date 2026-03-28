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
- Updated `README.md`, `gemini.md`, `claude.md`, and architecture SOPs for the new plugin render path.

### Errors
- A delegated worker was interrupted during plugin scaffolding, so the final plugin implementation was completed locally.

### Test / Verification
- `python -m compileall tools` passed.
- `.venv\Scripts\python tools\build_render_payload.py --job-id sheet-row-2` passed and wrote `.tmp/render-jobs/sheet-row-2.render.json`.
- `.venv\Scripts\python tools\ensure_queue_sheet.py` passed and updated the queue header row to the expanded schema.
- `Get-Content .\figma_plugin\manifest.json | ConvertFrom-Json` passed.
- `.venv\Scripts\python tools\plan_carousel.py --help` passed.
- `.venv\Scripts\python tools\apply_render_result.py --help` passed.
- Live end-to-end plugin rendering inside Figma is not yet verified in this turn.

### Current Status
- Google Sheets, OpenAI planning, and plugin render-payload generation are working.
- The repo now has a local Figma plugin render path that can replace the chat-bound MCP render step.
- The local finalize step exists, but it still needs one live plugin run for end-to-end confirmation.
- PNG export automation is still not implemented in the local toolchain.
