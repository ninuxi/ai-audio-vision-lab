# AI Audio Vision Lab, fase 0: log di validazione VLM

Data: 22 luglio 2026

## Obiettivo della sessione

Eseguire la fase 0: testare Qwen2.5-VL-7B e Moondream 2 su un set di immagini con lo stesso prompt JSON strutturato, per giudicare se le descrizioni sono abbastanza ricche da alimentare il mapping musicale.

Questo log documenta il lavoro corrispondente a `scripts/fase0_test.sh` e `scripts/README.md` già presenti nel repo, con i risultati in `results/*.json`.

## Ambiente

- Ollama installato via `brew install ollama`
- Modelli scaricati: `qwen2.5vl:7b` (6.0 GB), `moondream:latest` (1.7 GB)
- Script: `scripts/fase0_test.sh`, usa l'API HTTP locale di Ollama (`http://localhost:11434/api/generate`, `stream: false`) invece della CLI `ollama run`, per evitare la cattura di sequenze di escape del terminale nell'output

## Set di immagini di test

14 immagini in `test-images/`: mix di oggetti (bici vintage, orologio d'epoca), materiali (metallo ossidato, tessuto), natura, texture astratte, e due ritratti generici (uomo, donna, scelti apposta generati/anonimi per evitare di testare volti di persone reali riconoscibili).

## Problemi tecnici incontrati e risolti

1. **Output CLI corrotto**: `ollama run` in redirezione produceva output con sequenze ANSI. Risolto passando all'API HTTP.
2. **Moondream in loop di ripetizione sintattica**: alcune immagini generavano JSON mai chiuso (`done_reason: length`). Risolto in gran parte aggiungendo `"format": "json"` (decoding vincolato lato server) solo per moondream.
3. **Validazione insufficiente**: il controllo iniziale verificava solo "è JSON parsabile", lasciando passare risposte semanticamente vuote (es. array di soli numeri al posto della struttura attesa). Rafforzata la validazione per richiedere i campi attesi come chiavi di primo livello con valori stringa/lista di stringhe.
4. **Prompt più prescrittivo su `texture`**: ha migliorato qwen (8/14 → 11/14 file validi) ma ha peggiorato drasticamente moondream (4/14 → 0/14), causando anche la ricomparsa di loop di ripetizione su due immagini. Non risolto ulteriormente: trattato come limite strutturale del modello più piccolo rispetto a prompt più complessi, non come bug da inseguire.

## Risultato finale (stesso prompt per entrambi i modelli, dataset omogeneo)

| Modello | Validi | Invalidi |
|---|---|---|
| qwen2.5vl:7b | 11/14 | 3/14 |
| moondream | 0/14 | 14/14 |

**Decisione presa**: accettare questo risultato come dato di fatto, senza rincorrere ulteriori varianti di prompt per far rientrare moondream. Con lo schema richiesto dal progetto, moondream è quasi inutilizzabile in pipeline automatica, indipendentemente dalla qualità delle rare risposte corrette.

## Valutazione di contenuto (criterio di ricchezza descrittiva, qwen)

- **bici_vintage**: buono. Dettagli concreti e distinti ("fine del XIX secolo", "acciaio/legno", "rugosa/liscia"), coerente con il criterio del progetto.
- **ritratto_uomo**: debole. Descrizione quasi interamente generica ("uomo, maglione grigio/blu, contemporanea, ben curato"), nessun dettaglio fisico specifico. Possibile segnale che il modello è sistematicamente più povero sui ritratti che sugli oggetti.

## Nota per il progetto attuale (Telegram + Gemini)

Questo test di fase 0 è stato fatto su modelli locali via Ollama (qwen2.5vl, moondream), non su Gemini. Il **prompt JSON strutturato** (campi: soggetto, materiali, colori, epoca, condizione, atmosfera, postura, texture) e il **criterio di validazione** (campi attesi come chiavi di primo livello, valori stringa/lista di stringhe) restano il riferimento di partenza per il prompt Gemini nel bot Telegram, ma vanno ri-testati contro le risposte reali di Gemini, che potrebbe comportarsi diversamente dai modelli locali testati qui.

## Prossimo passo (storico, superato dalla decisione di andare su Gemini cloud)
1. Investigare il file di output non valido per `metallo_ossidato` (fallito per campo `postura` non valido), immagine chiave per il mapping d'autore del progetto (metallo ossidato = inarmonicità).
2. Rivedere il contenuto degli altri file qwen validi rimasti.
3. Costruire il vocabolario di mapping descrizione → parametri musicali.