"""
VoiceShield — Signal-Based Acoustic Analysis

Secondary detection layer using rule-based acoustic analysis.
These checks look for physical/digital artifacts that synthetic voices
commonly exhibit, providing interpretable signals alongside the ML model.

Each check returns:
    {
        "check_name": str,
        "passed": bool,  # True = looks natural/real
        "score": float,  # 0.0 (definitely synthetic) to 1.0 (definitely real)
        "detail": str    # Human-readable explanation
    }
"""

import numpy as np
import librosa
from typing import Dict, Any, List


def check_pitch_stability(audio: np.ndarray, sr: int = 16000) -> Dict[str, Any]:
    """
    Check if pitch variation is unnaturally stable.
    
    Real voices have natural micro-variations in pitch (jitter).
    Synthetic voices often have unnaturally smooth, stable pitch contours.
    
    Measures: coefficient of variation of F0, jitter (pitch perturbation).
    """
    try:
        # Extract F0 using pyin (probabilistic YIN)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio, fmin=50, fmax=500, sr=sr, frame_length=2048
        )
        
        # Filter to only voiced frames
        voiced_f0 = f0[voiced_flag]
        
        if len(voiced_f0) < 10:
            return {
                "check_name": "pitch_stability",
                "passed": True,
                "score": 0.5,
                "detail": "Insufficient voiced frames for analysis"
            }
        
        # Calculate coefficient of variation (CV) of F0
        cv = np.std(voiced_f0) / np.mean(voiced_f0) if np.mean(voiced_f0) > 0 else 0
        
        # Calculate jitter (average absolute difference between consecutive periods)
        diffs = np.abs(np.diff(voiced_f0))
        jitter = np.mean(diffs) / np.mean(voiced_f0) if np.mean(voiced_f0) > 0 else 0
        
        # Natural speech typically has CV > 0.05 and jitter > 0.005
        # Synthetic speech tends to have very low CV and jitter
        pitch_natural = cv > 0.03 and jitter > 0.003
        
        # Score: higher = more natural
        score = min(1.0, (cv / 0.1) * 0.5 + (jitter / 0.01) * 0.5)
        score = max(0.0, min(1.0, score))
        
        detail = f"Pitch CV: {cv:.4f}, Jitter: {jitter:.4f}. "
        if pitch_natural:
            detail += "Natural pitch variation detected."
        else:
            detail += "Unnaturally stable pitch — possible synthetic voice."
        
        return {
            "check_name": "pitch_stability",
            "passed": bool(pitch_natural),
            "score": float(round(score, 4)),
            "detail": detail
        }
    
    except Exception as e:
        return {
            "check_name": "pitch_stability",
            "passed": True,
            "score": 0.5,
            "detail": f"Analysis error: {str(e)}"
        }


def check_breath_presence(audio: np.ndarray, sr: int = 16000) -> Dict[str, Any]:
    """
    Check for the presence of natural micro-breaths in speech pauses.
    
    Real speech contains subtle inhalation/exhalation sounds between phrases.
    Synthetic voices often have completely clean pauses with no breath energy.
    """
    try:
        # Compute short-time energy
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop
        
        energy = np.array([
            np.sum(audio[i:i + frame_length] ** 2)
            for i in range(0, len(audio) - frame_length, hop_length)
        ])
        
        if len(energy) == 0:
            return {
                "check_name": "breath_presence",
                "passed": True,
                "score": 0.5,
                "detail": "Audio too short for breath analysis"
            }
        
        # Normalize energy
        energy = energy / (np.max(energy) + 1e-10)
        
        # Find low-energy regions (potential pauses)
        threshold = 0.05
        low_energy_mask = energy < threshold
        
        # Look for breath-like energy in low regions
        # Breaths have low but non-zero energy (typically 0.001 to 0.03 of max)
        breath_threshold_low = 0.001
        breath_threshold_high = 0.03
        
        breath_regions = np.logical_and(
            energy > breath_threshold_low,
            energy < breath_threshold_high
        )
        
        # Count frames that look like breaths vs total pause frames
        total_pause_frames = np.sum(low_energy_mask)
        breath_frames = np.sum(np.logical_and(breath_regions, low_energy_mask))
        
        if total_pause_frames < 5:
            return {
                "check_name": "breath_presence",
                "passed": True,
                "score": 0.5,
                "detail": "No significant pauses found in audio"
            }
        
        breath_ratio = breath_frames / total_pause_frames
        
        # Natural speech typically has breath_ratio > 0.1
        has_breaths = breath_ratio > 0.08
        score = min(1.0, breath_ratio / 0.2)
        
        detail = f"Breath ratio in pauses: {breath_ratio:.3f}. "
        if has_breaths:
            detail += "Natural breathing patterns detected."
        else:
            detail += "Very clean pauses — missing natural breath sounds."
        
        return {
            "check_name": "breath_presence",
            "passed": bool(has_breaths),
            "score": float(round(score, 4)),
            "detail": detail
        }
    
    except Exception as e:
        return {
            "check_name": "breath_presence",
            "passed": True,
            "score": 0.5,
            "detail": f"Analysis error: {str(e)}"
        }


