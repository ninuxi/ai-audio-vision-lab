# 🎛️ AI Audio Vision Lab

## 🇮🇹 Descrizione
In questo progetto utilizzo una camera su Raspberry Pi per riconoscere oggetti in tempo reale e generare musica coerente tramite modelli di intelligenza artificiale (AI).  
Il sistema funziona in modalità **offline** su Raspberry Pi 4, utilizzando PyTorch per il riconoscimento e modelli Magenta convertiti in TensorFlow Lite per la generazione musicale.

## 🇬🇧 Description
In this project I use a camera on Raspberry Pi to recognize objects in real time and generate coherent music via AI models.  
The system works **offline** on Raspberry Pi 4, using PyTorch for object detection and Magenta models converted to TensorFlow Lite for music generation.

---

## 🇮🇹 Caratteristiche principali
- Riconoscimento oggetti in tempo reale con PyTorch  
- Conversione dei modelli Magenta in TensorFlow Lite per esecuzione locale  
- Generazione musicale basata su oggetti rilevati  
- Intero sistema offline su Raspberry Pi 4  

## 🇬🇧 Key Features
- Real-time object detection with PyTorch  
- Conversion of Magenta models to TensorFlow Lite for local execution  
- Music generation driven by detected objects  
- Fully offline system on Raspberry Pi 4  

---

## 🇮🇹 Tecnologie utilizzate
- **Python**  
- **TorchVision / PyTorch**  
- **Magenta**  
- **TensorFlow Lite**  
- **pretty_midi**  
- **Raspberry Pi 4**

## 🇬🇧 Technologies used
- **Python**  
- **TorchVision / PyTorch**  
- **Magenta**  
- **TensorFlow Lite**  
- **pretty_midi**  
- **Raspberry Pi 4**

---

## 🇮🇹 Installazione & Usage

1. Clona il repository  
```bash
git clone https://github.com/ninuxi/ai-audio-vision-lab.git
cd ai-audio-vision-lab
2. Installa le dipendenze Python

pip install -r requirements.txt

    Inserisci la SD nel Raspberry Pi 4

    Esegui lo script
python3 main.py

 5. Inquadra un oggetto: verrà generata una melodia coerente.

🇬🇧 Installation & Usage

    Clone the repo

git clone https://github.com/ninuxi/ai-audio-vision-lab.git
cd ai-audio-vision-lab
    Install Python dependencies

pip install -r requirements.txt

    Insert microSD into Raspberry Pi 4

    Run the script
python3 main.py
Point the camera at an object: a coherent melody will be generated.

Email: oggettosonoro@gmail.com

GitHub: ninuxi
