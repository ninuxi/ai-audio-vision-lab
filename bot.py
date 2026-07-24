"""
AI Audio Vision Lab - bot Telegram

Riceve una foto, la descrive tramite Gemini (VLM) in JSON strutturato,
traduce la descrizione in un piano compositivo musicale (secondo passaggio
Gemini), poi in parametri numerici di sintesi (terzo passaggio Gemini),
li invia a Pd (main.pd) via OSC, attende il WAV generato e lo rimanda
all'utente su Telegram.
"""

import asyncio
import hashlib
import json
import logging
import os

from google import genai
from google.genai import types
from pythonosc.udp_client import SimpleUDPClient
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import i18n
import score_generator
import storage

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("ai_audio_vision_bot")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Variabile d'ambiente TELEGRAM_BOT_TOKEN mancante.")
if not GEMINI_API_KEY:
    raise RuntimeError("Variabile d'ambiente GEMINI_API_KEY mancante.")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Pd (main.pd) ascolta OSC su questa porta. WAV e flag di completamento
# usano nomi FISSI (non uno per render): main.pd li ha hardcoded agli stessi
# path, vanno cambiati in coppia. Un nome fisso invece che basato sul seed
# evita un problema empiricamente verificato in Pd vanilla (costruire un
# messaggio "open <path dinamico>" via $1/makefilename non è affidabile:
# un singolo atomo in arrivo da routeOSC viene sempre trattato come
# selettore, mai come argomento sostituibile). Il lock in handle_photo
# garantisce che non ci siano mai due render sovrapposti sullo stesso file.
PD_OSC_HOST = os.environ.get("PD_OSC_HOST", "127.0.0.1")
PD_OSC_PORT = int(os.environ.get("PD_OSC_PORT", "9000"))
PD_RENDER_DIR = os.environ.get("PD_RENDER_DIR", "/tmp/pd_render")
PD_RENDER_TIMEOUT_SECONDS = float(os.environ.get("PD_RENDER_TIMEOUT_SECONDS", "45"))
PD_WAV_PATH = os.path.join(PD_RENDER_DIR, "current.wav")
PD_DONE_PATH = os.path.join(PD_RENDER_DIR, "current.done")

os.makedirs(PD_RENDER_DIR, exist_ok=True)

pd_client = SimpleUDPClient(PD_OSC_HOST, PD_OSC_PORT)

# Pd è un singolo motore di sintesi: senza questo lock, due render richiesti
# quasi in contemporanea si sovrapporrebbero e corromperebbero l'output.
pd_render_lock = asyncio.Lock()

# Stesso prompt e stesso criterio di validazione usati in fase 0
# (scripts/fase0_test.sh), da ri-testare empiricamente contro Gemini.
VISION_PROMPT = (
    "Descrivi questa immagine in JSON con campi: soggetto, materiali, "
    "colori, epoca, condizione, atmosfera, postura, texture. Solo JSON. "
    "Ogni campo deve essere una stringa singola o una lista di stringhe, "
    'mai un oggetto annidato. Se un campo ha più valori (es. più texture '
    'diverse nella stessa immagine), usa una lista: ["ruvida", "umida"], '
    "non un dizionario."
)

VISION_REQUIRED_FIELDS = [
    "soggetto",
    "materiali",
    "colori",
    "epoca",
    "condizione",
    "atmosfera",
    "postura",
    "texture",
]

COMPOSITION_PROMPT_TEMPLATE = (
    "Sei un compositore. Data questa descrizione JSON di una scena, "
    "traducila in un piano compositivo musicale in JSON con campi: "
    "scala (modo/scala musicale), tempo (BPM, numero), forma (struttura "
    "del brano), densita (densità delle voci), timbrica (lista di timbri/"
    "strumenti), dinamica (andamento dinamico). Solo JSON. Ogni campo "
    "deve essere una stringa, un numero, o una lista di stringhe, mai un "
    "oggetto annidato.\n\n"
    "Direzione emotiva richiesta dalla persona: {mood_hint}.\n\n"
    "{variation_note}"
    "Descrizione scena:\n{scene_json}"
)