def check_silence_naturalness(audio: np.ndarray, sr: int = 16000) -> Dict[str, Any]:
    """
    Check if silent regions contain natural ambient noise floor.
    
    Real recordings always have some ambient noise (room tone, microphone hiss).
    Synthetic audio often has mathematically perfect silence (exact zeros) in pauses.
    """
    try:
        # Find silent/quiet regions
        frame_length = int(0.025 * sr)
        hop_length = int(0.010 * sr)
        
        # Use RMS energy per frame
        rms = np.array([
            np.sqrt(np.mean(audio[i:i + frame_length] ** 2))
            for i in range(0, len(audio) - frame_length, hop_length)
        ])
        
        if len(rms) == 0:
            return {
                "check_name": "silence_naturalness",
                "passed": True,
                "score": 0.5,
                "detail": "Audio too short for silence analysis"
            }
        
        # Find frames below 5% of max RMS (quiet regions)
        quiet_threshold = 0.05 * np.max(rms)
        quiet_frames_idx = np.where(rms < quiet_threshold)[0]
        
        if len(quiet_frames_idx) < 3:
            return {
                "check_name": "silence_naturalness",
                "passed": True,
                "score": 0.5,
                "detail": "No quiet regions found for analysis"
            }
        
        # Extract the actual samples from quiet regions
        quiet_samples = []
        for idx in quiet_frames_idx[:20]:  # Check up to 20 quiet frames
            start = idx * hop_length
            end = start + frame_length
            if end <= len(audio):
                quiet_samples.extend(audio[start:end].tolist())
        
        quiet_samples = np.array(quiet_samples)
        
        # Check for mathematical silence (exact zeros or near-zeros)
        zero_ratio = np.mean(np.abs(quiet_samples) < 1e-7)
        
        # Check noise floor variance (real recordings have non-zero variance)
        noise_floor_std = np.std(quiet_samples)
        
        # Natural recordings: zero_ratio < 0.5 and noise_floor_std > 1e-5
        is_natural = zero_ratio < 0.4 and noise_floor_std > 1e-5
        
        # Score
        score = (1.0 - zero_ratio) * 0.5 + min(1.0, noise_floor_std / 0.001) * 0.5
        score = max(0.0, min(1.0, score))
        
        detail = f"Zero-sample ratio: {zero_ratio:.3f}, Noise floor std: {noise_floor_std:.6f}. "
        if is_natural:
            detail += "Natural ambient noise detected in quiet regions."
        else:
            detail += "Mathematically clean silence — indicative of synthetic generation."
        
        return {
            "check_name": "silence_naturalness",
            "passed": bool(is_natural),
            "score": float(round(score, 4)),
            "detail": detail
        }
    
    except Exception as e:
        return {
            "check_name": "silence_naturalness",
            "passed": True,
            "score": 0.5,
            "detail": f"Analysis error: {str(e)}"
        }


def check_spectral_cutoff(audio: np.ndarray, sr: int = 16000) -> Dict[str, Any]:
    """
    Check for abrupt high-frequency spectral cutoff.
    
    Neural vocoders (used in voice cloning) often produce audio with a
    sharp cutoff in the high-frequency spectrum, typically around 7-8 kHz.
    Real speech has a more gradual rolloff extending to the Nyquist frequency.
    """
    try:
        # Compute spectrogram
        n_fft = 2048
        hop_length = 512
        
        stft = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
        magnitude = np.abs(stft)
        
        # Average across time to get mean spectral envelope
        mean_spectrum = np.mean(magnitude, axis=1)
        
        # Convert to dB
        mean_spectrum_db = librosa.amplitude_to_db(mean_spectrum + 1e-10)
        
        # Frequency bins
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
        
        # Check energy in high-frequency bands (6-8 kHz) vs mid-frequency (2-4 kHz)
        mid_band = np.logical_and(freqs >= 2000, freqs <= 4000)
        high_band = np.logical_and(freqs >= 6000, freqs <= 7500)
        very_high_band = freqs >= 7500
        
        mid_energy = np.mean(mean_spectrum_db[mid_band]) if np.any(mid_band) else -60
        high_energy = np.mean(mean_spectrum_db[high_band]) if np.any(high_band) else -60
        very_high_energy = np.mean(mean_spectrum_db[very_high_band]) if np.any(very_high_band) else -60
        
        # Calculate dropoff rate
        dropoff_mid_to_high = mid_energy - high_energy
        dropoff_high_to_very_high = high_energy - very_high_energy
        
        # Natural speech: gradual rolloff (dropoff < 30dB between bands)
        # Synthetic: sharp cutoff (dropoff > 20dB in high bands)
        is_natural = dropoff_mid_to_high < 30 and dropoff_high_to_very_high < 20
        
        # Score
        score = 1.0 - min(1.0, max(0.0, (dropoff_high_to_very_high - 10) / 30))
        
        detail = f"Spectral dropoff mid→high: {dropoff_mid_to_high:.1f}dB, high→very_high: {dropoff_high_to_very_high:.1f}dB. "
        if is_natural:
            detail += "Gradual spectral rolloff — consistent with natural speech."
        else:
            detail += "Sharp high-frequency cutoff detected — common in neural vocoders."
        
        return {
            "check_name": "spectral_cutoff",
            "passed": bool(is_natural),
            "score": float(round(score, 4)),
            "detail": detail
        }
    
    except Exception as e:
        return {
            "check_name": "spectral_cutoff",
            "passed": True,
            "score": 0.5,
            "detail": f"Analysis error: {str(e)}"
        }


def run_all_checks(audio: np.ndarray, sr: int = 16000) -> List[Dict[str, Any]]:
    """Run all signal-based checks on an audio sample."""
    return [
        check_pitch_stability(audio, sr),
        check_breath_presence(audio, sr),
        check_silence_naturalness(audio, sr),
        check_spectral_cutoff(audio, sr),
    ]
