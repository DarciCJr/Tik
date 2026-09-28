"""Geração de roteiro/legenda de vídeo usando a API da Anthropic."""

from __future__ import annotations

from dataclasses import dataclass

from anthropic import Anthropic

from app.core.config import get_settings


@dataclass
class VideoScript:
    hook: str
    body: str
    caption: str
    hashtags: list[str]


PROMPT_TEMPLATE = """Você é um roteirista de vídeos curtos para TikTok no nicho: {niche}.

Gere um roteiro para um vídeo de 30-45 segundos, com:
1. Um "hook" (primeiros 3 segundos, precisa prender atenção imediata)
2. Corpo do roteiro (narração completa)
3. Legenda para postar (curta, com call-to-action)
4. 5 a 8 hashtags relevantes (sem o #, uma por linha)

Responda em formato:
HOOK: ...
BODY: ...
CAPTION: ...
HASHTAGS:
tag1
tag2
"""


def _parse(text: str) -> VideoScript:
    sections: dict[str, str] = {}
    current_key = None
    hashtags: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("HOOK:"):
            current_key = "hook"
            sections[current_key] = stripped[len("HOOK:"):].strip()
        elif stripped.startswith("BODY:"):
            current_key = "body"
            sections[current_key] = stripped[len("BODY:"):].strip()
        elif stripped.startswith("CAPTION:"):
            current_key = "caption"
            sections[current_key] = stripped[len("CAPTION:"):].strip()
        elif stripped.startswith("HASHTAGS:"):
            current_key = "hashtags"
        elif current_key == "hashtags" and stripped:
            hashtags.append(stripped.lstrip("#"))
        elif current_key in ("hook", "body", "caption") and stripped:
            sections[current_key] = f"{sections.get(current_key, '')} {stripped}".strip()

    return VideoScript(
        hook=sections.get("hook", ""),
        body=sections.get("body", ""),
        caption=sections.get("caption", ""),
        hashtags=hashtags,
    )


def generate_script(niche: str, model: str = "claude-sonnet-5") -> VideoScript:
    settings = get_settings()
    client = Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(niche=niche)}],
    )
    text = "".join(block.text for block in message.content if block.type == "text")
    return _parse(text)