COMPOSITION_REQUIRED_FIELDS = [
    "scala",
    "tempo",
    "forma",
    "densita",
    "timbrica",
    "dinamica",
]

# Frasi iniettate nel prompt del piano compositivo in base al bottone scelto
# dall'utente (vedi i18n.MOOD_KEYS per le etichette mostrate nei bottoni).
MOOD_PROMPT_HINTS = {
    "malinconico": "malinconica, introspettiva, venata di nostalgia",
    "energico": "energica, mossa, ritmicamente vivace",
    "sospeso": "sospesa, immobile, come in attesa di qualcosa",
    "sorprendimi": (
        "libera: scegli tu la direzione emotiva più interessante e meno "
        "scontata per questa scena"
    ),
}


class GeminiJSONError(Exception):
    """Sollevata quando Gemini non restituisce JSON valido o conforme allo schema."""


def _strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _valore_valido(v) -> bool:
    if isinstance(v, str):
        return v.strip() != ""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return True
    if isinstance(v, list):
        return len(v) > 0 and all(
            isinstance(x, str) and x.strip() != "" for x in v
        )
    return False


def _valida_schema(obj, required_fields: list[str]) -> tuple[bool, str]:
    if not isinstance(obj, dict):
        return False, "la risposta non è un oggetto JSON di primo livello"
    mancanti = [k for k in required_fields if k not in obj]
    if mancanti:
        return False, f"campi mancanti: {', '.join(mancanti)}"
    non_validi = [k for k in required_fields if not _valore_valido(obj[k])]
    if non_validi:
        return False, (
            "campi con valore non valido (atteso stringa, numero o lista "
            f"di stringhe non vuote): {', '.join(non_validi)}"
        )
    return True, ""


def _parse_and_validate(text: str, validator) -> dict:
    """validator: callable(obj) -> (bool, messaggio_errore)."""
    stripped = _strip_markdown_fence(text)
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as e:
        raise GeminiJSONError(f"risposta non è JSON valido: {e}") from e

    ok, errore = validator(parsed)
    if not ok:
        raise GeminiJSONError(f"JSON valido ma schema non conforme ({errore})")

    return parsed


def describe_scene(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """Primo passaggio Gemini: foto -> JSON descrittivo della scena."""
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            VISION_PROMPT,
        ],
    )
    return _parse_and_validate(
        response.text, lambda obj: _valida_schema(obj, VISION_REQUIRED_FIELDS)
    )


def plan_composition(scene: dict, mood_key: str, previous_plan: dict | None = None) -> dict:
    """Secondo passaggio Gemini: JSON descrittivo -> JSON piano compositivo.

    previous_plan, se presente (caso "rigenera con variazione"), viene
    passato come piano da NON ripetere, per ottenere scelte musicali
    diverse a parità di scena e di direzione emotiva.
    """
    variation_note = ""
    if previous_plan is not None:
        variation_note = (
            "Genera una variazione DIVERSA dal piano precedente: stessa "
            "scena e stessa direzione emotiva, ma scelte musicali differenti "
            "(scala, forma, timbrica, dinamica). Piano precedente da NON "
            f"ripetere:\n{json.dumps(previous_plan, ensure_ascii=False)}\n\n"
        )
    prompt = COMPOSITION_PROMPT_TEMPLATE.format(
        scene_json=json.dumps(scene, ensure_ascii=False),
        mood_hint=MOOD_PROMPT_HINTS[mood_key],
        variation_note=variation_note,
    )
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return _parse_and_validate(
        response.text, lambda obj: _valida_schema(obj, COMPOSITION_REQUIRED_FIELDS)
    )


VOICE_OSC_TYPES = {"sine", "saw", "square", "fm"}

