import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# -------------------------
# Paths
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "crop_data.csv")
MODEL_FILE = os.path.join(BASE_DIR, "crop_model.pkl")

# -------------------------
# Load Kaggle Dataset
# -------------------------
df = pd.read_csv(DATA_FILE)

print("Dataset loaded:", df.shape)

# Kaggle columns:
# N, P, K, temperature, humidity, ph, rainfall, label

# -------------------------
# Feature engineering
# We only keep features we can realistically approximate with sensors
# -------------------------
df_model = df[["temperature", "humidity", "rainfall", "label"]].copy()

# Create synthetic "moisture proxy" from rainfall + humidity
df_model["moisture"] = (
    0.6 * df_model["rainfall"] +
    0.4 * df_model["humidity"]
)

# Normalize moisture to 0–100
df_model["moisture"] = (
    100 * (df_model["moisture"] - df_model["moisture"].min()) /
    (df_model["moisture"].max() - df_model["moisture"].min())
)

# Final features aligned to sensors
X = df_model[["temperature", "humidity", "moisture"]]
y = df_model["label"]

print("Features used:", list(X.columns))
print("Samples:", len(X))

# -------------------------
# Split
# -------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# -------------------------
# Pipeline (scaler + model)
# -------------------------
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("rf", RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=3,
        random_state=42
    ))
])

# -------------------------
# Train
# -------------------------
print("\nTraining model...")
pipeline.fit(X_train, y_train)

# -------------------------
# Evaluate
# -------------------------
y_pred = pipeline.predict(X_test)
acc = accuracy_score(y_test, y_pred)

print("\nAccuracy:", round(acc * 100, 2), "%")
print("\nClassification report:\n")
print(classification_report(y_test, y_pred))

# -------------------------
# Save model
# -------------------------
with open(MODEL_FILE, "wb") as f:
    pickle.dump(pipeline, f)

print(f"\nModel saved to: {MODEL_FILE}")
print("Done.")
