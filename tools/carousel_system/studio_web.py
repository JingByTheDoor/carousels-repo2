from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from carousel_system.config import ConfigError, ROOT_DIR, load_settings
from carousel_system.studio import (
    STUDIO_DIR,
    ReviewResetRequest,
    ReviewRoundCreateRequest,
    ReviewWinnerRequest,
    StudioCreateRequest,
    StudioRateRequest,
    create_minimal_review_round,
    create_next_review_round,
    create_next_round,
    create_review_round,
    load_latest_review_round,
    load_latest_round,
    load_round,
    rate_variant,
    reset_review_round,
    save_review_winner,
    submit_review_round,
    studio_bootstrap_payload,
)


ASSETS_DIR = ROOT_DIR / "studio_assets"


def create_app() -> FastAPI:
    STUDIO_DIR.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title="Carousel Review Studio", version="0.1.0")
    app.mount("/studio-assets", StaticFiles(directory=ASSETS_DIR), name="studio-assets")
    app.mount("/studio-output", StaticFiles(directory=STUDIO_DIR), name="studio-output")
    app.mount("/tmp-output", StaticFiles(directory=ROOT_DIR / ".tmp"), name="tmp-output")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(ASSETS_DIR / "index.html")

    @app.get("/api/bootstrap")
    def bootstrap() -> dict:
        payload = studio_bootstrap_payload()
        latest_round = load_latest_round()
        latest_review = load_latest_review_round()
        payload["latest_round"] = latest_round.model_dump(mode="json") if latest_round else None
        payload["latest_review_round"] = latest_review.model_dump(mode="json") if latest_review else None
        return payload

    @app.get("/api/review-rounds/latest")
    def latest_review_round() -> dict:
        round_record = load_latest_review_round()
        if round_record is None:
            raise HTTPException(status_code=404, detail="No review rounds generated yet.")
        return round_record.model_dump(mode="json")

    @app.get("/api/review-rounds/{round_id}")
    def get_review_round(round_id: str) -> dict:
        round_record = load_round(round_id)
        if round_record is None:
            raise HTTPException(status_code=404, detail="Review round not found.")
        return round_record.model_dump(mode="json")

    @app.post("/api/review-rounds")
    def create_review_lane_round(request: ReviewRoundCreateRequest) -> dict:
        try:
            settings = load_settings(require_openai=True)
            round_record = create_minimal_review_round(settings, request)
        except ConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return round_record.model_dump(mode="json")

    @app.post("/api/review-rounds/{round_id}/winner")
    def set_review_winner(round_id: str, request: ReviewWinnerRequest) -> dict:
        try:
            round_record = save_review_winner(round_id, request)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return round_record.model_dump(mode="json")

    @app.post("/api/review-rounds/{round_id}/submit")
    def submit_review_lane_round(round_id: str, request: ReviewWinnerRequest) -> dict:
        try:
            round_record = submit_review_round(round_id, request)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return round_record.model_dump(mode="json")

    @app.post("/api/review-rounds/{round_id}/next")
    def next_review_round(round_id: str) -> dict:
        try:
            settings = load_settings(require_openai=True)
            round_record = create_next_review_round(settings, round_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return round_record.model_dump(mode="json")

    @app.post("/api/review-rounds/reset")
    def reset_review_lane_round(request: ReviewResetRequest) -> dict:
        round_record = reset_review_round(request.round_id)
        return {
            "status": "ok",
            "cleared_round_id": round_record.round_id if round_record else None,
        }

    @app.get("/api/rounds/latest")
    def latest_round() -> dict:
        round_record = load_latest_round()
        if round_record is None:
            raise HTTPException(status_code=404, detail="No rounds generated yet.")
        return round_record.model_dump(mode="json")

    @app.get("/api/rounds/{round_id}")
    def get_round(round_id: str) -> dict:
        round_record = load_round(round_id)
        if round_record is None:
            raise HTTPException(status_code=404, detail="Round not found.")
        return round_record.model_dump(mode="json")

    @app.post("/api/rounds")
    def create_round(request: StudioCreateRequest) -> dict:
        try:
            settings = load_settings(require_openai=True)
            round_record = create_review_round(settings, request)
        except ConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return round_record.model_dump(mode="json")

    @app.post("/api/rounds/{round_id}/next")
    def next_round(round_id: str) -> dict:
        try:
            settings = load_settings(require_openai=True)
            round_record = create_next_round(settings, round_id)
        except ConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return round_record.model_dump(mode="json")

    @app.post("/api/rounds/{round_id}/variants/{variant_id}/rating")
    def set_rating(round_id: str, variant_id: str, request: StudioRateRequest) -> dict:
        try:
            round_record = rate_variant(round_id, variant_id, request.rating, request.note)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return round_record.model_dump(mode="json")

    return app


app = create_app()
