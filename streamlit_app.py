import streamlit as st

st.set_page_config(page_title="Polymind", layout="wide")

st.title("Polymind")
st.caption("Une boîte à outils IA : voix, documents et finance, réunis dans une seule application.")

st.markdown(
    """
Choisissez un outil dans la barre latérale :

| Outil | Ce qu'il fait | Modèle |
|---|---|---|
| **Audio to Text** | Transcrit un fichier audio en texte | OpenAI Whisper |
| **Text to Speech** | Génère une voix française à partir d'un texte | Meta MMS-TTS (VITS) |
| **RAG PDF** | Répond à vos questions sur un document PDF | Gemini 2.5 Flash + Chroma |
| **Chatbot Bourse** | Prévoit et commente l'évolution d'une action | Chronos / LSTM + Gemini |
"""
)

st.sidebar.success("Sélectionnez un outil ci-dessus.")
