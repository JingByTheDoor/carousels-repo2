# Figma Reference Strategy SOP

## Goal
Keep outputs visually anchored to the approved example file instead of inventing a new style.

## Approved source file
- File key: `SsqVEXMsFxp9WPbPIy9Sww`

## Approved local example source
- Folder: `Examples of carousels/`
- Local exported example assets may be used as approved references when a style family is harvested from disk instead of a live Figma node.
- Local reference IDs must use the prefix `local:` so they remain distinguishable from real Figma node IDs.

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
- `local:01-long-title` `Examples of carousels/01 – Long Title`: monochrome hook layout with creator footer
- `local:02-title` `Examples of carousels/02 – Title`: monochrome stacked-title body layout
- `local:03-copy` `Examples of carousels/03 – Copy`: soft rose copy layout with creator footer
- `local:05-call-to-action` `Examples of carousels/05 – Call to Action`: monochrome CTA layout with creator footer
- `local:light-1` `Examples of carousels/Light_1`: grainy light-glow hero layout
- `local:light-2` `Examples of carousels/Light_2`: grainy light-glow numbered/info layout
- `local:light-6` `Examples of carousels/Light_6`: grainy light-glow profile slide
- `local:title-01` `Examples of carousels/Title (01)`: textured retro creator CTA layout with swipe/follow button
- `local:twitter-post-default` `Examples of carousels/Twitter Post - Default`: flat tweet screenshot layout
- `local:twitter-post-soft` `Examples of carousels/TwitterPost_02`: tweet card on soft gradient background

## Rules
- Every output must log the exact reference nodes it used.
- When a style family comes from local exports instead of Figma, `reference_node_ids` and `design_reference_log.node_id` may carry approved `local:` IDs.
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
  - `reference_creator_mono_minimal`
  - `reference_light_grain_glow`
  - `reference_retro_swipe_creator`
  - `reference_twitter_card_soft`
- The system may vary slide layouts only within approved recipes documented in the plugin render payload.
- If a new reference node is adopted, update `gemini.md`, `findings.md`, and this SOP first.

## Current implementation boundary
- Deterministic Python tools produce content, style metadata, and plugin render payloads.
- The local Figma plugin consumes that payload and writes the actual frames into Figma.
