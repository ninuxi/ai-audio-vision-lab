"""
AI Audio Vision Lab - persistenza per utente

Un file JSON unico, protetto da un lock asyncio per gli accessi concorrenti
tra utenti diversi. Nessun database.

LIMITE NOTO SU RENDER FREE TIER (verificato su render.com/docs/free,
luglio 2026): i servizi free hanno filesystem effimero. Qualunque scrittura
locale -- inclusa questa, in USER_DB_PATH -- viene persa a ogni redeploy,
restart, E ANCHE a ogni spin-down per inattività (non solo ai redeploy
manuali: succede di routine su un servizio free poco usato). I Persistent
Disk che risolverebbero il problema richiedono un piano a pagamento, che
questo progetto ha deciso di non usare.

Conseguenza pratica per il budget Gemini: il contatore _global_quota in
questo file è una stima PREVENTIVA, utile a non sprecare chiamate quando
sappiamo già di essere a quota, ma non è la protezione reale contro lo
sforamento -- dopo un cold start il contatore riparte da zero anche se la
quota reale presso Google è già parzialmente o del tutto consumata. La
vera rete di sicurezza è la risposta 429 di Gemini stessa: quando arriva,
mark_quota_blocked() blocca subito il resto della finestra odierna a
prescindere da cosa dice il contatore (vedi bot.py, call_gemini_tracked).
Non c'è rischio economico in questo scarto (tier gratuito, Gemini rifiuta
e basta, non addebita), solo un possibile peggioramento temporaneo della UX
subito dopo un riavvio del servizio.

Soluzione più robusta valutata e scartata per ora: un key-value store
esterno gratuito (es. Upstash Redis) sopravviverebbe ai riavvii, ma
introduce una nuova dipendenza esterna e una nuova credenziale da
gestire, con margini "gratuito" che nel tempo possono cambiare -- un
rischio che si è deciso di non correre finché il 429-come-verità basta a
restare al sicuro dal punto di vista economico.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

USER_DB_PATH = os.environ.get("USER_DB_PATH", "/tmp/aavl_users.json")

_lock = asyncio.Lock()

# Chiave riservata per il budget giornaliero globale, dentro lo stesso file
# (non collide con gli ID utente Telegram, che sono puramente numerici).
_GLOBAL_QUOTA_KEY = "_global_quota"

# Le quote giornaliere (RPD) di Gemini si resettano a mezzanotte Pacific
# Time, non UTC (confermato su ai.google.dev/gemini-api/docs/rate-limits:
# "Requests per day (RPD) quotas reset at midnight Pacific time"). ZoneInfo
# gestisce da sola il passaggio PST/PDT (ora legale), a differenza di un
# offset fisso.
_GEMINI_QUOTA_TZ = ZoneInfo("America/Los_Angeles")


def _today() -> str:
    return datetime.now(_GEMINI_QUOTA_TZ).strftime("%Y-%m-%d")


def _default_user() -> dict:
    return {
        "language": None,
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
    return user


def _get_global_quota_locked(data: dict) -> dict:
    quota = data.get(_GLOBAL_QUOTA_KEY)
    if quota is None:
        quota = {"date": _today(), "count": 0, "blocked": False}
        data[_GLOBAL_QUOTA_KEY] = quota
    if quota.get("date") != _today():
        quota["date"] = _today()
        quota["count"] = 0
        quota["blocked"] = False
    return quota


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


async def check_and_consume_global_quota(daily_budget: int) -> bool:
    """Budget condiviso da TUTTE le chiamate Gemini di TUTTI gli utenti
    (non un limite per singolo utente, non un conteggio per foto): ritorna
    True e consuma una delle daily_budget chiamate odierne se disponibile,
    altrimenti False senza consumare nulla. Si azzera a mezzanotte Pacific
    Time (vedi _GEMINI_QUOTA_TZ), come la quota reale di Gemini.

    Ritorna False anche se una chiamata Gemini ha già segnalato 429 in
    questa stessa finestra (vedi mark_quota_blocked): quel segnale vale
    più del conteggio locale."""
    async with _lock:
        data = _load_all()
        quota = _get_global_quota_locked(data)
        if quota.get("blocked") or quota["count"] >= daily_budget:
            return False
        quota["count"] += 1
        _save_all(data)
        return True


async def mark_quota_blocked() -> None:
    """Chiamare quando Gemini risponde 429 (quota reale esaurita): blocca
    ogni nuova chiamata per il resto della finestra odierna (Pacific
    Time), indipendentemente da cosa dice il contatore locale -- che è
    solo una stima preventiva, il 429 è la verità finale."""
    async with _lock:
        data = _load_all()
        quota = _get_global_quota_locked(data)
        quota["blocked"] = True
        _save_all(data)


async def get_global_quota_status(daily_budget: int) -> tuple[int, int]:
    """Ritorna (chiamate usate oggi, budget) senza consumare nulla."""
    async with _lock:
        data = _load_all()
        quota = _get_global_quota_locked(data)
        return quota["count"], daily_budget


async def add_favorite(user_id: int, entry: dict) -> None:
    async with _lock:
        data = _load_all()
        user = _get_user_locked(data, user_id)
        entry = dict(entry)
        entry["saved_at"] = datetime.now(timezone.utc).isoformat()
        user["favorites"].append(entry)
        _save_all(data)
