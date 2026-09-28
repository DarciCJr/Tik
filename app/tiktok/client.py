"""Cliente para a Content Posting API oficial do TikTok.

Docs: https://developers.tiktok.com/doc/content-posting-api-get-started
Enquanto o app não estiver auditado pela TikTok, posts de vídeo criados
por esta API caem como rascunho privado no inbox do usuário dentro do
app do TikTok — ele precisa abrir o app e confirmar a publicação.
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings

TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"


class TikTokClient:
    def __init__(self, access_token: str):
        self._access_token = access_token
        self._settings = get_settings()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    async def init_video_upload(self, video_size_bytes: int, chunk_size: int) -> dict:
        """Inicia o upload de vídeo (post.publish/inbox/video/init/)."""
        async with httpx.AsyncClient(base_url=TIKTOK_API_BASE) as client:
            resp = await client.post(
                "/post/publish/inbox/video/init/",
                headers=self._headers(),
                json={
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_size": video_size_bytes,
                        "chunk_size": chunk_size,
                        "total_chunk_count": 1,
                    }
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def upload_video_chunk(self, upload_url: str, video_bytes: bytes) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                upload_url,
                headers={
                    "Content-Range": f"bytes 0-{len(video_bytes) - 1}/{len(video_bytes)}",
                    "Content-Type": "video/mp4",
                },
                content=video_bytes,
            )
            resp.raise_for_status()

    async def check_status(self, publish_id: str) -> dict:
        async with httpx.AsyncClient(base_url=TIKTOK_API_BASE) as client:
            resp = await client.post(
                "/post/publish/status/fetch/",
                headers=self._headers(),
                json={"publish_id": publish_id},
            )
            resp.raise_for_status()
            return resp.json()
