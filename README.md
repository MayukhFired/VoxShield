# 🛡️ VoxShield AI — AI-Powered Voice Cloning Detection & Prevention

> **Detect. Verify. Protect.**

Research prototype for detecting potential voice-cloning indicators and helping
users respond safely to suspected impersonation calls. Built for Smart India
Hackathon 2025 (CodeSprint 3.0).

> **Important:** This repository currently runs an interpretable signal-analysis
> baseline unless separately versioned, compatible model weights are installed.
> It is not a verified identity system and must not be used as the sole basis for
> a fraud, account, legal, or law-enforcement decision.

---

## The Problem

- Voice cloning requires just **3 seconds** of sample audio to clone any voice
- **70% of people** cannot distinguish cloned voices from real ones
- Voice fraud losses exceed **$25 billion** annually
- Criminals use cloned voices for kidnapping extortion, CEO fraud, and bank impersonation

## Our Solution

VoxShield AI is an AI-powered voice security platform that:
1. **Flags potential indicators** of synthetic/cloned voices using acoustic signal analysis
2. **Optionally correlates experimental voiceprints** across consented, suspicious submissions
3. **Fights back** with an AI decoy that wastes scammers' time and collects evidence
4. **Protects the community** through a shared blacklist database

---

## Features

### 1. Voice Authentication Detection
Upload audio or stream from microphone → instant REAL/FAKE verdict with spectrogram visualization and detailed acoustic breakdown.

### 2. Experimental Voiceprint Correlation
Extracts acoustic features from consented suspicious audio and searches for
similar prior submissions. Similarity is a research signal, not an identity or
an attribution of wrongdoing. See [validation guidance](docs/VALIDATION.md).

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
py -3.10 -m venv backend/.venv
.\backend\.venv\Scripts\Activate.ps1        # Windows PowerShell
# source backend/.venv/bin/activate            # Linux/Mac
cd backend
pip install -r requirements.txt
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

### ML status
The checked-in baseline uses four heuristic acoustic checks. The model wrapper
can load separately supplied compatible weights, but no validated model weights
or benchmark results are distributed with this repository. Do not claim a
specific accuracy until the evaluation plan has been completed.

### Experimental voiceprint engine
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

- **Temporary audio processing** — files are deleted immediately after analysis
- **No transcription** — only acoustic feature analysis
- **No cloud upload** — all processing on-server
- **Opt-in experimental correlation** — fingerprints are stored only after
  affirmative consent for suspicious audio; they are sensitive biometric data

See [privacy and retention requirements](docs/PRIVACY.md) and the
[validation plan](docs/VALIDATION.md) before deploying beyond a controlled demo.

---

## References

- AASIST: Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention Networks (Jung et al., ICASSP 2022)
- TRIDENT: Recovering Source Speaker Identity from Voice Conversion (research inspiration; independently validate before relying on it)
- ASVspoof Challenge: https://www.asvspoof.org/
- Daisy AI (Virgin Media O2) — AI scambaiter concept

---

## Team

Built for **Smart India Hackathon 2025 / CodeSprint 3.0**

© 2025 VoxShield AI — All Rights Reserved
