"""Minimal executable Keras ANN for shortlist classification."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow import keras

FEATURES = ["experience_months", "notice_period_days", "expected_salary", "skill_match_score"]


def train(csv_path, output_path, epochs=20):
    df = pd.read_csv(csv_path).drop_duplicates()
    x = SimpleImputer(strategy="median").fit_transform(df[FEATURES])
    x = StandardScaler().fit_transform(x).astype("float32")
    y = df["historical_selection_status"].astype(str).str.lower().isin({"selected", "1", "true", "yes"}).astype("float32").to_numpy()
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42, stratify=y)
    model = keras.Sequential([keras.layers.Input(shape=(len(FEATURES),)), keras.layers.Dense(12, activation="relu"), keras.layers.Dropout(0.2), keras.layers.Dense(6, activation="relu"), keras.layers.Dense(1, activation="sigmoid")])
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    model.fit(x_train, y_train, validation_split=0.2, epochs=epochs, batch_size=16, verbose=1)
    print(dict(zip(model.metrics_names, model.evaluate(x_test, y_test, verbose=0))))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv")
    parser.add_argument("--output", default="artifacts/shortlist_ann.keras")
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()
    train(Path(args.csv), Path(args.output), args.epochs)
