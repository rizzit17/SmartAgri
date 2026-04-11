import pandas as pd
import os
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# ---------------------------
# Paths
# ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "crop_data.csv")
SENSOR_PATH = os.path.join(BASE_DIR, "sensor_log.csv")
MODEL_PATH = os.path.join(BASE_DIR, "crop_model.pkl")

# ---------------------------
# Load Kaggle Dataset
# ---------------------------
print("\nLoading Kaggle dataset...")

df = pd.read_csv(DATASET_PATH)

print("Dataset shape:", df.shape)
print(df.head())

# ---------------------------
# Keep only relevant features
# ---------------------------
# Kaggle has: temperature, humidity, rainfall
# We will map these to our sensors:
# soil_temp ≈ temperature
# soil_humidity ≈ humidity
# soil_moisture ≈ rainfall proxy

df_ml = df[["temperature", "humidity", "rainfall", "label"]].copy()

# Rename columns to match our dashboard pipeline
df_ml.columns = ["soil_temp", "humidity", "moisture_proxy", "crop"]

# ---------------------------
# OPTIONAL: Add your real sensor data (if exists)
# ---------------------------
if os.path.exists(SENSOR_PATH):
    print("\nLoading sensor_log.csv and merging...")

    df_sensor = pd.read_csv(SENSOR_PATH)

    # Only keep valid rows
    df_sensor = df_sensor.dropna(subset=["soil_temp", "soil_humidity", "soil_moisture"])

    # Map to ML format
    df_sensor_ml = pd.DataFrame()
    df_sensor_ml["soil_temp"] = df_sensor["soil_temp"]
    df_sensor_ml["humidity"] = df_sensor["soil_humidity"]
    df_sensor_ml["moisture_proxy"] = df_sensor["soil_moisture"]
    
    # Since sensor data doesn't have crop labels, we skip label usage
    print(f"Sensor samples available: {len(df_sensor_ml)} (not used for supervised training)")

else:
    print("\nNo sensor_log.csv found. Training only on Kaggle data.")

# ---------------------------
# Features and labels
# ---------------------------
X = df_ml[["soil_temp", "humidity", "moisture_proxy"]]
y = df_ml["crop"]

print("\nTraining samples:", len(X))
print("Unique crops:", y.nunique())

# ---------------------------
# Train/Test Split
# ---------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ---------------------------
# Train Model
# ---------------------------
print("\nTraining RandomForest model...")

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    random_state=42
)

model.fit(X_train, y_train)

# ---------------------------
# Evaluation
# ---------------------------
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print("\nModel Accuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# ---------------------------
# Feature Importance
# ---------------------------
importance = model.feature_importances_

print("\nFeature Importance:")
for col, imp in zip(X.columns, importance):
    print(f"{col}: {round(imp * 100, 2)}%")

# ---------------------------
# Save model
# ---------------------------
with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

print("\nModel saved to:", MODEL_PATH)
print("\nTraining complete. You can now run dashboard.py")
