from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sys
import os

# Add project root to path so ML module is importable
# __file__ is backend/app/main.py → project root is 2 dirs up
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from app.routers import detect, blacklist, websocket_stream, demo, decloak

app = FastAPI(
    title="VoiceShield API",
    description="AI-Powered Real-Time Voice Cloning Detection",
    version="1.0.0",
)

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(detect.router, prefix="/api", tags=["Detection"])
app.include_router(blacklist.router, prefix="/api/blacklist", tags=["Blacklist"])
app.include_router(demo.router, prefix="/api", tags=["Demo"])
app.include_router(decloak.router, prefix="/api", tags=["De-Cloaking"])
app.include_router(websocket_stream.router, tags=["WebSocket"])

# Static frontend directory
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "VoiceShield API", "version": "1.0.0"}


@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/blacklist.html")
async def serve_blacklist():
    return FileResponse(os.path.join(STATIC_DIR, "blacklist.html"))


@app.get("/decloak.html")
async def serve_decloak():
    return FileResponse(os.path.join(STATIC_DIR, "decloak.html"))


# Mount static assets LAST (CSS, JS, images at /static/)
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
