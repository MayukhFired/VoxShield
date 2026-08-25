"""
VoxShield AI — Voice De-Cloaking Engine

Extracts the scammer's REAL voice fingerprint from cloned/converted audio.

Theory: Voice conversion systems transform the spectral envelope to match a target
speaker, but they cannot fully erase the source speaker's characteristics:
  - Vocal tract length (formant spacing ratios) partially survives conversion
  - Temporal dynamics (speaking rhythm, transition patterns) are source-dependent
  - Residual pitch patterns (micro-prosody) leak through most VC systems
  - Low-level excitation characteristics persist despite spectral transformation

This module extracts these "residual" features to create a voiceprint of the
ACTUAL person behind the cloned voice — enabling cross-case identification.

Reference: TRIDENT (arxiv 2607.23650, July 2025) — achieves 90.99% source
speaker identification accuracy against 7 state-of-the-art VC methods.
"""

import numpy as np
import librosa
import hashlib
from typing import Dict, Any, List, Optional
from scipy.signal import lfilter


class VoiceprintExtractor:
    """
    Extracts a multi-dimensional voiceprint fingerprint from audio.
    Designed to capture source-speaker characteristics that survive
    voice conversion/cloning transformations.
    """

    def __init__(self, sr: int = 16000):
        self.sr = sr
        # Fingerprint vector dimension
        self.fingerprint_dim = 128

    def extract(self, audio: np.ndarray) -> Dict[str, Any]:
        """
        Extract full voiceprint from audio.

        Returns:
            {
                "fingerprint_vector": list[float],  # 128-dim embedding
                "fingerprint_hash": str,            # SHA-256 hash for fast matching
                "features": {                       # Individual feature groups
                    "temporal_dynamics": [...],
                    "residual_pitch": [...],
                    "formant_ratios": [...],
                    "excitation_features": [...],
                    "spectral_residual": [...]
                },
                "confidence": float  # How reliable this fingerprint is
            }
        """
        if len(audio) < self.sr * 0.5:
            return self._empty_result("Audio too short for voiceprint extraction")

        # Normalize
        audio = audio / (np.max(np.abs(audio)) + 1e-10)

        # Extract 5 feature groups that survive voice conversion
        temporal = self._extract_temporal_dynamics(audio)
        pitch_residual = self._extract_residual_pitch(audio)
        formants = self._extract_formant_ratios(audio)
        excitation = self._extract_excitation_features(audio)
        spectral_res = self._extract_spectral_residual(audio)

        # Combine into fingerprint vector
        raw_features = np.concatenate([
            temporal,       # 24 dims
            pitch_residual, # 32 dims
            formants,       # 24 dims
            excitation,     # 24 dims
            spectral_res,   # 24 dims
        ])

        # Normalize to unit vector (for cosine similarity matching)
        fingerprint = raw_features[:self.fingerprint_dim]
        norm = np.linalg.norm(fingerprint)
        if norm > 0:
            fingerprint = fingerprint / norm

        fingerprint_list = [float(x) for x in fingerprint]

        # Generate hash for fast database matching
        fp_hash = self._generate_hash(fingerprint_list)

        # Calculate extraction confidence based on audio quality
        confidence = self._estimate_confidence(audio, temporal, pitch_residual)

        return {
            "fingerprint_vector": fingerprint_list,
            "fingerprint_hash": fp_hash,
            "features": {
                "temporal_dynamics": [float(x) for x in temporal[:8]],
                "residual_pitch": [float(x) for x in pitch_residual[:8]],
                "formant_ratios": [float(x) for x in formants[:8]],
                "excitation_features": [float(x) for x in excitation[:8]],
                "spectral_residual": [float(x) for x in spectral_res[:8]],
            },
            "confidence": float(confidence),
        }

    def compare(self, fp1: List[float], fp2: List[float]) -> float:
        """
        Compare two fingerprint vectors using cosine similarity.
        Returns: similarity score 0.0 (different person) to 1.0 (same person)
        """
        v1 = np.array(fp1)
        v2 = np.array(fp2)

        # Ensure same length
        min_len = min(len(v1), len(v2))
        v1 = v1[:min_len]
        v2 = v2[:min_len]

        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot / (norm1 * norm2)
        # Clamp to [0, 1]
        return float(max(0.0, min(1.0, (similarity + 1) / 2)))

    # ========================
    # FEATURE EXTRACTION
    # ========================

    def _extract_temporal_dynamics(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract speaking rhythm and temporal patterns.
        These reflect the source speaker's habitual timing, which VC doesn't alter.
        - Speech rate patterns
        - Pause duration distributions
        - Energy contour dynamics
        """
        frame_length = int(0.025 * self.sr)
        hop_length = int(0.010 * self.sr)

        # Energy contour
        energy = np.array([
            np.sqrt(np.mean(audio[i:i + frame_length] ** 2))
            for i in range(0, len(audio) - frame_length, hop_length)
        ])

        if len(energy) < 10:
            return np.zeros(24)

        # Temporal features
        features = []

        # Energy statistics
        features.append(np.mean(energy))
        features.append(np.std(energy))
        features.append(np.median(energy))

        # Energy delta (rate of change)
        delta_energy = np.diff(energy)
        features.append(np.mean(np.abs(delta_energy)))
        features.append(np.std(delta_energy))

        # Speech/silence ratio
        threshold = np.mean(energy) * 0.3
        speech_frames = np.sum(energy > threshold)
        features.append(speech_frames / len(energy))

        # Pause analysis
        is_silence = energy < threshold
        pause_lengths = []
        current_pause = 0
        for s in is_silence:
            if s:
                current_pause += 1
            else:
                if current_pause > 0:
                    pause_lengths.append(current_pause)
                current_pause = 0

        if pause_lengths:
            features.append(np.mean(pause_lengths))
            features.append(np.std(pause_lengths))
            features.append(len(pause_lengths))
        else:
            features.extend([0, 0, 0])

        # Energy autocorrelation (rhythm patterns)
        if len(energy) > 50:
            autocorr = np.correlate(energy[:200], energy[:200], mode='full')
            autocorr = autocorr[len(autocorr) // 2:]
            autocorr = autocorr / (autocorr[0] + 1e-10)
            features.extend(autocorr[1:16].tolist())
        else:
            features.extend([0] * 15)

        result = np.array(features[:24])
        if len(result) < 24:
            result = np.pad(result, (0, 24 - len(result)))
        return result

    def _extract_residual_pitch(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract micro-prosody patterns that leak through voice conversion.
        VC systems modify the mean pitch but don't perfectly transform the
        micro-level pitch dynamics of the source speaker.
        """
        # Extract F0
        f0, voiced_flag, _ = librosa.pyin(
            audio, fmin=50, fmax=500, sr=self.sr, frame_length=2048
        )

        voiced_f0 = f0[voiced_flag] if voiced_flag is not None else f0[~np.isnan(f0)]

        if len(voiced_f0) < 10:
            return np.zeros(32)

        features = []

        # Pitch statistics (relative, not absolute — survives VC)
        mean_f0 = np.mean(voiced_f0)
        features.append(np.std(voiced_f0) / (mean_f0 + 1e-10))  # Coefficient of variation
        features.append(np.median(voiced_f0) / (mean_f0 + 1e-10))

        # Pitch delta patterns (how pitch changes — speaker-specific)
        pitch_delta = np.diff(voiced_f0)
        features.append(np.mean(np.abs(pitch_delta)) / (mean_f0 + 1e-10))
        features.append(np.std(pitch_delta) / (mean_f0 + 1e-10))

        # Pitch acceleration (second derivative)
        if len(pitch_delta) > 2:
            pitch_accel = np.diff(pitch_delta)
            features.append(np.mean(np.abs(pitch_accel)) / (mean_f0 + 1e-10))
            features.append(np.std(pitch_accel) / (mean_f0 + 1e-10))
        else:
            features.extend([0, 0])

        # Pitch range ratio
        features.append((np.max(voiced_f0) - np.min(voiced_f0)) / (mean_f0 + 1e-10))

        # Jitter and shimmer (micro-perturbation — source speaker dependent)
        diffs = np.abs(np.diff(voiced_f0))
        jitter = np.mean(diffs) / (mean_f0 + 1e-10)
        features.append(jitter)

        # Pitch contour autocorrelation (speaking style fingerprint)
        if len(voiced_f0) > 30:
            normalized_f0 = (voiced_f0 - mean_f0) / (np.std(voiced_f0) + 1e-10)
            autocorr = np.correlate(normalized_f0[:100], normalized_f0[:100], mode='full')
            autocorr = autocorr[len(autocorr) // 2:]
            autocorr = autocorr / (autocorr[0] + 1e-10)
            features.extend(autocorr[1:25].tolist())
        else:
            features.extend([0] * 24)

        result = np.array(features[:32])
        if len(result) < 32:
            result = np.pad(result, (0, 32 - len(result)))
        return result

    def _extract_formant_ratios(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract formant frequency ratios.
        Absolute formants change with VC, but RATIOS between formants
        partially reflect vocal tract geometry of the source speaker.
        """
        # LPC analysis for formant estimation
        frame_length = int(0.030 * self.sr)
        hop_length = int(0.015 * self.sr)
        lpc_order = 12

        formant_ratios_all = []

        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i + frame_length]

            # Pre-emphasis
            frame = np.append(frame[0], frame[1:] - 0.97 * frame[:-1])

            # Window
            frame = frame * np.hamming(len(frame))

            # LPC
            try:
                a = librosa.lpc(frame, order=lpc_order)
                # Find roots (formant candidates)
                roots = np.roots(a)
                roots = roots[np.imag(roots) >= 0]

                # Convert to frequencies
                angles = np.arctan2(np.imag(roots), np.real(roots))
                freqs = sorted(angles * (self.sr / (2 * np.pi)))
                freqs = [f for f in freqs if 90 < f < 5000]

                if len(freqs) >= 3:
                    # Formant ratios (relative, not absolute)
                    f1, f2, f3 = freqs[0], freqs[1], freqs[2]
                    formant_ratios_all.append([
                        f2 / (f1 + 1e-10),
                        f3 / (f1 + 1e-10),
                        f3 / (f2 + 1e-10),
                        (f2 - f1) / (f3 - f1 + 1e-10),
                    ])
            except Exception:
                continue

        if not formant_ratios_all:
            return np.zeros(24)

        ratios = np.array(formant_ratios_all)

        features = []
        # Statistics of formant ratios across frames
        for col in range(min(4, ratios.shape[1])):
            col_data = ratios[:, col]
            features.append(np.mean(col_data))
            features.append(np.std(col_data))
            features.append(np.median(col_data))
            features.append(np.percentile(col_data, 75) - np.percentile(col_data, 25))

        # Formant transition patterns
        if ratios.shape[0] > 5:
            for col in range(min(4, ratios.shape[1])):
                delta = np.diff(ratios[:, col])
                features.append(np.mean(np.abs(delta)))
                features.append(np.std(delta))
        else:
            features.extend([0] * 8)

        result = np.array(features[:24])
        if len(result) < 24:
            result = np.pad(result, (0, 24 - len(result)))
        return result

    def _extract_excitation_features(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract glottal excitation characteristics.
        The glottal pulse shape is source-speaker specific and partially
        survives voice conversion (especially in analysis-synthesis VC).
        """
        features = []

        # Spectral tilt (relates to glottal open quotient)
        n_fft = 2048
        hop = 512
        S = np.abs(librosa.stft(audio, n_fft=n_fft, hop_length=hop))
        S_db = librosa.amplitude_to_db(S + 1e-10)

        # Average spectrum
        mean_spectrum = np.mean(S_db, axis=1)
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=n_fft)

        # Spectral tilt via linear regression on log spectrum
        valid = freqs > 50
        if np.sum(valid) > 10:
            x = np.log(freqs[valid] + 1)
            y = mean_spectrum[valid]
            slope = np.polyfit(x, y, 1)[0]
            features.append(slope)
        else:
            features.append(0)

        # Harmonic-to-noise ratio (source excitation quality)
        try:
            harmonic, percussive = librosa.effects.hpss(audio)
            hnr = np.mean(harmonic ** 2) / (np.mean(percussive ** 2) + 1e-10)
            features.append(np.log(hnr + 1e-10))
        except Exception:
            features.append(0)

        # Zero crossing rate statistics (glottal characteristics)
        zcr = librosa.feature.zero_crossing_rate(audio, frame_length=2048, hop_length=512)[0]
        features.append(np.mean(zcr))
        features.append(np.std(zcr))
        features.append(np.median(zcr))

        # Spectral centroid dynamics
        centroid = librosa.feature.spectral_centroid(y=audio, sr=self.sr, n_fft=2048, hop_length=512)[0]
        features.append(np.mean(centroid) / self.sr)
        features.append(np.std(centroid) / self.sr)

        # Spectral rolloff
        rolloff = librosa.feature.spectral_rolloff(y=audio, sr=self.sr, n_fft=2048, hop_length=512)[0]
        features.append(np.mean(rolloff) / self.sr)
        features.append(np.std(rolloff) / self.sr)

        # Spectral bandwidth
        bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=self.sr, n_fft=2048, hop_length=512)[0]
        features.append(np.mean(bandwidth) / self.sr)
        features.append(np.std(bandwidth) / self.sr)

        # MFCC delta statistics (speaker rhythm in spectral space)
        mfccs = librosa.feature.mfcc(y=audio, sr=self.sr, n_mfcc=13, n_fft=2048, hop_length=512)
        mfcc_delta = librosa.feature.delta(mfccs)
        for i in range(min(13, mfcc_delta.shape[0])):
            features.append(np.mean(mfcc_delta[i]))

        result = np.array(features[:24])
        if len(result) < 24:
            result = np.pad(result, (0, 24 - len(result)))
        return result

    def _extract_spectral_residual(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract residual spectral features after removing dominant spectral envelope.
        The residual contains source-speaker information that VC doesn't fully mask.
        """
        # Compute MFCCs (captures vocal tract shape)
        mfccs = librosa.feature.mfcc(y=audio, sr=self.sr, n_mfcc=20, n_fft=2048, hop_length=512)

        features = []

        # Higher-order MFCCs (less affected by VC spectral warping)
        for i in range(8, 20):
            features.append(float(np.mean(mfccs[i])))
            features.append(float(np.std(mfccs[i])))

        result = np.array(features[:24])
        if len(result) < 24:
            result = np.pad(result, (0, 24 - len(result)))
        return result

    # ========================
    # UTILITIES
    # ========================

    def _generate_hash(self, fingerprint: List[float]) -> str:
        """Generate a SHA-256 hash from the fingerprint for fast DB matching."""
        # Quantize to reduce noise sensitivity
        quantized = [round(x, 3) for x in fingerprint]
        data = str(quantized).encode()
        return hashlib.sha256(data).hexdigest()[:16]

    def _estimate_confidence(self, audio: np.ndarray, temporal: np.ndarray, pitch: np.ndarray) -> float:
        """Estimate how reliable the extracted voiceprint is."""
        confidence = 0.5

        # Longer audio = more reliable
        duration = len(audio) / self.sr
        if duration > 3:
            confidence += 0.2
        elif duration > 1.5:
            confidence += 0.1

        # Non-zero features = better extraction
        non_zero_temporal = np.sum(np.abs(temporal) > 1e-6) / len(temporal)
        non_zero_pitch = np.sum(np.abs(pitch) > 1e-6) / len(pitch)
        confidence += non_zero_temporal * 0.15
        confidence += non_zero_pitch * 0.15

        return min(1.0, confidence)

    def _empty_result(self, reason: str) -> Dict[str, Any]:
        return {
            "fingerprint_vector": [0.0] * self.fingerprint_dim,
            "fingerprint_hash": "0" * 16,
            "features": {
                "temporal_dynamics": [0.0] * 8,
                "residual_pitch": [0.0] * 8,
                "formant_ratios": [0.0] * 8,
                "excitation_features": [0.0] * 8,
                "spectral_residual": [0.0] * 8,
            },
            "confidence": 0.0,
            "error": reason,
        }