SYNTH_PROMPT_TEMPLATE = (
    "Traduci questo piano compositivo musicale in parametri numerici per un "
    "motore di sintesi Pure Data, in JSON con campi:\n"
    "- scale_root: nota MIDI della fondamentale (numero 0-127, es. 60 = Do "
    "centrale)\n"
    "- scale_intervals: lista di 2-12 numeri (semitoni dalla fondamentale, "
    "0-24) che definiscono la scala/modo\n"
    "- tempo_bpm: numero 20-300\n"
    "- voices: lista di 1-3 voci, ciascuna oggetto con i campi: osc_type "
    '(una stringa tra "sine", "saw", "square", "fm"), freq_offset (numero, '
    "semitoni di offset dalla fondamentale, può essere negativo o "
    "frazionario), amplitude (numero 0-1), inharmonicity (numero 0-1)\n"
    "- reverb_mix: numero 0-1 (quantità di riverbero)\n"
    "- duration_seconds: numero 5-120 (durata del brano; per una prima "
    "prova preferisci un valore tra 20 e 30)\n"
    "- rhythm_density: numero 0-1 (densità ritmica: 0 = rado e spoglio, "
    "1 = fitto e insistito; guida il generatore di pattern percussivi, "
    "non descrive il brano in astratto)\n\n"
    "Solo JSON, nessun testo fuori dal JSON, nessun campo in più oltre a "
    "quelli elencati.\n\n"
    "Piano compositivo:\n{plan_json}"
)


def _numero_in_range(v, lo, hi) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and lo <= v <= hi


def _valida_voce(v) -> tuple[bool, str]:
    if not isinstance(v, dict):
        return False, "la voce non è un oggetto JSON"
    if v.get("osc_type") not in VOICE_OSC_TYPES:
        return False, (
            "osc_type mancante o non valido (atteso uno tra "
            f"{sorted(VOICE_OSC_TYPES)})"
        )
    if not _numero_in_range(v.get("freq_offset"), -36, 48):
        return False, "freq_offset mancante o fuori range (-36..48)"
    if not _numero_in_range(v.get("amplitude"), 0, 1):
        return False, "amplitude mancante o fuori range (0..1)"
    if not _numero_in_range(v.get("inharmonicity"), 0, 1):
        return False, "inharmonicity mancante o fuori range (0..1)"
    return True, ""


def _valida_synth_params(obj) -> tuple[bool, str]:
    if not isinstance(obj, dict):
        return False, "la risposta non è un oggetto JSON di primo livello"

    richiesti = [
        "scale_root",
        "scale_intervals",
        "tempo_bpm",
        "voices",
        "reverb_mix",
        "duration_seconds",
        "rhythm_density",
    ]
    mancanti = [k for k in richiesti if k not in obj]
    if mancanti:
        return False, f"campi mancanti: {', '.join(mancanti)}"

    if not _numero_in_range(obj["scale_root"], 0, 127):
        return False, "scale_root fuori range (atteso 0-127)"

    intervals = obj["scale_intervals"]
    if not isinstance(intervals, list) or not (2 <= len(intervals) <= 12):
        return False, "scale_intervals deve essere una lista di 2-12 elementi"
    if not all(_numero_in_range(x, 0, 24) for x in intervals):
        return False, "scale_intervals deve contenere solo numeri 0-24"

    if not _numero_in_range(obj["tempo_bpm"], 20, 300):
        return False, "tempo_bpm fuori range (atteso 20-300)"

    voices = obj["voices"]
    if not isinstance(voices, list) or not (1 <= len(voices) <= 3):
        return False, "voices deve essere una lista di 1-3 voci"
    for i, v in enumerate(voices):
        ok, errore = _valida_voce(v)
        if not ok:
            return False, f"voices[{i}]: {errore}"

    if not _numero_in_range(obj["reverb_mix"], 0, 1):
        return False, "reverb_mix fuori range (atteso 0-1)"

    if not _numero_in_range(obj["duration_seconds"], 5, 120):
        return False, "duration_seconds fuori range (atteso 5-120)"

    if not _numero_in_range(obj["rhythm_density"], 0, 1):
        return False, "rhythm_density fuori range (atteso 0-1)"

    return True, ""


