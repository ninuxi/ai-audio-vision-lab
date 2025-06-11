# 🎤 Edge Audio Classifier

Classificatore audio in tempo reale progettato per riconoscere suoni semplici (es. *clap*, *fischio*, *silenzio*) su PC.  
Progetto pensato per essere convertito in modelli leggeri compatibili con Raspberry Pi o ESP32 via TFLite Micro.

## 📁 Struttura
- `data/`: dataset audio WAV per l'addestramento
- `models/`: modelli salvati (.pt, .tflite)
- `notebooks/`: esperimenti e prototipi
- `scripts/`: codice per training, inferenza e conversione modello

## ▶️ Esecuzione base
```
pip install -r requirements.txt
python scripts/train.py
python scripts/inference.py --file example.wav
```

## 🚀 Obiettivi futuri
- Integrazione con ESP32 via TFLite Micro
- Mapping audio → MIDI / generazione musicale

## 👨‍🔧 Autore
[Il tuo nome] – 2025
