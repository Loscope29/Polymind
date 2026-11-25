import os
import tempfile

import streamlit as st

st.set_page_config(page_title="Audio to Text · Polymind")
st.title("Audio to Text avec Whisper")
st.write("Téléversez un fichier audio pour le transcrire en texte.")


@st.cache_resource(show_spinner="Chargement du modèle Whisper...")
def get_stt():
    from polymind import speech_to_text
    return speech_to_text


audio_file = st.file_uploader("Choisir un fichier audio", type=["wav", "mp3", "m4a"])

if audio_file is not None and st.button("Transcrire"):
    suffix = os.path.splitext(audio_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_file.getbuffer())
        temp_path = tmp.name
    try:
        with st.spinner("Transcription en cours..."):
            transcription = get_stt().audio_to_text(temp_path)
    finally:
        os.remove(temp_path)

    st.success("Transcription terminée !")
    st.text_area("Transcription :", transcription, height=200)
    st.download_button(
        "Télécharger la transcription", transcription,
        file_name="transcription.txt", mime="text/plain",
    )
