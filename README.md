# 🛡️ VoxShield AI — AI-Powered Voice Cloning Detection & Prevention

> **Detect. Verify. Protect.**

Real-time detection and prevention of voice cloning impersonation attacks. Built for Smart India Hackathon 2025 (CodeSprint 3.0).

---

## The Problem

- Voice cloning requires just **3 seconds** of sample audio to clone any voice
- **70% of people** cannot distinguish cloned voices from real ones
- Voice fraud losses exceed **$25 billion** annually
- Criminals use cloned voices for kidnapping extortion, CEO fraud, and bank impersonation

## Our Solution

VoxShield AI is an AI-powered voice security platform that:
1. **Detects** synthetic/cloned voices in real-time using acoustic signal analysis
2. **De-Cloaks** the scammer's real voice hidden beneath their disguise
3. **Fights back** with an AI decoy that wastes scammers' time and collects evidence
4. **Protects the community** through a shared blacklist database

---

## Features

### 1. Voice Authentication Detection
Upload audio or stream from microphone → instant REAL/FAKE verdict with spectrogram visualization and detailed acoustic breakdown.

### 2. Voice De-Cloaking (Novel)
Extracts the scammer's **real underlying voiceprint** from cloned audio. If the same scammer calls again using a different voice or number, we identify them. Inspired by TRIDENT (arxiv 2607.23650, July 2025).

### 3. ScamTrap AI (Novel)
Deploys an AI persona that engages scammers in conversation — wasting their time while collecting intelligence about their tactics. Every minute wasted = a minute they can't scam real victims.

### 4. Community Blacklist
Reported scam numbers are shared across all users. When one person catches a scammer, everyone is protected.

### 5. Real-Time Live Mic Detection
WebSocket-based streaming analysis from browser microphone with live confidence meter.

### 6. Call Simulation
Interactive demo showing how detection works during actual phone calls.

---

## Quick Start

```bash
cd backend
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Linux/Mac
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** — single server, full application.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Uvicorn |
| Frontend | HTML5, CSS3, Vanilla JavaScript (PWA) |
| ML/AI | PyTorch, librosa, NumPy, SciPy |
| Database | SQLite (zero-config) |
| Real-time | WebSocket, Web Audio API |
| Audio | ffmpeg (imageio-ffmpeg), soundfile |

---

## Detection Engine

### Signal-Based Analysis (4 Acoustic Checks)
| Check | What it detects |
|-------|----------------|
| **Silence Naturalness** | Mathematical silence vs ambient noise floor |
| **Spectral Cutoff** | Sharp high-frequency rolloff from neural vocoders |
| **Pitch Stability** | Unnaturally stable F0 (low jitter/shimmer) |
| **Breath Presence** | Absence of natural micro-breaths in pauses |

### ML Model
ResNet + BiGRU + Multi-Head Attention classifier trained on mel-spectrograms. Architecture supports pretrained weights for 98%+ accuracy on ASVspoof benchmark data.

### Voice De-Cloaking Engine
128-dimensional voiceprint extracted from 5 feature groups:
- Temporal dynamics (speaking rhythm)
- Residual pitch (micro-prosody that survives voice conversion)
- Formant ratios (vocal tract geometry)
- Excitation features (glottal characteristics)
- Spectral residual (higher-order MFCCs)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main application |
| GET | `/health` | Health check |
| POST | `/api/detect` | Upload audio for detection |
| WS | `/ws/stream` | Live mic WebSocket |
| POST | `/api/decloak` | Voice de-cloaking + fingerprint |
| GET | `/api/decloak/stats` | De-cloaking statistics |
| POST | `/api/scamtrap/auto` | Run ScamTrap conversation |
| GET | `/api/demo/samples` | List demo samples |
| GET | `/api/demo/analyze/{id}` | Analyze demo sample |
| POST | `/api/blacklist/report` | Report scam number |
| GET | `/api/blacklist/check/{number}` | Check if blacklisted |
| GET | `/api/blacklist/list` | Paginated blacklist |

---

## Project Structure

```
VoxShield-AI/
├── backend/                    # FastAPI server
│   ├── app/
│   │   ├── main.py            # Entry point + static serving
│   │   ├── database.py        # SQLite (blacklist + voiceprints)
│   │   └── routers/
│   │       ├── detect.py      # Audio detection API
│   │       ├── decloak.py     # Voice de-cloaking API
│   │       ├── scamtrap.py    # ScamTrap AI engine
│   │       ├── blacklist.py   # Community blacklist
│   │       ├── demo.py        # Pre-loaded demo samples
│   │       └── websocket_stream.py
│   └── requirements.txt
├── static/                     # PWA Frontend
│   ├── index.html, blacklist.html, decloak.html, scamtrap.html
│   ├── style.css, emergency.css, script.js
│   ├── manifest.json, sw.js   # PWA support
│   └── icons
├── ml/                         # AI Detection Engine
│   ├── detector.py            # Model wrapper
│   ├── signal_checks.py       # 4 acoustic analyzers
│   ├── ensemble.py            # Weighted scoring
│   ├── voiceprint.py          # De-cloaking fingerprint
│   └── ssl_model.py           # ResNet+GRU classifier
├── data/
│   ├── demo/                  # Quick demo audio
│   ├── real/                  # Real voice samples
│   └── synthetic/             # TTS-generated samples
└── README.md
```

---

## Privacy

- **Zero audio storage** — files deleted immediately after analysis
- **No transcription** — only acoustic feature analysis
- **No cloud upload** — all processing on-server
- **Voiceprints are non-reversible** — cannot reconstruct voice from fingerprint

---

## References

- AASIST: Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention Networks (Jung et al., ICASSP 2022)
- TRIDENT: Recovering Source Speaker Identity from Voice Conversion (arxiv 2607.23650, July 2025)
- ASVspoof Challenge: https://www.asvspoof.org/
- Daisy AI (Virgin Media O2) — AI scambaiter concept

---

## Team

Built for **Smart India Hackathon 2025 / CodeSprint 3.0**

© 2025 VoxShield AI — All Rights Reserved
