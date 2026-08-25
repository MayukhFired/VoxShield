# VoxShield AI — AI-Powered Voice Cloning Detection

> Detect. Verify. Protect.

Real-time detection and prevention of voice cloning impersonation attacks.
Built for Smart India Hackathon 2025.

---

## Quick Start

```bash
cd backend
.\venv\Scripts\activate        # Windows
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** — that's it. Single server, full app.

---

## Features

1. **Upload & Detect** — Upload WAV/MP3/FLAC audio, get instant real/fake verdict with spectrogram
2. **Live Microphone** — Stream audio from browser mic, real-time detection via WebSocket
3. **Community Blacklist** — Report scam numbers, search database, auto-escalation
4. **Call Simulation** — Interactive demo showing how detection works during phone calls
5. **Quick Demo Mode** — Pre-loaded samples for reliable live presentations

---

## Project Structure

```
VoxShield AI/
├── backend/                    # FastAPI server
│   ├── app/
│   │   ├── main.py            # App entry point + static file serving
│   │   ├── database.py        # SQLite blacklist database
│   │   └── routers/
│   │       ├── detect.py      # POST /api/detect (file upload)
│   │       ├── blacklist.py   # CRUD /api/blacklist/*
│   │       ├── demo.py        # GET /api/demo/* (pre-loaded samples)
│   │       └── websocket_stream.py  # WS /ws/stream (live mic)
│   ├── requirements.txt
│   └── venv/                   # Python virtual environment
├── static/                     # Frontend (HTML/CSS/JS)
│   ├── index.html             # Main app page
│   ├── blacklist.html         # Blacklist page
│   ├── style.css              # Premium dark theme
│   ├── script.js              # API-connected JavaScript
│   └── logo.png               # App logo
├── ml/                         # AI Detection Engine
│   ├── detector.py            # AASIST model wrapper
│   ├── signal_checks.py       # 4 acoustic signal analyzers
│   ├── ensemble.py            # Weighted scoring engine
│   └── models/                # Place AASIST.pth weights here
├── data/
│   ├── demo/                  # Pre-loaded demo audio samples
│   ├── real/                  # Real voice samples (for training)
│   └── synthetic/             # Synthetic samples (for training)
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve frontend |
| GET | `/health` | Health check |
| POST | `/api/detect` | Upload audio file for detection |
| WS | `/ws/stream` | Live mic WebSocket streaming |
| GET | `/api/demo/samples` | List demo samples |
| GET | `/api/demo/analyze/{id}` | Analyze pre-loaded sample (instant) |
| GET | `/api/demo/audio/{id}` | Serve demo audio for playback |
| POST | `/api/blacklist/report` | Report a scam number |
| GET | `/api/blacklist/check/{number}` | Check if number is blacklisted |
| GET | `/api/blacklist/list` | Paginated blacklist |
| GET | `/api/blacklist/search?q=` | Search numbers |

---

## Detection Engine

**Signal-based checks (4 analyzers):**
- **Pitch Stability** — Detects unnaturally stable F0 (low jitter)
- **Breath Presence** — Checks for natural micro-breaths in pauses
- **Silence Naturalness** — Detects mathematical silence vs ambient noise floor
- **Spectral Cutoff** — Identifies sharp high-frequency rolloff from neural vocoders

**ML Model (AASIST):**
- Graph Attention Network trained on ASVspoof 2019 dataset
- 0.83% EER when pretrained weights are loaded
- Falls back to signal-only mode without weights

---

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **ML:** PyTorch, librosa, NumPy, SciPy
- **Database:** SQLite
- **Audio:** ffmpeg (via imageio-ffmpeg), soundfile
- **Real-time:** WebSocket

---

## Privacy

- Zero audio storage — files deleted immediately after analysis
- No transcription — only acoustic feature analysis
- No cloud upload — all processing happens on the server
- On-device concept — designed for future mobile deployment

---

© 2025 VoxShield AI · Smart India Hackathon
