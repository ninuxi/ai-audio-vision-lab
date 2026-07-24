# AI Audio Vision Lab, versione browser/PWA: decisioni e stato

Data: 21 luglio 2026

## Cos'è questa versione

Non è una mostra, non è un'installazione fissa. È una macchina fotografica personale: fotografa una scena, in qualsiasi luogo si trovi la persona, e genera musica dall'immagine catturata. Lo smartphone via browser è la scelta perché è lo strumento che chiunque ha già in tasca, senza installazione, senza App Store.

Pubblico di riferimento: artisti e utenti tecnicamente disinvolti, non un pubblico generico da mostra. Questo cambia le decisioni rispetto a un'installazione pubblica.

**Nota per il progetto attuale:** questa versione browser/PWA è stata esplorata concettualmente ma non implementata. Il progetto attuale usa un bot Telegram invece del browser, per riutilizzare la pipeline Python/Pd/OSC esistente invece di riscrivere il motore audio in Web Audio API. Vedi sotto per il confronto delle due opzioni, ancora valido come riferimento.

## Perché il browser e non un'app nativa

Antonio non è uno sviluppatore, non può pubblicare su App Store (serve account sviluppatore Apple, revisione, ecc). Una pagina web statica risolve il problema alla radice: si ospita gratis (es. GitHub Pages), si apre con un URL, funziona su Safari, Chrome, Firefox, su iPhone, iPad, Android.

**PWA (Progressive Web App)**: su iOS, Safari permette "Aggiungi a Home" per qualsiasi pagina, che diventa un'icona a schermo intero senza barra del browser, senza passare per l'App Store. Basta un `manifest.json` e poche righe di configurazione. Vale la pena farlo da subito.

## Architettura (versione browser, non usata nel progetto attuale)

Una sola modalità, niente server proprio da mantenere.

1. **Camera**: la pagina apre la camera dello smartphone (`getUserMedia`).
2. **Scatto**: un tap dell'utente cattura il frame. Su iOS il tap è anche il gesto obbligatorio che sblocca l'audio (Web Audio non parte senza interazione utente).
3. **Chiave API**: l'utente inserisce la propria chiave (BYOK, bring your own key). Nessuna chiave salvata su un server: resta nel browser dell'utente. Questo va dichiarato chiaramente nella pagina.
4. **Doppio passaggio LLM** (stessa logica del progetto originale, solo cloud invece che Ollama locale):
   - passaggio 1: foto -> JSON descrittivo (soggetto, materiali, colori, epoca, condizione, atmosfera, postura, texture)
   - passaggio 2: JSON descrittivo -> JSON piano compositivo (scala/modo, tempo, forma, densità, timbrica, dinamica)
5. **Sintesi**: Web Audio API riceve il piano e genera il suono (oscillatori, sample player per i field recording propri di Antonio, envelope).

Il cuore autoriale, cioè il prompt di visione e il mapping descrizione -> parametri musicali, è identico alla versione locale con Ollama. Cambia solo il trasporto: JSON diretto invece di OSC verso Pd.

## Cosa NON sopravvive dalla versione locale

- **Pure Data**: non gira nel browser. Va riscritto in Web Audio API. Non è un adattamento, è una riscrittura del motore sonoro.
- **Ollama/VLM locale**: sostituito da chiamata API cloud (Gemini, Claude o OpenAI, a scelta dell'utente in base a quale chiave possiede).
- **OSC**: sostituito da JSON passato direttamente in memoria nel browser (nessun bisogno nemmeno di WebSocket, è tutto client-side tranne la chiamata API).

## Scelta del provider API

Nel progetto attuale (Telegram, non browser): scelto **Gemini** come provider VLM/LLM cloud, chiave gestita server-side (non BYOK, dato che il bot gira su un server condiviso, non nel browser dell'utente).

- **Gemini Flash**: ha un tier gratuito, minor attrito per chi prova lo strumento senza spendere. Scelto per il progetto attuale.
- **Claude**: da testare per qualità descrizione JSON.
- **OpenAI (GPT-4o)**: opzione aggiuntiva, nessun tier gratuito.

## Cosa NON cambia rispetto al progetto originale

- L'obiettivo resta lo stesso: descrizione ricca della scena tradotta in composizione musicale originale e coerente.
- Il criterio di validazione della fase 0 resta lo stesso: le descrizioni devono contenere dettagli utilizzabili (materiale, texture, epoca, condizione), non genericità tipo "persona con maglia scura".
- Il mapping d'autore (es. metallo ossidato = inarmonicità) resta il cuore compositivo, indipendente dal trasporto tecnico.