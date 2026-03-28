# Progress

## 2026-03-27

### Completed
- Inspected the repository root and confirmed the active project folder is `carousels-repo2`.
- Inspected the project and confirmed it had no files beyond `.git/`.
- Initialized project memory files:
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `claude.md`
  - `gemini.md`
- Created scaffold directories:
  - `architecture/`
  - `tools/`
  - `.tmp/`
- Captured initial product direction from the user:
  - Instagram carousel automation
  - 7-slide structure
  - Figma MCP integration
  - Template carousels as design references
- Parsed the provided Figma file and identified concrete reference nodes for cover, body, CTA, and portrait examples.
- Drafted the canonical input/output schemas in `gemini.md`.
- Drafted a Google Sheets queue schema for automation input.
- Recorded external research sources for Google Sheets API setup.
- Received user approval for:
  - topic-only automatic copy generation
  - portrait `1080x1350` as the default output ratio
  - the Google Sheets queue design
- Added architecture SOPs for queue intake, content planning, Figma references, and Link verification.
- Added Python project scaffolding, environment contract, and initial queue/planning tools.
- Created a local `.venv` and installed the project in editable mode.
- Added clean CLI handling for missing configuration values.
- Updated `.gitignore` to exclude Google service-account JSON files.
- Created a new target Figma file for rendered output:
  - `https://www.figma.com/design/SL9uqVFWC8oEDjn2th47Im`

### Errors
- `rg --files` returned no tracked files because the repository was empty. No corrective action required.

### Test / Verification
- Verified repository contents before bootstrap.
- Verified post-bootstrap file and directory creation in the repository root.
- Verified Figma reference access through MCP with concrete node lookups:
  - `1:46227`
  - `1:46232`
  - `1:46239`
  - `1:46288`
  - `1:46485`
- Live credential-based Link tests are still pending because `.env` has not been configured yet.
- `python -m compileall tools` passed.
- `.venv\Scripts\python -m pip install -e .` succeeded.
- `.venv\Scripts\python tools\plan_carousel.py --help` succeeded.
- `.venv\Scripts\python tools\ensure_queue_sheet.py` failed cleanly with missing `GOOGLE_SERVICE_ACCOUNT_JSON`.
- `.venv\Scripts\python tools\check_figma_access.py` failed cleanly with missing `FIGMA_ACCESS_TOKEN`.
- `.venv\Scripts\python tools\process_next_job.py` succeeded and generated `.tmp/jobs/sheet-row-2.json`.
- Figma draft file creation via MCP succeeded.
- Figma slide rendering via MCP succeeded after the connected Figma account was upgraded to a Pro plan with a Developer seat.
- Rendered 7 portrait slides into the Figma file on page `sheet-row-2`.
- Updated the payload artifact and Google Sheet row with the final Figma URL and slide node IDs.

### Current Status
- Blueprint is approved.
- Tooling has been scaffolded and is ready for local verification.
- Google Sheets and OpenAI planning are working.
- Figma rendering through MCP is working.
- PNG export automation is still not implemented in the local toolchain.
