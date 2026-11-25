"""Test rapide des deux moteurs de prévision (à lancer depuis la racine du projet).

    python -m scripts.smoke_test_finance
"""

import traceback

from polymind.finance import prediction

for name, fn in [("Chronos", prediction.predict_with_hf), ("LSTM", prediction.predict_with_lstm)]:
    try:
        preds = fn("AMD")
        print(f"[OK] {name}: {len(preds)} jours, premiers prix = {preds[:3]}")
    except Exception:
        print(f"[ECHEC] {name}")
        traceback.print_exc()
