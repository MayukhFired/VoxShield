"""Bounded, short-lived audio upload handling."""

import os
import tempfile

from fastapi import HTTPException, UploadFile

from app.config import settings

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".webm"}


async def save_audio_upload(upload: UploadFile) -> str:
    extension = os.path.splitext(upload.filename or "")[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported audio format.")

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
                    raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
                temporary.write(chunk)
        if total == 0:
            raise HTTPException(status_code=400, detail="Uploaded audio is empty.")
        return path
    except Exception:
        if path and os.path.exists(path):
            os.unlink(path)
        raise
