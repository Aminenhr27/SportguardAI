from pathlib import Path

import joblib
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parents[2] / "ml" / "model.pkl"
_bundle = joblib.load(MODEL_PATH)


def predict_risk(features: dict) -> float:
    X = pd.DataFrame([features])[_bundle["features"]]
    return float(_bundle["model"].predict_proba(X)[0, 1])


def risk_level(score: float) -> str:
    if score < 0.4:
        return "low"
    if score < 0.7:
        return "medium"
    return "high"


def model_version() -> str:
    return _bundle["version"]