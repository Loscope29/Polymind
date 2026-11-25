"""Synthèse vocale texte → audio (français) avec Meta MMS-TTS (VITS)."""

import numpy as np
import torch
from langsmith import traceable
from transformers import AutoTokenizer, VitsModel

from polymind.config import setup_tracing

setup_tracing()

MODEL_NAME = "facebook/mms-tts-fra"

model = VitsModel.from_pretrained(MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


@traceable(run_type="chain", name="TextToSpeech-VITS")
def text_to_speech(text: str) -> np.ndarray:
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        audio = model(**inputs).waveform
    return audio.squeeze().cpu().numpy()
