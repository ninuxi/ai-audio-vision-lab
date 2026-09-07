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


def _get_model_quota_locked(data: dict, model: str) -> dict:
    """Contatore giornaliero PER MODELLO, non piu' uno globale: ogni modello
    della catena (vedi GEMINI_MODEL_CHAIN in bot.py) ha una sua RPD, quindi
    un contatore unico non saprebbe dire quale modello e' ancora usabile.
    Formato: {"date": "AAAA-MM-GG", "models": {"nome-modello": {"count": N,
    "blocked": bool}}}. Il vecchio formato a contatore unico, se trovato in
    un file scritto da una versione precedente, viene semplicemente
    ricreato: e' una stima preventiva, perderla non ha conseguenze.
    """
    quota = data.get(_GLOBAL_QUOTA_KEY)
    if quota is None or "models" not in quota:
        quota = {"date": _today(), "models": {}}
        data[_GLOBAL_QUOTA_KEY] = quota
    if quota.get("date") != _today():
        quota["date"] = _today()
        quota["models"] = {}
    per_modello = quota["models"].get(model)
    if per_modello is None:
        per_modello = {"count": 0, "blocked": False}
        quota["models"][model] = per_modello
    return per_modello


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


async def check_and_consume_model_quota(model: str, daily_budget: int) -> bool:
    """Budget giornaliero del singolo MODELLO, condiviso da tutti gli utenti
    (non un limite per utente, non un conteggio per foto): ritorna True e
    consuma una delle daily_budget chiamate odierne di quel modello se
    disponibile, altrimenti False senza consumare nulla. Si azzera a
    mezzanotte Pacific Time (vedi _GEMINI_QUOTA_TZ), come la quota reale.

    Ritorna False anche se quel modello ha gia' risposto 429 in questa
    finestra (vedi mark_model_quota_blocked): quel segnale vale piu' del
    conteggio locale. Un modello bloccato non blocca gli altri della
    catena: e' esattamente il punto di avere una catena."""
    async with _lock:
        data = _load_all()
        quota = _get_model_quota_locked(data, model)
        if quota.get("blocked") or quota["count"] >= daily_budget:
            return False
        quota["count"] += 1
        _save_all(data)
        return True


async def mark_model_quota_blocked(model: str) -> None:
    """Chiamare quando Gemini risponde 429 per QUESTO modello (quota reale
    esaurita): blocca ogni nuova chiamata a questo modello per il resto
    della finestra odierna (Pacific Time), lasciando liberi gli altri
    modelli della catena."""
    async with _lock:
        data = _load_all()
        quota = _get_model_quota_locked(data, model)
        quota["blocked"] = True
        _save_all(data)


async def get_model_quota_status(model: str, daily_budget: int) -> tuple[int, int]:
    """Ritorna (chiamate usate oggi da questo modello, budget) senza
    consumare nulla."""
    async with _lock:
        data = _load_all()
        quota = _get_model_quota_locked(data, model)
        return quota["count"], daily_budget


async def add_favorite(user_id: int, entry: dict) -> None:
    async with _lock:
        data = _load_all()
        user = _get_user_locked(data, user_id)
        entry = dict(entry)
        entry["saved_at"] = datetime.now(timezone.utc).isoformat()
        user["favorites"].append(entry)
        _save_all(data)
