from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.content.script_generator import generate_script
from app.content.video_processor import brand_video
from app.tiktok.oauth import build_authorize_url, exchange_code_for_token

app = FastAPI(title="Tik API")

_oauth_states: set[str] = set()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/oauth/start")
def oauth_start() -> dict[str, str]:
    state = secrets.token_urlsafe(16)
    _oauth_states.add(state)
    return {"authorize_url": build_authorize_url(state)}


@app.get("/oauth/callback")
async def oauth_callback(code: str, state: str) -> dict:
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="invalid state")
    _oauth_states.discard(state)
    token_data = await exchange_code_for_token(code)
    # TODO: persistir token_data (access_token, refresh_token, open_id) no banco
    return {"connected": True, "open_id": token_data.get("open_id")}


class ScriptRequest(BaseModel):
    niche: str


@app.post("/content/script")
def create_script(payload: ScriptRequest) -> dict:
    script = generate_script(payload.niche)
    return {
        "hook": script.hook,
        "body": script.body,
        "caption": script.caption,
        "hashtags": script.hashtags,
    }


class BrandVideoRequest(BaseModel):
    source_video_path: str
    logo_path: str = "app/storage/assets/logo.png"
    caption_text: str = ""
    start_seconds: float = 0.0
    duration_seconds: float | None = None


@app.post("/content/brand-video")
def brand_video_endpoint(payload: BrandVideoRequest) -> dict:
    source = Path(payload.source_video_path)
    if not source.exists():
        raise HTTPException(status_code=404, detail="source video not found")

    output = Path("storage/videos") / f"branded_{source.stem}.mp4"
    brand_video(
        source_path=source,
        logo_path=Path(payload.logo_path),
        output_path=output,
        caption_text=payload.caption_text,
        start_seconds=payload.start_seconds,
        duration_seconds=payload.duration_seconds,
    )
    return {"output_path": str(output)}
