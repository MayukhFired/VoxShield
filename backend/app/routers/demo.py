"""
Demo samples endpoint — serves preloaded audio files and their detection results
for reliable live presentations. No upload needed, instant results.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import json

router = APIRouter()

# Path to demo audio files
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEMO_DIR = os.path.join(PROJECT_ROOT, "data", "demo")

# Cache detection results so demo is instant
_cached_results = {}


def get_demo_result(sample_name: str):
    """Run detection on a demo sample and cache the result."""
    if sample_name in _cached_results:
        return _cached_results[sample_name]

    file_path = os.path.join(DEMO_DIR, sample_name)
    if not os.path.exists(file_path):
        return None

    from ml.ensemble import EnsembleDetector
    detector = EnsembleDetector()
    result = detector.analyze(file_path)
    result["sample_name"] = sample_name

    _cached_results[sample_name] = result
    return result


# Available demo samples
DEMO_SAMPLES = [
    {
        "id": "real_voice",
        "filename": "real_voice.wav",
        "label": "Real Human Voice",
        "description": "Natural speech with pitch variation, breath sounds, and ambient noise.",
        "expected": "real",
    },
    {
        "id": "fake_voice",
        "filename": "fake_voice.wav",
        "label": "AI Cloned Voice #1",
        "description": "Synthetic speech with stable pitch, no breath, clean silence.",
        "expected": "fake",
    },
    {
        "id": "fake_voice_2",
        "filename": "fake_voice_2.wav",
        "label": "AI Cloned Voice #2",
        "description": "Different synthetic voice — lower pitch, sharp spectral cutoff.",
        "expected": "fake",
    },
]


@router.get("/demo/samples")
async def list_demo_samples():
    """List all available demo audio samples."""
    return {
        "samples": DEMO_SAMPLES,
        "description": "Pre-loaded audio samples for demonstration. Use /api/demo/analyze/{sample_id} for instant results.",
    }


@router.get("/demo/analyze/{sample_id}")
async def analyze_demo_sample(sample_id: str):
    """
    Analyze a demo sample and return cached results instantly.
    This is the 'reliable demo' endpoint — results are deterministic.
    """
    # Find sample
    sample = next((s for s in DEMO_SAMPLES if s["id"] == sample_id), None)
    if not sample:
        raise HTTPException(status_code=404, detail=f"Demo sample '{sample_id}' not found.")

    file_path = os.path.join(DEMO_DIR, sample["filename"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Audio file not found at {file_path}")

    result = get_demo_result(sample["filename"])
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to analyze demo sample.")

    # Add sample metadata to result
    result["demo_info"] = sample
    return result


@router.get("/demo/audio/{sample_id}")
async def serve_demo_audio(sample_id: str):
    """Serve the actual audio file for playback in the browser."""
    sample = next((s for s in DEMO_SAMPLES if s["id"] == sample_id), None)
    if not sample:
        raise HTTPException(status_code=404, detail=f"Demo sample '{sample_id}' not found.")

    file_path = os.path.join(DEMO_DIR, sample["filename"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found.")

    return FileResponse(file_path, media_type="audio/wav", filename=sample["filename"])
