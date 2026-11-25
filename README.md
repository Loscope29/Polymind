<div align="center">

# Polymind

**Une boîte à outils IA multimodale : voix, documents et finance, dans une seule application Streamlit.**

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.67-FF4B4B?logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1.8-1C3C3C?logo=langchain&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.21-FF6F00?logo=tensorflow&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.15-EE4C2C?logo=pytorch&logoColor=white)
![Gemini](https://img.shields.io/badge/Google-Gemini%202.5-4285F4?logo=google&logoColor=white)

</div>

---

## Aperçu

Polymind réunit quatre outils d'IA appliquée derrière une interface unique :

| Outil | Description | Technologies |
|---|---|---|
| **Audio to Text** | Transcription de fichiers audio (wav, mp3, m4a) | OpenAI Whisper |
| **Text to Speech** | Synthèse vocale en français | Meta MMS-TTS (VITS) · Hugging Face |
| **RAG PDF** | Questions/réponses sur un document PDF | LangChain · ChromaDB · MiniLM · Gemini 2.5 Flash |
| **Chatbot Bourse** | Prévision de cours sur 6 mois commentée par un LLM | Amazon Chronos · LSTM (Keras) · yfinance · Gemini |

Toutes les chaînes sont instrumentées avec **LangSmith** (traçabilité des appels LLM, latence, tokens).

## Architecture

```text
             ┌──────────────────────── Streamlit (streamlit_app.py + pages/) ────────────────────────┐
             │                                                                                         │
   Audio ──▶ │  Whisper ──▶ texte          Texte ──▶ VITS ──▶ audio .wav                              │
             │                                                                                         │
   PDF ────▶ │  PyPDF ──▶ chunks ──▶ embeddings MiniLM ──▶ Chroma ──▶ top-5 ──▶ Gemini ──▶ réponse     │
             │                                                                                         │
   Ticker ─▶ │  yfinance ──▶ Chronos (zero-shot) | LSTM entraîné ──▶ prévision ──▶ Gemini ──▶ analyse  │
             └─────────────────────────────────────────────────────────────────────────────────────────┘
                                                   │
                                                LangSmith (tracing)
```

## Structure du projet

```text
polymind/
├── streamlit_app.py          # Point d'entrée de l'application
├── pages/                    # Une page Streamlit par outil
│   ├── 1_Audio_to_Text.py
│   ├── 2_Text_to_Speech.py
│   ├── 3_RAG_PDF.py
│   └── 4_Chatbot_Bourse.py
├── polymind/                 # Logique métier (package Python)
│   ├── config.py             # Chemins + variables d'environnement + tracing
│   ├── speech_to_text.py     # Whisper
│   ├── text_to_speech.py     # MMS-TTS / VITS
│   ├── rag.py                # Pipeline RAG
│   └── finance/
│       ├── prediction.py     # Prévisions Chronos & LSTM
│       └── chatbot.py        # Analyse des prévisions par Gemini
├── models/
│   ├── finance/              # LSTM entraînés (AMD, AMZN, GE, INTC) + prédictions .npy
│   └── ml/                   # Modèles des notebooks ML (diabète, immobilier)
├── notebooks/
│   ├── nlp/                  # RAG, Whisper, Edge-TTS
│   ├── ml/                   # Classification diabète, régression prix immobilier (ANN)
│   └── finance/              # Entraînement LSTM, direction des rendements, Chronos
├── scripts/                  # Smoke tests, pré-téléchargement des modèles
├── assets/samples/           # Fichier audio d'exemple
├── data/                     # Jeux de données (non versionnés, voir data/README.md)
├── requirements.in           # Dépendances directes de l'application
├── requirements.txt          # Leur résolution figée (installée dans l'image)
├── requirements-dev.txt      # + extras des notebooks (Jupyter, seaborn, statsmodels…)
├── packages.txt              # Dépendances système (ffmpeg) pour Streamlit Cloud
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Installation

**Prérequis :** Python 3.12+ (3.13 recommandé), [ffmpeg](https://ffmpeg.org/download.html) (requis par Whisper), une clé API [Google Gemini](https://aistudio.google.com/apikey).

```bash
git clone https://github.com/Loscope29/polymind.git
cd polymind

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt       # application seule
pip install -r requirements-dev.txt   # application + notebooks
```

### Configuration

```bash
cp .env.example .env      # Windows : copy .env.example .env
```

| Variable | Obligatoire | Rôle |
|---|---|---|
| `GEMINI_API_KEY` | Oui | LLM du RAG et du chatbot bourse |
| `LANGSMITH_API_KEY` | Non | Active le tracing LangSmith |
| `LANGSMITH_PROJECT` | Non | Nom du projet dans LangSmith (défaut : `Polymind`) |

## Utilisation

```bash
streamlit run streamlit_app.py
```

L'application s'ouvre sur <http://localhost:8501>. Chaque outil est accessible depuis la barre latérale.

> Au premier lancement, les modèles Whisper, MMS-TTS, MiniLM et Chronos sont téléchargés depuis Hugging Face / OpenAI (plusieurs centaines de Mo).

### Chatbot Bourse

1. Choisissez une entreprise : `AMD`, `AMZN`, `GE` ou `INTC`.
2. Choisissez le moteur de prévision :
   - **Hugging Face (Chronos)** : modèle de fondation pour séries temporelles, sans entraînement (`amazon/chronos-t5-small`).
   - **Local LSTM** : modèles entraînés dans `notebooks/finance/lstm_price_prediction.ipynb` sur 10 ans d'historique (transformation log → sqrt → différenciation).
3. Posez votre question. Gemini répond à partir de la tendance prévue sur ~126 jours de bourse.

> **Avertissement :** projet pédagogique, les prévisions ne constituent pas un conseil en investissement.

### Test rapide

```bash
python -m scripts.smoke_test_finance
```

## Notebooks

| Notebook | Sujet |
|---|---|
| `notebooks/nlp/rag_pdf.ipynb` | Prototype du pipeline RAG avec persistance Chroma |
| `notebooks/nlp/speech_to_text_whisper.ipynb` | Transcription avec Whisper |
| `notebooks/nlp/text_to_speech_edge_tts.ipynb` | Synthèse vocale avec Edge-TTS |
| `notebooks/ml/diabetes_prediction.ipynb` | Classification du diabète (BRFSS 2015), réseau de neurones |
| `notebooks/ml/house_price_ann.ipynb` | Régression du prix immobilier, ANN |
| `notebooks/finance/lstm_price_prediction.ipynb` | Entraînement des LSTM de prix de clôture |
| `notebooks/finance/lstm_return_direction.ipynb` | Direction des rendements, *directional accuracy*, ratio de Sharpe |
| `notebooks/finance/chronos_forecasting.ipynb` | Prévision zero-shot avec Chronos |

Les notebooks se lancent depuis leur dossier et lisent les données dans `data/` (voir [data/README.md](data/README.md)).

## Docker

L'image embarque l'application, ffmpeg, PyTorch en version CPU et les modèles pré-entraînés (Whisper, MMS-TTS, MiniLM, Chronos), téléchargés au build par `scripts/download_models.py` : le conteneur démarre sans accès à Hugging Face. Les clés API sont injectées à l'exécution et ne sont jamais copiées dans l'image.

```bash
cp .env.example .env          # renseigner GEMINI_API_KEY
docker compose up --build -d
```

L'application est disponible sur <http://localhost:8501>.

Sans Compose :

```bash
docker build -t polymind .
docker run -p 8501:8501 --env-file .env polymind
```

Commandes utiles : `docker compose logs -f` (journaux), `docker compose down` (arrêt).

### Sécurité des dépendances

`requirements.txt` est audité avec [pip-audit](https://pypi.org/project/pip-audit/) :

```bash
pip install pip-audit
pip-audit -r requirements.txt --no-deps --disable-pip
```

Seule exception connue : **chromadb** (CVE-2026-45829, -45830, -45831, -45833, sans correctif publié). Ces failles visent le serveur HTTP de Chroma et son contrôle d'accès ; Polymind utilise Chroma en mémoire, dans le processus de l'application, sans exposer ce serveur : elles ne sont pas exploitables ici.

L'image écoute sur le port 8501 et expose un healthcheck (`/_stcore/health`). Elle peut donc être déployée telle quelle sur un service de conteneurs (Google Cloud Run, Azure Container Apps, AWS App Runner, Hugging Face Spaces). Prévoyez au moins 4 Go de RAM : Whisper, Chronos et TensorFlow sont chargés en mémoire.

## Déploiement (Streamlit Community Cloud)

1. Connectez le dépôt sur [share.streamlit.io](https://share.streamlit.io).
2. *Main file path* : `streamlit_app.py`.
3. Ajoutez `GEMINI_API_KEY` (et éventuellement `LANGSMITH_API_KEY`) dans **Settings → Secrets**.
4. `packages.txt` installe automatiquement `ffmpeg`.

## Auteur

**Loscope29** · Master 2 Data Science, ISJ · [GitHub](https://github.com/Loscope29)
