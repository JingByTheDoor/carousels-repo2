from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from carousel_system.config import ROOT_DIR, Settings
from carousel_system.models import (
    CarouselOutput,
    ImageAsset,
    ImageStrategy,
    PluginRenderPayload,
    RenderImageAssetSpec,
)


IMAGE_ASSETS_DIR = ROOT_DIR / ".tmp" / "image-assets"
IMAGE_FRIENDLY_FAMILIES = {
    "reference_alder_split_media",
    "reference_cp_gallery_wall",
    "reference_twitter_card_soft",
    "reference_light_grain_glow",
    "reference_typography_signal",
}
IMAGE_SLOT_BY_FAMILY = {
    "reference_alder_split_media": ("cover_media", "mask"),
    "reference_cp_gallery_wall": ("cover_media", "gallery_wall"),
    "reference_twitter_card_soft": ("cover_media", "card_embed"),
    "reference_light_grain_glow": ("cover_media", "blur_glow"),
    "reference_typography_signal": ("cover_media", "blur_glow"),
}
LOCALE_BY_LANGUAGE = {
    "ru": "ru-RU",
    "en": "en-US",
}


@dataclass(frozen=True)
class ImageRequest:
    slide_number: int
    role: str
    slot: str
    treatment: str
    query: str
    reason: str


@dataclass(frozen=True)
class PexelsCandidate:
    photo_id: int
    width: int
    height: int
    alt_text: str
    photographer: str
    page_url: str | None
    download_url: str


def resolve_image_assets(settings: Settings, record: CarouselOutput, payload: PluginRenderPayload) -> None:
    _apply_slot_defaults(record, payload)
    strategy = _resolve_image_strategy(settings, record, payload)
    record.image_strategy = strategy
    record.image_assets = []
    payload.image_strategy.mode = strategy.mode
    payload.image_strategy.provider = strategy.provider

    if strategy.mode == "none":
        _write_image_manifest(record)
        return

    if strategy.provider != "pexels":
        record.image_strategy.reason = "Only Pexels stock acquisition is implemented right now."
        _write_image_manifest(record)
        return

    if not settings.pexels_api_key:
        record.image_strategy.reason = "PEXELS_API_KEY is not configured, so stock images were skipped."
        _write_image_manifest(record)
        return

    requests = _build_image_requests(record, payload)
    if not requests:
        record.image_strategy.reason = "No image slots are active for the selected style family."
        _write_image_manifest(record)
        return

    assets: list[ImageAsset] = []
    for image_request in requests:
        asset = _find_and_cache_pexels_asset(settings, record, image_request)
        if asset:
            assets.append(asset)

    if assets:
        record.image_assets = assets
        _attach_assets_to_payload(payload, assets)
        record.image_strategy.reason = (
            f"Attached {len(assets)} stock image asset"
            f"{'' if len(assets) == 1 else 's'} via Pexels for {payload.style_family}."
        )
    else:
        record.image_strategy.reason = "No acceptable Pexels candidate was found for the active image slots."

    _write_image_manifest(record)


def _apply_slot_defaults(record: CarouselOutput, payload: PluginRenderPayload) -> None:
    slot, treatment = IMAGE_SLOT_BY_FAMILY.get(payload.style_family, ("none", "none"))
    for slide in payload.slides:
        slide.image_slot = "none"
        slide.image_required = False
        slide.image_treatment = "none"
        slide.image_asset = None

    if slot == "none" or payload.style_family not in IMAGE_FRIENDLY_FAMILIES:
        return

    hook_slide = next((slide for slide in payload.slides if slide.slide_number == 1), None)
    if hook_slide is None:
        return

    hook_slide.image_slot = slot
    hook_slide.image_required = record.normalized_input.image_mode in {"stock", "ai"}
    hook_slide.image_treatment = treatment


def _resolve_image_strategy(
    settings: Settings,
    record: CarouselOutput,
    payload: PluginRenderPayload,
) -> ImageStrategy:
    requested_mode = record.normalized_input.image_mode
    preferred_provider = record.normalized_input.image_source_preference

    if requested_mode == "none":
        return ImageStrategy(mode="none", provider=None, reason="User explicitly disabled images.")

    if payload.style_family not in IMAGE_FRIENDLY_FAMILIES:
        return ImageStrategy(
            mode="none",
            provider=None,
            reason=f"{payload.style_family} is currently treated as a text-led family.",
        )

    if requested_mode == "ai":
        return ImageStrategy(
            mode="ai",
            provider="openai_gpt_image",
            reason="AI generation was requested, but only stock acquisition is implemented in this pass.",
        )

    if requested_mode == "stock":
        return ImageStrategy(mode="stock", provider="pexels", reason="Stock-only mode.")

    if requested_mode == "hybrid":
        provider = "pexels"
        reason = "Hybrid requested. Stock-first is implemented now; AI fallback will come later."
        if preferred_provider == "openai_gpt_image":
            reason = "Hybrid requested. AI fallback is not implemented yet, so stock-first remains active."
        return ImageStrategy(mode="hybrid", provider=provider, reason=reason)

    if requested_mode == "auto":
        if not settings.pexels_api_key:
            return ImageStrategy(
                mode="none",
                provider=None,
                reason="Auto image mode chose stock-first, but PEXELS_API_KEY is missing.",
            )
        return ImageStrategy(
            mode="stock",
            provider="pexels",
            reason="Auto image mode chose stock-first for an image-friendly family.",
        )

    return ImageStrategy(mode="none", provider=None, reason="No image strategy matched.")


