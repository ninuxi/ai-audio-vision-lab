# AI Audio Vision Lab, redesign: decisioni e stato

Data: 9 luglio 2026

## Obiettivo

Riprogettare il progetto fermo ad agosto 2025 (repo `ai-audio-vision-lab`). Un solo hardware deve: catturare un'immagine dalla camera, generare una descrizione ricca della scena, tradurla in una composizione musicale originale (melodia, armonia, percussioni) coerente con l'immagine.

Esempi del livello di dettaglio voluto:
- persona: corporatura, capelli, occhi, altezza, abbigliamento specifico
- oggetto: bicicletta anni '90, colore, tipo di copertoni, dettagli di allestimento

## Decisioni prese

### Hardware: un solo dispositivo, niente Jetson
- Jetson Orin Nano Super valutato e scartato: Antonio l'ha già venduto, lo trova ostico.
- Raspberry Pi 5 possibile ma al limite: niente uscita mini jack di serie (serve DAC USB o HAT audio), niente GPU/NPU utile per VLM, CPU-only lento (Qwen2.5-VL-7B: minuti per immagine; Moondream 2: 30-90s ma descrizioni più povere).
- Proposta alternativa preferita: mini PC x86 (tipo Ryzen 5800H/6900HX, 32GB RAM), stesso tipo di setup già usato per MOOD. Ubuntu standard, mini jack reale, Qwen2.5-VL-7B in 30-60s per immagine.
- Se si resta sul Pi 5: versione 16GB, Camera Module 3, DAC USB, modello Moondream 2, accettando descrizioni più asciutte.
- Decisione hardware finale rimandata alla fase di validazione (fase 0).

**Nota per il progetto attuale (bot Telegram + Gemini cloud):** questa sezione hardware è superata. Il progetto attuale non richiede hardware dedicato: gira come container Docker su Render.com, con VLM in cloud (Gemini) invece di Ollama locale. La sezione resta come riferimento storico delle decisioni.

### Motore audio: Pure Data, non SuperCollider
Cambio rispetto alla prima proposta (SuperCollider). Motivo: Antonio conosce già un po' Pd, non conosce SC. Divisione dei compiti:
- **Python**: cervello del sistema. Cattura frame, chiama il VLM, produce il JSON descrittivo, produce il JSON del piano compositivo (scala, tempo, forma, densità, timbri), traduce il piano in eventi OSC nel tempo.
- **Pure Data (headless, `pd -nogui`)**: solo voci/sintesi. Riceve OSC, sintetizza o suona campioni (possibilità di usare field recording propri come materia prima timbrica). Nessuna logica compositiva dentro Pd.

### Architettura a quattro blocchi
1. Cattura: frame singolo su trigger, non stream continuo (latenza fino a un minuto accettabile).
2. Visione: VLM via Ollama, prompt che impone output JSON strutturato (soggetto, materiali, colori, epoca, condizione, atmosfera, postura, texture).
3. Piano di composizione: secondo passaggio LLM, dal JSON descrittivo a JSON musicale (modo/scala, tempo, forma, densità, timbrica, dinamica). Qui vive il mapping d'autore (es. metallo ossidato = inarmonicità).
4. Motore Pd: Python invia il piano via OSC, Pd esegue con synth e campioni propri. Seed dall'hash della descrizione per riproducibilità e unicità.

Stessa struttura di MOOD (percezione, mapping, motore): il giorno che si vogliono fondere i due sistemi, la strada è già tracciata.

## Limiti da tenere presenti
- Attributi come "occhi azzurri" o "alto 1,80m" richiedono condizioni che una camera fissa spesso non garantisce (primo piano, riferimento metrico in scena): il VLM può confabulare valori plausibili ma non misurati. Da considerare nel design del mapping, non necessariamente un problema se accettato come interpretazione.
- Se l'installazione finirà in spazio pubblico con persone riprese: temi GDPR/AI Act da progettare fin dall'inizio (nessun salvataggio, tutto effimero in RAM).
- Generazione audio neurale on-device (MusicGen, Stable Audio Open) scartata: troppo pesante, suono generico, contrario dell'obiettivo di unicità compositiva.

## Fase 0, in corso: validazione gratuita sul laptop Ubuntu
Non richiede decisioni hardware, si fa subito.

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5vl:7b
ollama pull moondream
ollama run qwen2.5vl:7b "Descrivi questa immagine in JSON con campi: soggetto, materiali, colori, epoca, condizione, atmosfera. Solo JSON." --image /percorso/foto.jpg
```

Test da fare: stesse 10 foto personali su entrambi i modelli, con prompt JSON strutturato.

Criterio di verifica: le descrizioni sono abbastanza ricche da alimentare un mapping musicale (non solo "persona con maglia scura", ma dettagli utilizzabili come materiale, texture, epoca, condizione)?

## Prossimo passo
Antonio riporta 2-3 output JSON reali dei due modelli. Da lì:
- si costruisce il vocabolario di mapping tra descrizione e parametri musicali
- si decide definitivamente tra mini PC x86 e Raspberry Pi 5 in base alla qualità reale ottenuta (superato: vedi nota sopra, ora si va su Render/Docker)
- si prepara il primo prompt completo per Claude Code (script Python: cattura, doppio passaggio JSON, invio OSC) e la prima patch Pd minimale (2-3 synth)