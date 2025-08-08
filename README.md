# 🎛️ AI Audio Vision Lab

![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4-green)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![AI](https://img.shields.io/badge/AI-PyTorch%20%2B%20Magenta-orange)

> **Un sistema AI innovativo che trasforma la visione in musica**  
> Riconosce oggetti in tempo reale e genera composizioni musicali coerenti, completamente offline su Raspberry Pi 4.

---

## 🎥 Demo in Azione

[![Demo Video](https://img.shields.io/badge/▶️-Guarda%20la%20Demo-red?style=for-the-badge)](https://youtu.be/your-demo-link)

| Oggetto Rilevato | Stile Generato | Sample Audio |
|------------------|----------------|--------------|
| 🌱 Pianta | Ambient, Rilassante | [▶️ Ascolta](examples/plant_music.mp3) |
| 📚 Libro | Classico, Contemplativo | [▶️ Ascolta](examples/book_music.mp3) |
| ☕ Tazza | Jazz, Intimo | [▶️ Ascolta](examples/cup_music.mp3) |

---

## 🧠 Architettura del Sistema

```mermaid
graph LR
    A[Camera Raspberry Pi] --> B[PyTorch Object Detection]
    B --> C[Semantic Mapping Engine]
    C --> D[Magenta Music Generation]
    D --> E[TensorFlow Lite Inference]
    E --> F[MIDI/Audio Output]
    
    style A fill:#ff9999
    style F fill:#99ff99
```

### 🔧 Stack Tecnologico

- **Computer Vision**: PyTorch + TorchVision (MobileNet V2 ottimizzato)
- **AI Music**: Google Magenta convertito in TensorFlow Lite
- **Hardware**: Raspberry Pi 4, Camera Module v2
- **Audio**: pretty_midi + FluidSynth per sintesi real-time
- **Ottimizzazioni**: Quantizzazione INT8, Pipeline asincrona

---

## 📊 Performance su Raspberry Pi 4

| Metrica | Valore |
|---------|--------|
| **FPS Detection** | 12-15 fps |
| **Latenza Generazione** | < 2 secondi |
| **RAM Utilizzata** | ~1.4GB |
| **CPU Load** | 65-75% |
| **Tempo Boot** | ~15 secondi |

---

## 🎵 Esempi di Output Musicale

### Mappatura Semantica Oggetto → Musica

Il sistema utilizza un algoritmo proprietario per mappare caratteristiche visive in parametri musicali:

```python
# Esempio concettuale (implementazione proprietaria)
def object_to_music_params(detected_object):
    """
    Converte oggetti rilevati in parametri musicali
    Logica proprietaria non pubblica
    """
    semantic_features = extract_semantic_features(detected_object)
    musical_params = {
        'tempo': map_to_tempo(semantic_features.energy),
        'key': map_to_key(semantic_features.emotion),
        'instruments': select_instruments(semantic_features.category)
    }
    return musical_params
```

### 🎼 Composizioni Generate

**Oggetto: Pianta in Vaso** 🌱
- **Stile**: Ambient, New Age
- **Tonalità**: Do Maggiore
- **Tempo**: 72 BPM
- **Strumenti**: Pad sintetici, Archi soft

**Oggetto: Libro Aperto** 📖
- **Stile**: Neoclassico
- **Tonalità**: La minore
- **Tempo**: 60 BPM
- **Strumenti**: Pianoforte, Quartetto d'archi

---

## 🚀 Setup e Installazione

### Requisiti Hardware
- Raspberry Pi 4 (4GB RAM minimo)
- MicroSD 32GB+ (Classe 10)
- Camera Module v2 o USB Camera
- Speaker USB o Jack 3.5mm

### Installazione Rapida
```bash
# Clona il repository demo
git clone https://github.com/ninuxi/ai-audio-vision-lab.git
cd ai-audio-vision-lab

# Installa dipendenze
pip3 install -r requirements.txt

# Configura hardware
sudo raspi-config  # Abilita Camera

# Avvia demo
python3 demo/vision_music_demo.py
```

---

## 🔬 Ricerca e Sviluppo

### Contributi Tecnici Originali

1. **Pipeline Ottimizzata per Edge Computing**
   - Quantizzazione personalizzata dei modelli Magenta
   - Buffer circolare per elaborazione real-time
   - Memory mapping intelligente per Raspberry Pi

2. **Algoritmo di Mappatura Semantica**
   - Correlazione oggetto-emozione basata su ricerca cognitiva
   - Parametrizzazione musicale multi-dimensionale
   - Sistema di coerenza temporale per transizioni fluide

3. **Framework di Inferenza Offline**
   - Zero dipendenze cloud
   - Modelli completamente embedded
   - Latenza < 2s garantita

### 📈 Roadmap Futura

- [ ] **Versione Mobile**: Porting su Android/iOS
- [ ] **Multi-Modalità**: Audio input + Visual input
- [ ] **Learning Personalizzato**: Adattamento alle preferenze utente
- [ ] **ESP32 Port**: Versione ultra-compatta con TinyML

---

## 🤝 Collaborazioni e Contatti

**Interessato a collaborare?** Questo progetto è aperto a:

- 🎓 **Ricercatori** in AI/Music Information Retrieval
- 🎵 **Musicisti** interessati a tecnologie creative
- 💻 **Sviluppatori** con esperienza in edge computing
- 🏢 **Aziende** per applicazioni commerciali

### 📧 Contatti
- **Email**: oggettosonoro@gmail.com  
- **GitHub**: [@ninuxi](https://github.com/ninuxi)
- **Portfolio**: [Link al portfolio completo]

---

## ⚖️ Licenza e Utilizzo

Questo repository contiene una **versione dimostrativa** del progetto AI Audio Vision Lab.  

- ✅ **Demo e esempi**: Liberamente utilizzabili (MIT License)
- ❌ **Codice sorgente completo**: Proprietario, non pubblico
- 🤝 **Collaborazioni commerciali**: Contatta per licenze specifiche

> **Nota**: Gli algoritmi core e i modelli addestrati rappresentano ricerca originale e non sono pubblicamente disponibili. Per accesso completo o partnership commerciali, contatta direttamente l'autore.

---

## 🌟 Riconoscimenti

Progetto sviluppato da **Antonio Mainenti** (2024-2025)

*Se questo progetto ti ispira, lascia una ⭐ e condividilo!*

---

**© 2025 Antonio Mainenti - Alcuni diritti riservati**