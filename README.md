<p align="center">
  <img src="static/logo.png" alt="VoxShield AI Logo" width="120" />
</p>

<h1 align="center">VoxShield AI</h1>

<p align="center">
  <strong>AI-Powered Real-Time Voice Cloning Detection</strong>
</p>

<p align="center">
  <em>Detect. Verify. Protect.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PyTorch-2.1-EE4C2C?logo=pytorch&logoColor=white" alt="PyTorch" />
  <img src="https://img.shields.io/badge/WebSocket-Real--Time-blue" alt="WebSocket" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License" />
</p>

<p align="center">
  Built for <strong>Smart India Hackathon 2025</strong>
</p>

---

## Overview

**VoxShield AI** is an intelligent voice security platform that detects synthetic and cloned voices in real-time. It combines a deep learning model (AASIST) with interpretable acoustic signal analysis to identify AI-generated speech with high accuracy.

As voice cloning technology becomes increasingly accessible, VoxShield provides a defense layer for individuals and organizations against voice-based impersonation attacks, scam calls, and deepfake audio.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Upload & Detect** | Upload WAV/MP3/FLAC/OGG audio files and get instant real/fake verdict with spectrogram visualization |
| **Live Microphone** | Stream audio from your browser microphone for real-time detection via WebSocket |
| **Community Blacklist** | Report scam phone numbers, search the database, and benefit from community-powered protection |
| **Call Simulation** | Interactive demo showing how VoxShield protects users during phone calls |
| **Quick Demo Mode** | Pre-loaded audio samples for instant live presentations without file uploads |
| **De-Cloak** | Advanced voice unmasking and identity verification |
| **ScamTrap** | Automated scam caller identification and trapping |

---

## Detection Engine

VoxShield uses a **dual-layer ensemble architecture** that combines machine learning with rule-based acoustic analysis:

### Layer 1: AASIST Deep Learning Model (60% weight)

- **Architecture:** Graph Attention Network (Integrated Spectro-Temporal)
- **Training Data:** ASVspoof 2019 LA dataset
- **Performance:** 0.83% Equal Error Rate (EER) with pretrained weights
- **Fallback:** Gracefully degrades to signal-only mode if weights are unavailable

### Layer 2: Acoustic Signal Analysis (40% weight)

Four specialized analyzers examine physical and digital artifacts:

| Check | What It Detects |
|-------|----------------|
| **Pitch Stability** | Unnaturally stable F0 and low jitter common in TTS systems |
| **Breath Presence** | Missing micro-inhalation sounds in speech pauses |
| **Silence Naturalness** | Mathematical silence (exact zeros) vs. natural room tone |
| **Spectral Cutoff** | Sharp high-frequency rolloff from neural vocoders (7-8 kHz) |

### Scoring

```
Final Score = (AASIST_realness x 0.60) + (Signal_combined x 0.40)
Verdict: Real if score > 0.5, Fake otherwise
```

A penalty multiplier is applied when 3+ signal checks fail, increasing fake detection sensitivity.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, FastAPI, Uvicorn |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **ML/AI** | PyTorch, AASIST, librosa, NumPy, SciPy |
| **Real-Time** | WebSocket (browser mic streaming) |
| **Database** | SQLite (blacklist storage) |
| **Audio Processing** | librosa, soundfile, pydub |

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- A modern web browser (Chrome, Firefox, Edge)

### Installation

