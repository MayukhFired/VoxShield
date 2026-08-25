"""Generate realistic demo audio samples for VoxShield presentation."""
import sys
sys.path.insert(0, '.')

import numpy as np
import soundfile as sf
import os
from scipy.signal import butter, filtfilt

os.makedirs('data/demo', exist_ok=True)
sr = 16000


# === GENERATE REALISTIC 'REAL' SPEECH-LIKE AUDIO ===
print("Generating realistic 'REAL' voice sample...")
duration = 4.0
t = np.linspace(0, duration, int(sr * duration))

# Base fundamental frequency with natural variation
f0 = 150 + 20 * np.sin(2 * np.pi * 5 * t) + 8 * np.sin(2 * np.pi * 0.7 * t) + np.random.randn(len(t)) * 3

# Generate harmonics (like real vocal cords)
signal = np.zeros_like(t)
for harmonic in range(1, 8):
    amplitude = 1.0 / (harmonic ** 1.2)
    phase = np.cumsum(2 * np.pi * f0 * harmonic / sr)
    signal += amplitude * np.sin(phase)

# Speech envelope with natural pauses
envelope = np.ones_like(t)
pause_starts = [int(0.8 * sr), int(1.9 * sr), int(3.1 * sr)]
pause_lengths = [int(0.15 * sr), int(0.2 * sr), int(0.12 * sr)]
for ps, pl in zip(pause_starts, pause_lengths):
    if ps + pl < len(envelope):
        envelope[ps:ps + pl] = 0.0
        # Add breath sound in pauses (natural)
        breath = 0.008 * np.random.randn(pl)
        signal[ps:ps + pl] = breath

signal = signal * envelope

# Add room ambience / mic noise
signal += 0.003 * np.random.randn(len(t))

# Normalize
signal = signal / (np.max(np.abs(signal)) + 1e-6) * 0.7
sf.write('data/demo/real_voice.wav', signal.astype(np.float32), sr)
print("  Created: data/demo/real_voice.wav")


# === GENERATE 'FAKE' TTS-LIKE AUDIO ===
print("Generating 'FAKE' TTS-like sample...")
t = np.linspace(0, duration, int(sr * duration))

# Very stable F0 (TTS has almost no jitter)
f0_fake = 160 + 2 * np.sin(2 * np.pi * 3 * t)

# Clean harmonics
signal_fake = np.zeros_like(t)
for harmonic in range(1, 6):
    amplitude = 1.0 / (harmonic ** 1.5)
    phase = np.cumsum(2 * np.pi * f0_fake * harmonic / sr)
    signal_fake += amplitude * np.sin(phase)

# Speech envelope with CLEAN silences (no breath, no noise)
envelope_fake = np.ones_like(t)
pause_starts_fake = [int(0.9 * sr), int(2.0 * sr), int(3.2 * sr)]
pause_lengths_fake = [int(0.18 * sr), int(0.22 * sr), int(0.15 * sr)]
for ps, pl in zip(pause_starts_fake, pause_lengths_fake):
    if ps + pl < len(envelope_fake):
        envelope_fake[ps:ps + pl] = 0.0
        signal_fake[ps:ps + pl] = 0.0  # Perfect silence

signal_fake = signal_fake * envelope_fake

# Sharp low-pass at 7kHz (neural vocoder cutoff artifact)
nyquist = sr / 2
cutoff = 7000 / nyquist
b, a = butter(8, cutoff, btype='low')
signal_fake = filtfilt(b, a, signal_fake)

# NO ambient noise (dead clean — synthetic giveaway)
signal_fake = signal_fake / (np.max(np.abs(signal_fake)) + 1e-6) * 0.7
sf.write('data/demo/fake_voice.wav', signal_fake.astype(np.float32), sr)
print("  Created: data/demo/fake_voice.wav")


# === GENERATE A SECOND FAKE (slightly different characteristics) ===
print("Generating second 'FAKE' sample (different voice)...")
t = np.linspace(0, duration, int(sr * duration))
f0_fake2 = 120 + 1.5 * np.sin(2 * np.pi * 2.5 * t)

signal_fake2 = np.zeros_like(t)
for harmonic in range(1, 7):
    amplitude = 1.0 / (harmonic ** 1.3)
    phase = np.cumsum(2 * np.pi * f0_fake2 * harmonic / sr)
    signal_fake2 += amplitude * np.sin(phase)

# Longer pauses, perfectly silent
envelope_fake2 = np.ones_like(t)
for ps in [int(1.0 * sr), int(2.5 * sr)]:
    pl = int(0.3 * sr)
    if ps + pl < len(envelope_fake2):
        envelope_fake2[ps:ps + pl] = 0.0
        signal_fake2[ps:ps + pl] = 0.0

signal_fake2 = signal_fake2 * envelope_fake2
b2, a2 = butter(6, 6500 / nyquist, btype='low')
signal_fake2 = filtfilt(b2, a2, signal_fake2)
signal_fake2 = signal_fake2 / (np.max(np.abs(signal_fake2)) + 1e-6) * 0.7
sf.write('data/demo/fake_voice_2.wav', signal_fake2.astype(np.float32), sr)
print("  Created: data/demo/fake_voice_2.wav")


# === TEST DETECTION ===
print("\n" + "=" * 50)
print("TESTING DETECTION ON DEMO SAMPLES")
print("=" * 50)

from ml.ensemble import EnsembleDetector
detector = EnsembleDetector()

for name, path in [("REAL VOICE", "data/demo/real_voice.wav"),
                   ("FAKE VOICE 1", "data/demo/fake_voice.wav"),
                   ("FAKE VOICE 2", "data/demo/fake_voice_2.wav")]:
    result = detector.analyze(path)
    v = result['verdict'].upper()
    c = result['confidence']
    passed = result['signal_summary']['checks_passed']
    total = result['signal_summary']['checks_total']
    print(f"\n{name}: {v} (confidence: {c:.1%}) — {passed}/{total} checks passed")
    for check in result['signal_checks']:
        status = "PASS" if check['passed'] else "FAIL"
        print(f"  [{status}] {check['check_name']}: {check['score']:.2f}")

print("\n" + "=" * 50)
print("DONE — Demo audio ready!")
print("=" * 50)
