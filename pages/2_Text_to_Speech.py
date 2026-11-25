import io

import numpy as np
import streamlit as st
from scipy.io.wavfile import write

st.set_page_config(page_title="Text to Speech · Polymind", page_icon="🔊")
st.title("🔊 Text to Speech avec VITS")
st.write("Entrez un texte en français pour générer l'audio correspondant.")


@st.cache_resource(show_spinner="Chargement du modèle TTS...")
def get_tts():
    from polymind import text_to_speech
    return text_to_speech


text = st.text_area("Texte à convertir :", height=100)

if text and st.button("Générer l'audio"):
    tts = get_tts()
    with st.spinner("Génération en cours..."):
        audio = tts.text_to_speech(text)

    audio_bytes = io.BytesIO()
    write(audio_bytes, tts.model.config.sampling_rate, audio.astype(np.float32))

    st.success("Audio généré !")
    st.audio(audio_bytes.getvalue(), format="audio/wav")
    st.download_button(
        "Télécharger l'audio", audio_bytes.getvalue(),
        file_name="generated_audio.wav", mime="audio/wav",
    )
