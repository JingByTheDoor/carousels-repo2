# Findings

## Initial Discoveries
- Repository state at bootstrap: effectively empty except for `.git/`.
- No existing B.L.A.S.T. memory files were present.
- No implementation files, SOPs, or tools were found.
- Bootstrap scaffold now exists and contains only memory files plus empty `architecture/`, `tools/`, and `.tmp/` directories.

## Discovery Answers
- Desired outcome: automate creation of Instagram carousels.
- Target format: 7 slides total.
- Slide structure:
  - Slide 1: attractive hook
  - Slides 2-6: informational content
  - Slide 7: call to action
- Workflow direction: simple input model of `topic/script in -> carousel out`.
- Integrations named so far: Figma MCP and Google Sheets.
- Design guidance: use template carousels as examples/reference.
- Delivery target: editable Figma output and exported image output.
- Styling rule: reuse the palette and styles from the examples and explicitly report which references were used.

## Figma Reference Findings
- Figma file key: `SsqVEXMsFxp9WPbPIy9Sww`
- Primary square reference family identified: `Alder_1`
  - Cover reference: node `1:46227`
  - Text-first body reference: node `1:46232`
  - Image-plus-text body reference: node `1:46239`
- Secondary CTA reference identified: `typography slide 2` node `1:46288`
- Secondary portrait reference identified: node `1:46485`
- `Alder_1` gives the most coherent square carousel family for v1.

## Research
- Official Google Sheets Python quickstart:
  - https://developers.google.com/workspace/sheets/api/quickstart/python
- Official Google Workspace credential guide:
  - https://developers.google.com/workspace/guides/create-credentials
- Official Google Sheets client libraries guide:
  - https://developers.google.com/workspace/sheets/api/guides/libraries
- Official Google Workspace Python samples:
  - https://github.com/googleworkspace/python-samples

## Constraints
- Do not write scripts in `tools/` until discovery is complete, the data schema is defined, and the blueprint is approved.
- Business logic must be deterministic and encoded in SOPs plus atomic tools.
- Intermediate artifacts belong in `.tmp/`.

## Open Questions
- Should topic-only input generate the full slide copy automatically? This is assumed for v1 but not yet explicitly approved.
- Should v1 default to square `1080x1080` output, or should portrait `1080x1350` become the default?
- Which Google account or Google Cloud project will own the Sheets credentials?

## Notes
- The user prompt references both `claude.md` and `gemini.md` for project law. This bootstrap treats `claude.md` as the constitution for rules and invariants, and `gemini.md` as the canonical schema and maintenance log.
