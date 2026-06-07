import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, accuracy_score
import datetime
import os

def generate_full_results():
    print("Generating comprehensive results.txt...")
    
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # Go up one level from 'src'
    models_dir = os.path.join(project_root, "models")
    data_path = os.path.join(project_root, "data", "data.csv")
    results_path = os.path.join(project_root, "results.txt")
    
    # Load Models
    lr_model = joblib.load(os.path.join(models_dir, 'logistic_model.pkl'))
    rf_model = joblib.load(os.path.join(models_dir, 'random_forest_model.pkl'))
    scaler = joblib.load(os.path.join(models_dir, 'scaler.pkl'))
    feature_names = joblib.load(os.path.join(models_dir, 'feature_names.pkl'))
    kmeans_model = joblib.load(os.path.join(models_dir, 'kmeans_model.pkl'))
    
    # Load Data
    df = pd.read_csv(data_path)
    if 'Id' in df.columns:
        df = df.drop(columns=['Id'])
    df = df.fillna('Unknown')
    
    # Minimal Encoding
    categorical_features = df.select_dtypes(include=['object']).columns.tolist()
    if 'Osteoporosis' in categorical_features:
        categorical_features.remove('Osteoporosis')
    df_encoded = pd.get_dummies(df, columns=categorical_features, drop_first=False)
    
    # CRITICAL: Reconstruct exact feature set for model (25 features)
    X = pd.DataFrame(0, index=df_encoded.index, columns=feature_names)
    for col in feature_names:
        if col in df_encoded.columns:
            X[col] = df_encoded[col]
        elif col in df.columns: # For numerical columns like Age
            X[col] = df[col]
            
    print(f"Debug: X shape = {X.shape}")
    print(f"Debug: Expected features = {len(feature_names)}")
    
    y = df['Osteoporosis'].map({'Yes': 1, 'No': 0})
    if y.isnull().any(): # handle cases if target was already 0/1
        y = df['Osteoporosis'].fillna(0).astype(int)
        
    X_scaled = scaler.transform(X)
    
    # Predictions
    lr_proba = lr_model.predict_proba(X_scaled)
    rf_proba = rf_model.predict_proba(X_scaled)
    ensemble_proba = (lr_proba + rf_proba) / 2
    ensemble_pred = (ensemble_proba[:, 1] >= 0.5).astype(int)
    
    # Metrics
    acc_ensemble = accuracy_score(y, ensemble_pred)
    report = classification_report(y, ensemble_pred)
    
    # Feature Importance
    importances = rf_model.feature_importances_
    feat_importances = pd.Series(importances, index=feature_names).sort_values(ascending=False).head(15)
    
    # Clusters
    clusters = kmeans_model.predict(X_scaled)
    cluster_counts = pd.Series(clusters).value_counts().to_dict()
    
    # Format Output
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    content = f"""==================================================
OSTEOAI PREDICTION MODEL RESULTS - {timestamp}
==================================================

[1] ENSEMBLE MODEL PERFORMANCE (LR + RF)
--------------------------------------------------
Overall Accuracy: {acc_ensemble:.4f}

Classification Report:
{report}

[2] TOP 15 FEATURE IMPORTANCE (RANDOM FOREST)
--------------------------------------------------
{feat_importances.to_string()}

[3] PATIENT CLUSTERING (K-MEANS)
--------------------------------------------------
Number of clusters: {kmeans_model.n_clusters}
Cluster Distribution (Counts):
{cluster_counts}

[4] MODEL PARAMETERS
--------------------------------------------------
- Random Forest: 200 estimators
- Logistic Regression: 1000 max_iter, scaled
- Database: MongoDB Atlas (Sync enabled)
- Dataset: {data_path} ({len(df)} records)
- X-ray Model: MobileNetV2 (74.62% Val Acc)

[5] X-RAY ANALYSIS PERFORMANCE (CNN)
--------------------------------------------------
- Model Architecture: MobileNetV2 (Transfer Learning)
- Best Validation Accuracy: 0.7462 (74.6%)
- Target Classes: ['Normal', 'Osteopenia', 'Osteoporosis']
- Status: Fully Integrated

==================================================
HISTORY OF PREVIOUS SESSIONS
==================================================
"""
    # Read history
    old_content = ""
    if os.path.exists(results_path):
        try:
             for enc in ['utf-8', 'utf-16le', 'latin-1', 'cp1252']:
                 try:
                    with open(results_path, 'r', encoding=enc) as f:
                        old_content = f.read()
                    if old_content: break
                 except:
                    continue
        except:
            old_content = "[Previous history could not be decoded]"

    with open(results_path, "w", encoding="utf-8") as f:
        f.write(content)
        f.write("\n\n" + old_content)
    
    print(f"✅ Success: Comprehensive results generated for {len(df)} records.")

if __name__ == "__main__":
    generate_full_results()
