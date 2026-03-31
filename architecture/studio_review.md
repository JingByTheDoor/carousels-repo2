# Studio Review SOP

## Goal
Provide a fast local review loop for generating multiple carousel variants, rating them, and iterating into the next round without using Google Sheets as the primary interface.

## Entry Points
- `tools/studio_server.py`
- `tools/start_studio.py`

## Review Loop
1. User opens the local studio in a browser.
2. User enters `topic` or `script`, plus optional CTA, notes, and language.
3. User chooses:
   - batch mode: `vary_both`, `vary_style`, or `vary_copy`
   - preferred style
   - style pool
   - base copy length
   - image mode
4. Studio generates one review round with multiple variants.
5. Each variant produces:
   - a canonical job artifact in `.tmp/jobs/`
   - a render payload in `.tmp/render-jobs/`
   - embedded review metadata inside the round record
6. User rates variants as `love`, `good`, or `bad`.
7. Studio generates the next round using those ratings as the anchor.
8. If the Figma plugin bridge is running, the bridge may acquire studio variants directly, render them, and sync the result back into the studio round file.

## Deterministic Rules
- Variant count is bounded and explicit.
- Copy-length variation is driven by fixed review profiles:
  - `tight`
  - `balanced`
  - `expanded`
  - `punchy`
- Style variation is driven by fixed force values already supported by the style engine.
- The next round should prefer the best-rated variant's copy length and, unless the batch mode is `vary_copy`, its style.
- Styles rated `bad` should be deprioritized or excluded from the immediate next round.

## Artifacts
- Round files live in `.tmp/studio/rounds/`.
- Studio state lives in `.tmp/studio/state.json`.
- Rendered slide thumbnails live in `.tmp/studio/previews/`.
- Canonical job artifacts remain in `.tmp/jobs/`.
- Canonical render payloads remain in `.tmp/render-jobs/`.
- Canonical render results remain in `.tmp/render-results/`.

## Boundaries
- The studio is a review/orchestration layer, not a replacement for the canonical job artifact.
- Ratings do not overwrite previous artifacts.
- The studio may bias the next round, but it must not silently mutate previous results.
- The studio is allowed to sit above Google Sheets; the sheet remains valid as a backend queue, not the only UX.

## Current Limitations
- The studio can now show real rendered thumbnails after the plugin bridge finishes a variant, but there is still a pre-render state where only payload metadata exists.
- Real rendered visuals still depend on the Figma plugin path and a live Figma desktop session.
