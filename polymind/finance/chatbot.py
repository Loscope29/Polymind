"""Chatbot financier : Gemini commente les prévisions de cours."""

import numpy as np
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable

from polymind.config import MODELS_DIR, get_gemini_key, setup_tracing

setup_tracing(project="Polymind - Bourse")

@st.cache_resource
@traceable
def get_chatbot_response(company, predictions, user_question):
    gemini_key = get_gemini_key()

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        google_api_key=gemini_key
    )

    if len(predictions) == 0:
        return "Erreur : Aucune donnée de prédiction disponible."

    last_price = predictions[-1]
    first_price = predictions[0]
    if first_price == 0:
        variation = 0
    else:
        variation = ((last_price - first_price) / first_price) * 100
    trend = "hausse" if variation > 0 else "baisse"

    system_prompt = f"""Tu es un assistant financier expert.Tu aides les utilisateurs à comprendre les tendances du marché boursier en te basant sur des données de prédiction. 


Voici les données de prédiction pour {company} :
- Prix prédit dans {len(predictions)//21} mois : {last_price:.2f} $
- Variation estimée : {variation:.2f}% ({trend})
- Tendance générale : {trend}

Réponds aux questions de l'utilisateur en te basant sur ces données.
Rappelle toujours que ce sont des prédictions, pas des certitudes."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]

    response = llm.invoke(messages)
    usage = response.usage_metadata
    print(f"Tokens utilisés : {usage.get('total_tokens', 'N/A')}, Coût estimé : ${usage.get('total_cost', 'N/A')}")
    return response.content

if __name__ == "__main__":
    # Démo en ligne de commande à partir des prédictions sauvegardées
    predictions_path = MODELS_DIR / "finance" / "predicted_prices.npy"
    predictions = np.load(predictions_path).flatten().tolist()
    question = (
        "Quelle est la tendance générale pour Amazon dans les prochains mois ? "
        "Donne des actions à faire pour un investisseur qui veut investir dans Amazon."
    )
    print("Chatbot :", get_chatbot_response("Amazon", predictions, question))
