"""Transcription audio → texte avec OpenAI Whisper."""

import whisper
from langsmith import traceable

from polymind.config import WHISPER_MODEL, setup_tracing

setup_tracing()

# Chargement du modèle Whisper sur CPU (pas de GPU en production)
model = whisper.load_model(WHISPER_MODEL, device="cpu")


@traceable(run_type="chain", name="AudioToText-Whisper")
def audio_to_text(audio_path: str) -> str:
    result = model.transcribe(audio_path)
    return result["text"]
