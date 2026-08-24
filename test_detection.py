"""Quick test script to verify the full detection pipeline works."""
import sys
sys.path.insert(0, '.')

import numpy as np
import soundfile as sf
import os

os.makedirs('data/test_pairs', exist_ok=True)

# Generate a 3-second synthetic-like audio (pure tone, no noise, no breath)
sr = 16000
t = np.linspace(0, 3, sr * 3)
synthetic_audio = 0.5 * np.sin(2 * np.pi * 220 * t)
# Add mathematically perfect silence in the middle (no noise floor)
synthetic_audio[sr:sr + int(0.3 * sr)] = 0.0
sf.write('data/test_pairs/test_synthetic.wav', synthetic_audio, sr)

# Generate a 3-second real-like audio (noise, pitch variation, breath-like sounds)
real_audio = 0.3 * np.sin(2 * np.pi * 220 * t)
# Add natural noise floor
real_audio += 0.02 * np.random.randn(len(t))
# Add pitch variation (frequency modulation)
real_audio += 0.1 * np.sin(2 * np.pi * (220 + 10 * np.sin(2 * np.pi * 5 * t)) * t)
# Add breath-like noise in a pause
pause_start = sr
pause_end = sr + int(0.3 * sr)
real_audio[pause_start:pause_end] = 0.005 * np.random.randn(pause_end - pause_start)
sf.write('data/test_pairs/test_real.wav', real_audio, sr)

print("Test audio files created successfully!")
print(f"  - data/test_pairs/test_synthetic.wav (pure tone, no noise)")
print(f"  - data/test_pairs/test_real.wav (with noise, variation, breath)")

# Run detection
from ml.ensemble import EnsembleDetector
detector = EnsembleDetector()

print("\n" + "=" * 50)
print("ANALYZING SYNTHETIC TEST AUDIO")
print("=" * 50)
result = detector.analyze('data/test_pairs/test_synthetic.wav')
print(f"Verdict: {result['verdict'].upper()} | Confidence: {result['confidence']:.1%}")
print(f"Ensemble score: {result['ensemble_score']:.4f}")
print(f"\nSignal checks ({result['signal_summary']['checks_passed']}/{result['signal_summary']['checks_total']} passed):")
for check in result['signal_checks']:
    status = "PASS" if check['passed'] else "FAIL"
    print(f"  [{status}] {check['check_name']}: {check['score']:.2f} - {check['detail']}")

print("\n" + "=" * 50)
print("ANALYZING REAL-LIKE TEST AUDIO")
print("=" * 50)
result2 = detector.analyze('data/test_pairs/test_real.wav')
print(f"Verdict: {result2['verdict'].upper()} | Confidence: {result2['confidence']:.1%}")
print(f"Ensemble score: {result2['ensemble_score']:.4f}")
print(f"\nSignal checks ({result2['signal_summary']['checks_passed']}/{result2['signal_summary']['checks_total']} passed):")
for check in result2['signal_checks']:
    status = "PASS" if check['passed'] else "FAIL"
    print(f"  [{status}] {check['check_name']}: {check['score']:.2f} - {check['detail']}")

print("\n" + "=" * 50)
print("TEST COMPLETE - Pipeline is working!")
print("=" * 50)
