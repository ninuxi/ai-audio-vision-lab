# AI Audio Vision Lab — Stato del progetto (bot Telegram)

Ultimo aggiornamento: 7 settembre 2026 (sostituisce la versione del 25 luglio 2026)
Repository: https://github.com/ninuxi/ai-audio-vision-lab
Percorso locale: `/Users/mainenti/ai-audio-vision-lab`
Servizio live: https://ai-audio-vision-lab.onrender.com (Render, Web Service Free, Docker)

Documento di riferimento per riprendere il lavoro in una nuova sessione
senza perdere contesto. Da leggere insieme a
`ai-audio-vision-lab_503-visione.md` (guasto e fix di settembre),
`ai-audio-vision-lab_decisioni.md`, `ai-audio-vision-lab_versione-browser.md`
e `ai-audio-vision-lab_fase0-log.md`.

---

## Cos'è il progetto, in breve

Un bot Telegram: l'utente manda una foto, il bot restituisce una
composizione musicale originale ispirata alla scena, non una colonna sonora
generica. Gira come container Docker su Render.com (piano gratuito). Niente
hardware dedicato, niente Ollama locale: visione e composizione passano da
Google Gemini in cloud, la sintesi audio da Pure Data headless dentro lo
stesso container.

## Architettura a blocchi

```
Foto Telegram
    │
    ▼
[Python] Analisi scena (Gemini) ──▶ JSON descrittivo
    │
    ▼
[Python] Scelta umore utente + Piano compositivo e parametri di sintesi
         (Gemini, UNA sola chiamata) ──▶ JSON musicale
    │
    ▼
[Python] Generatore di partitura (melodia, basso, ritmo, forma)
    │
    ▼  OSC (localhost, porta 9000)
[Pure Data headless] Sintesi (oscillatori, percussioni da rumore, riverbero)
    │
    ▼
File audio ──▶ risposta su Telegram + narrazione poetica (Gemini)
```

Principio guida invariato: **Python è il cervello** (logica compositiva,
chiamate Gemini, validazione, generazione partitura), **Pure Data è solo il
motore di sintesi**, nessuna logica compositiva dentro la patch.

---

## Stato attuale: cosa funziona

Pipeline completa verificata end-to-end il 7 settembre 2026: foto ricevuta,
scena descritta, umore scelto dall'utente, piano musicale generato, audio
sintetizzato da Pd, file audio e testo poetico consegnati su Telegram.

## Il guasto di settembre 2026 e come è stato risolto

