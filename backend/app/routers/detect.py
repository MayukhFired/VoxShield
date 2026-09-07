from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
import os
from threading import Lock
from starlette.concurrency import run_in_threadpool
from app.security import enforce_rate_limit
from app.uploads import save_audio_upload

router = APIRouter()
_detector = None
_detector_lock = Lock()


def get_detector():
    """Reuse the model and avoid reloading weights for every upload."""
    global _detector
    if _detector is None:
        with _detector_lock:
            if _detector is None:
                from ml.ensemble import EnsembleDetector
                _detector = EnsembleDetector()
    return _detector


@router.post("/detect")
async def detect_voice(request: Request, file: UploadFile = File(...)):
    """
    Upload an audio file and detect if the voice is real or synthetic.
    Accepts: WAV, MP3, FLAC, OGG
    Returns: verdict, confidence score, individual check results, spectrogram data
    """
    enforce_rate_limit(request, "detect")
    temp_path = None
    try:
        temp_path = await save_audio_upload(file)
        
        import json

        detector = get_detector()
        # librosa/PyTorch work is CPU-bound; keep the async event loop available
        # for other requests while it runs.
        result = await run_in_threadpool(detector.analyze, temp_path)
        
        # Ensure all values are JSON serializable (convert numpy types)
        result_json = json.loads(json.dumps(result, default=lambda x: float(x) if hasattr(x, 'item') else x))
        
        return JSONResponse(content=result_json)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    finally:
        # Privacy-first: always delete uploaded audio immediately
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
