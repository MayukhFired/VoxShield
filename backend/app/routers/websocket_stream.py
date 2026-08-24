from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import tempfile
import os
import json

router = APIRouter()


@router.websocket("/ws/stream")
async def stream_audio(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice detection.
    Client sends audio chunks (binary), server responds with detection results (JSON).
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive binary audio data from client
            data = await websocket.receive_bytes()
            
            # Save chunk to temp file for analysis
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(data)
                    temp_path = tmp.name
                
                # Run detection on the chunk
                from ml.ensemble import EnsembleDetector
                
                detector = EnsembleDetector()
                result = detector.analyze(temp_path)
                
                # Send result back to client
                await websocket.send_json(result)
            
            finally:
                # Privacy: delete temp audio immediately
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
