"""
Pulse Guardian ICU - Model Training & Validation
=================================================
Trains a real, validated mortality-risk classifier on the MIMIC-III
derived dataset (final_icu_dataset.csv) and evaluates it against a
held-out test set AND against the hand-tuned rule-based risk engine
(risk_engine.py), which serves as the project's baseline.

Ground-truth label: HOSPITAL_EXPIRE_FLAG (in-hospital mortality),
the only outcome column available in the dataset that can serve as
a real target for supervised validation.

Run:
    python -m app.ml.train_model

Outputs (checked into the repo for reproducibility and so the API can
serve real numbers without retraining on every boot):
    app/ml/artifacts/metrics.json   - full evaluation report (this project's
                                       answer to assignment section 3:
                                       "results, baseline comparison, discussion")
    app/ml/artifacts/model.joblib   - trained classifier
    app/ml/artifacts/imputer.joblib - median imputer fit on the training split

IMPORTANT: This is an academic validation exercise on a retrospective,
de-identified research dataset. It is NOT a validated clinical tool.
"""

import json
import os
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split

from app.ml.risk_engine import calculate_risk_score

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "..", "..", "data", "final_icu_dataset.csv")
ARTIFACT_DIR = os.path.join(HERE, "artifacts")

# Feature columns -> map straight to the indicators the rule engine already
# scores, so the ML model and the baseline are evaluated on the same
# clinical inputs (apples-to-apples comparison).
FEATURE_COLUMNS = {
    "HeartRate_mean": "heart_rate",
    "RespiratoryRate_mean": "resp_rate",
    "SpO2_mean": "spo2",
    "SystolicBP_mean": "bp_systolic",
    "DiastolicBP_mean": "bp_diastolic",
    "Creatinine_mean": "creatinine",
    "Glucose_mean": "glucose",
    "Hemoglobin_mean": "hemoglobin",
    "Potassium_mean": "potassium",
    "Sodium_mean": "sodium",
    "WBC_mean": "wbc",
    "LOS": "icu_los",
}

RANDOM_STATE = 42


def _load_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, low_memory=False)
    df = df.dropna(subset=["HOSPITAL_EXPIRE_FLAG"])
    return df


def _metrics_at_threshold(y_true, y_score, threshold) -> dict:
    y_pred = (y_score >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "threshold": threshold,
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_true, y_pred, zero_division=0), 4),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
    }


def evaluate_rule_based_baseline(df: pd.DataFrame) -> dict:
    """
    Runs the existing hand-weighted rule engine (risk_engine.py) over every
    row and scores it against the real mortality label. This is the
    project's baseline for the required baseline comparison.
    """
    scores = []
    for _, row in df.iterrows():
        indicators = {v: row.get(k) for k, v in FEATURE_COLUMNS.items()}
        result = calculate_risk_score(indicators)
        scores.append(result["score"])

    y_true = df["HOSPITAL_EXPIRE_FLAG"].astype(int).to_numpy()
    y_score = np.array(scores) / 100.0  # normalize 0-100 -> 0-1 for AUC

    auc = round(roc_auc_score(y_true, y_score), 4)
    # The rule engine's own published risk bands: High risk = score >= 70
    at_high_band = _metrics_at_threshold(y_true, y_score, 0.70)

    # What the rule engine COULD achieve if its threshold were calibrated
    # on real outcomes, instead of picked by hand. This isolates "the
    # engine can rank patients reasonably" from "the published 70-point
    # cutoff was never validated against data."
    best_f1, best_threshold = -1.0, 0.5
    for t in np.arange(0.05, 0.95, 0.01):
        f1 = f1_score(y_true, (y_score >= t).astype(int), zero_division=0)
        if f1 > best_f1:
            best_f1, best_threshold = f1, round(float(t), 2)
    at_best_threshold = _metrics_at_threshold(y_true, y_score, best_threshold)

    return {
        "name": "Rule-based risk engine (hand-tuned weights, no training)",
        "auc_roc": auc,
        "as_published": at_high_band,
        "if_threshold_were_calibrated": at_best_threshold,
    }


