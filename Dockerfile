# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    HF_HOME=/home/app/.cache/huggingface \
    XDG_CACHE_HOME=/home/app/.cache

# ffmpeg : requis par Whisper ; curl : healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 app
WORKDIR /app

# L'index CPU de PyTorch fournit torch « +cpu », préféré à la version PyPI (évite ~5 Go
# de bibliothèques CUDA). Triton (~1 Go, installé par Whisper) ne sert qu'avec un GPU.
COPY requirements.txt .
RUN pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu \
    && pip uninstall -y triton

# Modèles pré-entraînés intégrés à l'image : aucun téléchargement au démarrage
# (indispensable sur Cloud Run, sans disque persistant). Couche placée avant le code
# de l'application pour rester en cache tant que les noms des modèles ne changent pas.
COPY --chown=app:app polymind/__init__.py polymind/config.py polymind/
COPY --chown=app:app scripts/__init__.py scripts/download_models.py scripts/
USER app
RUN python -m scripts.download_models

# Exécution hors ligne : Hugging Face ne doit plus rien télécharger
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

COPY --chown=app:app . .
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fs http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
