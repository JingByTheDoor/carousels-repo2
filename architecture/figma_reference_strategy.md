# Figma Reference Strategy SOP

## Goal
Keep outputs visually anchored to the approved example file instead of inventing a new style.

## Approved source file
- File key: `SsqVEXMsFxp9WPbPIy9Sww`

## Approved references
- `1:46227` `Alder_1`: bold hook-cover direction
- `1:46232` `Alder_1`: text-first body layout
- `1:46239` `Alder_1`: image-plus-text body layout
- `1:46288` `typography slide 2`: CTA language and end-card composition
- `1:46485` `1971245499`: portrait `1080x1350` layout reference

## Rules
- Every output must log the exact reference nodes it used.
- Portrait outputs use `1:46485` for layout direction and the `Alder_1` family for palette and typography.
- The current style family `reference_mix_alder_portrait` is a curated mix grounded in those approved nodes.
- The system may vary slide layouts only within approved recipes documented in the plugin render payload.
- If a new reference node is adopted, update `gemini.md`, `findings.md`, and this SOP first.

## Current implementation boundary
- Deterministic Python tools produce content, style metadata, and plugin render payloads.
- The local Figma plugin consumes that payload and writes the actual frames into Figma.
