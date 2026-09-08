"""Bounded, short-lived audio upload handling."""

import os
import tempfile

from fastapi import HTTPException, UploadFile

from app.config import settings

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".webm", ".aac", ".opus", ".3gp", ".wma", ".aiff", ".mp4"}


async def save_audio_upload(upload: UploadFile) -> str:
    extension = os.path.splitext(upload.filename or "")[1].lower()
    if not extension or extension not in ALLOWED_EXTENSIONS:
        # Fallback based on content_type if extension is missing/unrecognized
        content_type = (upload.content_type or "").lower()
        if "webm" in content_type:
            extension = ".webm"
        elif "wav" in content_type:
            extension = ".wav"
        elif "mp3" in content_type or "mpeg" in content_type:
            extension = ".mp3"
        elif "ogg" in content_type:
            extension = ".ogg"
        elif "flac" in content_type:
            extension = ".flac"
        elif "mp4" in content_type or "m4a" in content_type or "aac" in content_type:
            extension = ".m4a"
        elif extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported audio format. Please upload WAV, MP3, FLAC, OGG, M4A, or WEBM.")

    declared_size = upload.headers.get("content-length")
    if declared_size and declared_size.isdigit() and int(declared_size) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File too large.")

    total = 0
    path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temporary:
            path = temporary.name
            while chunk := await upload.read(1024 * 1024):
                total += len(chunk)
                if total > settings.max_upload_bytes:
                    limit_mb = settings.max_upload_bytes / (1024 * 1024)
                    raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {limit_mb:.0f}MB.")
                temporary.write(chunk)
        if total == 0:
            raise HTTPException(status_code=400, detail="Uploaded audio is empty.")
        return path
    except Exception:
        if path and os.path.exists(path):
            os.unlink(path)
        raise
