"""
AI Audio Vision Lab - generatore di partitura

Tutta la logica compositiva (quali note, quale ritmo) vive qui: main.pd
riceve solo array piatti (un valore per sedicesimo) e li esegue, senza
prendere alcuna decisione musicale.

Perche' appiattito invece di note+durate compatte: far tracciare a Pd
"quanti step mancano alla nota corrente" e' uno stato in piu' in un
ambiente (Pd vanilla) dove si e' gia' rivelato fragile qualunque stato
implicito. Appiattendo qui, main.pd deve solo reagire un passo alla
volta: nuovo grado -> attacca, HOLD -> non fare nulla, REST -> rilascia.

Valori nelle sequenze melodia/basso:
  >= 0   grado di scala (indice in scale_intervals): nuova nota
  -1     REST (pausa)
  -2     HOLD (tieni la nota precedente, per codificare le durate)
Kick/hat: 0/1 (silenzio/colpo), nessun sentinel.
"""

import random
import re

STEPS_PER_QUARTER = 4  # risoluzione: sedicesimi
MAX_STEPS = 2560  # deve combaciare con la taglia delle table in main.pd

REST = -1
HOLD = -2


def step_duration_ms(tempo_bpm: float) -> float:
    return 60000.0 / tempo_bpm / STEPS_PER_QUARTER


def compute_total_steps(duration_seconds: float, tempo_bpm: float) -> int:
    n = round(duration_seconds * 1000.0 / step_duration_ms(tempo_bpm))
    return max(1, min(MAX_STEPS, n))


def _normalize_section_name(label: str) -> str:
    """"A" "A'" "A''" "A2" "a" -> "a": stessa sezione a prescindere da
    apici/numeri/maiuscole, per riconoscere le ripetizioni nella forma."""
    base = re.sub(r"[\'’′\"\d\s]+", "", label).strip().lower()
    return base or label.strip().lower()


def parse_sections(forma) -> list[str]:
    if isinstance(forma, list):
        raw = [str(x) for x in forma]
    else:
        raw = re.split(r"[-–—,/]+", str(forma))
    sections = [s.strip() for s in raw if s.strip()]
    return sections or ["A", "B", "A", "Coda"]


def _is_coda(label: str) -> bool:
    return "coda" in label.lower()


def _section_step_counts(sections: list[str], total: int) -> list[int]:
    weights = [0.5 if _is_coda(s) else 1.0 for s in sections]
    total_w = sum(weights)
    counts = [max(1, round(total * w / total_w)) for w in weights]
    diff = total - sum(counts)
    counts[-1] = max(1, counts[-1] + diff)
    return counts


def _rng_for(seed: str, *parts: str) -> random.Random:
    return random.Random(seed + "|" + "|".join(parts))


def _pad_or_trim(seq: list[int], n: int, fill: int = REST) -> list[int]:
    if len(seq) >= n:
        return seq[:n]
    return seq + [fill] * (n - len(seq))


def _generate_melody_events(rng, n_degrees, n_steps, start_degree):
    """Lista di (grado_o_REST, durata_in_step) che copre esattamente n_steps.
    Preferenza per movimento congiunto, qualche pausa, ritorno alla
    fondamentale sul finale di frase."""
    events = []
    covered = 0
    degree = start_degree
    step_choices = [-2, -1, -1, 0, 1, 1, 2]
    dur_choices = [1, 1, 1, 2, 2, 3]
    while covered < n_steps:
        remaining = n_steps - covered
        if remaining <= 2:
            events.append((0, remaining))
            covered += remaining
            break
        if rng.random() < 0.15:
            events.append((REST, 1))
            covered += 1
            continue
        move = rng.choice(step_choices)
        degree = max(0, min(n_degrees - 1, degree + move))
        dur = min(rng.choice(dur_choices), remaining)
        events.append((degree, dur))
        covered += dur
    return events


