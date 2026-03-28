# Figma Reference Strategy SOP

## Goal
Keep outputs visually anchored to the approved example file instead of inventing a new style.

## Approved source file
- File key: `SsqVEXMsFxp9WPbPIy9Sww`

## Approved references
- `1:46227` `Alder_1`: bold hook-cover direction
- `1:46232` `Alder_1`: text-first body layout
- `1:46239` `Alder_1`: image-plus-text body layout
- `1:46248` `Alder_1`: split text-left / media-right body layout
- `1:46256` `Alder_1`: split media-left / text-right body layout
- `1:46264` `Alder_1`: airy text-only body layout
- `1:46201` `typography slide 1`: centered dark typography signal layout
- `1:46288` `typography slide 2`: CTA language and end-card composition
- `1:46184` `CP_3`: minimal statement plus right-side object card
- `1:46190` `CP_3`: minimal split body layout with right-side object rail
- `1:46271` `CP_3`: short statement cover with right-side object card
- `1:46277` `CP_3`: longform split body layout
- `1:46283` `CP_3`: image-wall / gallery collage layout
- `1:46485` `1971245499`: portrait `1080x1350` layout reference
- `1:9052` `1971245110`: black portrait cover with profile header and footer rail
- `1:9064` `1971245119`: white portrait cover with profile header and footer rail
- `1:9076` `1971245111`: black portrait body slide with profile header and open text field
- `1:9086` `1971245120`: white portrait body slide with profile header and open text field
- `1:9176` `1971245118`: black portrait CTA slide with centered call-to-action
- `1:9187` `1971245125`: white portrait CTA slide with centered call-to-action
- `1:14767` `typography slide 1`: white editorial comparison layout
- `1:14775` `typography slide 1`: dark image-bottom cover layout
- `1:14788` `typography slide 1`: white centered CTA with footer signals

## Rules
- Every output must log the exact reference nodes it used.
- Portrait outputs may draw from either the `1:46485` portrait layout direction or the lower black-profile portrait family (`1:9052`, `1:9076`, `1:9176`), depending on the selected recipe.
- The style engine must choose from named recipe families grounded in approved nodes, not invent ad hoc layouts per run.
- The current approved style families are:
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
- The system may vary slide layouts only within approved recipes documented in the plugin render payload.
- If a new reference node is adopted, update `gemini.md`, `findings.md`, and this SOP first.

## Current implementation boundary
- Deterministic Python tools produce content, style metadata, and plugin render payloads.
- The local Figma plugin consumes that payload and writes the actual frames into Figma.
