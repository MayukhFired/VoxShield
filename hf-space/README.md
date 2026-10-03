---
title: VoxShield
emoji: 🛡️
colorFrom: green
colorTo: green
sdk: gradio
sdk_version: 6.29.1
app_file: app.py
python_version: "3.12"
pinned: false
license: mit
---

VoxShield AI runs on the `AI-Yoru/wav2vec2-spoof-detector` classifier, loaded once
at start-up and run on CPU, so this Space consumes no ZeroGPU quota.

Measured on a 56-clip test set whose real and synthetic audio were pushed through
the same codec history: 26 of 32 AI voices caught, 0 of 24 human speakers falsely
accused. The earlier heuristic engine missed 96% of AI voices; those checks measured
encoding artefacts, not spoofing.