Il bot rispondeva "Errore nel contattare il servizio di visione" perché
`gemini-3.5-flash-lite` tornava **503 UNAVAILABLE** ("This model is
currently experiencing high demand"), il 5 e di nuovo il 7 settembre.
Non era quota, non era la chiave, non era Render.

Fix (commit `b572d56`): **catena di modelli con ripiego**. Dettaglio
completo, log, tabella delle quote reali e limiti della verifica in
`ai-audio-vision-lab_503-visione.md`. In sintesi:

- catena di default
  `gemini-3.5-flash-lite:500,gemini-3.1-flash-lite:500,gemini-3.8-flash:20`;
- 5xx → retry breve, poi modello successivo; 429 → modello escluso per la
  giornata e si passa alla riserva; JSON non conforme → come il 5xx;
- budget giornaliero contato per modello, non più globale;
- messaggio utente distinto per sovraccarico (passa in minuti) e quota
  esaurita (si ricarica domani).

## Storia delle decisioni principali

### Hosting: da Oracle Cloud a Render.com

Prima ipotesi: VM Oracle Cloud Always Free (ARM Ampere A1.Flex), abbandonata
dopo ripetuti "out of capacity" sulla shape ARM. Decisione finale:
container Docker su Render.com, piano gratuito. L'istanza Oracle creata per
errore è stata smantellata (istanza + VCN).

### Polling → webhook (25 luglio 2026)

Un Web Service Free va in sleep dopo inattività e si risveglia **solo**
ricevendo una richiesta HTTP in ingresso. In polling il bot chiamava
Telegram solo in uscita (`getUpdates`), quindi una volta addormentato
restava morto per sempre. Convertito a `Application.run_webhook()`: ora il
POST di Telegram è l'evento che risveglia l'istanza (lag fino a ~50s sul
primo messaggio dopo inattività, accettato). Variabili `WEBHOOK_PATH` e
`WEBHOOK_SECRET` su Render, `RENDER_EXTERNAL_URL` hardcodata in `bot.py`
(da aggiornare a mano se il servizio cambia nome).

### Motore audio: Pure Data headless

Pd gira con `pd -nogui -noaudio` nello stesso container del bot,
comunicazione via OSC su localhost porta 9000, un solo verso Python → Pd.

### VLM/LLM: Ollama locale → Gemini cloud

Cambio esplicito rispetto ai documenti originali (che prevedevano Ollama
locale con Qwen2.5-VL/Moondream): niente hardware dedicato. Il prompt JSON
strutturato e il criterio di validazione della Fase 0 (8 campi: soggetto,
materiali, colori, epoca, condizione, atmosfera, postura, texture; ogni
valore stringa o lista di stringhe, mai oggetti annidati) sono stati
riusati per Gemini con successo.

### Scelta del modello Gemini: la lezione imparata

Cronologia sintetica: `gemini-2.5-flash` (404, non più disponibile ai nuovi
utenti) → `gemini-flash-latest` (alias instabile, puntava a un modello con
RPD 20) → `gemini-3.5-flash` (GA ma RPD 20, inutilizzabile per un bot
condiviso) → `gemini-3.5-flash-lite` (RPD 500) → **catena di modelli**
(settembre 2026), perché anche un modello con quota generosa può essere
sovraccarico.

**Regola consolidata: mai fidarsi del nome o dei numeri di un modello a
memoria. Verificare sempre sulla dashboard reale (pagina Rate Limit di
Google AI Studio) e sulla documentazione, incrociando due fonti.**

### Pipeline sonora: da drone statico a sequencing reale

Il primo risultato end-to-end produceva solo un drone statico. Risolto con
un lungo debug su Pd vanilla. Risultato attuale: melodia, basso,
percussioni, articolazione in sezioni (forma A-B-A'-Coda).

Architettura del sequencing: approccio **pattern-based**, non event-based
in tempo reale. Python genera l'intera partitura come pattern flat (un
valore per ogni sedicesimo), Pd la esegue con il proprio clock interno
(`metro` + contatore di step), perché il clock di Pd è campione-accurato in
rendering headless mentre il timing via OSC in tempo reale può derivare.

Encoding delle note: tre valori per step (melodia/basso): grado di scala
(0..N-1), `-1` = pausa, `-2` = tieni la nota precedente. Percussioni
(kick/hat): 0/1 per step.

Inviluppi: ADSR completo con sustain per melodia/basso (senza sustain il
sentinel `-2` non ha effetto udibile), AD semplice per kick/hat.

Mapping delle 3 voci definite da Gemini: voice 1 = melodia, voice 2 = basso
(o raddoppio -8va se assente), voice 3 = raddoppio melodico con timbro
proprio.

### Bug di Pure Data vanilla trovati e risolti (riferimento tecnico)

- `>~` non esiste in Pd vanilla: onda quadra con `expr~ ($v1 > 0.5) * 2 - 1`.
- `-noaudio` è **indispensabile** per `pd -nogui` headless: senza device
  audio reale il clock DSP non avanza, `writesf~` scrive 0 frame. Deve
  stare in `entrypoint.sh`.
- Un atomo singolo da `routeOSC` è sempre trattato come selettore: serve un
  `[symbol]` come convertitore prima di `[select]`.
- `[value]`: un float sull'inlet lo imposta senza emettere nulla, solo un
  bang lo fa uscire. Il payload di `/render/start` rischia di sovrascrivere
  silenziosamente `duration_seconds` e `tempo_bpm` se non gestito.
- `[f]` non capisce un messaggio "set": ha solo il secondo inlet freddo.
- Pattern lunghi: `[table NOME N]` + `[array set NOME]` + `[tabread NOME]`,
  non `list store`/routeOSC.
- Limite di trasporto OSC: un array oltre ~1839 elementi supera il limite
  del socket UDP di **sistema** (non di Pd). Invio a blocchi con
  `array set <nome>` + onset.
- Virgole nei messaggi `vline~` scritte nel `.pd` grezzo spezzano il box:
  due messaggi distinti allo stesso trigger.
- Pacchetti Debian necessari: `pd-osc`, `pd-mrpeach-net`, `pd-freeverb`.
  Il pacchetto `puredata` di Debian è vanilla puro, non include nulla per
  OSC/rete.

### Protocollo OSC e concorrenza

Nessun OSC di ritorno Pd → Python: il segnale di fine rendering è un
**file-flag** (`/tmp/pd_render/current.wav` + `current.done`).
`wait_for_generated_audio()` fa polling di `.done` ogni ~0,5s, timeout 45s.
Un `asyncio.Lock()` serializza `send_plan_to_pd()` +
`wait_for_generated_audio()`: Pd è un motore singolo e non gestisce render
concorrenti.

---

## Personalità e UX del bot (decisione di design fissata da Antonio)

**Voce del bot**, riferimenti espliciti:
- **Pasolini**: intellettuale ma popolare, mai gergo accademico.
- **Eduardo De Filippo / Totò / Monicelli**: ironia affettuosa, mai cinica.
- **Fotografi di reportage moda**: dettaglio visivo preciso, mai piatto.
- **Miles Davis / Jean-Michel Jarre / Daft Punk**: economia di parole,
  ritmo, frasi brevi.

**Questo riferimento è stato fissato esplicitamente da Antonio e non va
modificato o "smussato" di iniziativa propria da chi lavora al codice,
nemmeno se sembra troppo caratterizzato.**

**Due registri distinti**:
1. Messaggi di stato: concreti, diretti, brevi, senza ermetismo poetico.
   ("Foto ricevuta. Le do un'occhiata." / "Sto guardando la scena, un
   minuto." / "Ora scrivo la musica.")
2. Messaggio del risultato finale: registro poetico, traduzione narrativa,
   mai JSON grezzo mostrato all'utente.

**Funzionalità implementate**: scelta lingua IT/EN all'avvio; scelta
umore con bottoni inline (Malinconico / Energico / Sospeso / Sorprendimi
tu) che condiziona il prompt del piano compositivo; bottoni "Rigenera con
variazione" e "Salva nei preferiti" dopo il risultato; comando `/dona`
(`/donate`) con link statico PayPal.me.

**Deciso esplicitamente di NON includere** un bottone per mostrare il JSON
tecnico grezzo agli utenti finali.

---

## Limite di utilizzo e monetizzazione

Il limite per-utente originale (5 foto al giorno) è stato sostituito da un
**budget giornaliero condiviso**, contato in chiamate Gemini reali e non in
foto, con margine di sicurezza all'80% della RPD. Da settembre 2026 il
budget è contato **per modello** della catena.

La logica "donazione PayPal sblocca di più" resta un'idea valida ma non
implementata: oggi `/dona` è solo un link, nessun collegamento automatico
fra donazione e budget.

---

## Sicurezza

Token Telegram e chiave API Gemini erano finiti in chiaro in una
conversazione a luglio 2026 ed erano considerati compromessi. Entrambi
rigenerati (token via @BotFather, chiave ricreata su Google AI Studio,
progetto "fotosuoni", account oggettosonoro@gmail.com) e inseriti come
variabili d'ambiente su Render, mai in un file del repository.

**Regola per il futuro**: non scrivere mai credenziali in chiaro in log di
debug o in messaggi di chat. Se succede di nuovo, considerarle compromesse
e ripetere la procedura.

---

## File del repository

- `bot.py` — logica del bot: Telegram in webhook, catena di modelli Gemini
  (visione, piano compositivo + parametri di sintesi in una chiamata,
  narrazione poetica), invio OSC, attesa audio, lingua/umore/bottoni
  inline, lock di concorrenza.
- `storage.py` — persistenza per utente su file JSON, budget Gemini per
  modello. Filesystem effimero su Render free (vedi note sotto).
- `i18n.py` — stringhe IT/EN dei messaggi di processo ed errore.
- `score_generator.py` — generatore di partitura, tutta la logica del
  sequencing. Esiste una versione locale più avanzata (lavoro musicale di
  Antonio) non ancora committata, con chiavi aggiuntive
  (`effective_duration_seconds`, array `*_timing`/`*_velocity`) che
  `bot.py` già gestisce con fallback.
- `main.pd` — patch Pure Data headless.
- `Dockerfile`, `entrypoint.sh` — containerizzazione, porta letta da `PORT`.
- `requirements.txt` — include `python-telegram-bot[webhooks]` (l'extra
  serve per `tornado`, richiesto da `run_webhook()`).

## Variabili d'ambiente su Render

`TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, `WEBHOOK_PATH`, `WEBHOOK_SECRET`,
`PAYPAL_ME_URL`. Opzionali con default nel codice: `GEMINI_MODEL_CHAIN`,
`GEMINI_MODEL`, `GEMINI_MODEL_RPD`, `QUOTA_SAFETY_MARGIN`,
`GEMINI_REQUEST_TIMEOUT_SECONDS`, `GEMINI_ATTEMPTS_PER_MODEL`,
`GEMINI_RETRY_BACKOFF_SECONDS`, `USER_DB_PATH`.

## Note operative

- **Auto-deploy attivo e verificato dal 7 settembre 2026**: l'impostazione
  era già su "On Commit", ma il servizio era collegato come "Public Git
  Repository", cioè un semplice URL, quindi Render non riceveva nessun
  evento di push e non deployava mai da solo (il repo non aveva nessun
  webhook e la GitHub App di Render non era installata). Risolto
  collegando il provider Git: Settings → Source → Edit → GitHub, con
  autorizzazione della GitHub App di Render sul repository. Verificato sul
  campo: il commit 1509d88 ha prodotto un deploy con trigger "Auto-Deploy"
  riuscito in 32,9s.
- Filesystem effimero su Render free: la scelta della lingua e il contatore
  di budget si perdono a ogni risveglio dell'istanza, non solo ai redeploy.
  Il 429 di Gemini resta la vera rete di sicurezza sulla quota.

## Prossimi passi, in ordine

1. Verificare al prossimo 503 reale che la catena di ripiego funzioni in
   produzione (nei test simulati funziona, sul campo non è ancora stata
   esercitata).
2. Valutare un secondo fornitore fuori da Google (Groq, OpenRouter) come
   garanzia contro il sovraccarico simultaneo di tutti i modelli Gemini.
3. Test empirico di qualità descrittiva fra i modelli della catena, stesso
   criterio della Fase 0 (dettagli concreti: materiale, texture, epoca,
   condizione, non genericità).
4. Risolvere la perdita della lingua a ogni risveglio (oggi è la prima cosa
   che nota un utente nuovo).
5. Committare il lavoro musicale locale su `score_generator.py` quando
   pronto.
6. Ripensare la logica donazione/sblocco in funzione del budget condiviso.
7. Affinamento della qualità melodica.
