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

## Architectural Invariants
- `architecture/` stores technical SOPs and edge-case policy.
- Navigation decisions route between SOPs and deterministic tools.
- `tools/` stores atomic, testable Python scripts only.
- `.tmp/` stores intermediate and disposable artifacts only.
- Environment secrets belong in `.env`, never in source files.
- A task is not complete until the payload reaches its final destination.

## Schema Governance
- Canonical input/output schemas live in `gemini.md`.
- No implementation may begin until the payload shape is defined and approved.

## Change Control
- If a tool fails: analyze, patch, test, then update the relevant SOP with the learning.
- Do not bypass Link verification when external systems are involved.