```bash
# Clone the repository
git clone https://github.com/MayukhFired/VoxShield.git
cd VoxShield

# Create and activate virtual environment
python -m venv backend/venv

# Windows
backend\venv\Scripts\activate

# macOS/Linux
source backend/venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Run the Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Open the App

Navigate to **http://localhost:8000** in your browser. That's it — single server, full application.

---

## Project Structure

```
VoxShield/
├── backend/                         # FastAPI application server
│   ├── app/
│   │   ├── main.py                  # App entry point, static file serving, CORS
│   │   ├── database.py              # SQLite blacklist database layer
│   │   └── routers/
│   │       ├── detect.py            # POST /api/detect — file upload analysis
│   │       ├── blacklist.py         # CRUD /api/blacklist/* — scam number DB
│   │       ├── demo.py              # GET /api/demo/* — pre-loaded samples
│   │       └── websocket_stream.py  # WS /ws/stream — live mic streaming
│   ├── requirements.txt             # Python dependencies
│   └── venv/                        # Virtual environment (not tracked)
│
├── ml/                              # AI Detection Engine
│   ├── detector.py                  # AASIST model wrapper & inference
│   ├── signal_checks.py            # 4 acoustic signal analyzers
│   ├── ensemble.py                  # Weighted ensemble scoring engine
│   └── models/                      # Place AASIST.pth weights here
│
├── static/                          # Frontend (served by FastAPI)
│   ├── index.html                   # Main application page
│   ├── blacklist.html               # Community blacklist page
│   ├── style.css                    # Premium dark theme UI
│   ├── script.js                    # Client-side JavaScript
│   └── logo.png                     # App logo
│
├── data/
│   ├── demo/                        # Pre-loaded demo audio samples
│   ├── real/                        # Real voice samples
│   └── synthetic/                   # Synthetic voice samples
│
└── README.md
```

---

## API Reference

### Detection

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/detect` | Upload an audio file for voice authenticity analysis |
| `WS` | `/ws/stream` | Real-time mic audio streaming via WebSocket |

### Demo

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/demo/samples` | List available demo samples |
| `GET` | `/api/demo/analyze/{id}` | Analyze a pre-loaded sample instantly |
| `GET` | `/api/demo/audio/{id}` | Serve demo audio for playback |

### Blacklist

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/blacklist/report` | Report a scam phone number |
| `GET` | `/api/blacklist/check/{number}` | Check if a number is blacklisted |
| `GET` | `/api/blacklist/list` | Paginated list of reported numbers |
| `GET` | `/api/blacklist/search?q=` | Search reported numbers |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve frontend application |
| `GET` | `/health` | Health check endpoint |

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                      User Input                              │
│            (Upload File / Live Microphone)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Audio Preprocessing                         │
│          (16kHz mono, trim silence, normalize)               │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
┌──────────────────┐    ┌──────────────────────┐
│   AASIST Model   │    │   Signal Checks (4)  │
│   (60% weight)   │    │   (40% weight)       │
│                  │    │                      │
│  Graph Attention │    │  • Pitch Stability   │
│  Network on      │    │  • Breath Presence   │
│  spectro-temporal│    │  • Silence Natural.  │
│  features        │    │  • Spectral Cutoff   │
└────────┬─────────┘    └──────────┬───────────┘
         │                         │
         └────────────┬────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Ensemble Scoring                             │
│         Weighted combination + penalty logic                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     Output                                    │
│  Verdict (Real/Fake) + Confidence + Spectrogram + Details   │
└─────────────────────────────────────────────────────────────┘
```

---

## Using Pretrained Weights

For maximum accuracy, download the AASIST pretrained weights and place them in the models directory:

```
ml/models/AASIST.pth
```

Without weights, the system operates in **signal-checks-only mode** using the 4 acoustic analyzers. This still provides useful detection but with reduced accuracy.

---

## Privacy & Security

- **Zero Audio Storage** — Uploaded files are deleted immediately after analysis
- **No Transcription** — Only acoustic features are analyzed, not speech content
- **No Cloud Upload** — All processing happens locally on the server
- **No Tracking** — No user analytics or behavioral tracking
- **On-Device Ready** — Architecture designed for future mobile/edge deployment

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port |
| `HOST` | `0.0.0.0` | Server host binding |

---

## Contributing

Contributions are welcome! Here's how to get involved:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m "Add your feature"`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## Acknowledgments

- **AASIST** — [Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention Networks](https://arxiv.org/abs/2110.01200)
- **ASVspoof 2019** — Automatic Speaker Verification Spoofing and Countermeasures Challenge
- **librosa** — Audio analysis library for Python
- **FastAPI** — Modern Python web framework

---

## Team

Built with passion for **Smart India Hackathon 2025**.

---

<p align="center">
  <strong>VoxShield AI</strong> — Because every voice deserves to be verified.
</p>

<p align="center">
  <sub>© 2025 VoxShield AI · Smart India Hackathon · All Rights Reserved</sub>
</p>
