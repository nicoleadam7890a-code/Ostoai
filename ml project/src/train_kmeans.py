import joblib
from sklearn.cluster import KMeans
import pandas as pd
import os

# ── 1. Load Data ─────────────────────────────────────────────────
df = pd.read_csv("data/data.csv")
if 'Id' in df.columns:
    df = df.drop(columns=['Id'])
df = df.fillna('Unknown')

# ── 2. Load Unified Scaling Artifacts ──────────────────────────────
models_dir = 'models'
scaler = joblib.load(os.path.join(models_dir, 'scaler.pkl'))
feature_names = joblib.load(os.path.join(models_dir, 'feature_names.pkl'))

# ── 3. Encode and Align Features ──────────────────────────────────
categorical_features = df.select_dtypes(include=['object']).columns.tolist()
if 'Osteoporosis' in categorical_features:
    categorical_features.remove('Osteoporosis')
df_encoded = pd.get_dummies(df, columns=categorical_features)

# Reconstruct exact feature set
X = pd.DataFrame(0, index=df_encoded.index, columns=feature_names)
for col in feature_names:
    if col in df_encoded.columns:
        X[col] = df_encoded[col]
    elif col in df.columns:
        X[col] = df[col]

# ── 4. Scale and Train ────────────────────────────────────────────
X_scaled = scaler.transform(X)

print(f"🔄 Training KMeans on {X_scaled.shape[1]} features...")
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
kmeans.fit(X_scaled)

# ── 5. Save ───────────────────────────────────────────────────────
joblib.dump(kmeans, os.path.join(models_dir, "kmeans_model.pkl"))
print("✅ KMeans model retrained and synchronized.")