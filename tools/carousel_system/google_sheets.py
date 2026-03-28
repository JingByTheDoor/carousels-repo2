from __future__ import annotations

from dataclasses import dataclass
from string import ascii_uppercase

from google.oauth2 import service_account
from googleapiclient.discovery import build

from carousel_system.config import Settings
from carousel_system.models import CarouselInput, QueueRow


SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"
QUEUE_HEADERS = [
    "job_id",
    "status",
    "topic",
    "script",
    "cta_text",
    "aspect_ratio",
    "output_modes",
    "reference_style",
    "notes",
    "figma_url",
    "export_paths",
    "reference_nodes_used",
    "error",
    "language",
    "style_family",
    "style_recipe",
    "prompt_version",
    "render_payload_path",
    "render_result_path",
]


@dataclass(frozen=True)
class SpreadsheetInfo:
    spreadsheet_id: str
    title: str


class GoogleSheetsQueue:
    def __init__(self, settings: Settings) -> None:
        credentials = service_account.Credentials.from_service_account_file(
            str(settings.google_service_account_json),
            scopes=[SHEETS_SCOPE],
        )
        self.settings = settings
        self.service = build("sheets", "v4", credentials=credentials, cache_discovery=False)

    def get_spreadsheet_info(self) -> SpreadsheetInfo:
        response = (
            self.service.spreadsheets()
            .get(spreadsheetId=self.settings.google_spreadsheet_id)
            .execute()
        )
        return SpreadsheetInfo(
            spreadsheet_id=self.settings.google_spreadsheet_id or "",
            title=response["properties"]["title"],
        )

    def ensure_queue_sheet(self) -> None:
        spreadsheet = (
            self.service.spreadsheets()
            .get(spreadsheetId=self.settings.google_spreadsheet_id)
            .execute()
        )
        sheet_titles = {sheet["properties"]["title"] for sheet in spreadsheet.get("sheets", [])}
        if self.settings.google_worksheet_name not in sheet_titles:
            body = {
                "requests": [
                    {
                        "addSheet": {
                            "properties": {
                                "title": self.settings.google_worksheet_name,
                            }
                        }
                    }
                ]
            }
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.settings.google_spreadsheet_id,
                body=body,
            ).execute()

        header_range = f"{self.settings.google_worksheet_name}!A1:{_column_letter(len(QUEUE_HEADERS))}1"
        self.service.spreadsheets().values().update(
            spreadsheetId=self.settings.google_spreadsheet_id,
            range=header_range,
            valueInputOption="RAW",
            body={"values": [QUEUE_HEADERS]},
        ).execute()

    def read_queue_rows(self) -> list[QueueRow]:
        end_column = _column_letter(len(QUEUE_HEADERS))
        response = (
            self.service.spreadsheets()
            .values()
            .get(
                spreadsheetId=self.settings.google_spreadsheet_id,
                range=f"{self.settings.google_worksheet_name}!A:{end_column}",
            )
            .execute()
        )
        values = response.get("values", [])
        if not values:
            return []

        headers = values[0]
        rows: list[QueueRow] = []
        for index, raw_row in enumerate(values[1:], start=2):
            padded = raw_row + [""] * (len(headers) - len(raw_row))
            rows.append(QueueRow(row_number=index, values=dict(zip(headers, padded))))
        return rows

    def find_next_pending_row(self) -> QueueRow | None:
        for row in self.read_queue_rows():
            status = row.values.get("status", "").strip().lower()
            if status in {"", "queued"}:
                return row
        return None

    def update_row(self, row_number: int, updates: dict[str, str]) -> None:
        data = []
        for header, value in updates.items():
            if header not in QUEUE_HEADERS:
                raise ValueError(f"Unknown queue header: {header}")
            column = _column_letter(QUEUE_HEADERS.index(header) + 1)
            data.append(
                {
                    "range": f"{self.settings.google_worksheet_name}!{column}{row_number}",
                    "values": [[value]],
                }
            )

        self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.settings.google_spreadsheet_id,
            body={"valueInputOption": "RAW", "data": data},
        ).execute()

    def queue_row_to_input(self, row: QueueRow) -> CarouselInput:
        output_modes = [
            mode.strip()
            for mode in row.values.get("output_modes", "figma,png").split(",")
            if mode.strip()
        ]
        reference_nodes = [
            node.strip()
            for node in row.values.get("reference_nodes_used", "").split(",")
            if node.strip()
        ]
        input_data = {
            "job_id": row.values.get("job_id") or f"sheet-row-{row.row_number}",
            "source": "google_sheets",
            "topic": row.values.get("topic"),
            "script": row.values.get("script"),
            "cta_text": row.values.get("cta_text"),
            "language": row.values.get("language"),
            "aspect_ratio": row.values.get("aspect_ratio") or "portrait_1080x1350",
            "output_modes": output_modes or ["figma", "png"],
            "reference_style": row.values.get("reference_style") or "alder_1",
            "reference_file_key": self.settings.figma_reference_file_key,
            "notes": row.values.get("notes"),
        }
        if reference_nodes:
            input_data["reference_node_ids"] = reference_nodes
        return CarouselInput(**input_data)


def _column_letter(index: int) -> str:
    if index < 1:
        raise ValueError("Column index must be 1 or greater.")
    result = ""
    current = index
    while current:
        current, remainder = divmod(current - 1, 26)
        result = ascii_uppercase[remainder] + result
    return result
