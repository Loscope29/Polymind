"""Pré-télécharge les modèles pré-entraînés dans le cache local.

Exécuté au build de l'image Docker : les conteneurs (Cloud Run notamment, sans disque
persistant) démarrent ainsi sans rien télécharger. Chaque modèle est chargé avec la même
bibliothèque que l'application, ce qui met en cache exactement les fichiers qu'elle lit.

Usage (depuis la racine du projet) : python -m scripts.download_models
"""

import whisper
from chronos import ChronosPipeline
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, VitsModel

from polymind.config import CHRONOS_MODEL, EMBEDDING_MODEL, TTS_MODEL, WHISPER_MODEL


def main() -> None:
    print(f"Whisper : {WHISPER_MODEL}", flush=True)
    whisper.load_model(WHISPER_MODEL, device="cpu")

    print(f"Text-to-speech : {TTS_MODEL}", flush=True)
    VitsModel.from_pretrained(TTS_MODEL)
    AutoTokenizer.from_pretrained(TTS_MODEL)

    print(f"Embeddings : {EMBEDDING_MODEL}", flush=True)
    SentenceTransformer(EMBEDDING_MODEL, device="cpu")

    print(f"Chronos : {CHRONOS_MODEL}", flush=True)
    ChronosPipeline.from_pretrained(CHRONOS_MODEL, device_map="cpu")

    print("Modèles en cache.", flush=True)


if __name__ == "__main__":
    main()
