# scripts/

## fase0_test.sh

Confronta `qwen2.5vl:7b` e `moondream` (via Ollama) sullo stesso set di
immagini, usando lo stesso prompt fisso, per una validazione manuale rapida.

### Requisiti

- [Ollama](https://ollama.com/download) installato e nel PATH.
- Modelli scaricati:
  ```
  ollama pull qwen2.5vl:7b
  ollama pull moondream
  ```
  Lo script controlla la loro presenza con `ollama list` e, se mancano,
  stampa il comando da lanciare invece di uscire con un errore criptico.

### Uso

1. Metti le immagini (`.jpg`, `.jpeg`, `.png`) dentro `test-images/` nella
   root del progetto (oppure passa un'altra cartella come argomento).
2. Lancia lo script dalla root del progetto:
   ```
   ./scripts/fase0_test.sh
   ```
   oppure con una cartella diversa:
   ```
   ./scripts/fase0_test.sh /percorso/a/altre-immagini
   ```
3. Per ogni immagine, lo script interroga in sequenza `qwen2.5vl:7b` e
   `moondream` con il prompt:
   > Descrivi questa immagine in JSON con campi: soggetto, materiali,
   > colori, epoca, condizione, atmosfera, postura, texture. Solo JSON.

### Dove trovare i risultati

- `results/<nomefoto>_qwen.json` — output del modello qwen2.5vl:7b.
- `results/<nomefoto>_moondream.json` — output del modello moondream.
- `results/timing.csv` — tempo (in secondi) di ciascuna inferenza, colonne
  `immagine,modello,secondi`.

Nota: `results/` e `test-images/*.json` non sono script "di produzione":
è solo per test manuali, senza gestione errori sofisticata.
