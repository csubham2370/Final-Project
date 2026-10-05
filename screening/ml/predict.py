from pathlib import Path
import joblib
import numpy as np

MODEL_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "shortlist_model.joblib"


def _feature_row(payload):
    required = ("experience_months", "notice_period_days", "expected_salary", "skill_match_score")
    missing = [key for key in required if key not in payload]
    if missing:
        raise KeyError("Missing fields: " + ", ".join(missing))
    return np.array([[float(payload[key]) for key in required]])


def predict_shortlist(payload):
    row = _feature_row(payload)
    if MODEL_PATH.exists():
        bundle = joblib.load(MODEL_PATH)
        model = bundle["model"]
        probability = float(model.predict_proba(row)[0, 1])
        algorithm = bundle.get("algorithm", model.__class__.__name__)
    else:
        experience, notice, salary, skill = row[0]
        raw = 0.35 * min(experience / 24, 1) + 0.45 * min(max(skill, 0), 1) + 0.1 * (notice <= 30) + 0.1 * (salary <= 700000)
        probability = float(np.clip(raw, 0, 1))
        algorithm = "documented-rule-fallback"
    return {"prediction": "SELECTED" if probability >= 0.5 else "REJECTED", "confidence": round(probability, 4), "algorithm": algorithm}
