# Guasto 503 sulla visione — diagnosi e fix (7 settembre 2026, RISOLTO)

## Sintomo

Su Telegram, dopo aver mandato una foto: "Errore nel contattare il servizio
di visione. Riprova più tardi." Nessun audio, nessuna descrizione.

## Causa accertata (dai log di produzione Render, non ipotesi)

`gemini-3.5-flash-lite` rispondeva **503 UNAVAILABLE** alla chiamata di
visione:

```
google.genai.errors.ServerError: 503 UNAVAILABLE.
{'error': {'code': 503, 'message': 'This model is currently experiencing
high demand. Spikes in demand are usually temporary. Please try again
later.', 'status': 'UNAVAILABLE'}}
```

Occorrenze verificate: 5 settembre alle 14:01 e 7 settembre alle 07:09 (ora
di Roma), quindi non un picco isolato ma una condizione che si ripresenta a
giorni di distanza. Nel test del 7 settembre il retry interno del SDK
(tenacity, dentro `google/genai/_api_client.py`) ha insistito **24 secondi**
prima di arrendersi: non era un blip di un secondo.

Il messaggio che vedeva l'utente arrivava dal ramo generico
`except Exception` attorno a `describe_scene` in `bot.py`.

### Cosa è stato escluso, e perché

- **Non era la quota**: il 429 ha un ramo di gestione dedicato
  (`QuotaExhaustedError`) e un messaggio diverso ("Per oggi ho già scritto
  tutta la musica che potevo").
- **Non era JSON malformato**: anche quello ha il suo ramo e il suo
  messaggio (`error_vision_invalid`).
- **Non era la chiave API né il progetto Google**: una chiave revocata o un
  progetto disabilitato danno 400 o 403, non 503. Il 503 arriva dal
  servizio del modello.
- **Non era Render**: il container si svegliava dallo spin-down, riceveva
  il webhook Telegram, scaricava la foto (1,19s, 82868 byte) e rispondeva.
- **Non era il modello dismesso**: `gemini-3.5-flash` e
  `gemini-3.5-flash-lite` risultavano entrambi "Stable" nella
  documentazione Google a settembre 2026, nessuna dismissione annunciata
  per agosto/settembre.

## Vincolo che ha determinato la soluzione: quote reali del livello gratuito

Lette sulla pagina Rate Limit di Google AI Studio il 7 settembre 2026, non
a memoria (la regola di questo progetto: mai fidarsi del nome o dei numeri
di un modello ricordati a mente):

| Modello | RPM | TPM | RPD |
|---|---|---|---|
| Gemini 3.5 Flash Lite | 15 | 250K | **500** |
| Gemini 3.1 Flash Lite | 15 | 250K | **500** |
| Gemini 3.5 Flash | 5 | 250K | 20 |
| Gemini 3.6 Flash | 5 | 250K | 20 |
| Gemini 3.7 Flash | 5 | 250K | 20 |
| Gemini 3.8 Flash | 5 | 250K | 20 |

**Conseguenza**: l'unico modello alternativo con la stessa quota generosa
(RPD 500) è `gemini-3.1-flash-lite`. Tutti i Flash "pieni" restano a RPD
20, inutilizzabili come default ma preziosi come ultima riserva: venti
risposte al giorno sono meglio di zero.

## Fix implementato (commit b572d56)

File toccati: `bot.py`, `storage.py`, `i18n.py`. **Non** toccati, perché
contengono lavoro musicale in corso non ancora committato:
`score_generator.py`, `main.pd`.

- `call_gemini_tracked` percorre una **catena di modelli**
  (`GEMINI_MODEL_CHAIN`) invece di usarne uno solo. Default:
  `gemini-3.5-flash-lite:500,gemini-3.1-flash-lite:500,gemini-3.8-flash:20`,
  sovrascrivibile con l'omonima variabile d'ambiente (formato
  `nome:RPD,nome:RPD,...`).
- Comportamento per tipo di guasto:
  - **5xx** (500, 502, 503, 504): un retry breve sullo stesso modello
    (`GEMINI_ATTEMPTS_PER_MODEL`, default 2, attesa
    `GEMINI_RETRY_BACKOFF_SECONDS`, default 2s), poi si passa al modello
    successivo della catena;
  - **429**: il modello viene escluso per il resto della giornata
    (`storage.mark_model_quota_blocked`) e si passa alla riserva. È questa
    la risposta al caso "token finiti": un modello a secco non ferma più
    tutto il bot;
  - **JSON non conforme**: stesso trattamento del 5xx, perché un modello
    diverso ha buone probabilità di rispettare lo schema dove un altro ha
    sbagliato;
  - **altri errori** (es. 400): si passa al modello successivo senza
    ritentare, ritentare un 400 non serve a niente.
- Le tre funzioni che parlano con Gemini (`describe_scene`,
  `plan_composition_and_synth`, `narrate_result`) ricevono il modello come
  **primo argomento**: non esiste più una costante globale che decide.
- Budget giornaliero contato **per modello**
  (`storage.check_and_consume_model_quota`), non più uno globale: con una
  catena, un contatore unico non saprebbe dire quale modello è ancora
  usabile. Formato su disco: `{"date": "AAAA-MM-GG", "models":
  {"nome-modello": {"count": N, "blocked": bool}}}`.
- Nuova eccezione `ModelsUnavailableError` e messaggio utente dedicato
  `error_overloaded` (IT/EN): il sovraccarico passa in pochi minuti, la
  quota si ricarica domani, non è onesto dare lo stesso messaggio nei due
  casi.
- `GEMINI_MODEL` resta valida su Render: ora sceglie **da dove parte** la
  catena invece di sostituirla.

## Verifica

Otto test automatici sui percorsi della catena, con Gemini simulato: 503
sul primo modello con passaggio al secondo; tutti 503 fino a
`ModelsUnavailableError`; 429 sul primo con passaggio alla riserva e
modello escluso anche alla chiamata successiva; tutti 429 fino a
`QuotaExhaustedError`; JSON non conforme su tutta la catena; budget locale
esaurito sul primo modello; 400 senza retry inutili; presenza dei messaggi
in IT e EN. Tutti passati.

Test end-to-end reale del 7 settembre alle 07:28: pipeline completa
riuscita, `fase3_plan_composition_and_synth[gemini-3.5-flash-lite]` in
2,07s al primo tentativo e `fase6_narrate_result[gemini-3.5-flash-lite]` in
1,85s, audio consegnato su Telegram.

**Onestà sul limite della verifica**: al momento del test il 503 era
rientrato da solo, quindi in produzione la catena non è ancora stata
esercitata davvero, solo nei test simulati. Lo sapremo al prossimo picco di
domanda su Google.

## Rischio residuo e possibile passo successivo

Se tutti e tre i modelli Gemini fossero sovraccarichi nello stesso momento,
l'utente riceve comunque un errore, più onesto ma sempre un errore. Per una
garanzia vera servirebbe un **secondo fornitore fuori da Google** (Groq e
OpenRouter offrono modelli con visione sul piano gratuito), quindi una
nuova chiave API da creare e gestire. Non implementato: da valutare.

## Note operative emerse durante il lavoro

- **Auto-deploy: era impostato su "On Commit" ma non funzionava**, perché
  il servizio era collegato come "Public Git Repository" (un semplice URL)
  e Render non riceveva nessun evento di push: nel repo non c'era alcun
  webhook e la GitHub App di Render non era installata. Sistemato il 7
  settembre 2026 collegando il provider Git e autorizzando la GitHub App
  sul repository; verificato con il commit 1509d88, deploy automatico
  riuscito in 32,9s. Da qui in avanti il push basta.
- Il file utenti sta in `/tmp` (`USER_DB_PATH`) e su Render free è
  effimero: **la scelta della lingua si perde a ogni risveglio
  dell'istanza**, non solo a ogni redeploy. Verificato sul campo il 7
  settembre: la prima foto dopo il risveglio si è vista richiedere di nuovo
  la lingua. Compromesso già noto e documentato in `storage.py`, ma pesa
  sulla UX più di quanto sembri, ed è la prima cosa che nota un utente
  nuovo.
