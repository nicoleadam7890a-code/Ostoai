# Model Evaluation Script: Logistic Regression + Random Forest Ensemble
import pandas as pd
import numpy as np
import joblib
import os
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    classification_report,
    precision_score,
    recall_score,
    f1_score
)

def evaluate_ensemble():
    # ── 1. Load Models & Metadata ─────────────────────────────────────
    try:
        logistic_model = joblib.load("models/logistic_model.pkl")
        rf_model = joblib.load("models/random_forest_model.pkl")
        scaler = joblib.load("models/scaler.pkl")
        feature_names = joblib.load("models/feature_names.pkl")
        print("[SUCCESS] Models and metadata loaded successfully.")
    except Exception as e:
        print(f"[ERROR] Error loading models: {e}")
        return

    # ── 2. Load Data ─────────────────────────────────────────────────
    try:
        df = pd.read_csv("data/data.csv")
        print(f"[SUCCESS] Data loaded successfully. Shape: {df.shape}")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return

    # ── 3. Preprocessing ────────────────────────────────────────────
    if 'Id' in df.columns:
        df = df.drop(columns=['Id'])
    df = df.fillna('Unknown')

    # ── 4. Encoding ─────────────────────────────────────────────────
    categorical_features = df.select_dtypes(include=['object']).columns.tolist()
    if 'Osteoporosis' in categorical_features:
        categorical_features.remove('Osteoporosis')
    
    # Use the same encoding logic as in training
    df_encoded = pd.get_dummies(df, columns=categorical_features)
    
    # Ensure columns match the training set
    X = df_encoded.drop(columns=['Osteoporosis'])
    X = X.reindex(columns=feature_names, fill_value=0)
    y_true = df_encoded['Osteoporosis']

    # ── 5. Scaling ──────────────────────────────────────────────────
    X_scaled = scaler.transform(X)

    # ── 6. Ensemble Prediction (Average Probabilities) ─────────────
    proba_lr = logistic_model.predict_proba(X_scaled)
    proba_rf = rf_model.predict_proba(X_scaled)
    
    avg_proba = (proba_lr + proba_rf) / 2
    y_pred = (avg_proba[:, 1] >= 0.5).astype(int)

    # ── 7. Calculate Metrics ───────────────────────────────────────
    print("\n" + "="*40)
    print("       MODEL EVALUATION METRICS")
    print("="*40)
    
    # Accuracy
    acc = accuracy_score(y_true, y_pred)
    print(f"Accuracy Score:    {acc:.4f}")
    
    # Precision, Recall, F1 (Weighted)
    precision = precision_score(y_true, y_pred, average='weighted')
    recall = recall_score(y_true, y_pred, average='weighted')
    f1 = f1_score(y_true, y_pred, average='weighted')
    
    print(f"Precision Score:   {precision:.4f}")
    print(f"Recall Score:      {recall:.4f}")
    print(f"F1 Score:          {f1:.4f}")
    
    # Classification Report
    print("\nDetailed Classification Report:")
    print("-" * 30)
    print(classification_report(y_true, y_pred))
    
    # Confusion Matrix
    print("\nConfusion Matrix:")
    print("-" * 30)
    cm = confusion_matrix(y_true, y_pred)
    print(cm)
    
    # Error Calculation
    errors = (y_true != y_pred).sum()
    error_rate = errors / len(y_true)
    print("\nPrediction Summary:")
    print(f"Total Samples:     {len(y_true)}")
    print(f"Correct:           {len(y_true) - errors}")
    print(f"Incorrect Errors:  {errors}")
    print(f"Error Rate:        {error_rate:.4f}")
    print("="*40)

if __name__ == "__main__":
    evaluate_ensemble()
