"""Train, compare, evaluate and persist two shortlist classifiers."""
import argparse
from pathlib import Path
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, RocCurveDisplay
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

FEATURES = ["experience_months", "notice_period_days", "expected_salary", "skill_match_score"]


def remove_outliers(frame, columns):
    result = frame.copy(deep=True)
    for column in columns:
        q1, q3 = result[column].quantile([0.25, 0.75])
        iqr = q3 - q1
        result[column] = result[column].clip(q1 - 1.5 * iqr, q3 + 1.5 * iqr)
    return result


def train(csv_path, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(csv_path).drop_duplicates().drop(columns=["candidate_name", "email", "phone", "resume_text", "portfolio_url"], errors="ignore")
    target = df["historical_selection_status"].astype(str).str.lower().isin({"selected", "1", "true", "yes"}).astype(int)
    df = remove_outliers(df, ["experience_months", "notice_period_days", "expected_salary"])
    x = df[FEATURES].replace([np.inf, -np.inf], np.nan)
    x_train, x_test, y_train, y_test = train_test_split(x, target, test_size=0.25, random_state=42, stratify=target)
    preprocess = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("select", SelectKBest(f_classif, k="all"))])
    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced"),
    }
    results = {}
    best = None
    for name, estimator in candidates.items():
        pipeline = Pipeline([("preprocess", preprocess), ("model", estimator)])
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        probabilities = pipeline.predict_proba(x_test)[:, 1]
        results[name] = {"accuracy": accuracy_score(y_test, predictions), "roc_auc": roc_auc_score(y_test, probabilities), "report": classification_report(y_test, predictions)}
        if best is None or results[name]["roc_auc"] > results[best[0]]["roc_auc"]:
            best = (name, pipeline)
    joblib.dump({"model": best[1], "algorithm": best[0], "features": FEATURES, "metrics": results[best[0]]}, output_dir / "shortlist_model.joblib")
    RocCurveDisplay.from_estimator(best[1], x_test, y_test)
    plt.title(f"Shortlist ROC curve - {best[0]}")
    plt.tight_layout()
    plt.savefig(output_dir / "roc_curve.png", dpi=160)
    print(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv")
    parser.add_argument("--output-dir", default="artifacts")
    args = parser.parse_args()
    train(Path(args.csv), Path(args.output_dir))
