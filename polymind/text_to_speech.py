"""Synthèse vocale texte → audio (français) avec Meta MMS-TTS (VITS)."""

import numpy as np
import torch
from langsmith import traceable
from transformers import AutoTokenizer, VitsModel

from polymind.config import TTS_MODEL, setup_tracing

setup_tracing()

model = VitsModel.from_pretrained(TTS_MODEL)
tokenizer = AutoTokenizer.from_pretrained(TTS_MODEL)


@traceable(run_type="chain", name="TextToSpeech-VITS")
def text_to_speech(text: str) -> np.ndarray:
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        audio = model(**inputs).waveform
    return audio.squeeze().cpu().numpy()