def plan_to_synth_params(plan: dict) -> dict:
    """Terzo passaggio Gemini: JSON piano compositivo -> parametri numerici per Pd."""
    prompt = SYNTH_PROMPT_TEMPLATE.format(
        plan_json=json.dumps(plan, ensure_ascii=False)
    )
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return _parse_and_validate(response.text, _valida_synth_params)


NARRATE_PROMPT_TEMPLATE = (
    "Sei la voce di un piccolo strumento che trasforma fotografie in musica. "
    "Scrivi un breve testo (80-130 parole) in prosa -- mai elenco, mai JSON, "
    "mai dati tecnici o numerici (niente BPM, note, percentuali) -- che "
    "racconti cosa hai visto nella scena e che musica ne è nata, per la "
    "persona che ha appena ricevuto il file audio.\n\n"
    "Registro: colto ma popolare, mai accademico o gergale -- pensa a come "
    "Pasolini scriveva per tutti restando rigoroso; ironia affettuosa mai "
    "cinica, la stessa arguzia umana di Eduardo De Filippo, Totò, Monicelli; "
    "dettaglio visivo preciso come in un reportage di moda, mai descrizione "
    "piatta da catalogo; frasi brevi, un ritmo che pensa alla musica stessa "
    "-- l'economia di parole di Miles Davis, la pulizia elettronica di "
    "Jean-Michel Jarre e dei Daft Punk. Evocativo, mai sdolcinato.\n\n"
    "Scrivi il testo in {language_name}.\n\n"
    "Direzione emotiva scelta dalla persona: {mood_hint}.\n\n"
    "Descrizione della scena (solo per te, non citarla come JSON):\n"
    "{scene_json}\n\n"
    "Piano musicale generato (solo per te, non citarlo come JSON):\n"
    "{plan_json}"
)


def narrate_result(scene: dict, plan: dict, mood_key: str, language: str) -> str:
    """Quarto passaggio Gemini: scena + piano -> prosa breve ed evocativa
    nella lingua dell'utente. Testo libero, non JSON: nessuna validazione
    di schema, solo uno strip difensivo."""
    prompt = NARRATE_PROMPT_TEMPLATE.format(
        language_name=i18n.LANGUAGE_NAME_FOR_PROMPT.get(language, "italiano"),
        mood_hint=MOOD_PROMPT_HINTS[mood_key],
        scene_json=json.dumps(scene, ensure_ascii=False),
        plan_json=json.dumps(plan, ensure_ascii=False),
    )
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    text = (response.text or "").strip()
    if not text:
        raise ValueError("narrazione vuota")
    return text


