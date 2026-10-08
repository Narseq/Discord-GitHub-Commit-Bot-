"""Lokalna baza SQLite (repozytoria, ustawienia, historia) i drobne parsery."""

import re
import sqlite3

from .config import DB_PATH


db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row
db.executescript(
    """
    CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        repo TEXT NOT NULL,
        kind TEXT NOT NULL,
        title TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS repos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo TEXT NOT NULL UNIQUE,
        branch TEXT NOT NULL DEFAULT '',
        channel_id TEXT NOT NULL DEFAULT '',
        users TEXT NOT NULL DEFAULT '',
        roles TEXT NOT NULL DEFAULT '',
        watch_commits INTEGER NOT NULL DEFAULT 1,
        watch_releases INTEGER NOT NULL DEFAULT 1,
        enabled INTEGER NOT NULL DEFAULT 1,
        last_sha TEXT NOT NULL DEFAULT '',
        last_release TEXT NOT NULL DEFAULT '',
        etag_commits TEXT NOT NULL DEFAULT '',
        etag_releases TEXT NOT NULL DEFAULT '',
        last_check TEXT NOT NULL DEFAULT '',
        last_error TEXT NOT NULL DEFAULT ''
    );
    """
)
db.commit()

DEFAULT_SETTINGS = {"interval": "15", "channel_id": "", "users": "", "roles": "", "message_lang": "pl"}


def get_setting(key):
    row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else DEFAULT_SETTINGS[key]


def set_setting(key, value):
    db.execute(
        "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    db.commit()


def parse_ids(text):
    seen = []
    for found in re.findall(r"\d{15,20}", text or ""):
        if found not in seen:
            seen.append(found)
    return ",".join(seen)


def parse_repo(text):
    text = (text or "").strip()
    match = re.search(r"(?:github\.com[/:])?([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", text)
    if not match:
        return None
    return f"{match.group(1)}/{match.group(2)}"
