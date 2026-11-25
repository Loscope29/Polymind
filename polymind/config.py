"""Configuration centralisée : chemins du projet et variables d'environnement."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "models"
DATA_DIR = ROOT_DIR / "data"

# Modèles pré-entraînés (pré-téléchargés dans l'image Docker par scripts/download_models.py)
WHISPER_MODEL = "base"
TTS_MODEL = "facebook/mms-tts-fra"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHRONOS_MODEL = "amazon/chronos-t5-small"

load_dotenv(ROOT_DIR / ".env")


def setup_tracing(project: str = "Polymind") -> None:
    """Active le tracing LangSmith uniquement si une clé API est fournie."""
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        os.environ["LANGSMITH_TRACING"] = "false"
        return
    os.environ["LANGSMITH_API_KEY"] = api_key
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ.setdefault("LANGSMITH_PROJECT", os.getenv("LANGCHAIN_PROJECT", project))


def get_gemini_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise EnvironmentError(
            "La clé GEMINI_API_KEY n'est pas définie. Copiez .env.example vers .env et renseignez-la."
        )
    return key
