# VoiceShield — AI-Powered Voice Cloning Detection

Real-time detection and prevention of voice cloning impersonation attacks.

## Quick Start

### Backend (Python)
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (React)
```bash
cd frontend
npm install
npm run dev
```

### Access
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure
```
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── main.py           # App entry point
│   │   ├── database.py       # SQLite database
│   │   └── routers/
│   │       ├── detect.py     # Upload detection endpoint
│   │       ├── blacklist.py  # Blacklist CRUD API
│   │       └── websocket_stream.py  # Live mic WebSocket
│   └── requirements.txt
├── frontend/          # React + Vite frontend
│   └── src/
│       ├── pages/            # All page components
│       └── components/       # Reusable components
├── ml/                # ML detection engine
│   ├── detector.py           # AASIST model wrapper
│   ├── signal_checks.py      # Acoustic signal analysis
│   └── ensemble.py           # Combined scoring engine
└── data/              # Audio samples (not in git)
    ├── real/
    ├── synthetic/
    └── test_pairs/
```

## Features
1. **Upload & Detect** — Upload audio files for instant authenticity analysis
2. **Live Mic Detection** — Real-time voice analysis via browser microphone
3. **Community Blacklist** — Shared scam number database with fast lookup
4. **Call Simulation** — Interactive demo showing detection during phone calls
