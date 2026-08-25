"""
VoiceShield — Ensemble Detection Engine

Combines the AASIST deep learning model with signal-based acoustic checks
to produce a final weighted verdict with rich interpretable output.

Weights:
    - AASIST model: 60% (primary, highly accurate)
    - Signal checks: 40% (secondary, interpretable, catches edge cases)
"""

import os
import sys
import numpy as np
import librosa
from typing import Dict, Any, List

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ml.detector import VoiceAuthenticityDetector
from ml.signal_checks import run_all_checks


class EnsembleDetector:
    """
    Combines AASIST ML model + signal-based checks into a single
    detection pipeline with weighted scoring.
    """
    
    # Weight distribution
    AASIST_WEIGHT = 0.60
    SIGNAL_WEIGHT = 0.40
    
    # Individual signal check weights (must sum to 1.0)
    CHECK_WEIGHTS = {
        "pitch_stability": 0.30,
        "breath_presence": 0.20,
        "silence_naturalness": 0.25,
        "spectral_cutoff": 0.25,
    }
    
    def __init__(self):
        self.aasist_detector = VoiceAuthenticityDetector()
        self.sample_rate = 16000
    
    def analyze(self, audio_path: str) -> Dict[str, Any]:
        """
        Full analysis pipeline on an audio file.
        
        Returns a rich result including:
            - Final verdict (real/fake)
            - Overall confidence score
            - AASIST model prediction
            - Individual signal check results
            - Spectrogram data for visualization
        """
        # Step 1: Load audio
        try:
            audio, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)
        except Exception as e:
            return {
                "verdict": "error",
                "confidence": 0.0,
                "error": f"Failed to load audio: {str(e)}",
            }
        
        # Validate minimum duration
        duration = len(audio) / sr
        if duration < 0.5:
            return {
                "verdict": "error",
                "confidence": 0.0,
                "error": "Audio too short. Need at least 0.5 seconds of speech.",
            }
        
        # Step 2: Run AASIST model
        aasist_result = self.aasist_detector.predict(audio_path)
        
        # Step 3: Run signal-based checks
        signal_results = run_all_checks(audio, sr)
        
        # Step 4: Calculate weighted ensemble score
        # AASIST score: convert to "realness" score (1.0 = definitely real)
        if aasist_result["label"] in ("error", "neutral"):
            aasist_realness = 0.5  # Neutral if model fails or unavailable
            # When model is unavailable, rely 100% on signal checks
            aasist_weight = 0.0
            signal_weight = 1.0
        elif aasist_result["label"] == "real":
            aasist_realness = aasist_result["confidence"]
            aasist_weight = self.AASIST_WEIGHT
            signal_weight = self.SIGNAL_WEIGHT
        else:
            aasist_realness = 1.0 - aasist_result["confidence"]
            aasist_weight = self.AASIST_WEIGHT
            signal_weight = self.SIGNAL_WEIGHT
        
        # Signal checks combined score
        signal_combined = 0.0
        for check in signal_results:
            weight = self.CHECK_WEIGHTS.get(check["check_name"], 0.25)
            signal_combined += check["score"] * weight
        
        # Penalty: if majority of checks fail, reduce score further
        checks_failed = sum(1 for c in signal_results if not c["passed"])
        if checks_failed >= 3:
            signal_combined *= 0.6  # Strong penalty for multiple failures
        
        # Ensemble weighted score
        ensemble_score = (
            aasist_realness * aasist_weight +
            signal_combined * signal_weight
        )
        
        # Final verdict
        verdict = "real" if ensemble_score > 0.5 else "fake"
        confidence = abs(ensemble_score - 0.5) * 2  # Scale to 0-1 confidence
        confidence = round(min(1.0, max(0.0, confidence)), 4)
        
        # Step 5: Generate spectrogram data for frontend visualization
        spectrogram_data = self._generate_spectrogram(audio, sr)
        
        # Step 6: Count how many signal checks failed
        checks_failed = sum(1 for c in signal_results if not c["passed"])
        checks_total = len(signal_results)
        
        return {
            "verdict": verdict,
            "confidence": float(confidence),
            "ensemble_score": float(round(ensemble_score, 4)),
            "duration_seconds": float(round(duration, 2)),
            "model_result": {
                "label": aasist_result["label"],
                "confidence": float(aasist_result.get("confidence", 0.0)),
                "raw_scores": aasist_result.get("raw_scores", {}),
            },
            "signal_checks": signal_results,
            "signal_summary": {
                "checks_passed": int(checks_total - checks_failed),
                "checks_failed": int(checks_failed),
                "checks_total": int(checks_total),
                "combined_score": float(round(signal_combined, 4)),
            },
            "spectrogram": spectrogram_data,
        }
    
    def _generate_spectrogram(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """
        Generate mel-spectrogram data for frontend visualization.
        Returns a downsampled version suitable for rendering in the browser.
        """
        try:
            # Compute mel spectrogram
            mel_spec = librosa.feature.melspectrogram(
                y=audio, sr=sr, n_mels=64, n_fft=2048, hop_length=512
            )
            mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
            
            # Downsample time axis if too large (max 200 time frames for frontend)
            max_time_frames = 200
            if mel_spec_db.shape[1] > max_time_frames:
                step = mel_spec_db.shape[1] // max_time_frames
                mel_spec_db = mel_spec_db[:, ::step][:, :max_time_frames]
            
            # Normalize to 0-1 range for frontend color mapping
            spec_min = mel_spec_db.min()
            spec_max = mel_spec_db.max()
            if spec_max > spec_min:
                normalized = ((mel_spec_db - spec_min) / (spec_max - spec_min)).tolist()
            else:
                normalized = mel_spec_db.tolist()
            
            return {
                "data": normalized,
                "n_mels": int(mel_spec_db.shape[0]),
                "n_frames": int(mel_spec_db.shape[1]),
                "sr": int(sr),
            }
        
        except Exception:
            return {
                "data": [],
                "n_mels": 0,
                "n_frames": 0,
                "sr": sr,
            }
