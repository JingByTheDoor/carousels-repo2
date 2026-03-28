# Findings

## Initial Discoveries
- Repository state at bootstrap: effectively empty except for `.git/`.
- No existing B.L.A.S.T. memory files were present.
- No implementation files, SOPs, or tools were found.
- Bootstrap scaffold now exists and contains memory files, SOPs, tools, `.tmp/`, and a local `figma_plugin/` renderer.

## Discovery Answers
- Desired outcome: automate creation of Instagram carousels.
- Target format: 7 slides total.
- Slide structure:
  - Slide 1: attractive hook
  - Slides 2-6: informational content
  - Slide 7: call to action
- Workflow direction: simple input model of `topic/script in -> carousel out`.
- Integrations named so far: Figma, Google Sheets, OpenAI.
- Design guidance: use template carousels as examples/reference.
- Delivery target: editable Figma output and exported image output.
- Styling rule: reuse the palette and styles from the examples and explicitly report which references were used.
- Topic-only input is approved to generate the full slide copy automatically.
- Default aspect ratio is approved as `1080x1350`.
- Google Sheets queue setup is approved.

## Figma Reference Findings
- Figma file key: `SsqVEXMsFxp9WPbPIy9Sww`
- Primary square reference family identified: `Alder_1`
  - Cover reference: node `1:46227`
  - Text-first body reference: node `1:46232`
  - Image-plus-text body reference: node `1:46239`
- Secondary CTA reference identified: `typography slide 2` node `1:46288`
- Secondary centered dark reference identified: `typography slide 1` node `1:46201`
- Secondary minimal statement references identified:
  - `CP_3` node `1:46184`
  - `CP_3` node `1:46190`
- Additional `Alder_1` body variants identified:
  - `1:46248` split text-left / media-right
  - `1:46256` split media-left / text-right
  - `1:46264` airy text-only
- Additional `CP_3` variants identified:
  - `1:46271` short statement cover
  - `1:46277` longform split body
  - `1:46283` gallery wall
- Secondary portrait reference identified: node `1:46485`
- Additional portrait black-profile references identified:
  - `1:9052` cover with profile header / footer rail
  - `1:9076` body slide with open text field
  - `1:9176` centered CTA slide
- Additional portrait white-profile references identified:
  - `1:9064` cover with profile header / footer rail
  - `1:9086` body slide with open text field
  - `1:9187` centered CTA slide
- Additional light typography references identified:
  - `1:14767` white editorial comparison layout
  - `1:14775` dark image-bottom cover layout
  - `1:14788` white CTA with footer signals
- Portrait outputs now have two approved directions:
  - `1:46485` for the original portrait layout direction used by the upper families
  - `1:9052` / `1:9076` / `1:9176` for the black-profile portrait family
  - `1:9064` / `1:9086` / `1:9187` for the white-profile portrait family
- The current plugin renderer is a curated mix of those references:
  - Black dramatic cover from `1:46227`
  - Light editorial body slides from `1:46232`
  - Alternating mask-band body direction from `1:46239`
  - Dark CTA glow treatment from `1:46288`
  - Portrait framing from `1:46485`
- The next style-engine pass is approved to use three recipe families:
- The next style-engine pass is approved to use these recipe families:
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

## Research
- Official Google Sheets Python quickstart:
  - https://developers.google.com/workspace/sheets/api/quickstart/python
- Official Google Workspace credential guide:
  - https://developers.google.com/workspace/guides/create-credentials
- Official Google Sheets client libraries guide:
  - https://developers.google.com/workspace/sheets/api/guides/libraries
- Official Google Workspace Python samples:
  - https://github.com/googleworkspace/python-samples
- Official Figma plugin API docs:
  - https://developers.figma.com/docs/plugins/api/figma/

## Constraints
- Business logic must be deterministic and encoded in SOPs plus atomic tools.
- Intermediate artifacts belong in `.tmp/`.
- The Python layer must communicate rendering intent through versioned JSON payloads instead of chat/session memory.
- Raw `headline + body + layout_variant` is not enough for reliable rendering; the payload needs display-safe text variants and truncation metadata.
- Live plugin rendering still requires a human to open Figma and run the local plugin.
- The local bridge path can remove manual JSON upload/download, but it still depends on a live Figma desktop session with the development plugin running.
- Figma `fileKey` access from plugins depends on private-plugin API availability; the plugin tolerates `null` when unavailable.
- Figma Desktop’s plugin webview treats localhost fetches like browser requests, so the bridge must send CORS headers even on `204 No Content` and should advertise `Access-Control-Allow-Private-Network: true`.
- Using the plugin iframe for localhost bridge traffic is brittle; the better integration point is the plugin controller in `code.js`, which can make the bridge requests and send structured results back to the UI.
- A legacy default of `reference_style=alder_1` made older jobs look like the new selector was broken, because they still carried an old explicit style preference even after the style engine changed.
- Planned rows must be rehydrated from the current code path; otherwise stale `.render.json` payloads can mask style-engine changes.

## Open Questions
- Which Google account or Google Cloud project will own the Sheets credentials long term?
- Should the next automation step be localhost plugin orchestration or direct image export?

## Notes
- The user prompt references both `claude.md` and `gemini.md` for project law. This repository treats `claude.md` as the constitution for rules and invariants, and `gemini.md` as the canonical schema and maintenance log.
