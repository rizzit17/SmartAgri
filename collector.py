import paho.mqtt.client as mqtt
import json
import csv
import os
import requests
from datetime import datetime
import tempfile
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ========== CONFIG (loaded from .env) ==========
BROKER = os.getenv("MQTT_BROKER")
PORT = int(os.getenv("MQTT_PORT", "8883"))
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")
TOPIC = os.getenv("MQTT_TOPIC", "smartagri/data")

LAT = float(os.getenv("LATITUDE", "12.9676"))
LON = float(os.getenv("LONGITUDE", "79.1338"))
CITY = os.getenv("CITY", "Vellore")

# ========== PATHS ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "sensor_log.csv")
LATEST_JSON = os.path.join(BASE_DIR, "latest.json")

print("Working directory:", BASE_DIR)

# ========== WEATHER ==========
def get_weather():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current_weather=true"
        r = requests.get(url, timeout=5)
        data = r.json()
        cw = data.get("current_weather", {})
        return cw.get("temperature"), cw.get("windspeed")
    except Exception as e:
        print("Weather API error:", e)
        return None, None

# ========== ATOMIC JSON WRITE ==========
def write_latest_json(data):
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, dir=BASE_DIR, suffix=".tmp") as f:
            json.dump(data, f, indent=2)
            temp_path = f.name

        shutil.move(temp_path, LATEST_JSON)
        print("Updated latest.json")
    except Exception as e:
        print("JSON write error:", e)

# ========== CSV LOGGER ==========
def write_to_csv(data):
    exists = os.path.isfile(CSV_FILE)

    outside_temp, wind = get_weather()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [
        timestamp,
        data.get("temperature"),
        data.get("humidity"),
        data.get("moisture"),
        data.get("status"),
        data.get("action"),
        outside_temp,
        wind,
        CITY
    ]

    try:
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if not exists:
                writer.writerow([
                    "timestamp",
                    "soil_temp",
                    "soil_humidity",
                    "soil_moisture",
                    "status",
                    "action",
                    "outside_temp",
                    "wind_speed",
                    "city"
                ])

            writer.writerow(row)

        print("Logged to CSV")

    except Exception as e:
        print("CSV write error:", e)

# ========== MQTT ==========
def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected:", reason_code)
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print("Received:", data)

        # Get weather
        outside_temp, wind = get_weather()

        # Enriched live payload
        enriched = {
            **data,
            "outside_temp": outside_temp,
            "wind_speed": wind,
            "city": CITY
        }

        write_latest_json(enriched)
        write_to_csv(data)

    except Exception as e:
        print("Message error:", e)

# ========== RUN ==========
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()

client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT)
    print("Collector running...")
    client.loop_forever()
except KeyboardInterrupt:
    print("Stopped by user")
except Exception as e:
    print("MQTT error:", e)
