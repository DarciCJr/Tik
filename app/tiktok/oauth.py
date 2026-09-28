"""Fluxo OAuth2 do Login Kit do TikTok.

Docs: https://developers.tiktok.com/doc/login-kit-web
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

SCOPES = ["user.info.basic", "video.publish", "video.upload"]


def build_authorize_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_key": settings.tiktok_client_key,
        "scope": ",".join(SCOPES),
        "response_type": "code",
        "redirect_uri": settings.tiktok_redirect_uri,
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{AUTH_URL}?{query}"


async def exchange_code_for_token(code: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_key": settings.tiktok_client_key,
                "client_secret": settings.tiktok_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.tiktok_redirect_uri,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_key": settings.tiktok_client_key,
                "client_secret": settings.tiktok_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
        resp.raise_for_status()
        return resp.json()
