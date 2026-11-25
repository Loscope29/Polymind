import os
import tempfile

import streamlit as st

from polymind import rag

st.set_page_config(page_title="RAG PDF · Polymind", page_icon="📄")
st.title("📄 RAG : questions et réponses sur un PDF")
st.write("Téléversez un PDF et posez une question sur son contenu.")

pdf_file = st.file_uploader("Choisir un fichier PDF", type=["pdf"])
question = st.text_input("Votre question :")

if pdf_file is not None and question and st.button("Obtenir la réponse"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.getbuffer())
        temp_path = tmp.name
    try:
        with st.spinner("Analyse du document..."):
            result = rag.main(temp_path, question)
    except Exception as e:
        st.error(f"Erreur : {e}")
    else:
        st.success("Réponse générée !")
        st.markdown(f"**Question :** {question}")
        st.markdown(f"**Réponse :** {result['answer']}")
    finally:
        os.remove(temp_path)
