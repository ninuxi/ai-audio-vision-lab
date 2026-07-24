"""
AI Audio Vision Lab - stringhe bot in IT/EN

Registro "di processo" (benvenuto, stati, errori): diretto, concreto, breve.
Il testo poetico del risultato finale NON vive qui: è generato da Gemini
per ogni richiesta (vedi narrate_result() in bot.py), non è un template.
"""

MOOD_KEYS = ["malinconico", "energico", "sospeso", "sorprendimi"]

STRINGS = {
    "it": {
        "choose_language": "Scegli la lingua / Choose your language:",
        "lang_button_it": "Italiano",
        "lang_button_en": "English",
        "welcome": (
            "Ciao. Mandami una foto e ti restituisco una composizione musicale "
            "originale, nata da quello che vede l'obiettivo — non una colonna "
            "sonora generica, qualcosa scritto apposta per quella scena.\n\n"
            "Come funziona: scatta o scegli una foto e mandamela qui in chat, "
            "come faresti con chiunque altro.\n\n"
            "Poi: guardo la scena, ti chiedo che aria darle, scrivo la musica, "
            "te la mando come file audio. Ci vuole circa un minuto.\n\n"
            "Hai 5 foto al giorno. Cominciamo?"
        ),
        "need_language_first": (
            "Prima scegli la lingua qui sotto, poi rimandami la foto. / "
            "Pick a language below first, then send me the photo again."
        ),
        "rate_limit_exceeded": "Hai già usato le tue 5 foto di oggi. Torna domani.",
        "photo_received": "Foto ricevuta. Le do un'occhiata.",
        "analyzing_scene": "Sto guardando la scena, un minuto.",
        "choose_mood": "Che aria vuoi dare a questa scena?",
        "mood_malinconico": "Malinconico",
        "mood_energico": "Energico",
        "mood_sospeso": "Sospeso",
        "mood_sorprendimi": "Sorprendimi tu",
        "composing": "Ora scrivo la musica.",
        "synthesizing": "Traduco tutto in suono, quasi fatto.",
        "regenerating": "Provo un'altra strada, un minuto.",
        "button_regenerate": "Rigenera con variazione",
        "button_save_favorite": "Salva nei preferiti",
        "favorite_saved": "Salvato nei preferiti.",
        "done_fallback_caption": "Ecco cosa ne è venuto fuori.",
        "error_vision_invalid": (
            "Non sono riuscito a interpretare la scena in modo strutturato. "
            "Riprova con un'altra foto."
        ),
        "error_vision_service": (
            "Errore nel contattare il servizio di visione. Riprova più tardi."
        ),
        "error_plan_invalid": (
            "Ho descritto la scena ma non sono riuscito a generare un piano "
            "musicale valido. Riprova con un'altra foto."
        ),
        "error_plan_service": "Errore nel generare il piano compositivo. Riprova più tardi.",
        "error_synth_invalid": (
            "Ho generato il piano musicale ma non sono riuscito a tradurlo in "
            "parametri di sintesi validi. Riprova con un'altra foto."
        ),
        "error_synth_service": "Errore nel generare i parametri di sintesi. Riprova più tardi.",
        "error_timeout": "La sintesi audio ha impiegato troppo tempo. Riprova più tardi.",
        "error_audio_generic": "Errore durante la generazione dell'audio. Riprova più tardi.",
        "error_session_expired": (
            "Non ritrovo più i dati di questa richiesta (troppo tempo passato "
            "o il bot è stato riavviato). Rimandami la foto."
        ),
    },
    "en": {
        "choose_language": "Scegli la lingua / Choose your language:",
        "lang_button_it": "Italiano",
        "lang_button_en": "English",
        "welcome": (
            "Hi. Send me a photo and I'll turn it into an original piece of "
            "music — not a generic soundtrack, something written for that "
            "exact scene.\n\n"
            "How it works: take or pick a photo and send it here in chat, "
            "same as you would with anyone else.\n\n"
            "Then: I look at the scene, ask what mood you want, write the "
            "music, send it back as an audio file. Takes about a minute.\n\n"
            "You get 5 photos a day. Ready?"
        ),
        "need_language_first": (
            "Prima scegli la lingua qui sotto, poi rimandami la foto. / "
            "Pick a language below first, then send me the photo again."
        ),
        "rate_limit_exceeded": "You've used your 5 photos for today. Come back tomorrow.",
        "photo_received": "Photo received. Let me take a look.",
        "analyzing_scene": "Looking at the scene, one moment.",
        "choose_mood": "What mood should this scene take?",
        "mood_malinconico": "Melancholic",
        "mood_energico": "Energetic",
        "mood_sospeso": "Suspended",
        "mood_sorprendimi": "Surprise me",
        "composing": "Now I write the music.",
        "synthesizing": "Turning it into sound, almost there.",
        "regenerating": "Trying another direction, one moment.",
        "button_regenerate": "Regenerate with a variation",
        "button_save_favorite": "Save to favorites",
        "favorite_saved": "Saved to favorites.",
        "done_fallback_caption": "Here's what came out of it.",
        "error_vision_invalid": (
            "I couldn't make sense of the scene in a structured way. Try "
            "another photo."
        ),
        "error_vision_service": (
            "Error reaching the vision service. Please try again later."
        ),
        "error_plan_invalid": (
            "I described the scene but couldn't generate a valid musical "
            "plan. Try another photo."
        ),
        "error_plan_service": "Error generating the composition plan. Please try again later.",
        "error_synth_invalid": (
            "I generated the musical plan but couldn't turn it into valid "
            "synthesis parameters. Try another photo."
        ),
        "error_synth_service": "Error generating synthesis parameters. Please try again later.",
        "error_timeout": "Audio synthesis took too long. Please try again later.",
        "error_audio_generic": "Error while generating the audio. Please try again later.",
        "error_session_expired": (
            "I can't find this request anymore (too much time passed, or "
            "the bot restarted). Send me the photo again."
        ),
    },
}

DEFAULT_LANGUAGE = "it"


def t(language: str | None, key: str, **kwargs) -> str:
    lang = language if language in STRINGS else DEFAULT_LANGUAGE
    text = STRINGS[lang].get(key, STRINGS[DEFAULT_LANGUAGE].get(key, key))
    return text.format(**kwargs) if kwargs else text


def mood_label(language: str | None, mood_key: str) -> str:
    return t(language, f"mood_{mood_key}")


LANGUAGE_NAME_FOR_PROMPT = {"it": "italiano", "en": "inglese"}