def _flatten_events(events: list[tuple[int, int]]) -> list[int]:
    flat: list[int] = []
    for value, dur in events:
        if value == REST:
            flat.extend([REST] * dur)
        else:
            flat.append(value)
            flat.extend([HOLD] * (dur - 1))
    return flat


def _generate_bass_flat(rng, n_steps, fifth_degree, slot=4):
    flat: list[int] = []
    covered = 0
    while covered < n_steps:
        dur = min(slot, n_steps - covered)
        degree = fifth_degree if rng.random() < 0.35 else 0
        flat.append(degree)
        flat.extend([HOLD] * (dur - 1))
        covered += dur
    return flat


def _generate_drum_bar(rng, density: float, coda: bool) -> tuple[list[int], list[int]]:
    kick = [0] * 16
    hat = [0] * 16
    if coda:
        kick[0] = 1
        kick[8] = 1
        return kick, hat  # niente hi-hat in coda: densita' ridotta
    for i in range(16):
        kick_prob = (0.9 if i % 4 == 0 else 0.12) * (0.6 + 0.4 * density)
        if rng.random() < kick_prob:
            kick[i] = 1
        hat_prob = 0.25 + 0.55 * density + (0.2 if i % 2 == 1 else 0.0)
        if rng.random() < hat_prob:
            hat[i] = 1
    return kick, hat


def _tile(pattern16: list[int], n_steps: int) -> list[int]:
    reps = n_steps // 16 + 1
    return (pattern16 * reps)[:n_steps]


def generate_score(synth_params: dict, plan: dict, seed: str) -> dict:
    """Genera le quattro sequenze piatte (melodia, basso, kick, hat) piu'
    i metadati (total_steps, step_ms) da mandare a Pd."""
    tempo_bpm = synth_params["tempo_bpm"]
    duration_seconds = synth_params["duration_seconds"]
    scale_intervals = list(synth_params["scale_intervals"])
    n_degrees = len(scale_intervals)
    rhythm_density = synth_params.get("rhythm_density", 0.5)

    n_total = compute_total_steps(duration_seconds, tempo_bpm)
    sections = parse_sections(plan.get("forma", "A-B-A-Coda"))
    section_steps = _section_step_counts(sections, n_total)

    fifth_degree = min(range(n_degrees), key=lambda i: abs(scale_intervals[i] - 7))

    melody_flat: list[int] = []
    bass_flat: list[int] = []
    kick_flat: list[int] = []
    hat_flat: list[int] = []

    seen: dict[str, int] = {}
    last_degree = 0

    for label, n_steps in zip(sections, section_steps):
        norm = _normalize_section_name(label)
        occurrence = seen.get(norm, 0)
        seen[norm] = occurrence + 1
        variant = norm if occurrence == 0 else f"{norm}_var{occurrence}"

        mel_events = _generate_melody_events(
            _rng_for(seed, "melody", variant), n_degrees, n_steps, last_degree
        )
        mel_flat_section = _pad_or_trim(_flatten_events(mel_events), n_steps, fill=REST)
        melody_flat.extend(mel_flat_section)
        for v in reversed(mel_flat_section):
            if v != HOLD:
                last_degree = v if v != REST else last_degree
                break

        bass_flat.extend(
            _pad_or_trim(
                _generate_bass_flat(_rng_for(seed, "bass", variant), n_steps, fifth_degree),
                n_steps,
                fill=HOLD,
            )
        )

        kick16, hat16 = _generate_drum_bar(
            _rng_for(seed, "drums", variant), rhythm_density, _is_coda(label)
        )
        kick_flat.extend(_tile(kick16, n_steps))
        hat_flat.extend(_tile(hat16, n_steps))

    return {
        "total_steps": n_total,
        "step_ms": step_duration_ms(tempo_bpm),
        "melody": melody_flat,
        "bass": bass_flat,
        "kick": kick_flat,
        "hat": hat_flat,
    }
