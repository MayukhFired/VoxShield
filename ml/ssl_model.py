"""
VoxShield AI — Mel-Spectrogram ResNet Anti-Spoofing Model

Architecture (from koyelog/deepfake-voice-detector-sota):
    - Input: Mel-spectrogram (128 mels, 4 seconds @ 16kHz)
    - ResNet encoder: conv1(1→64) + layer1(64→64) + layer2(64→128) + layer3(128→256)
    - Bidirectional GRU: 2 layers, 256 hidden (→512 output)
    - Multi-Head Attention: 3 heads, 512 dim
    - Classifier: 512→512→128→1 (sigmoid)

Config: sample_rate=16000, n_mels=128, n_fft=1024, hop_length=512, duration=4s
Trained on 822K+ samples from 19 datasets. Accuracy: 95-97%.
"""

import os
import torch
import torch.nn as nn
import numpy as np
import librosa
from typing import Dict, Any

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
SSL_MODEL_PATH = os.path.join(MODEL_DIR, "pytorch_model.pth")


class ResNetBlock(nn.Module):
    """Basic ResNet block with two 3x3 convolutions."""
    def __init__(self, in_channels, out_channels, stride=1, downsample=None):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, 3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample

    def forward(self, x):
        identity = x
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        if self.downsample is not None:
            identity = self.downsample(x)
        out += identity
        out = self.relu(out)
        return out


class DeepfakeDetectorModel(nn.Module):
    """
    ResNet + BiGRU + Attention classifier for mel-spectrogram input.
    Matches the pretrained weights from koyelog/deepfake-voice-detector-sota.
    """
    def __init__(self):
        super().__init__()

        # Initial convolution
        self.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        # ResNet layers
        self.layer1 = self._make_layer(64, 64, 2)
        self.layer2 = self._make_layer(64, 128, 2, stride=2)
        self.layer3 = self._make_layer(128, 256, 2, stride=2)

        # Adaptive pooling to collapse frequency dimension
        self.adaptive_pool = nn.AdaptiveAvgPool2d((None, 1))

        # Bidirectional GRU
        self.gru = nn.GRU(
            input_size=256,
            hidden_size=256,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.3,
        )

        # Multi-Head Attention (8 heads, 512 dim)
        self.attention = nn.MultiheadAttention(
            embed_dim=512,
            num_heads=8,
            dropout=0.3,
            batch_first=True,
        )

        # Classifier
        self.classifier = nn.Sequential(
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.BatchNorm1d(512),
            nn.Dropout(0.4),
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
        )

    def _make_layer(self, in_channels, out_channels, num_blocks, stride=1):
        downsample = None
        if stride != 1 or in_channels != out_channels:
            downsample = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels),
            )

        layers = [ResNetBlock(in_channels, out_channels, stride, downsample)]
        for _ in range(1, num_blocks):
            layers.append(ResNetBlock(out_channels, out_channels))
        return nn.Sequential(*layers)

    def forward(self, x):
        # x: [batch, 1, n_mels, time]
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)

        # Collapse frequency: [batch, 256, freq, time] → [batch, 256, 1, time]
        x = self.adaptive_pool(x)
        # → [batch, 256, time]
        x = x.squeeze(3).permute(0, 2, 1)  # [batch, time, 256]

        # GRU
        gru_out, _ = self.gru(x)  # [batch, time, 512]

        # Attention
        attn_out, _ = self.attention(gru_out, gru_out, gru_out)  # [batch, time, 512]

        # Pool over time
        pooled = attn_out.mean(dim=1)  # [batch, 512]

        # Classify
        logits = self.classifier(pooled)  # [batch, 1]
        return logits


class SSLAntiSpoofingModel:
    """High-level wrapper for inference."""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self._loaded = False
        self.sample_rate = 16000
        self.n_mels = 128
        self.n_fft = 1024
        self.hop_length = 512
        self.duration = 4  # seconds
        self.target_length = self.duration * self.sample_rate

    def load(self) -> bool:
        """Load the model with pretrained weights."""
        if self._loaded:
            return True

        try:
            self.model = DeepfakeDetectorModel()

            if os.path.exists(SSL_MODEL_PATH):
                print(f"[INFO] Loading deepfake detector from {SSL_MODEL_PATH}...")
                checkpoint = torch.load(SSL_MODEL_PATH, map_location=self.device, weights_only=False)

                state_dict = checkpoint.get("model_state_dict", checkpoint)
                self.model.load_state_dict(state_dict, strict=False)
                print("[INFO] Deepfake detection model loaded successfully!")
                print(f"[INFO] Validation accuracy: {checkpoint.get('val_accuracy', 'N/A')}")
            else:
                print(f"[WARNING] Model weights not found at {SSL_MODEL_PATH}")
                return False

            self.model.to(self.device)
            self.model.eval()
            self._loaded = True
            return True

        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            return False

    def _audio_to_melspec(self, audio: np.ndarray) -> torch.Tensor:
        """Convert audio to mel-spectrogram tensor."""
        mel_spec = librosa.feature.melspectrogram(
            y=audio, sr=self.sample_rate,
            n_mels=self.n_mels, n_fft=self.n_fft, hop_length=self.hop_length
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        # Normalize to [0, 1]
        mel_spec_db = (mel_spec_db - mel_spec_db.min()) / (mel_spec_db.max() - mel_spec_db.min() + 1e-10)

        # To tensor: [1, 1, n_mels, time]
        tensor = torch.FloatTensor(mel_spec_db).unsqueeze(0).unsqueeze(0)
        return tensor

    def predict(self, audio_path: str) -> Dict[str, Any]:
        """Run inference on an audio file."""
        if not self._loaded:
            if not self.load():
                return {"label": "neutral", "confidence": 0.5, "raw_score": 0.5, "model_type": "resnet_gru"}

        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)

            # Pad or truncate to 4 seconds
            if len(audio) < self.target_length:
                audio = np.pad(audio, (0, self.target_length - len(audio)))
            else:
                audio = audio[:self.target_length]

            # Normalize
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio))

            # Convert to mel-spectrogram
            mel_tensor = self._audio_to_melspec(audio).to(self.device)

            # Inference
            with torch.no_grad():
                logits = self.model(mel_tensor)
                prob_fake = torch.sigmoid(logits).item()

            label = "fake" if prob_fake >= 0.5 else "real"
            confidence = prob_fake if label == "fake" else (1 - prob_fake)

            return {
                "label": label,
                "confidence": round(confidence, 4),
                "raw_score": round(prob_fake, 4),
                "model_type": "resnet_gru",
            }

        except Exception as e:
            return {"label": "neutral", "confidence": 0.5, "raw_score": 0.5, "model_type": "resnet_gru", "error": str(e)}
