# Link Phase SOP

## Goal
Verify credentials and external access before relying on automation.

## Required environment variables
- `OPENAI_API_KEY`
- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `GOOGLE_SHEETS_SPREADSHEET_ID`

## Optional but recommended
- `OPENAI_MODEL`
- `GOOGLE_SHEETS_WORKSHEET_NAME`
- `FIGMA_ACCESS_TOKEN`
- `FIGMA_REFERENCE_FILE_KEY`

## Verification tools
- `tools/ensure_queue_sheet.py`
- `tools/check_google_sheets.py`
- `tools/check_figma_access.py`

## Google Sheets setup
1. Create a Google Cloud project.
2. Enable the Google Sheets API.
3. Create a service account.
4. Download the service account JSON key.
5. Save the JSON path into `GOOGLE_SERVICE_ACCOUNT_JSON`.
6. Share the target sheet with the service account email.

## Figma access setup
1. Generate a personal access token in Figma with file read access.
2. Save it into `FIGMA_ACCESS_TOKEN`.
3. Verify the approved reference file via `GET /v1/files/:key/meta`.

## Failure policy
- Do not proceed to queue processing if Google Sheets access fails.
- Do not rely on a Figma REST path if the token cannot read the reference file.