def compute_seed(scene: dict, plan: dict) -> str:
    """Hash di scena+piano, usato da Pd per il seed di riproducibilità.
    Include il piano (non solo la scena) apposta: una "rigenerazione" ha
    la stessa scena ma un piano diverso, e deve ottenere un seed diverso.
    """
    canonical = json.dumps(
        {"scene": scene, "plan": plan}, sort_keys=True, ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


DEFAULT_VOICE = {"osc_type": "sine", "freq_offset": 0, "amplitude": 0.0, "inharmonicity": 0.0}


def send_plan_to_pd(synth_params: dict, score: dict) -> None:
    """Invia i parametri di sintesi e la partitura (score_generator) a Pd
    via OSC. Indirizzi attesi da main.pd: /scale_root, /scale_intervals,
    /tempo_bpm, /voice/<1-3>/{type,amplitude,inharmonicity,freq_offset},
    /reverb_mix, /duration_seconds, /score/total_steps, /melody/*, /bass/*,
    /drums/kick/*, /drums/hat/*, /render/start (bang finale che avvia la
    registrazione, va mandato per ultimo: main.pd lo usa come segnale che
    tutti i pattern sono gia' stati scritti).

    Dentro ogni voce, "inharmonicity" va inviato PRIMA di "freq_offset":
    in main.pd, l'arrivo di freq_offset innesca subito il calcolo della
    frequenza (che usa anche inharmonicity per il detune), quindi
    inharmonicity deve essere già stato ricevuto.
    """
    pd_client.send_message("/scale_root", synth_params["scale_root"])
    pd_client.send_message("/scale_intervals", list(synth_params["scale_intervals"]))
    pd_client.send_message("/tempo_bpm", synth_params["tempo_bpm"])

    voices = synth_params["voices"]
    for i in range(1, 4):
        voice = voices[i - 1] if i <= len(voices) else DEFAULT_VOICE
        # Le tre voci vengono sempre riscritte, comprese quelle inutilizzate:
        # Pd è un processo persistente tra un render e l'altro, senza questo
        # reset una voce attiva in un render precedente resterebbe udibile
        # anche quando il piano corrente non la prevede.
        pd_client.send_message(f"/voice/{i}/type", voice["osc_type"])
        pd_client.send_message(f"/voice/{i}/amplitude", voice["amplitude"])
        pd_client.send_message(f"/voice/{i}/inharmonicity", voice["inharmonicity"])
        pd_client.send_message(f"/voice/{i}/freq_offset", voice["freq_offset"])

    pd_client.send_message("/reverb_mix", synth_params["reverb_mix"])
    pd_client.send_message("/duration_seconds", synth_params["duration_seconds"])

    send_score_to_pd(score)

    pd_client.send_message("/render/start", 1)


# Taglia dei blocchi per l'invio dei pattern via OSC. Verificato
# empiricamente: un singolo datagram UDP su questa macchina rifiuta oltre
# ~1839 float (limite del socket, non di Pd). 500 tiene ampio margine su
# qualunque piattaforma, incluso il container Linux di produzione, senza
# fare assunzioni sul suo limite specifico.
PATTERN_CHUNK_SIZE = 500


def _send_pattern_chunked(address_prefix: str, values: list[int]) -> None:
    """Scrive una sequenza in una table di Pd a blocchi, via
    "<prefix>/onset <indice>" seguito da "<prefix>/chunk <valori...>",
    ripetuto finche' la sequenza non e' interamente scritta. Verificato
    empiricamente byte-per-byte sui bordi tra un blocco e l'altro."""
    for start in range(0, len(values), PATTERN_CHUNK_SIZE):
        chunk = values[start : start + PATTERN_CHUNK_SIZE]
        pd_client.send_message(f"{address_prefix}/onset", start)
        pd_client.send_message(f"{address_prefix}/chunk", chunk)


def send_score_to_pd(score: dict) -> None:
    """Invia la partitura generata (vedi score_generator.generate_score) a
    Pd: numero di step totali e i quattro pattern piatti, ciascuno scritto
    nella sua table via onset+chunk. Va chiamato PRIMA di /render/start,
    che main.pd usa come segnale "i pattern sono pronti, si parte"."""
    pd_client.send_message("/score/total_steps", score["total_steps"])
    _send_pattern_chunked("/melody", score["melody"])
    _send_pattern_chunked("/bass", score["bass"])
    _send_pattern_chunked("/drums/kick", score["kick"])
    _send_pattern_chunked("/drums/hat", score["hat"])


async def wait_for_generated_audio() -> str:
    """Polling del flag di completamento scritto da Pd a fine sintesi.
    Ritorna il path del WAV, o solleva TimeoutError.
    """
    poll_interval = 0.5
    elapsed = 0.0
    while elapsed < PD_RENDER_TIMEOUT_SECONDS:
        if os.path.exists(PD_DONE_PATH):
            if not os.path.exists(PD_WAV_PATH):
                raise RuntimeError(
                    "Pd ha segnalato il completamento ma il file WAV atteso "
                    f"non esiste: {PD_WAV_PATH}"
                )
            return PD_WAV_PATH
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(
        f"Timeout ({PD_RENDER_TIMEOUT_SECONDS}s) in attesa dell'audio da Pd."
    )


def cleanup_render_files() -> None:
    """Rimuove WAV e flag di completamento dopo l'invio, per non riempire
    lo storage del container nel tempo."""
    for path in (PD_WAV_PATH, PD_DONE_PATH):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(i18n.t("it", "lang_button_it"), callback_data="lang:it"),
                InlineKeyboardButton(i18n.t("en", "lang_button_en"), callback_data="lang:en"),
            ]
        ]
    )


