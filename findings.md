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
- Secondary portrait reference identified: node `1:46485`
- Portrait outputs should borrow layout direction from `1:46485` while preserving `Alder_1` palette and typography choices.
- The current plugin renderer is a curated mix of those references:
  - Black dramatic cover from `1:46227`
  - Light editorial body slides from `1:46232`
  - Alternating mask-band body direction from `1:46239`
  - Dark CTA glow treatment from `1:46288`
  - Portrait framing from `1:46485`

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

## Open Questions
- Which Google account or Google Cloud project will own the Sheets credentials long term?
- Should the next automation step be localhost plugin orchestration or direct image export?

## Notes
- The user prompt references both `claude.md` and `gemini.md` for project law. This repository treats `claude.md` as the constitution for rules and invariants, and `gemini.md` as the canonical schema and maintenance log.
