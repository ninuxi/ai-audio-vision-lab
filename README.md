
Markdown

# 🎛️ AI Audio Vision Lab

![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4-green)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Issues](https://img.shields.io/github/issues/ninuxi/ai-audio-vision-lab)
![Last Commit](https://img.shields.io/github/last-commit/ninuxi/ai-audio-vision-lab)

Un sistema AI su Raspberry Pi che riconosce oggetti in tempo reale e genera musica coerente tramite modelli di intelligenza artificiale, funzionando completamente offline.

---

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

## 🇮🇹 Installazione & Uso

1. Clona il repository  
   ```bash
   git clone https://github.com/ninuxi/ai-audio-vision-lab.git
   cd ai-audio-vision-lab

    Installa le dipendenze Python
    bash

pip install -r requirements.txt

Inserisci la microSD nel Raspberry Pi 4
Esegui lo script
bash

    python3 main.py

    Inquadra un oggetto: verrà generata una melodia coerente.

🇬🇧 Installation & Usage

    Clone the repository
    bash

git clone https://github.com/ninuxi/ai-audio-vision-lab.git
cd ai-audio-vision-lab

Install Python dependencies
bash

pip install -r requirements.txt

Insert the microSD into Raspberry Pi 4
Run the script
bash

    python3 main.py

    Point the camera at an object: a coherent melody will be generated.

🤝 Contributing

Contributions are welcome!
If you want to contribute, please:

    Fork the repository
    Create a new branch (git checkout -b feature/your-feature)
    Commit your changes (git commit -m 'Add your feature')
    Push to the branch (git push origin feature/your-feature)
    Open a Pull Request

Any help with code, documentation or ideas is appreciated!
📄 License

This project is licensed under the MIT License.
See the LICENSE file for details.
📧 Contatti / Contacts

    Email: oggettosonoro@gmail.com
    GitHub: ninuxi