def mood_keyboard(language: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(i18n.mood_label(language, key), callback_data=f"mood:{key}")
        for key in i18n.MOOD_KEYS
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)


def result_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(i18n.t(language, "button_regenerate"), callback_data="regen"),
                InlineKeyboardButton(
                    i18n.t(language, "button_save_favorite"), callback_data="save_fav"
                ),
            ]
        ]
    )


async def run_composition_and_finish(
    status_message,
    scene: dict,
    mood_key: str,
    language: str,
    context: ContextTypes.DEFAULT_TYPE,
    previous_plan: dict | None = None,
) -> None:
    """Dal JSON scena (già ottenuto) fino all'invio dell'audio: piano
    compositivo, parametri di sintesi, render via Pd, narrazione poetica.
    Condivisa tra il flusso normale (dopo la scelta dell'umore) e la
    rigenerazione (stessa scena, piano nuovo).
    """
    try:
        plan = await asyncio.to_thread(plan_composition, scene, mood_key, previous_plan)
    except GeminiJSONError as e:
        logger.warning("Piano compositivo non valido: %s", e)
        await status_message.edit_text(i18n.t(language, "error_plan_invalid"))
        return
    except Exception:
        logger.exception("Errore chiamando Gemini per il piano compositivo")
        await status_message.edit_text(i18n.t(language, "error_plan_service"))
        return

    await status_message.edit_text(i18n.t(language, "synthesizing"))

    try:
        synth_params = await asyncio.to_thread(plan_to_synth_params, plan)
    except GeminiJSONError as e:
        logger.warning("Parametri di sintesi non validi: %s", e)
        await status_message.edit_text(i18n.t(language, "error_synth_invalid"))
        return
    except Exception:
        logger.exception("Errore chiamando Gemini per i parametri di sintesi")
        await status_message.edit_text(i18n.t(language, "error_synth_service"))
        return

    seed = compute_seed(scene, plan)
    score = score_generator.generate_score(synth_params, plan, seed)

    # L'intera sezione critica (invio OSC, attesa, lettura e invio del file,
    # cleanup) resta dentro il lock: Pd scrive sempre sullo stesso path
    # fisso, quindi un secondo render non può iniziare finché questo non ha
    # anche finito di leggere/inviare/ripulire il proprio file.
    try:
        async with pd_render_lock:
            send_plan_to_pd(synth_params, score)
            wav_path = await wait_for_generated_audio()
            try:
                try:
                    caption = await asyncio.to_thread(
                        narrate_result, scene, plan, mood_key, language
                    )
                except Exception:
                    logger.exception("Errore generando la narrazione poetica")
                    caption = i18n.t(language, "done_fallback_caption")
                caption = caption[:1000]  # limite didascalia Telegram: 1024

                context.user_data["pending_scene"] = scene
                context.user_data["pending_plan"] = plan
                context.user_data["mood"] = mood_key
                context.user_data["seed"] = seed

                with open(wav_path, "rb") as audio_file:
                    await status_message.reply_audio(
                        audio=audio_file,
                        filename=f"ai_audio_vision_{seed[:8]}.wav",
                        caption=caption,
                        reply_markup=result_keyboard(language),
                    )
                await status_message.delete()
            finally:
                cleanup_render_files()
    except TimeoutError as e:
        logger.warning("Timeout in attesa dell'audio da Pd: %s", e)
        await status_message.edit_text(i18n.t(language, "error_timeout"))
    except Exception:
        logger.exception("Errore durante la sintesi o l'invio dell'audio")
        await status_message.edit_text(i18n.t(language, "error_audio_generic"))


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None or not message.photo:
        return

    user = update.effective_user
    language = await storage.get_language(user.id)
    if language is None:
        await message.reply_text(
            i18n.t(None, "need_language_first"), reply_markup=language_keyboard()
        )
        return

    allowed = await storage.check_and_consume_quota(user.id)
    if not allowed:
        await message.reply_text(i18n.t(language, "rate_limit_exceeded"))
        return

    context.user_data["language"] = language

    status_message = await message.reply_text(i18n.t(language, "photo_received"))

    photo = message.photo[-1]
    telegram_file = await photo.get_file()
    image_bytes = bytes(await telegram_file.download_as_bytearray())

    await status_message.edit_text(i18n.t(language, "analyzing_scene"))

    try:
        scene = await asyncio.to_thread(describe_scene, image_bytes)
    except GeminiJSONError as e:
        logger.warning("Descrizione scena non valida: %s", e)
        await status_message.edit_text(i18n.t(language, "error_vision_invalid"))
        return
    except Exception:
        logger.exception("Errore chiamando Gemini per la descrizione della scena")
        await status_message.edit_text(i18n.t(language, "error_vision_service"))
        return

    context.user_data["pending_scene"] = scene
    context.user_data["pending_plan"] = None
    context.user_data["mood"] = None
    context.user_data["seed"] = None

    await status_message.edit_text(
        i18n.t(language, "choose_mood"), reply_markup=mood_keyboard(language)
    )


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        i18n.t(None, "choose_language"), reply_markup=language_keyboard()
    )


