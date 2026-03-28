# Task Plan

## Status
- Phase: `A - Architect`
- Blueprint approval: `Approved`
- Current milestone: `Plugin renderer foundation implemented`

## Goal
Bootstrap this repository under the B.L.A.S.T. protocol and evolve the v1 planning pipeline into a tool-owned system that no longer depends on a live Codex session for Figma rendering.

## Active Blueprint
- Product: Instagram carousel automation
- Core flow: `topic/script in -> 7-slide carousel out`
- Source of truth: Google Sheets queue for automation, with manual input supported during local testing
- Primary output: editable Figma carousel
- Secondary output: exported PNG slide set
- Default aspect ratio for v1: `1080x1350` portrait
- Design rule: use the palette and visual language from approved Figma references and log exact reference nodes used
- Primary Figma reference family:
  - Cover: `Alder_1` node `1:46227`
  - Body: `Alder_1` node `1:46232`
  - Body with image-mask variation: `Alder_1` node `1:46239`
- Secondary references:
  - CTA inspiration: `typography slide 2` node `1:46288`
  - Portrait reference: node `1:46485`
- Working assumption:
  - If only a topic is provided, the system generates the full hook, five informational slides, and CTA copy automatically.

## Phases

### Phase 0: Initialization
- [x] Create project memory files
- [x] Initialize constitution and schema files
- [x] Create scaffold directories: `architecture/`, `tools/`, `.tmp/`
- [x] Confirm project intent through discovery

### Phase 1: Blueprint
- [x] Capture North Star outcome
- [x] Identify integrations and credential readiness
- [x] Confirm source of truth
- [x] Confirm delivery payload and destination
- [x] Confirm behavioral rules and guardrails
- [x] Define canonical JSON data schema in `gemini.md`
- [x] Research relevant repos, docs, and prior art
- [x] Approve Blueprint

### Phase 2: Link
- [x] Verify `.env` existence and required keys
- [x] Test service handshakes
- [x] Add minimal connectivity checks in `tools/`

### Phase 3: Architect
- [x] Write SOPs in `architecture/`
- [x] Build deterministic planning tools in `tools/`
- [x] Build canonical plugin render payload generation
- [x] Scaffold a local Figma plugin renderer
- [x] Build a local render-result finalizer
- [ ] Validate the plugin against a live manual Figma run
- [ ] Expand style selection beyond the curated first-pass recipes

### Phase 4: Stylize
- [ ] Refine payload formatting
- [ ] Present results for feedback
- [ ] Improve copy quality with a stronger prompt registry

### Phase 5: Trigger
- [ ] Prepare production transfer plan
- [ ] Set up automation trigger(s)
- [ ] Finalize maintenance log in `gemini.md`

## Current Blockers
- The local plugin renderer still needs a live manual Figma run for end-to-end verification.
- PNG export automation is still not implemented.
- The plugin handoff is file-based; localhost or cloud-triggered orchestration is still pending.
