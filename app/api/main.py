from __future__ import annotations

import secrets

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.content.script_generator import generate_script
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
