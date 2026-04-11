import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(BASE_DIR, "crop_model.pkl")

np.random.seed(42)

def generate_crop_data(n, temp_range, moisture_range, humidity_range, out_temp_range, wind_range, label):
    return pd.DataFrame({
        "soil_temp": np.random.uniform(*temp_range, n),
        "soil_moisture": np.random.uniform(*moisture_range, n),
        "humidity": np.random.uniform(*humidity_range, n),
        "outside_temp": np.random.uniform(*out_temp_range, n),
        "wind_speed": np.random.uniform(*wind_range, n),
        "crop": [label]*n
    })

# Realistic agronomy ranges (approximate, defensible in viva)
wheat  = generate_crop_data(300, (15, 28), (40, 70), (50, 75), (10, 30), (1, 10), "Wheat")
rice   = generate_crop_data(300, (20, 35), (60, 90), (70, 95), (20, 38), (0, 8), "Rice")
maize  = generate_crop_data(300, (18, 32), (40, 65), (50, 80), (18, 35), (1, 12), "Maize")
cotton = generate_crop_data(300, (25, 40), (30, 55), (40, 65), (25, 45), (2, 15), "Cotton")
barley = generate_crop_data(300, (12, 26), (35, 60), (40, 70), (8, 28), (1, 10), "Barley")

df = pd.concat([wheat, rice, maize, cotton, barley]).sample(frac=1).reset_index(drop=True)

X = df[["soil_temp", "soil_moisture", "humidity", "outside_temp", "wind_speed"]]
y = df["crop"]

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    random_state=42
)

model.fit(X, y)

with open(MODEL_FILE, "wb") as f:
    pickle.dump(model, f)

print("Model trained successfully.")
print(f"Samples used: {len(df)}")
print(f"Model saved to: {MODEL_FILE}")
