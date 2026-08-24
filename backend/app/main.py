from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add project root to path so ML module is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.routers import detect, blacklist, websocket_stream

app = FastAPI(
    title="VoiceShield API",
    description="AI-Powered Real-Time Voice Cloning Detection",
    version="1.0.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(detect.router, prefix="/api", tags=["Detection"])
app.include_router(blacklist.router, prefix="/api/blacklist", tags=["Blacklist"])
app.include_router(websocket_stream.router, tags=["WebSocket"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "VoiceShield API", "version": "1.0.0"}
