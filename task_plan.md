# Task Plan

## Status
- Phase: `B - Blueprint`
- Blueprint approval: `Pending user answers`
- Tool/script authoring in `tools/`: `Blocked`

## Goal
Bootstrap this repository under the B.L.A.S.T. protocol and pause implementation until discovery, schema definition, and blueprint approval are complete.

## Draft Blueprint
- Product: Instagram carousel automation
- Core flow: `topic/script in -> 7-slide carousel out`
- Source of truth: Google Sheets queue for automation, with manual input supported during local testing
- Primary output: editable Figma carousel
- Secondary output: exported PNG slide set
- Default aspect ratio for v1: `1080x1080` square
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
- [ ] Confirm project intent through discovery

### Phase 1: Blueprint
- [x] Capture North Star outcome
- [x] Identify integrations and credential readiness
- [x] Confirm source of truth
- [x] Confirm delivery payload and destination
- [x] Confirm behavioral rules and guardrails
- [x] Define canonical JSON data schema in `gemini.md`
- [ ] Research relevant repos, docs, and prior art
- [ ] Approve Blueprint

### Phase 2: Link
- [ ] Verify `.env` existence and required keys
- [ ] Test service handshakes
- [ ] Add minimal connectivity checks in `tools/`

### Phase 3: Architect
- [ ] Write SOPs in `architecture/`
- [ ] Build deterministic tools in `tools/`
- [ ] Validate edge cases and repair loop coverage

### Phase 4: Stylize
- [ ] Refine payload formatting
- [ ] Present results for feedback

### Phase 5: Trigger
- [ ] Prepare production transfer plan
- [ ] Set up automation trigger(s)
- [ ] Finalize maintenance log in `gemini.md`

## Current Blockers
- Blueprint is not yet approved.
- Google Sheets credentials and access model are not yet configured.
- No implementation work may begin until the above are resolved.
