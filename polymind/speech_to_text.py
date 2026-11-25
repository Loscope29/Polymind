"""Transcription audio → texte avec OpenAI Whisper."""

import whisper
from langsmith import traceable

from polymind.config import setup_tracing

setup_tracing()

# Chargement du modèle Whisper (CPU pour compatibilité avec Streamlit Cloud)
model = whisper.load_model("base", device="cpu")


@traceable(run_type="chain", name="AudioToText-Whisper")
def audio_to_text(audio_path: str) -> str:
    result = model.transcribe(audio_path)
    return result["text"]