def train_and_evaluate_ml_model(df: pd.DataFrame) -> dict:
    X = df[list(FEATURE_COLUMNS.keys())].copy()
    y = df["HOSPITAL_EXPIRE_FLAG"].astype(int).to_numpy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    imputer = SimpleImputer(strategy="median")
    X_train_imp = imputer.fit_transform(X_train)
    X_test_imp = imputer.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=25,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train_imp, y_train)

    # 5-fold cross-validated AUC on the training split, for a stability
    # estimate that isn't just a single lucky train/test split.
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_aucs = []
    for train_idx, val_idx in skf.split(X_train_imp, y_train):
        fold_model = RandomForestClassifier(
            n_estimators=300, max_depth=8, min_samples_leaf=25,
            class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1,
        )
        fold_model.fit(X_train_imp[train_idx], y_train[train_idx])
        fold_pred = fold_model.predict_proba(X_train_imp[val_idx])[:, 1]
        cv_aucs.append(roc_auc_score(y_train[val_idx], fold_pred))

    y_score = model.predict_proba(X_test_imp)[:, 1]
    test_auc = round(roc_auc_score(y_test, y_score), 4)
    at_default = _metrics_at_threshold(y_test, y_score, 0.5)

    feature_importance = sorted(
        zip(FEATURE_COLUMNS.keys(), model.feature_importances_),
        key=lambda t: t[1], reverse=True,
    )

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(ARTIFACT_DIR, "model.joblib"))
    joblib.dump(imputer, os.path.join(ARTIFACT_DIR, "imputer.joblib"))

    return {
        "name": "Random Forest classifier (trained, held-out test set)",
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "positive_rate_train": round(float(y_train.mean()), 4),
        "positive_rate_test": round(float(y_test.mean()), 4),
        "cv_auc_mean": round(float(np.mean(cv_aucs)), 4),
        "cv_auc_std": round(float(np.std(cv_aucs)), 4),
        "test_auc_roc": test_auc,
        **at_default,
        "feature_importance": [
            {"feature": name, "importance": round(float(imp), 4)}
            for name, imp in feature_importance
        ],
    }


def main():
    print("Loading dataset...")
    df = _load_dataset()
    print(f"Rows with a valid outcome label: {len(df)}")
    print(f"Mortality rate in dataset: {df['HOSPITAL_EXPIRE_FLAG'].mean():.3%}")

    print("Evaluating rule-based baseline against ground truth...")
    baseline = evaluate_rule_based_baseline(df)

    print("Training + evaluating Random Forest model (train/test split + 5-fold CV)...")
    ml_result = train_and_evaluate_ml_model(df)

    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "dataset": {
            "source": "MIMIC-III derived, final_icu_dataset.csv",
            "n_rows": int(len(df)),
            "label": "HOSPITAL_EXPIRE_FLAG (in-hospital mortality)",
            "positive_rate": round(float(df["HOSPITAL_EXPIRE_FLAG"].mean()), 4),
        },
        "baseline_rule_engine": baseline,
        "ml_model": ml_result,
        "comparison": {
            "auc_roc_improvement": round(
                ml_result["test_auc_roc"] - baseline["auc_roc"], 4
            ),
            "note": (
                "The rule-based engine uses fixed, manually chosen weights "
                "and was never fit to outcome data. The Random Forest is "
                "trained on a stratified 80/20 split and validated with "
                "5-fold cross-validation; AUC-ROC is reported on the "
                "untouched test set. Both are scored against the same "
                "ground-truth label (HOSPITAL_EXPIRE_FLAG) for a fair "
                "comparison."
            ),
        },
        "disclaimer": (
            "Academic validation on a retrospective, de-identified "
            "research dataset. Not a validated clinical decision support "
            "tool and not intended for real patient care."
        ),
    }

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    out_path = os.path.join(ARTIFACT_DIR, "metrics.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nSaved evaluation report to {out_path}")
    print(json.dumps(report["comparison"], indent=2))


if __name__ == "__main__":
    main()
