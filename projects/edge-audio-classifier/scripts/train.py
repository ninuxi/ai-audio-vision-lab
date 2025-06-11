import os
import torch
import torch.nn as nn
import torch.optim as optim
import torchaudio
from torch.utils.data import Dataset, DataLoader
import librosa
import numpy as np

# Dataset audio semplificato
class AudioDataset(Dataset):
    def __init__(self, folder):
        self.files = []
        self.labels = []
        self.label_map = {"clap": 0, "silence": 1, "whistle": 2}
        for f in os.listdir(folder):
            if f.endswith(".wav"):
                path = os.path.join(folder, f)
                self.files.append(path)
                for key in self.label_map:
                    if key in f:
                        self.labels.append(self.label_map[key])
                        break

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        x, sr = librosa.load(self.files[idx], sr=16000)
        mfcc = librosa.feature.mfcc(y=x, sr=sr, n_mfcc=13)
        return torch.tensor(mfcc, dtype=torch.float32), self.labels[idx]

# Rete semplice
class AudioClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(13, 32, 3), nn.ReLU(),
            nn.Conv1d(32, 64, 3), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1)
        )
        self.fc = nn.Linear(64, 3)

    def forward(self, x):
        x = self.conv(x)
        x = x.squeeze(-1)
        return self.fc(x)

def main():
    dataset = AudioDataset("projects/edge-audio-classifier/data")
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)

    model = AudioClassifier()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(20):
        for x, y in dataloader:
            x = x.permute(0, 1, 2)  # (B, MFCC, T)
            y = torch.tensor(y)
            out = model(x)
            loss = criterion(out, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}")

    os.makedirs("projects/edge-audio-classifier/models", exist_ok=True)
    torch.save(model.state_dict(), "projects/edge-audio-classifier/models/audio_classifier.pt")

if __name__ == "__main__":
    main()
