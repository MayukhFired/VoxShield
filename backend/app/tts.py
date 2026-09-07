"""Optional cloud TTS for the scripted ScamTrap demo.

Browser speech is the privacy-preserving default. Cloud synthesis is opt-in
because persona dialogue leaves this server for a third-party provider.
"""

import asyncio
import io
import logging
from typing import Dict

from starlette.concurrency import run_in_threadpool

from app.config import settings

logger = logging.getLogger(__name__)


class TTSUnavailableError(RuntimeError):
    """Raised when optional cloud TTS is disabled or unavailable."""


PERSONA_VOICES: Dict[str, Dict[str, str]] = {
    "elderly_grandma": {"voice": "hi-IN-SwaraNeural", "rate": "-15%", "pitch": "+5Hz", "fallback_lang": "hi"},
    "nervous_uncle": {"voice": "en-IN-PrabhatNeural", "rate": "-5%", "pitch": "-3Hz", "fallback_lang": "en"},
    "chatty_student": {"voice": "en-IN-NeerjaNeural", "rate": "+15%", "pitch": "+10Hz", "fallback_lang": "en"},
}
DEFAULT_PERSONA_VOICE = {"voice": "en-IN-NeerjaNeural", "rate": "0%", "pitch": "0Hz", "fallback_lang": "en"}


async def _edge_tts(text: str, config: Dict[str, str]) -> bytes:
    import edge_tts

    communicator = edge_tts.Communicate(text=text, voice=config["voice"], rate=config["rate"], pitch=config["pitch"])
    buffer = io.BytesIO()
    async for chunk in communicator.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    return buffer.getvalue()


def _google_tts(text: str, language: str) -> bytes:
    from gtts import gTTS

    buffer = io.BytesIO()
    gTTS(text=text, lang=language, tld="co.in").write_to_fp(buffer)
    return buffer.getvalue()


async def synthesize_speech(text: str, persona: str = "elderly_grandma") -> bytes:
    """Return provider-generated MP3 audio or fail transparently.

    We never return fake MP3 bytes: the client can fall back to local browser
    speech when cloud synthesis is unavailable.
    """
    if not text or not text.strip():
        raise ValueError("Text content cannot be empty.")
    if not settings.enable_cloud_tts:
        raise TTSUnavailableError("Cloud TTS is disabled; use browser speech instead.")

    config = PERSONA_VOICES.get(persona, DEFAULT_PERSONA_VOICE)
    try:
        audio = await asyncio.wait_for(_edge_tts(text, config), timeout=settings.tts_timeout_seconds)
        if len(audio) > 500:
            return audio
    except Exception as error:
        logger.info("Edge TTS unavailable; trying fallback: %s", type(error).__name__)

    try:
        audio = await asyncio.wait_for(
            run_in_threadpool(_google_tts, text, config["fallback_lang"]),
            timeout=settings.tts_timeout_seconds,
        )
        if len(audio) > 500:
            return audio
    except Exception as error:
        logger.info("Google TTS unavailable: %s", type(error).__name__)

    raise TTSUnavailableError("Cloud TTS providers are unavailable; use browser speech instead.")
