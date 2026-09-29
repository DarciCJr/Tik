from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.core.config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    open_id TEXT PRIMARY KEY,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    connected_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS content_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niche TEXT,
    caption TEXT,
    hashtags TEXT,
    video_path TEXT,
    status TEXT NOT NULL DEFAULT 'script_generated',
    publish_id TEXT,
    open_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _db_path() -> Path:
    settings = get_settings()
    url = settings.database_url
    path_str = url.removeprefix("sqlite:///")
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def get_connection():
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(_SCHEMA)


def save_account(open_id: str, access_token: str, refresh_token: str | None) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO accounts (open_id, access_token, refresh_token)
            VALUES (?, ?, ?)
            ON CONFLICT(open_id) DO UPDATE SET
                access_token = excluded.access_token,
                refresh_token = excluded.refresh_token
            """,
            (open_id, access_token, refresh_token),
        )


def list_accounts() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT open_id, connected_at FROM accounts ORDER BY connected_at DESC"
        ).fetchall()


def get_account_token(open_id: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT access_token FROM accounts WHERE open_id = ?", (open_id,)
        ).fetchone()
        return row["access_token"] if row else None


def create_content_item(niche: str, caption: str, hashtags: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO content_items (niche, caption, hashtags) VALUES (?, ?, ?)",
            (niche, caption, hashtags),
        )
        return cursor.lastrowid


def update_content_item(item_id: int, **fields: str) -> None:
    if not fields:
        return
    fields["updated_at"] = "CURRENT_TIMESTAMP_PLACEHOLDER"
    assignments = ", ".join(f"{key} = ?" for key in fields if key != "updated_at")
    assignments += ", updated_at = datetime('now')"
    values = [value for key, value in fields.items() if key != "updated_at"]
    with get_connection() as conn:
        conn.execute(
            f"UPDATE content_items SET {assignments} WHERE id = ?",
            (*values, item_id),
        )


def list_content_items(limit: int = 50) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM content_items ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
