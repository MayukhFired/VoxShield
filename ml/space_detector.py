"""Detection through the Hugging Face Space that hosts the real classifier.

Render's free tier cannot hold torch plus the ~900 MB the model needs, so the
app forwards the uploaded file to the Space and passes its verdict through.
The Space also returns the spectrogram, which keeps every decibel of DSP work
off the web process.
"""

import os
import threading

SPACE_URL = os.getenv("VOXSHIELD_SPACE_URL", "").rstrip("/")

_detector = None
_lock = threading.Lock()


class SpaceDetector:
    def __init__(self, url: str):
        self._url = url
        self._client = None

    def _analyze(self, audio_path: str) -> dict:
        from gradio_client import Client, handle_file

        if self._client is None:
            self._client = Client(self._url, verbose=False)
        response = self._client.predict(handle_file(audio_path), api_name="/analyze")
        # Output 4 is the machine payload. A Space still running the older
        # three-output app.py would otherwise fail with an opaque IndexError.
        if len(response) < 4 or not isinstance(response[3], dict):
            raise RuntimeError(
                "Detection service predates the payload contract - re-upload hf-space/app.py"
            )
        payload = response[3] or {}
        if payload.get("verdict") not in ("real", "fake"):
            raise RuntimeError("Detection service returned no verdict")
        return payload

    def analyze(self, audio_path: str) -> dict:
        payload = self._analyze(audio_path)
        return {
            "verdict": payload["verdict"],
            "confidence": payload["confidence"],
            "p_fake": payload["p_fake"],
            "duration_seconds": payload["duration_seconds"],
            "analyzed_seconds": payload["analyzed_seconds"],
            "model_result": {
                "label": payload["verdict"],
                "confidence": payload["confidence"],
                "raw_scores": {"p_fake": payload["p_fake"]},
                "source": payload["model"],
            },
            # The old heuristic checks measured file encoding, not spoofing, so
            # they no longer contribute to a verdict. Kept empty for API shape.
            "signal_checks": [],
            "signal_summary": {"engine": payload["model"], "p_fake": payload["p_fake"]},
            "spectrogram": payload["spectrogram"],
        }


def get_detector():
    """Space-backed detector when configured, otherwise the local heuristics."""
    global _detector
    if _detector is None:
        with _lock:
            if _detector is None:
                if SPACE_URL:
                    _detector = SpaceDetector(SPACE_URL)
                else:
                    from ml.ensemble import EnsembleDetector

                    _detector = EnsembleDetector()
    return _detector
