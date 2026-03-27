# Carousel Automation

This repo turns a `topic` or `script` into a validated 7-slide Instagram carousel payload, with Google Sheets as the queue and Figma references locked to the approved source file.

## Current scope
- Deterministic queue setup and handshake tooling
- Deterministic payload generation around the approved schema
- AI-assisted content planning for:
  - slide 1 hook
  - slides 2-6 informational content
  - slide 7 CTA
- Figma reference logging for every generated payload

## Current limitation
Local Python tools do not write frames into Figma directly. The deterministic tooling produces the structured payload that the agent-side Figma MCP step can render into Figma.

## Setup
1. Copy `.env.example` to `.env`.
2. Add your OpenAI API key.
3. Create a Google service account JSON file and set `GOOGLE_SERVICE_ACCOUNT_JSON`.
4. Create a Google Sheet, copy its spreadsheet ID, and set `GOOGLE_SHEETS_SPREADSHEET_ID`.
5. Share the Google Sheet with the service account email.
6. Optionally add a Figma personal access token to verify REST access to the reference file.

## Install
```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -e .
```

## Link phase
```powershell
.venv\Scripts\python tools\ensure_queue_sheet.py
.venv\Scripts\python tools\check_google_sheets.py
.venv\Scripts\python tools\check_figma_access.py
```

## Manual planning
```powershell
.venv\Scripts\python tools\plan_carousel.py --topic "3 AI mistakes small businesses make"
```

## Queue processing
Add rows to the `queue` worksheet using the approved headers, then run:

```powershell
.venv\Scripts\python tools\process_next_job.py
```
