import pandas as pd
from sklearn.preprocessing import StandardScaler

def load_data(path):
    df = pd.read_csv(path)
    df = df.drop("Id", axis=1)
    return df

def encode_data(df):
    df_encoded = pd.get_dummies(df, drop_first=True)
    return df_encoded

def scale_features(X):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled, scaler
