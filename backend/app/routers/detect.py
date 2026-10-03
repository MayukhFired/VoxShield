from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
import os
from starlette.concurrency import run_in_threadpool
from app.security import enforce_rate_limit
from app.uploads import save_audio_upload
from ml.space_detector import get_detector

router = APIRouter()


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
        # The call blocks on audio loading plus a round trip to the detection
        # service; run it off the event loop so other requests stay served.
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
