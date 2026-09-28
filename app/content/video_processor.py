"""Edição de vídeo de produto via ffmpeg.

Pega um vídeo-fonte (de fornecedor liberado pra revenda), corta um trecho,
aplica overlay de logo + texto, e ajusta levemente velocidade/crop pra não
bater como duplicata exata no TikTok.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def brand_video(
    source_path: Path,
    logo_path: Path,
    output_path: Path,
    caption_text: str = "",
    start_seconds: float = 0.0,
    duration_seconds: float | None = None,
    speed_factor: float = 1.03,
) -> Path:
    """Corta, ajusta velocidade e aplica overlay de logo (+ texto opcional).

    speed_factor levemente > 1 já é suficiente pra alterar o hash percebido
    do vídeo sem ficar perceptível ao espectador.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    filters = [
        f"setpts=PTS/{speed_factor}",
        "scale=1080:1920:force_original_aspect_ratio=increase",
        "crop=1080:1920",
    ]

    overlay_filter = (
        "[1:v]scale=180:-1[logo];"
        "[0:v][logo]overlay=W-w-30:30"
    )

    cmd = ["ffmpeg", "-y", "-i", str(source_path), "-i", str(logo_path)]

    if start_seconds:
        cmd[1:1] = ["-ss", str(start_seconds)]
    if duration_seconds:
        cmd += ["-t", str(duration_seconds)]

    video_filter = f"{','.join(filters)}"
    full_filter = f"[0:v]{video_filter}[base];{overlay_filter.replace('[0:v]', '[base]')}"

    if caption_text:
        safe_text = caption_text.replace("'", r"\'").replace(":", r"\:")
        full_filter += (
            f",drawtext=text='{safe_text}':fontcolor=white:fontsize=48:"
            "borderw=3:bordercolor=black:x=(w-text_w)/2:y=h-th-120"
        )

    cmd += [
        "-filter_complex",
        full_filter,
        "-af",
        f"atempo={speed_factor}",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        str(output_path),
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_path
