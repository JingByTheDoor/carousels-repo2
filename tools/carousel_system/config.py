from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_REFERENCE_FILE_KEY = "SsqVEXMsFxp9WPbPIy9Sww"
DEFAULT_WORKSHEET_NAME = "queue"

load_dotenv(ROOT_DIR / ".env")


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    google_service_account_json: Path | None
    google_spreadsheet_id: str | None
    google_worksheet_name: str
    figma_access_token: str | None
    figma_reference_file_key: str
    render_server_host: str
    render_server_port: int


def _optional_path(raw_value: str | None) -> Path | None:
    if not raw_value:
        return None
    path = Path(raw_value)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path.resolve()


def load_settings(
    *,
    require_openai: bool = False,
    require_google: bool = False,
    require_figma: bool = False,
) -> Settings:
    settings = Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        google_service_account_json=_optional_path(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")),
        google_spreadsheet_id=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID"),
        google_worksheet_name=os.getenv("GOOGLE_SHEETS_WORKSHEET_NAME", DEFAULT_WORKSHEET_NAME),
        figma_access_token=os.getenv("FIGMA_ACCESS_TOKEN"),
        figma_reference_file_key=os.getenv("FIGMA_REFERENCE_FILE_KEY", DEFAULT_REFERENCE_FILE_KEY),
        render_server_host=os.getenv("RENDER_SERVER_HOST", "127.0.0.1"),
        render_server_port=int(os.getenv("RENDER_SERVER_PORT", "8765")),
    )

    if require_openai and not settings.openai_api_key:
        raise ConfigError("OPENAI_API_KEY is required for AI planning.")

    if require_google:
        if not settings.google_service_account_json:
            raise ConfigError("GOOGLE_SERVICE_ACCOUNT_JSON is required for Google Sheets access.")
        if not settings.google_service_account_json.exists():
            raise ConfigError(
                f"Google service account file not found: {settings.google_service_account_json}"
            )
        if not settings.google_spreadsheet_id:
            raise ConfigError("GOOGLE_SHEETS_SPREADSHEET_ID is required for Google Sheets access.")

    if require_figma and not settings.figma_access_token:
        raise ConfigError("FIGMA_ACCESS_TOKEN is required for Figma REST verification.")

    return settings
