"""
VoxShield AI — Voice De-Cloaking API

Unmasks the scammer's real voice fingerprint from cloned/converted audio.
Stores the fingerprint and cross-matches against previously seen scammers.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
import json

router = APIRouter()


class DecloakRequest(BaseModel):
    phone_number: Optional[str] = None


@router.post("/decloak")
async def decloak_voice(file: UploadFile = File(...), phone_number: Optional[str] = None):
    """
    Full de-cloaking pipeline:
    1. Detect if voice is real or fake
    2. If fake → extract scammer's underlying voiceprint
    3. Search database for matching voiceprints (same scammer, different cases)
    4. Store new voiceprint and record the case
    
    Returns: detection result + voiceprint + matches from database
    """
    # Validate file
    allowed_extensions = [".wav", ".mp3", ".flac", ".ogg", ".m4a", ".webm"]
    file_ext = os.path.splitext(file.filename or "")[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported audio format.")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Max 10MB.")

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            tmp.write(contents)
            temp_path = tmp.name

        # Step 1: Run detection
        from ml.ensemble import EnsembleDetector
        detector = EnsembleDetector()
        detection_result = detector.analyze(temp_path)

        if detection_result.get("verdict") == "error":
            raise HTTPException(status_code=400, detail=detection_result.get("error", "Analysis failed"))

        # Step 2: Extract voiceprint (regardless of verdict — useful for both)
        import librosa
        audio, sr = librosa.load(temp_path, sr=16000, mono=True)

        from ml.voiceprint import VoiceprintExtractor
        extractor = VoiceprintExtractor(sr=16000)
        voiceprint = extractor.extract(audio)

        # Step 3: Search for matching voiceprints in database
        from app.database import find_similar_voiceprints, store_voiceprint, record_decloak_case

        matches = await find_similar_voiceprints(
            voiceprint["fingerprint_vector"],
            threshold=0.62
        )

        # Step 4: Store this voiceprint
        store_result = await store_voiceprint(
            fingerprint_hash=voiceprint["fingerprint_hash"],
            fingerprint_vector=voiceprint["fingerprint_vector"],
            confidence=voiceprint["confidence"],
            phone_number=phone_number,
        )

        # Step 5: Record the case
        best_match_similarity = matches[0]["similarity"] if matches else 0.0
        case_id = await record_decloak_case(
            voiceprint_id=store_result["voiceprint_id"],
            phone_number=phone_number,
            detection_verdict=detection_result["verdict"],
            detection_confidence=detection_result["confidence"],
            voiceprint_confidence=voiceprint["confidence"],
            matched_existing=len(matches) > 0 and not store_result["is_new"],
            similarity_score=best_match_similarity,
        )

        # Build response
        response = {
            "detection": {
                "verdict": detection_result["verdict"],
                "confidence": detection_result["confidence"],
                "signal_checks": detection_result.get("signal_checks", []),
                "signal_summary": detection_result.get("signal_summary", {}),
            },
            "voiceprint": {
                "fingerprint_hash": voiceprint["fingerprint_hash"],
                "confidence": voiceprint["confidence"],
                "features": voiceprint["features"],
                "is_new_scammer": store_result["is_new"],
                "times_seen": store_result["times_seen"],
                "voiceprint_id": store_result["voiceprint_id"],
            },
            "matches": matches,
            "case_id": case_id,
            "summary": _build_summary(detection_result, voiceprint, matches, store_result),
        }

        return JSONResponse(content=response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"De-cloaking failed: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.get("/decloak/stats")
async def decloak_statistics():
    """Get overall de-cloaking system statistics."""
    from app.database import get_decloak_stats
    stats = await get_decloak_stats()
    return stats


@router.get("/decloak/scammer/{voiceprint_id}")
async def get_scammer_details(voiceprint_id: int):
    """Get full profile of a known scammer by their voiceprint ID."""
    from app.database import get_scammer_profile
    profile = await get_scammer_profile(voiceprint_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Scammer voiceprint not found.")
    return profile


def _build_summary(detection: dict, voiceprint: dict, matches: list, store_result: dict) -> dict:
    """Build a human-readable summary of the de-cloaking analysis."""
    verdict = detection["verdict"]

    if verdict == "real":
        headline = "Voice appears authentic — no de-cloaking needed"
        threat_level = "low"
        description = "This voice shows natural acoustic characteristics. No synthetic markers detected."
    elif matches and not store_result["is_new"]:
        headline = "KNOWN SCAMMER IDENTIFIED — Voice matches previous cases"
        threat_level = "critical"
        top_match = matches[0]
        description = (
            f"This scammer's underlying voice matches a known profile "
            f"(ID: {top_match['voiceprint_id']}) with {top_match['similarity']:.0%} similarity. "
            f"They have been seen {top_match['times_seen']} time(s) before, "
            f"linked to numbers: {', '.join(top_match['linked_numbers'][:3]) or 'unknown'}."
        )
    elif matches:
        headline = "POTENTIAL MATCH — Similar voiceprint found in database"
        threat_level = "high"
        description = (
            f"Synthetic voice detected. The underlying scammer voiceprint has "
            f"{matches[0]['similarity']:.0%} similarity to a previously recorded scammer. "
            f"This may be the same individual using a different cloned voice or phone number."
        )
    else:
        headline = "NEW SCAMMER IDENTIFIED — Voiceprint recorded"
        threat_level = "high"
        description = (
            "Synthetic voice detected. This is a NEW scammer voiceprint not previously "
            "seen in our database. Their voice fingerprint has been recorded. "
            "If they attempt to scam anyone else, they will be identified."
        )

    return {
        "headline": headline,
        "threat_level": threat_level,
        "description": description,
        "voiceprint_hash": voiceprint["fingerprint_hash"],
        "extraction_confidence": voiceprint["confidence"],
    }
