from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os

router = APIRouter()


@router.post("/detect")
async def detect_voice(file: UploadFile = File(...)):
    """
    Upload an audio file and detect if the voice is real or synthetic.
    Accepts: WAV, MP3, FLAC, OGG
    Returns: verdict, confidence score, individual check results, spectrogram data
    """
    # Validate file type
    allowed_types = [
        "audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3",
        "audio/flac", "audio/ogg", "audio/wave"
    ]
    
    # Also check by extension since content_type can be unreliable
    allowed_extensions = [".wav", ".mp3", ".flac", ".ogg", ".m4a", ".webm"]
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    
    if file.content_type not in allowed_types and file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Accepted: WAV, MP3, FLAC, OGG"
        )
    
    # Check file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    # Save to temp file for processing
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            tmp.write(contents)
            temp_path = tmp.name
        
        # Import detector here to avoid slow startup
        from ml.ensemble import EnsembleDetector
        
        detector = EnsembleDetector()
        result = detector.analyze(temp_path)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    finally:
        # Privacy-first: always delete uploaded audio immediately
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
