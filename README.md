# Carousel Automation

This repo turns a `topic` or `script` into a validated 7-slide Instagram carousel pipeline with Google Sheets as the queue, OpenAI as the copy planner, and a local Figma plugin as the renderer.

## Current scope
- Deterministic queue setup and handshake tooling
- Deterministic payload generation around the approved schema
- AI-assisted content planning for:
  - slide 1 hook
  - slides 2-6 informational content
  - slide 7 CTA
- Plugin-ready render payload generation
- Render-aware plugin payload generation with display-safe text variants
- Figma reference logging for every generated payload

## Current render architecture
- Python tools generate:
  - a canonical job artifact in `.tmp/jobs/`
  - a Figma plugin render payload in `.tmp/render-jobs/`
- The local Figma plugin in [figma_plugin](C:/Users/User/OneDrive%20-%20Board%20of%20Education%20of%20SD%2039%20(Vancouver)/Documents/Carousels/carousels-repo2/figma_plugin) consumes the render payload and creates the slides inside Figma.
- A local finalize step writes the plugin render result back into the job artifact and Google Sheet.

## Setup
1. Copy `.env.example` to `.env`.
2. Add your OpenAI API key.
3. Create a Google service account JSON file and set `GOOGLE_SERVICE_ACCOUNT_JSON`.
4. Create a Google Sheet, copy its spreadsheet ID, and set `GOOGLE_SHEETS_SPREADSHEET_ID`.
5. Share the Google Sheet with the service account email.
6. Optionally add a Figma personal access token to verify REST access to the reference file.

## Install
```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -e .
```

## Link phase
```powershell
.venv\Scripts\python tools\ensure_queue_sheet.py
.venv\Scripts\python tools\check_google_sheets.py
.venv\Scripts\python tools\check_figma_access.py
```

## Manual planning
```powershell
.venv\Scripts\python tools\plan_carousel.py --topic "3 AI mistakes small businesses make"
```

That command now writes both:
- `.tmp/jobs/<job_id>.json`
- `.tmp/render-jobs/<job_id>.render.json`

## Queue processing
Add rows to the `queue` worksheet using the approved headers, then run:

```powershell
.venv\Scripts\python tools\process_next_job.py
```

That command now plans the content and writes the plugin render payload in one pass.

## Plugin render flow
1. Import the plugin from [figma_plugin/manifest.json](C:/Users/User/OneDrive%20-%20Board%20of%20Education%20of%20SD%2039%20(Vancouver)/Documents/Carousels/carousels-repo2/figma_plugin/manifest.json) into Figma as a local plugin.
2. Run the plugin inside your target Figma file.
3. Upload or paste the `.tmp/render-jobs/<job_id>.render.json` payload.
   The current payload schema is `figma_plugin_payload_v2`, which includes `headline_display`, `body_display`, CTA button labels, and safe-area metadata.
4. Render the carousel into a new page.
5. Download the result JSON from the plugin UI.
6. Apply the result locally:

```powershell
.venv\Scripts\python tools\apply_render_result.py --job-id <job_id> --result-file <path-to-result-json>
```

## Rebuild render payloads for existing jobs
```powershell
.venv\Scripts\python tools\build_render_payload.py --job-id <job_id>
```

## Current limitations
- PNG export automation is still not implemented in the local toolchain.
- The plugin renderer is file-based for now. It does not yet fetch jobs automatically from a local server.
- The richer style engine is still a curated first pass grounded in the approved Figma references, not a full harvested library of every example frame.
