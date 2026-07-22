#!/usr/bin/env bash
#
# Fase 0 - test manuale di confronto tra qwen2.5vl:7b e moondream su un set
# di immagini locali, via API HTTP locale di Ollama. Script di validazione,
# uso singolo/manuale.

set -uo pipefail

PROMPT="Descrivi questa immagine in JSON con campi: soggetto, materiali, colori, epoca, condizione, atmosfera, postura, texture. Solo JSON. Ogni campo deve essere una stringa singola o una lista di stringhe, mai un oggetto annidato. Se un campo ha più valori (es. più texture diverse nella stessa immagine), usa una lista: [\"ruvida\", \"umida\"], non un dizionario."

QWEN_MODEL="qwen2.5vl:7b"
MOONDREAM_MODEL="moondream"
OLLAMA_API_URL="http://localhost:11434/api/generate"

# moondream con le impostazioni di default va spesso in loop di ripetizione
# ed esaurisce il contesto (prompt_eval + eval = num_ctx di default, 2048)
# prima di chiudere il JSON. Alziamo sia num_predict che num_ctx per dargli
# margine. qwen2.5vl:7b resta invariato (nessuna "options" nella richiesta).
MOONDREAM_NUM_PREDICT=2048
MOONDREAM_NUM_CTX=4096

# Impostare FASE0_SKIP_QWEN=1 nell'ambiente per rilanciare solo moondream
# (utile per ripetere in modo mirato solo le immagini fallite in precedenza).
FASE0_SKIP_QWEN="${FASE0_SKIP_QWEN:-0}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

IMAGES_DIR="${1:-$ROOT_DIR/test-images}"
RESULTS_DIR="$ROOT_DIR/results"
TIMING_CSV="$RESULTS_DIR/timing.csv"

# 1. Cartelle di lavoro
mkdir -p "$ROOT_DIR/test-images"
mkdir -p "$RESULTS_DIR"
touch "$ROOT_DIR/test-images/.gitkeep"

# 2. Verifica ollama installato e servizio raggiungibile
if ! command -v ollama >/dev/null 2>&1; then
  echo "Errore: 'ollama' non e' installato o non e' nel PATH."
  echo "Installa Ollama da https://ollama.com/download e riprova."
  exit 0
fi

if ! OLLAMA_LIST_RAW="$(ollama list 2>&1)"; then
  echo "Errore: impossibile contattare il servizio Ollama."
  echo "Avvialo con: brew services start ollama"
  echo "oppure con: ollama serve"
  exit 0
fi

OLLAMA_MODELS="$(echo "$OLLAMA_LIST_RAW" | tail -n +2 | awk '{print $1}')"

MISSING=0

if ! echo "$OLLAMA_MODELS" | grep -qx "$QWEN_MODEL"; then
  echo "Modello '$QWEN_MODEL' non trovato tra i modelli scaricati."
  echo "Scaricalo con: ollama pull $QWEN_MODEL"
  MISSING=1
fi

if ! echo "$OLLAMA_MODELS" | grep -qE "^${MOONDREAM_MODEL}(:.*)?$"; then
  echo "Modello '$MOONDREAM_MODEL' non trovato tra i modelli scaricati."
  echo "Scaricalo con: ollama pull $MOONDREAM_MODEL"
  MISSING=1
fi

if [ "$MISSING" -eq 1 ]; then
  echo ""
  echo "Scarica i modelli mancanti (vedi sopra) e rilancia lo script."
  exit 0
fi

# 3. Verifica cartella immagini
if [ ! -d "$IMAGES_DIR" ]; then
  echo "Errore: la cartella immagini '$IMAGES_DIR' non esiste."
  echo "Metti le immagini in test-images/ (o passa un percorso valido come argomento) e riprova."
  exit 0
fi

