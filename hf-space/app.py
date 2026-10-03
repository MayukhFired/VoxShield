"""VoxShield AI — public detector demo.

Runs the wav2vec2 spoofing classifier that replaced the shipped heuristics.
Deliberately no @spaces.GPU anywhere: inference is CPU-only, so this Space
never consumes ZeroGPU quota.
"""

import os

import gradio as gr
import librosa
import torch
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

MODEL_ID = os.getenv("VOXSHIELD_MODEL", "AI-Yoru/wav2vec2-spoof-detector")
MAX_SECONDS = 10.0
FAKE_WORDS = {"fake", "ai", "spoof", "synthetic", "clone", "deepfake", "convert"}

torch.set_num_threads(2)

_extractor = AutoFeatureExtractor.from_pretrained(MODEL_ID)
_model = AutoModelForAudioClassification.from_pretrained(MODEL_ID).eval()

_id2label = {int(k): str(v) for k, v in _model.config.id2label.items()}
_FAKE_IDX = next(i for i, label in _id2label.items() if label.lower() in FAKE_WORDS)
_MODEL_SR = int(getattr(_extractor, "sampling_rate", 16000) or 16000)


def fake_probability(path: str) -> float:
    audio, sr = librosa.load(path, sr=_MODEL_SR, mono=True)
    duration = len(audio) / sr
    if duration < 0.5:
        raise ValueError("Need at least 0.5 seconds of speech.")
    # The published error rates were measured on the first 10 seconds, so the
    # demo analyses the same window rather than a longer, unmeasured one.
    audio = audio[: int(MAX_SECONDS * sr)]
    inputs = _extractor(audio, sampling_rate=sr, return_tensors="pt")
    with torch.inference_mode():
        logits = _model(**inputs).logits[0]
    return float(torch.softmax(logits.float(), dim=-1)[_FAKE_IDX])


def analyze(path):
    if not path:
        return "No audio received.", None, ""
    try:
        p_fake = fake_probability(path)
    except ValueError as exc:
        return f"Could not analyse this file: {exc}", None, ""

    verdict = "AI-GENERATED" if p_fake >= 0.5 else "HUMAN"
    strength = abs(p_fake - 0.5) * 2
    if strength < 0.2:
        caveat = "\n\n*Close call — the clip sits near the decision boundary.*"
    else:
        caveat = ""

    banner = (
        f"## {verdict}\n\n"
        f"Probability the voice is synthetic: **{p_fake:.3f}** "
        f"(threshold 0.50){caveat}"
    )
    details = (
        f"- Model: `{MODEL_ID}`\n"
        f"- Audio window analysed: first {MAX_SECONDS:.0f} s at {_MODEL_SR} Hz\n"
        f"- Label map: {_id2label} → synthetic index {_FAKE_IDX}\n"
        f"- Measured on a 56-clip test set with matched codec history: "
        f"caught 26 of 32 AI voices, falsely accused 0 of 24 human speakers."
    )
    return banner, p_fake, details


with gr.Blocks(title="VoxShield AI") as demo:
    gr.Markdown(
        "# VoxShield AI\n"
        "Upload a recording or speak into the microphone. The classifier decides "
        "whether the voice is human or AI-generated."
    )
    with gr.Row():
        with gr.Column():
            audio_in = gr.Audio(sources=["upload", "microphone"], type="filepath", label="Voice sample")
            run = gr.Button("Analyse", variant="primary")
        with gr.Column():
            out_verdict = gr.Markdown()
            out_prob = gr.Number(label="P(synthetic)", precision=4)
            out_details = gr.Markdown()

    run.click(analyze, inputs=audio_in, outputs=[out_verdict, out_prob, out_details])

demo.launch(
    theme=gr.themes.Soft(),
    server_name=os.getenv("GRADIO_SERVER_NAME", "0.0.0.0"),
    server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
)
