import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from preprocessing import load_data, encode_data, scale_features

# Load
df = load_data("data/data.csv")
df = encode_data(df)

# Split
X = df.drop("Osteoporosis", axis=1)
y = df["Osteoporosis"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Scale
X_train_scaled, scaler = scale_features(X_train)
X_test_scaled = scaler.transform(X_test)

# Train
model = LogisticRegression(max_iter=1000)
model.fit(X_train_scaled, y_train)

# Evaluate
pred = model.predict(X_test_scaled)
print("Accuracy:", accuracy_score(y_test, pred))
print(classification_report(y_test, pred))

# Save
joblib.dump(model, "models/logistic_model.pkl")
joblib.dump(scaler, "models/scaler.pkl")
feature_names = X.columns
joblib.dump(feature_names, "models/feature_names.pkl")