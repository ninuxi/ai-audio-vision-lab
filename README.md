# 🎛️ AI Audio Vision Lab

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Issues](https://img.shields.io/github/issues/ninuxi/ai-audio-vision-lab)
![Last Commit](https://img.shields.io/github/last-commit/ninuxi/ai-audio-vision-lab)

Un bot Telegram che trasforma una fotografia in una composizione musicale originale, generata su misura per quella scena.

> 📜 Questo progetto ha avuto una versione precedente, basata su Raspberry Pi + PyTorch + Magenta: vedi [README_IT.md](README_IT.md) per l'architettura originale (con il render dell'hardware).

---

## 🇮🇹 Descrizione

Manda una foto al bot, ricevi un brano musicale scritto apposta per quell'immagine: non una colonna sonora generica pescata da una libreria, ma una composizione originale (melodia, armonia, basso, percussioni) che nasce da ciò che il bot vede nella foto.

Il sistema funziona in tre passaggi, ciascuno affidato a un modello Gemini in cloud:
1. **Visione**: la foto viene analizzata e tradotta in una descrizione strutturata della scena (soggetto, materiali, colori, epoca, condizione, atmosfera, texture)
2. **Composizione**: la descrizione della scena, insieme a una direzione emotiva scelta dall'utente (malinconico, energico, sospeso...), diventa un piano musicale (scala, tempo, forma, dinamica, timbrica)
3. **Sintesi**: il piano viene tradotto in parametri concreti e inviato via OSC a un motore **Pure Data** headless, che genera melodia, basso, percussioni e riverbero, con una forma articolata (es. A-B-A'-Coda) invece di un semplice drone statico

Il bot ha una voce e un carattere definiti, non risposte da assistente generico, e supporta italiano e inglese.

Il progetto gira come container Docker, pensato per il deploy su piattaforme cloud gratuite (Render).

## 🇬🇧 Description

Send a photo to the bot, get back a piece of music written specifically for that image: not a generic soundtrack pulled from a library, but an original composition (melody, harmony, bassline, percussion) born from what the bot sees in the picture.

The system works in three stages, each handled by a Gemini model in the cloud:
1. **Vision**: the photo is analyzed and translated into a structured scene description (subject, materials, colors, era, condition, atmosphere, texture)
2. **Composition**: the scene description, together with an emotional direction chosen by the user (melancholic, energetic, suspended...), becomes a musical plan (scale, tempo, form, dynamics, timbre)
3. **Synthesis**: the plan is translated into concrete parameters and sent via OSC to a headless **Pure Data** engine, which generates melody, bass, percussion, and reverb, with an articulated form (e.g. A-B-A'-Coda) instead of a static drone

The bot has a defined voice and personality, not generic assistant replies, and supports Italian and English.

The project runs as a Docker container, designed for deployment on free cloud platforms (Render).

---

## 🇮🇹 Architettura

```
Foto Telegram
   │
   ▼
[Python] Analisi scena (Gemini) ──▶ JSON descrittivo
   │
   ▼
[Python] Scelta umore utente + Piano compositivo (Gemini) ──▶ JSON musicale
   │
   ▼
[Python] Generatore di partitura (melodia, basso, ritmo, forma)
   │
   ▼ OSC
[Pure Data headless] Sintesi (oscillatori, percussioni da rumore, riverbero)
   │
   ▼
File audio ──▶ risposta su Telegram
```

**Python** è il "cervello": cattura, chiamate Gemini, validazione JSON, generazione della partitura (melodia, basso, pattern ritmici), invio OSC.
**Pure Data** è il motore di sintesi: riceve pattern già pronti e li esegue con il proprio clock interno, nessuna logica compositiva al suo interno.

## 🇬🇧 Architecture

```
Telegram photo
   │
   ▼
[Python] Scene analysis (Gemini) ──▶ descriptive JSON
   │
   ▼
[Python] User mood choice + Composition plan (Gemini) ──▶ musical JSON
   │
   ▼
[Python] Score generator (melody, bass, rhythm, form)
   │
   ▼ OSC
[Pure Data headless] Synthesis (oscillators, noise-based percussion, reverb)
   │
   ▼
Audio file ──▶ Telegram reply
```

**Python** is the "brain": capture, Gemini calls, JSON validation, score generation (melody, bass, rhythm patterns), OSC dispatch.
**Pure Data** is the synthesis engine: receives ready-made patterns and plays them on its own internal clock, with no compositional logic inside it.

---

## 🇮🇹 Tecnologie utilizzate

- **Python 3.11**
- **python-telegram-bot** (polling)
- **Google Gemini API** (`google-genai`) — visione, composizione, sintesi parametri
- **Pure Data** (headless, `pd -nogui`) — motore di sintesi
- **python-osc** — comunicazione Python ↔ Pd
- **Docker** — containerizzazione per il deploy

## 🇬🇧 Technologies used

- **Python 3.11**
- **python-telegram-bot** (polling)
- **Google Gemini API** (`google-genai`) — vision, composition, synth parameters
- **Pure Data** (headless, `pd -nogui`) — synthesis engine
- **python-osc** — Python ↔ Pd communication
- **Docker** — containerization for deployment

---

## 🇮🇹 Installazione & Uso

1. Clona il repository
```bash
   git clone https://github.com/ninuxi/ai-audio-vision-lab.git
   cd ai-audio-vision-lab
```
2. Imposta le variabili d'ambiente necessarie: `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`
3. Costruisci ed esegui con Docker
```bash
   docker build -t ai-audio-vision-lab .
   docker run -e TELEGRAM_BOT_TOKEN=xxx -e GEMINI_API_KEY=xxx ai-audio-vision-lab
```
4. Cerca il bot su Telegram, invia `/start`, scegli la lingua, manda una foto

## 🇬🇧 Installation & Usage

1. Clone the repository
```bash
   git clone https://github.com/ninuxi/ai-audio-vision-lab.git
   cd ai-audio-vision-lab
```
2. Set the required environment variables: `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`
3. Build and run with Docker
```bash
   docker build -t ai-audio-vision-lab .
   docker run -e TELEGRAM_BOT_TOKEN=xxx -e GEMINI_API_KEY=xxx ai-audio-vision-lab
```
4. Find the bot on Telegram, send `/start`, choose your language, send a photo

---

## 🇮🇹 Stato del progetto

Il progetto è in sviluppo attivo. Funzionante: pipeline completa foto → composizione → audio, con melodia, basso e percussioni sequenziati (non più un drone statico). In lavorazione: raffinamento della qualità melodica, sistema di limite giornaliero con sblocco tramite donazione.

## 🇬🇧 Project status

Actively in development. Working: complete photo → composition → audio pipeline, with sequenced melody, bass, and percussion (no longer a static drone). In progress: melodic quality refinement, daily usage limit system with donation-based unlock.

---

## 🤝 Contributing

Contributions are welcome! Fork, branch, commit, push, open a Pull Request.

## 📄 License

MIT License. See the LICENSE file for details.

## 📧 Contatti / Contacts

- Email: oggettosonoro@gmail.com
- GitHub: ninuxi
