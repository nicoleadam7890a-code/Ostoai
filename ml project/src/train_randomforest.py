# Ensemble Model: Logistic Regression + Random Forest for Osteoporosis Prediction
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
import os

# ── 1. Load Data ─────────────────────────────────────────────────
df = pd.read_csv("data/data.csv")
print("✅ Data loaded successfully. Shape:", df.shape)

# ── 2. Preprocessing ────────────────────────────────────────────
if 'Id' in df.columns:
    df = df.drop(columns=['Id'])

df = df.fillna('Unknown')

# ── 3. Encode Categorical Features ───────────────────────────────
categorical_features = df.select_dtypes(include=['object']).columns.tolist()
if 'Osteoporosis' in categorical_features:
    categorical_features.remove('Osteoporosis')

print(f"📋 Encoding {len(categorical_features)} categorical features: {categorical_features}")
df_encoded = pd.get_dummies(df, columns=categorical_features)

# ── 4. Feature / Target Split ────────────────────────────────────
X = df_encoded.drop(columns=['Osteoporosis'])
y = df_encoded['Osteoporosis']
feature_names = X.columns.tolist()
print(f"📊 Total features after encoding: {len(feature_names)}")

# ── 5. Train / Test Split ────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"🔀 Train: {X_train.shape[0]} samples | Test: {X_test.shape[0]} samples")

# ── 6. Feature Scaling ───────────────────────────────────────────
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ── 7. Train Logistic Regression ─────────────────────────────────
lr_model = LogisticRegression(max_iter=1000, random_state=42)
lr_model.fit(X_train_scaled, y_train)
lr_pred = lr_model.predict(X_test_scaled)
lr_proba = lr_model.predict_proba(X_test_scaled)
print(f"\n🎯 Logistic Regression Accuracy: {accuracy_score(y_test, lr_pred):.4f}")

# ── 8. Train Random Forest ───────────────────────────────────────
rf_model = RandomForestClassifier(n_estimators=200, random_state=42)
rf_model.fit(X_train_scaled, y_train)
rf_pred = rf_model.predict(X_test_scaled)
rf_proba = rf_model.predict_proba(X_test_scaled)
print(f"🎯 Random Forest Accuracy: {accuracy_score(y_test, rf_pred):.4f}")

# ── 9. Ensemble: Average of both model probabilities ─────────────
ensemble_proba = (lr_proba + rf_proba) / 2
ensemble_pred = (ensemble_proba[:, 1] >= 0.5).astype(int)

ensemble_accuracy = accuracy_score(y_test, ensemble_pred)
print(f"\n🏆 Ensemble (Average) Accuracy: {ensemble_accuracy:.4f}")
print("\n📄 Ensemble Classification Report:")
print(classification_report(y_test, ensemble_pred))
print("📊 Ensemble Confusion Matrix:")
print(confusion_matrix(y_test, ensemble_pred))

# ── 10. Save All Models ──────────────────────────────────────────
os.makedirs('models', exist_ok=True)
joblib.dump(lr_model, "models/logistic_model.pkl")
joblib.dump(rf_model, "models/random_forest_model.pkl")
joblib.dump(scaler, "models/scaler.pkl")
joblib.dump(feature_names, "models/feature_names.pkl")

print("\n✅ All models saved to models/ directory:")
print("   - logistic_model.pkl       (Logistic Regression)")
print("   - random_forest_model.pkl  (Random Forest)")
print("   - scaler.pkl               (StandardScaler)")
print("   - feature_names.pkl        (Feature Names)")
