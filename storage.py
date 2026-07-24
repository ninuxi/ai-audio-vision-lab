"""
AI Audio Vision Lab - persistenza per utente

Un file JSON unico, protetto da un lock asyncio per gli accessi concorrenti
tra utenti diversi. Nessun database: coerente con l'ephemeral storage già
usato per l'audio (vedi bot.py, PD_RENDER_DIR). Su Render, senza un disco
persistente montato su USER_DB_PATH, questi dati si azzerano a ogni
redeploy/restart del container.
"""

import asyncio
import json
import os
from datetime import datetime, timezone

USER_DB_PATH = os.environ.get("USER_DB_PATH", "/tmp/aavl_users.json")
DAILY_PHOTO_LIMIT = int(os.environ.get("DAILY_PHOTO_LIMIT", "5"))

_lock = asyncio.Lock()


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _default_user() -> dict:
    return {
        "language": None,
        "daily_date": _today(),
        "daily_count": 0,
        "favorites": [],
    }


def _load_all() -> dict:
    if not os.path.exists(USER_DB_PATH):
        return {}
    try:
        with open(USER_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_all(data: dict) -> None:
    tmp_path = USER_DB_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, USER_DB_PATH)


def _get_user_locked(data: dict, user_id: int) -> dict:
    key = str(user_id)
    user = data.get(key)
    if user is None:
        user = _default_user()
        data[key] = user
    if user.get("daily_date") != _today():
        user["daily_date"] = _today()
        user["daily_count"] = 0
    return user


async def get_language(user_id: int) -> str | None:
    async with _lock:
        data = _load_all()
        user = _get_user_locked(data, user_id)
        return user["language"]


async def set_language(user_id: int, language: str) -> None:
    async with _lock:
        data = _load_all()
        user = _get_user_locked(data, user_id)
        user["language"] = language
        _save_all(data)


async def check_and_consume_quota(user_id: int) -> bool:
    """Ritorna True e consuma una delle DAILY_PHOTO_LIMIT richieste odierne
    se disponibile, altrimenti False senza consumare nulla."""
    async with _lock:
        data = _load_all()
        user = _get_user_locked(data, user_id)
        if user["daily_count"] >= DAILY_PHOTO_LIMIT:
            return False
        user["daily_count"] += 1
        _save_all(data)
        return True


async def add_favorite(user_id: int, entry: dict) -> None:
    async with _lock:
        data = _load_all()
        user = _get_user_locked(data, user_id)
        entry = dict(entry)
        entry["saved_at"] = datetime.now(timezone.utc).isoformat()
        user["favorites"].append(entry)
        _save_all(data)
