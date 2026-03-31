# Project Constitution

## Purpose
This repository follows the B.L.A.S.T. protocol and A.N.T. 3-layer architecture for deterministic, self-healing automation.

## Behavioral Rules
- Reliability takes priority over speed.
- Do not guess at business logic.
- Define data first, then implement.
- Update SOPs before code when logic changes.
- After meaningful work, update `progress.md` and `findings.md`.
- Update `gemini.md` only when schema, rules, or architecture change.
- Every generated carousel must preserve the fixed 7-slide structure.
- The system must log the exact Figma reference nodes used for each output.
- The system should reuse the palette and visual language of the approved reference family instead of inventing a new style.
- The planning step and the rendering step must communicate through versioned JSON contracts, not hidden chat/session state.

## Architectural Invariants
- `architecture/` stores technical SOPs and edge-case policy.
- Navigation decisions route between SOPs and deterministic tools.
- `tools/` stores atomic, testable Python scripts only.
- `.tmp/` stores intermediate and disposable artifacts only.
- `figma_plugin/` stores the local Figma renderer that consumes plugin payloads and emits plugin result files.
- `tools/render_server.py` is the local bridge between the queue/planning layer and the live Figma plugin session.
- `tools/studio_server.py` and `tools/start_studio.py` provide the local review-and-rating layer above the planner and style engine.
- The studio is allowed to display real rendered slide thumbnails after the plugin bridge syncs a render result back into the round record.
- Environment secrets belong in `.env`, never in source files.
- A task is not complete until the payload reaches its final destination.
- The local Python layer must be able to produce both the canonical job artifact and the dedicated plugin render payload before any Figma render begins.
- The preferred local automation path is: queue/planner -> localhost bridge -> Figma plugin -> result finalization.
- The preferred local ideation path is: review studio -> job artifacts/render payloads -> optional Figma render.

## Schema Governance
- Canonical input/output schemas live in `gemini.md`.
- No implementation may begin until the payload shape is defined and approved.
- Queue schemas for external systems such as Google Sheets must be documented in `gemini.md`.

## Change Control
- If a tool fails: analyze, patch, test, then update the relevant SOP with the learning.
- Do not bypass Link verification when external systems are involved.
