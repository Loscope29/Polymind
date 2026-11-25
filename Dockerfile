# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/home/app/.cache/huggingface \
    XDG_CACHE_HOME=/home/app/.cache

# ffmpeg : requis par Whisper ; curl : healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 app
WORKDIR /app

# PyTorch CPU (évite ~5 Go de bibliothèques CUDA), puis le reste des dépendances.
# Triton (~1 Go, installé par Whisper) ne sert qu'avec un GPU : on le retire.
COPY requirements.txt .
RUN pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt \
    && pip uninstall -y triton

COPY --chown=app:app . .
RUN mkdir -p /home/app/.cache && chown -R app:app /home/app/.cache

USER app
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fs http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