shopt -s nullglob nocaseglob
IMAGES=("$IMAGES_DIR"/*.jpg "$IMAGES_DIR"/*.jpeg "$IMAGES_DIR"/*.png)
shopt -u nocaseglob nullglob

if [ ${#IMAGES[@]} -eq 0 ]; then
  echo "Nessuna immagine .jpg/.jpeg/.png trovata in '$IMAGES_DIR'."
  echo "Aggiungi delle immagini nella cartella e rilancia lo script."
  exit 0
fi

if [ ! -f "$TIMING_CSV" ]; then
  echo "immagine,modello,secondi" > "$TIMING_CSV"
fi

# Helper Python scritto su file temporaneo (non inline in una command
# substitution: un heredoc con parentesi non bilanciate annidato dentro
# $(...) confonde il parser di bash). Chiama /api/generate (stream:false)
# con l'immagine in base64, valida che il campo "response" sia JSON valido
# (tollerando eventuali fence markdown) e lo salva. Se non e' JSON valido,
# NON salva testo corrotto: logga un errore esplicito e mette il testo
# grezzo in un file .invalid.txt per ispezione.
HELPER_PY="$(mktemp -t fase0_ollama_call).py"
trap 'rm -f "$HELPER_PY"' EXIT

cat > "$HELPER_PY" <<'PYEOF'
import base64
import json
import os
import sys
import urllib.request

REQUIRED_FIELDS = [
    "soggetto", "materiali", "colori", "epoca",
    "condizione", "atmosfera", "postura", "texture",
]


def valore_valido(v):
    if isinstance(v, str):
        return v.strip() != ""
    if isinstance(v, list):
        return len(v) > 0 and all(isinstance(x, str) and x.strip() != "" for x in v)
    return False


def valida_schema(obj):
    if not isinstance(obj, dict):
        return False, "la risposta non e' un oggetto JSON (dict) di primo livello"
    mancanti = [k for k in REQUIRED_FIELDS if k not in obj]
    if mancanti:
        return False, f"campi mancanti: {', '.join(mancanti)}"
    non_validi = [k for k in REQUIRED_FIELDS if not valore_valido(obj[k])]
    if non_validi:
        return False, (
            "campi con valore non valido (atteso stringa o lista di stringhe "
            f"non vuote, non numeri): {', '.join(non_validi)}"
        )
    return True, ""


model, image_path, out_file, invalid_file = sys.argv[1:5]
prompt = os.environ["FASE0_PROMPT"]
api_url = os.environ["FASE0_API_URL"]

with open(image_path, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("ascii")

payload_dict = {
    "model": model,
    "prompt": prompt,
    "images": [img_b64],
    "stream": False,
}

options = {}
num_predict = os.environ.get("FASE0_NUM_PREDICT")
if num_predict:
    options["num_predict"] = int(num_predict)
num_ctx = os.environ.get("FASE0_NUM_CTX")
if num_ctx:
    options["num_ctx"] = int(num_ctx)
if options:
    payload_dict["options"] = options

fmt = os.environ.get("FASE0_FORMAT")
if fmt:
    payload_dict["format"] = fmt

payload = json.dumps(payload_dict).encode("utf-8")

req = urllib.request.Request(
    api_url, data=payload, headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = json.loads(resp.read().decode("utf-8"))
except Exception as e:
    print(f"Errore chiamata API Ollama: {e}", file=sys.stderr)
    print("ERROR")
    print("n/a")
    sys.exit(1)

done_reason = body.get("done_reason", "n/a")
text = body.get("response", "")

# Tollera risposte avvolte in fence markdown ```json ... ```
stripped = text.strip()
if stripped.startswith("```"):
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    stripped = "\n".join(lines).strip()

try:
    parsed = json.loads(stripped)
except json.JSONDecodeError as e:
    with open(invalid_file, "w") as f:
        f.write(text)
    print(f"risposta non e' JSON valido ({e}); testo grezzo salvato in {invalid_file}", file=sys.stderr)
    print("ERROR")
    print(done_reason)
    sys.exit(1)

schema_ok, schema_errore = valida_schema(parsed)
if not schema_ok:
    with open(invalid_file, "w") as f:
        f.write(text)
    print(f"JSON valido ma schema non conforme ({schema_errore}); testo grezzo salvato in {invalid_file}", file=sys.stderr)
    print("ERROR")
    print(done_reason)
    sys.exit(1)

with open(out_file, "w") as f:
    f.write(stripped + "\n")

print("OK")
print(done_reason)
PYEOF

call_ollama() {
  local model="$1"
  local label="$2"
  local image_path="$3"
  local basename_noext="$4"

  local out_file="$RESULTS_DIR/${basename_noext}_${label}.json"
  local invalid_file="$RESULTS_DIR/${basename_noext}_${label}.invalid.txt"
  local status_file err_file
  status_file="$(mktemp)"
  err_file="$(mktemp)"

  echo "  -> $label ($model) via API..."

  local num_predict="" num_ctx="" fmt=""
  if [ "$label" = "moondream" ]; then
    num_predict="$MOONDREAM_NUM_PREDICT"
    num_ctx="$MOONDREAM_NUM_CTX"
    fmt="json"
  fi

  local TIMEFORMAT='%R'
  local elapsed
  elapsed=$( { time FASE0_PROMPT="$PROMPT" FASE0_API_URL="$OLLAMA_API_URL" \
    FASE0_NUM_PREDICT="$num_predict" FASE0_NUM_CTX="$num_ctx" FASE0_FORMAT="$fmt" \
    python3 "$HELPER_PY" "$model" "$image_path" "$out_file" "$invalid_file" \
    > "$status_file" 2>"$err_file"; } 2>&1 )

  local result done_reason err_msg
  result="$(sed -n '1p' "$status_file")"
  done_reason="$(sed -n '2p' "$status_file")"
  err_msg="$(cat "$err_file")"
  rm -f "$status_file" "$err_file"

  echo "$basename_noext,$label,$elapsed" >> "$TIMING_CSV"

  if [ "$result" = "OK" ]; then
    echo "     tempo: ${elapsed}s -> $out_file [done_reason: $done_reason]"
  else
    echo "     tempo: ${elapsed}s -> ERRORE: $err_msg [done_reason: $done_reason]"
  fi
}

# 4. Ciclo su tutte le immagini
for img in "${IMAGES[@]}"; do
  filename="$(basename "$img")"
  basename_noext="${filename%.*}"

  echo "Immagine: $filename"

  if [ "$FASE0_SKIP_QWEN" != "1" ]; then
    call_ollama "$QWEN_MODEL" "qwen" "$img" "$basename_noext"
  fi
  call_ollama "$MOONDREAM_MODEL" "moondream" "$img" "$basename_noext"

  echo ""
done

echo "Fatto. Risultati in: $RESULTS_DIR"
echo "Tempi di inferenza in: $TIMING_CSV"
