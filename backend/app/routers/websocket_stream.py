from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import tempfile
import os
import json
import subprocess

router = APIRouter()

# Cache detector instance globally to avoid reloading model per chunk
_detector = None


def get_detector():
    global _detector
    if _detector is None:
        from ml.ensemble import EnsembleDetector
        _detector = EnsembleDetector()
    return _detector


def convert_webm_to_wav(input_path: str, output_path: str) -> bool:
    """
    Convert webm/ogg audio to 16kHz mono WAV.
    Tries: imageio-ffmpeg bundled binary → system ffmpeg → pydub → librosa
    """
    # Try imageio-ffmpeg bundled binary first
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        result = subprocess.run(
            [ffmpeg_exe, "-y", "-i", input_path, "-ar", "16000", "-ac", "1", "-f", "wav", output_path],
            capture_output=True, timeout=10
        )
        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 100:
            return True
    except Exception:
        pass

    # Try system ffmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", "-f", "wav", output_path],
            capture_output=True, timeout=10
        )
        if result.returncode == 0 and os.path.exists(output_path):
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: try librosa directly (works for some formats)
    try:
        import librosa
        import soundfile as sf
        audio, sr = librosa.load(input_path, sr=16000, mono=True)
        sf.write(output_path, audio, 16000)
        return True
    except Exception:
        pass

    return False


@router.websocket("/ws/stream")
async def stream_audio(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice detection.
    Client sends audio chunks (binary webm), server converts and analyzes.
    """
    await websocket.accept()
    detector = get_detector()

    try:
        while True:
            # Receive binary audio data from client (webm format from MediaRecorder)
            data = await websocket.receive_bytes()

            if len(data) < 100:
                # Too small to be valid audio
                continue

            webm_path = None
            wav_path = None
            try:
                # Save incoming webm chunk
                with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                    tmp.write(data)
                    webm_path = tmp.name

                # Convert to WAV
                wav_path = webm_path.replace(".webm", ".wav")
                converted = convert_webm_to_wav(webm_path, wav_path)

                if not converted:
                    await websocket.send_json({
                        "error": "Could not convert audio. Install ffmpeg for live mic support."
                    })
                    continue

                # Check if WAV has enough data
                if os.path.getsize(wav_path) < 1000:
                    continue

                # Run detection
                result = detector.analyze(wav_path)

                # Serialize safely (remove spectrogram for speed on live stream)
                result.pop("spectrogram", None)

                await websocket.send_json(result)

            except Exception as e:
                try:
                    await websocket.send_json({"error": str(e)})
                except Exception:
                    pass

            finally:
                # Privacy: delete temp files immediately
                for path in [webm_path, wav_path]:
                    if path and os.path.exists(path):
                        try:
                            os.unlink(path)
                        except OSError:
                            pass

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
