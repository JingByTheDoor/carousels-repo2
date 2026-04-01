# Studio Review SOP

## Goal
Provide a minimal local review loop for generating 3 real Figma variants, picking the winner, writing what is wrong with the other 2, and immediately generating the next 3 without using Google Sheets as the primary interface.

## Entry Points
- `tools/studio_server.py`
- `tools/start_studio.py`

## Review Loop
1. User opens the local studio in a browser.
2. User clicks `Generate 3`.
3. If no topic or script is supplied, Studio auto-generates the brief in the fixed niche `materials helpful to English teachers`.
4. Studio generates one review round with exactly 3 variants.
5. Each variant produces:
   - a canonical job artifact in `.tmp/jobs/`
   - a render payload in `.tmp/render-jobs/`
   - embedded review metadata inside the round record
6. If the Figma plugin bridge is running, the bridge acquires only studio review variants in this launcher mode, renders them, and syncs the result back into the round file.
7. The browser shows only real rendered thumbnails or a waiting state. It must not show payload-only fake slides in default review mode.
8. User picks 1 winning variant and writes short rejection notes for the other 2.
9. Studio generates the next round using the winner plus loser notes as the anchor.

## Deterministic Rules
- Review mode always creates exactly 3 variants.
- Default niche preset is `english_teacher_materials`.
- Default review-safe families are limited to image-capable styles:
  - `alder_split_right`
  - `light_glow`
  - `twitter_card`
- Copy-length variation in review mode is driven by:
  - `tight`
  - `balanced`
  - `expanded`
- Review mode defaults to `hybrid` image sourcing.
- Review-mode image rule:
  - slide 1 must have an image
  - at least 3 info slides must have images
  - slide 7 CTA does not carry an image by default
- The next round must not be generated until the user selects a winner.
- The next round should anchor on the winner's style and copy profile, then incorporate loser rejection notes into planner guidance.

## Artifacts
- Round files live in `.tmp/studio/rounds/`.
- Studio state lives in `.tmp/studio/state.json`.
- Rendered slide thumbnails live in `.tmp/studio/previews/`.
- Canonical job artifacts remain in `.tmp/jobs/`.
- Canonical render payloads remain in `.tmp/render-jobs/`.
- Canonical render results remain in `.tmp/render-results/`.

## Boundaries
- The studio is a review/orchestration layer, not a replacement for the canonical job artifact.
- Review mode is isolated from Google Sheets when started through `tools/start_studio.py`; the bridge runs in `studio_only` mode for the default launcher path.
- Ratings and winner selection do not overwrite previous artifacts.
- The studio may bias the next round, but it must not silently mutate previous results.
- The studio is allowed to sit above Google Sheets; the sheet remains valid as backend plumbing, not the primary UX.

## Current Limitations
- Real rendered visuals still depend on the Figma plugin path and a live Figma desktop session.
- The default review lane expects the plugin to be running so the waiting state can turn into real thumbnails.
- The current renderer uses separate pages inside the active Figma file rather than creating a brand-new Figma file per round.