def _build_image_requests(record: CarouselOutput, payload: PluginRenderPayload) -> list[ImageRequest]:
    requests: list[ImageRequest] = []
    for slide in payload.slides:
        if slide.image_slot == "none":
            continue
        query = _build_query(record, slide.slide_number)
        requests.append(
            ImageRequest(
                slide_number=slide.slide_number,
                role=slide.slide_role,
                slot=slide.image_slot,
                treatment=slide.image_treatment,
                query=query,
                reason=f"{payload.style_family} exposes a hook-media slot.",
            )
        )
    return requests


def _build_query(record: CarouselOutput, slide_number: int) -> str:
    slide = next((item for item in record.content_plan if item.slide_number == slide_number), None)
    topic = record.normalized_input.topic or ""
    headline = slide.headline if slide else ""
    source = topic or headline or record.content_plan[0].headline
    keywords = _compact_keywords(source)
    focus = record.normalized_input.image_focus
    if focus == "brand_safe":
        return f"{keywords} professional clean"
    if focus == "literal":
        return f"{keywords} realistic"
    if focus == "abstract":
        return f"{keywords} conceptual"
    return f"{keywords} editorial"


def _compact_keywords(text: str, *, max_words: int = 6) -> str:
    tokens = re.findall(r"[A-Za-z\u0400-\u04FF0-9]+", text.lower())
    if not tokens:
        return "professional education"
    return " ".join(tokens[:max_words])


def _find_and_cache_pexels_asset(
    settings: Settings,
    record: CarouselOutput,
    image_request: ImageRequest,
) -> ImageAsset | None:
    candidates = _search_pexels_candidates(
        settings,
        image_request.query,
        language=record.language or record.normalized_input.language or "en",
    )
    if not candidates:
        return None

    best = max(candidates, key=lambda candidate: _score_candidate(candidate, image_request.query))
    asset_dir = IMAGE_ASSETS_DIR / record.job_id
    asset_dir.mkdir(parents=True, exist_ok=True)
    extension = _detect_extension(best.download_url)
    asset_path = asset_dir / f"slide-{image_request.slide_number:02d}-pexels-{best.photo_id}{extension}"
    if not asset_path.exists():
        _download_binary(settings, best.download_url, asset_path)

    return ImageAsset(
        slide_number=image_request.slide_number,
        role=image_request.role,
        source_mode="stock",
        provider="pexels",
        query_or_prompt=image_request.query,
        original_url=best.page_url or best.download_url,
        local_path=str(asset_path),
        credit=f"Photo by {best.photographer} on Pexels",
        width=best.width,
        height=best.height,
        alt_text=best.alt_text,
    )


def _search_pexels_candidates(settings: Settings, query: str, *, language: str) -> list[PexelsCandidate]:
    locale = LOCALE_BY_LANGUAGE.get(language.lower(), "en-US")
    params = urlencode(
        {
            "query": query,
            "per_page": 8,
            "orientation": "portrait",
            "page": 1,
            "locale": locale,
        }
    )
    url = f"https://api.pexels.com/v1/search?{params}"
    response = _read_json(settings, url)
    photos = response.get("photos", [])
    candidates: list[PexelsCandidate] = []
    for photo in photos:
        src = photo.get("src") or {}
        download_url = src.get("portrait") or src.get("large2x") or src.get("large") or src.get("original")
        if not download_url:
            continue
        candidates.append(
            PexelsCandidate(
                photo_id=int(photo.get("id", 0)),
                width=int(photo.get("width", 0) or 0),
                height=int(photo.get("height", 0) or 0),
                alt_text=(photo.get("alt") or "").strip(),
                photographer=(photo.get("photographer") or "Unknown").strip(),
                page_url=(photo.get("url") or "").strip() or None,
                download_url=download_url,
            )
        )
    return candidates


def _score_candidate(candidate: PexelsCandidate, query: str) -> float:
    score = 0.0
    if candidate.height >= candidate.width:
        score += 4.0
    if candidate.width and candidate.height:
        score += min(candidate.height / max(candidate.width, 1), 2.0)
    alt_words = set(_compact_keywords(candidate.alt_text, max_words=12).split())
    query_words = set(_compact_keywords(query, max_words=12).split())
    score += float(len(alt_words & query_words)) * 1.5
    if candidate.alt_text:
        score += 1.0
    return score


def _read_json(settings: Settings, url: str) -> dict:
    headers = {"User-Agent": "carousel-automation/0.1"}
    if settings.pexels_api_key:
        headers["Authorization"] = settings.pexels_api_key
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Pexels API error {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Pexels API: {exc.reason}") from exc


def _download_binary(settings: Settings, url: str, destination: Path) -> None:
    headers = {"User-Agent": "carousel-automation/0.1"}
    if settings.pexels_api_key:
        headers["Authorization"] = settings.pexels_api_key
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            destination.write_bytes(response.read())
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Pexels download error {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not download stock image: {exc.reason}") from exc


def _detect_extension(url: str) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return suffix
    query = parse_qs(parsed.query)
    if "fm" in query:
        fmt = query["fm"][0].lower()
        if fmt in {"jpg", "jpeg", "png", "webp"}:
            return f".{fmt}"
    return ".jpg"


def _attach_assets_to_payload(payload: PluginRenderPayload, assets: list[ImageAsset]) -> None:
    asset_map = {asset.slide_number: asset for asset in assets}
    for slide in payload.slides:
        asset = asset_map.get(slide.slide_number)
        if not asset:
            continue
        slide.image_asset = RenderImageAssetSpec(
            provider=asset.provider,
            local_path=asset.local_path,
            url=asset.original_url,
            credit=asset.credit,
        )


def _write_image_manifest(record: CarouselOutput) -> None:
    manifest_path = IMAGE_ASSETS_DIR / record.job_id / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "job_id": record.job_id,
                "image_strategy": record.image_strategy.model_dump(mode="json"),
                "image_assets": [asset.model_dump(mode="json") for asset in record.image_assets],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
