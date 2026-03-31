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
- Multi-family style selection grounded in approved Figma references
- Figma reference logging for every generated payload

## Current render architecture
- Python tools generate:
  - a canonical job artifact in `.tmp/jobs/`
  - a Figma plugin render payload in `.tmp/render-jobs/`
- The local Figma plugin in [figma_plugin](C:/Users/User/OneDrive%20-%20Board%20of%20Education%20of%20SD%2039%20(Vancouver)/Documents/Carousels/carousels-repo2/figma_plugin) consumes the render payload and creates the slides inside Figma.
- The local bridge server in `tools/render_server.py` can now serve the next job directly to the plugin and accept render results back over `http://localhost:8765`.
- A local finalize step still exists for manual result files, but the bridge path can now complete the Google Sheet update automatically.

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

## Review Studio
If you want a fast review loop instead of working directly in the Google Sheet, use the local studio.

One command:
```powershell
.\.venv\Scripts\python.exe tools\start_studio.py
```

That launcher:
- starts the browser review app at `http://127.0.0.1:3000`
- starts the render bridge too, unless you pass `--no-render-bridge`

Inside the studio you can:
- enter a topic or script
- generate a round of variants
- vary style, copy length, or both
- rate variants as `love`, `good`, or `bad`
- generate the next round from those ratings
- let the Figma plugin auto-render the generated variants through the localhost bridge
- see real rendered slide thumbnails appear in the studio as variants finish rendering

Studio artifacts:
- `.tmp/studio/rounds/<round_id>.json`
- `.tmp/jobs/<job_id>.json`
- `.tmp/render-jobs/<job_id>.render.json`

If you only want the review app without the bridge:
```powershell
.\.venv\Scripts\python.exe tools\studio_server.py
```

## Style families
The render payload can now choose among multiple reference-driven families:
- `reference_mix_alder_portrait`
- `reference_alder_split_media`
- `reference_alder_text_only`
- `reference_typography_signal`
- `reference_cp_minimal_split`
- `reference_cp_longform_split`
- `reference_cp_gallery_wall`
- `reference_sadekov_black_profile`
- `reference_sadekov_white_profile`
- `reference_typography_editorial_light`
- `reference_creator_mono_minimal`
- `reference_light_grain_glow`
- `reference_retro_swipe_creator`
- `reference_twitter_card_soft`

You can also force a family when testing:
```powershell
.venv\Scripts\python tools\plan_carousel.py --topic "4 principles of clear interfaces" --reference-style cp_3
.venv\Scripts\python tools\plan_carousel.py --topic "Why consistency matters in branding" --reference-style typography_signal
.venv\Scripts\python tools\plan_carousel.py --topic "Why systems beat hacks" --reference-style alder_forced
.venv\Scripts\python tools\plan_carousel.py --topic "How to simplify a complex workflow" --reference-style cp_longform
.venv\Scripts\python tools\plan_carousel.py --topic "Why clear dashboards convert better" --reference-style cp_gallery
.venv\Scripts\python tools\plan_carousel.py --topic "5 lessons from better onboarding" --reference-style alder_split_left
.venv\Scripts\python tools\plan_carousel.py --topic "3 reasons clear teaching wins" --reference-style sadekov
.venv\Scripts\python tools\plan_carousel.py --topic "Why a clear offer converts faster" --reference-style sadekov_light
.venv\Scripts\python tools\plan_carousel.py --topic "How to explain a product comparison clearly" --reference-style typography_light
.venv\Scripts\python tools\plan_carousel.py --topic "Why clear hooks beat clever hooks" --reference-style creator_mono
.venv\Scripts\python tools\plan_carousel.py --topic "4 ways to make educational content feel lighter" --reference-style light_glow
.venv\Scripts\python tools\plan_carousel.py --topic "Why consistency compounds on social media" --reference-style retro_swipe
.venv\Scripts\python tools\plan_carousel.py --topic "3 reasons tweet-sized ideas spread faster" --reference-style twitter_card
```

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

## Auto render bridge
1. Start the bridge:

```powershell
.venv\Scripts\python tools\render_server.py
```

2. Keep Figma open and run the local plugin.
3. In the plugin UI, leave the bridge URL at `http://localhost:8765`.
4. Use `Poll Next Job` to process one row, or `Start Auto Mode` to keep polling.
5. The bridge will:
   - serve the next `planned` row first
   - fall back to `queued` rows by planning them on demand
   - write render results into `.tmp/render-results/`
   - finalize the job artifact and Google Sheet automatically

The studio launcher can start this bridge for you automatically, so you do not need a second terminal in the normal review flow.

When the local Figma plugin is open in auto mode, studio-generated variants are picked up by the same bridge and pushed through the real renderer. The studio then updates each variant card with:
- `render_status`
- `figma_url`
- `render_result_path`
- exported slide thumbnail previews from the plugin result

## Rebuild render payloads for existing jobs
```powershell
.venv\Scripts\python tools\build_render_payload.py --job-id <job_id>
```

## Style coverage audit
Use this when new local examples are added and you want to verify whether the style engine actually covers them:

```powershell
.venv\Scripts\python tools\audit_style_coverage.py
```

That command writes:
- `.tmp/style_coverage_manifest.json`
- `style_coverage.md`

The audit is intentionally conservative:
- `covered` means a named local example family is explicitly mapped into the current style engine
- `duplicate` means a local export is a high-confidence alias of a covered family
- `missing` means the local group exists but is not yet mapped confidently into the engine

## Current limitations
- PNG export automation is still not implemented in the local toolchain.
- The plugin bridge still depends on a live Figma desktop session with the development plugin running.
- The studio can now show real rendered thumbnails after the plugin finishes a variant, but it still falls back to payload-driven preview state before a render exists.
- The style engine now covers the harvested Figma families plus the first local-example batch: mono minimal creator slides, light grain/glow slides, retro swipe creator slides, and soft tweet-card slides. It still does not cover every local example family in `Examples of carousels/`.

## Planned image layer
The next media recommendation for this repo is:
- default strategy: `stock_first`
- fallback: `ai_fallback`
- stock provider: `pexels`
- AI provider: OpenAI image generation

Reason:
- the current system is mainly text-led
- most families only benefit from one strong image slot, usually the hook
- stock is more trustworthy for business/education topics
- AI should be used when stock search fails or the concept is abstract

See [image_pipeline.md](/C:/Users/User/OneDrive%20-%20Board%20of%20Education%20of%20SD%2039%20(Vancouver)/Documents/Carousels/carousels-repo2/architecture/image_pipeline.md) for the full decision rules.
