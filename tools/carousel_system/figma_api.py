from __future__ import annotations

import json
from urllib import error, request


FIGMA_META_ENDPOINT = "https://api.figma.com/v1/files/{file_key}/meta"


class FigmaApiError(RuntimeError):
    """Raised when the Figma REST API returns an error."""


def get_file_metadata(access_token: str, file_key: str) -> dict:
    api_request = request.Request(
        FIGMA_META_ENDPOINT.format(file_key=file_key),
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    try:
        with request.urlopen(api_request, timeout=30) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise FigmaApiError(f"Figma API error {exc.code}: {details}") from exc
    except error.URLError as exc:
        raise FigmaApiError(f"Unable to reach the Figma API: {exc.reason}") from exc