async def handle_language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()
    language = query.data.split(":", 1)[1]
    await storage.set_language(update.effective_user.id, language)
    context.user_data["language"] = language
    await query.edit_message_text(i18n.t(language, "welcome"))


async def handle_mood_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()
    mood_key = query.data.split(":", 1)[1]
    language = context.user_data.get("language") or i18n.DEFAULT_LANGUAGE
    scene = context.user_data.get("pending_scene")
    status_message = query.message

    if scene is None:
        await status_message.edit_text(i18n.t(language, "error_session_expired"))
        return

    context.user_data["mood"] = mood_key
    await status_message.edit_text(i18n.t(language, "composing"))
    await run_composition_and_finish(status_message, scene, mood_key, language, context)


async def handle_regenerate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    language = context.user_data.get("language") or i18n.DEFAULT_LANGUAGE
    scene = context.user_data.get("pending_scene")
    mood_key = context.user_data.get("mood")
    previous_plan = context.user_data.get("pending_plan")

    if scene is None or mood_key is None:
        await query.message.reply_text(i18n.t(language, "error_session_expired"))
        return

    allowed = await storage.check_and_consume_quota(update.effective_user.id)
    if not allowed:
        await query.message.reply_text(i18n.t(language, "rate_limit_exceeded"))
        return

    status_message = await query.message.reply_text(i18n.t(language, "regenerating"))
    await run_composition_and_finish(
        status_message, scene, mood_key, language, context, previous_plan=previous_plan
    )


async def handle_save_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    language = context.user_data.get("language") or i18n.DEFAULT_LANGUAGE
    scene = context.user_data.get("pending_scene")
    plan = context.user_data.get("pending_plan")
    seed = context.user_data.get("seed")

    if scene is None or plan is None or seed is None:
        await query.answer(i18n.t(language, "error_session_expired"), show_alert=True)
        return

    await storage.add_favorite(
        update.effective_user.id,
        {
            "seed": seed,
            "scene": scene,
            "plan": plan,
            "mood": context.user_data.get("mood"),
        },
    )
    await query.answer(i18n.t(language, "favorite_saved"), show_alert=False)


def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(handle_language_choice, pattern=r"^lang:"))
    application.add_handler(CallbackQueryHandler(handle_mood_choice, pattern=r"^mood:"))
    application.add_handler(CallbackQueryHandler(handle_regenerate, pattern=r"^regen$"))
    application.add_handler(CallbackQueryHandler(handle_save_favorite, pattern=r"^save_fav$"))

    logger.info("Bot avviato, in polling.")
    application.run_polling()


if __name__ == "__main__":
    main()
