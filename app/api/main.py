from __future__ import annotations

import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.content.script_generator import generate_script
from app.content.video_processor import brand_video
from app.core import db
from app.tiktok.client import TikTokClient
from app.tiktok.oauth import build_authorize_url, exchange_code_for_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Tik API", lifespan=lifespan)

_oauth_states: set[str] = set()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/legal/terms", response_class=HTMLResponse)
def terms_of_service() -> str:
    return (
        "<html><body>"
        "<h1>Termos de Uso — Necx Auto</h1>"
        "<p>Esta ferramenta é de uso interno da Necx para gerar e publicar "
        "vídeos de produtos na conta TikTok da Necx, com legendas geradas "
        "por IA. Não coletamos dados de terceiros nem oferecemos este "
        "serviço a outros usuários.</p>"
        "<p>Contato: necxvendas@gmail.com</p>"
        "</body></html>"
    )


@app.get("/legal/privacy", response_class=HTMLResponse)
def privacy_policy() -> str:
    return (
        "<html><body>"
        "<h1>Política de Privacidade — Necx Auto</h1>"
        "<p>Esta ferramenta armazena apenas os tokens de acesso da conta "
        "TikTok da Necx, necessários para publicar conteúdo em nome dessa "
        "conta. Nenhum dado de terceiros é coletado, compartilhado ou "
        "vendido.</p>"
        "<p>Contato: necxvendas@gmail.com</p>"
        "</body></html>"
    )


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
    open_id = token_data.get("open_id")
    if open_id:
        db.save_account(
            open_id=open_id,
            access_token=token_data.get("access_token", ""),
            refresh_token=token_data.get("refresh_token"),
        )
    return {"connected": True, "open_id": open_id}


class ScriptRequest(BaseModel):
    niche: str


@app.post("/content/script")
def create_script(payload: ScriptRequest) -> dict:
    script = generate_script(payload.niche)
    item_id = db.create_content_item(
        niche=payload.niche,
        caption=script.caption,
        hashtags=",".join(script.hashtags),
    )
    return {
        "id": item_id,
        "hook": script.hook,
        "body": script.body,
        "caption": script.caption,
        "hashtags": script.hashtags,
    }


class BrandVideoRequest(BaseModel):
    content_item_id: int
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
    db.update_content_item(
        payload.content_item_id,
        video_path=str(output),
        status="video_ready",
    )
    return {"output_path": str(output)}


class PublishRequest(BaseModel):
    content_item_id: int
    open_id: str


@app.post("/content/publish")
async def publish_content(payload: PublishRequest) -> dict:
    items = {item["id"]: item for item in db.list_content_items(limit=200)}
    item = items.get(payload.content_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="content item not found")
    if not item["video_path"]:
        raise HTTPException(status_code=400, detail="video not branded yet")

    access_token = db.get_account_token(payload.open_id)
    if not access_token:
        raise HTTPException(status_code=404, detail="account not connected")

    video_bytes = Path(item["video_path"]).read_bytes()
    client = TikTokClient(access_token=access_token)
    init_result = await client.init_video_upload(
        video_size_bytes=len(video_bytes), chunk_size=len(video_bytes)
    )
    upload_url = init_result.get("data", {}).get("upload_url")
    publish_id = init_result.get("data", {}).get("publish_id")
    if not upload_url:
        raise HTTPException(status_code=502, detail=f"TikTok init failed: {init_result}")

    await client.upload_video_chunk(upload_url, video_bytes)
    db.update_content_item(
        payload.content_item_id,
        status="posted",
        publish_id=publish_id or "",
        open_id=payload.open_id,
    )
    return {"publish_id": publish_id, "status": "uploaded_as_draft"}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    accounts = db.list_accounts()
    items = db.list_content_items()

    accounts_rows = "".join(
        f"<tr><td>{a['open_id']}</td><td>{a['connected_at']}</td></tr>"
        for a in accounts
    ) or "<tr><td colspan='2'>Nenhuma conta conectada</td></tr>"

    items_rows = "".join(
        f"<tr><td>{i['id']}</td><td>{i['niche'] or ''}</td>"
        f"<td>{(i['caption'] or '')[:60]}</td>"
        f"<td>{i['status']}</td><td>{i['created_at']}</td></tr>"
        for i in items
    ) or "<tr><td colspan='5'>Nenhum conteúdo gerado ainda</td></tr>"

    return f"""
    <html>
    <head>
        <title>Necx Auto — Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: system-ui, sans-serif; margin: 24px; background: #fafafa; }}
            h1 {{ font-size: 20px; }}
            h2 {{ font-size: 16px; margin-top: 32px; }}
            table {{ width: 100%; border-collapse: collapse; background: white; }}
            th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #eee; font-size: 14px; }}
            th {{ background: #f0f0f0; }}
        </style>
    </head>
    <body>
        <h1>Necx Auto — Painel</h1>

        <h2>Contas conectadas</h2>
        <table>
            <tr><th>open_id</th><th>Conectado em</th></tr>
            {accounts_rows}
        </table>

        <h2>Conteúdo (roteiros / vídeos / posts)</h2>
        <table>
            <tr><th>ID</th><th>Nicho</th><th>Legenda</th><th>Status</th><th>Criado em</th></tr>
            {items_rows}
        </table>
    </body>
    </html>
    """
