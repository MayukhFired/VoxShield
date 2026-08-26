"""
VoxShield AI — SSL (Self-Supervised Learning) Anti-Spoofing Model

Uses wav2vec2-base as feature extractor + BiGRU + Multi-Head Attention classifier.
Based on koyelog/deepfake-voice-detector-sota (HuggingFace).

Architecture:
    - Wav2Vec2 encoder (facebook/wav2vec2-base) — pretrained speech features
    - Bidirectional GRU: 2 layers, 256 hidden units per direction (512 total)
    - Multi-Head Attention: 8 heads, 512-dimensional
    - Classification head: 512→512→128→1 (sigmoid output)

Input: 4-second audio clip at 16kHz
Output: probability of "fake" (0=real, 1=fake)
Accuracy: 95-97% on 822K+ samples from 19 datasets
"""

import os
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Any, Optional

# Model paths
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
SSL_MODEL_PATH = os.path.join(MODEL_DIR, "pytorch_model.pth")


class DeepfakeVoiceDetector(nn.Module):
    """
    BiGRU + Multi-Head Attention classifier on top of wav2vec2 features.
    Matches the architecture from koyelog/deepfake-voice-detector-sota.
    """

    def __init__(self, input_dim=768, hidden_dim=256, num_layers=2, num_heads=8, dropout=0.3):
        super().__init__()

        self.input_dim = input_dim  # wav2vec2-base output dimension

        # Bidirectional GRU
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0,
        )

        # Multi-Head Attention
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim * 2,  # bidirectional = 2x hidden
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
        )

        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 512),
            nn.ReLU(),
            nn.BatchNorm1d(512),
            nn.Dropout(0.4),
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
        )

    def forward(self, x):
        """
        Args:
            x: wav2vec2 features [batch, seq_len, 768]
        Returns:
            logits: [batch, 1]
        """
        # GRU
        gru_out, _ = self.gru(x)  # [batch, seq_len, 512]

        # Self-attention
        attn_out, _ = self.attention(gru_out, gru_out, gru_out)  # [batch, seq_len, 512]

        # Pool (mean over time)
        pooled = attn_out.mean(dim=1)  # [batch, 512]

        # Classify
        logits = self.classifier(pooled)  # [batch, 1]
        return logits


class SSLAntiSpoofingModel:
    """
    High-level wrapper that handles:
    - Loading wav2vec2 feature extractor
    - Loading the trained classifier
    - Running inference on audio files
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.feature_extractor = None
        self.wav2vec2_model = None
        self.classifier = None
        self._loaded = False
        self.sample_rate = 16000
        self.target_length = 4 * 16000  # 4 seconds

    def load(self) -> bool:
        """Load the feature extractor and classifier model."""
        if self._loaded:
            return True

        try:
            from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2Model

            # Load wav2vec2 feature extractor and model
            print("[INFO] Loading wav2vec2-base feature extractor...")
            self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained("facebook/wav2vec2-base")
            self.wav2vec2_model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base")
            self.wav2vec2_model.to(self.device)
            self.wav2vec2_model.eval()

            # Freeze wav2vec2 (we only use it as feature extractor)
            for param in self.wav2vec2_model.parameters():
                param.requires_grad = False

            # Load classifier
            self.classifier = DeepfakeVoiceDetector(input_dim=768)

            if os.path.exists(SSL_MODEL_PATH):
                print(f"[INFO] Loading trained classifier from {SSL_MODEL_PATH}...")
                state_dict = torch.load(SSL_MODEL_PATH, map_location=self.device)

                # Handle potential key mismatches
                try:
                    self.classifier.load_state_dict(state_dict, strict=False)
                    print("[INFO] SSL Anti-Spoofing model loaded successfully!")
                except Exception as e:
                    print(f"[WARNING] Partial weight loading: {e}")
                    # Try loading with key remapping
                    self._load_with_remap(state_dict)
            else:
                print(f"[WARNING] Model weights not found at {SSL_MODEL_PATH}")
                print(f"[INFO] Download from: https://huggingface.co/koyelog/deepfake-voice-detector-sota")
                print(f"[INFO] Place pytorch_model.pth in: {MODEL_DIR}")
                return False

            self.classifier.to(self.device)
            self.classifier.eval()
            self._loaded = True
            return True

        except ImportError:
            print("[WARNING] 'transformers' package not installed. Run: pip install transformers")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to load SSL model: {e}")
            return False

    def _load_with_remap(self, state_dict):
        """Attempt to load weights with key remapping for compatibility."""
        model_keys = set(self.classifier.state_dict().keys())
        loaded_keys = set(state_dict.keys())

        # Try direct subset loading
        compatible = {k: v for k, v in state_dict.items() if k in model_keys}
        if compatible:
            self.classifier.load_state_dict(compatible, strict=False)
            print(f"[INFO] Loaded {len(compatible)}/{len(model_keys)} weight tensors.")
        else:
            print("[WARNING] No compatible weights found. Using random initialization.")

    def predict(self, audio_path: str) -> Dict[str, Any]:
        """
        Run inference on an audio file.

        Returns:
            {
                "label": "real" | "fake",
                "confidence": float (0.0 to 1.0),
                "raw_score": float (probability of fake),
                "model_type": "ssl_wav2vec2"
            }
        """
        if not self._loaded:
            success = self.load()
            if not success:
                return {
                    "label": "neutral",
                    "confidence": 0.5,
                    "raw_score": 0.5,
                    "model_type": "ssl_wav2vec2",
                    "error": "Model not loaded"
                }

        try:
            import librosa

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

            # Extract features with wav2vec2
            inputs = self.feature_extractor(
                audio, sampling_rate=self.sample_rate, return_tensors="pt"
            )
            input_values = inputs.input_values.to(self.device)

            # Get wav2vec2 features
            with torch.no_grad():
                wav2vec_output = self.wav2vec2_model(input_values)
                features = wav2vec_output.last_hidden_state  # [1, seq_len, 768]

                # Run classifier
                logits = self.classifier(features)  # [1, 1]
                prob_fake = torch.sigmoid(logits).item()

            # Determine label
            label = "fake" if prob_fake >= 0.5 else "real"
            confidence = prob_fake if label == "fake" else (1 - prob_fake)

            return {
                "label": label,
                "confidence": round(confidence, 4),
                "raw_score": round(prob_fake, 4),
                "model_type": "ssl_wav2vec2",
            }

        except Exception as e:
            return {
                "label": "neutral",
                "confidence": 0.5,
                "raw_score": 0.5,
                "model_type": "ssl_wav2vec2",
                "error": str(e),
            }
