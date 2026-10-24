<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/MQTT-HiveMQ-FFD700?style=for-the-badge&logo=eclipsemosquitto&logoColor=black" />
  <img src="https://img.shields.io/badge/ML-scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

<h1 align="center">Smart Agriculture IoT System</h1>

<p align="center">
  <b>Sensor readings, crop model suggestions, weather and field reports in a simple cream-and-sage dashboard.</b>
</p>

---

## Overview

### Interactive research simulation

Run `python simulator/server.py` or double-click `Start-Simulator.cmd`, then open **http://127.0.0.1:8766**. The local browser lab includes nine synthetic scenarios, fuzzy and threshold comparison, replay, fault injection, signals/rules, CSV/JSON exports and a 17-check bench. Core simulation needs only Python 3.10+. See [the full simulation guide](simulator/README.md) and [research figure checklist](docs/SIMULATION_GUIDE.md). These software experiments do not establish water savings or field performance.

The [editable research paper](research/ProgIoT%20DA-7%20Research%20Paper%20Rishit%2023BCT0157.docx) includes the test conditions and 11 captured figures. Matching [raw experiment records](docs/simulation-evidence/) and [verification notes](docs/SIMULATION_VALIDATION.md) are archived with the source. The optional crop model can be reproduced with `python simulator/train_model.py`.

Smart Agriculture is a full-stack IoT solution designed for modern precision farming. It collects real-time environmental data from soil sensors via MQTT, enriches it with live weather data, uses a trained Random Forest model to recommend optimal crops, and surfaces everything through an interactive Streamlit dashboard with a built-in farming chatbot.

### Key Features

| Feature | Description |
|---|---|
| **Live Sensor Monitoring** | Real-time soil temperature, humidity, and moisture readings via MQTT |
| **AI Crop Recommendation** | Random Forest classifier predicts the best crop with confidence scores (Top 3) |
| **Weather Integration** | Live outside temperature and wind speed from Open-Meteo API |
| **Smart Alerts** | Automated warnings for low moisture, high wind, and extreme conditions |
| **Historical Trends** | Interactive line charts tracking soil metrics over time |
| **Farming Chatbot** | Rule-based assistant covering irrigation, pests, fertilizer, harvest, and more |
| **PDF Report Generation** | Professional farm reports with styled tables, generated via ReportLab |
| **Authentication** | Simple JSON-based login system with password-protected access |
| **Auto Refresh** | Overview refreshes every 5 seconds without resetting other screens |

---

## Architecture

```
┌──────────────┐     MQTT (TLS)      ┌──────────────────┐
│  IoT Sensors │ ──────────────────▶ │   collector.py    │
│  (ESP32/     │                     │  ┌──────────────┐ │
│   Arduino)   │                     │  │ MQTT Client  │ │
└──────────────┘                     │  └──────┬───────┘ │
                                     │         │         │
                                     │  ┌──────▼───────┐ │
                                     │  │ Weather API  │ │    ┌────────────────┐
                                     │  │ (Open-Meteo) │ │    │  dashboard.py   │
                                     │  └──────┬───────┘ │    │  ┌────────────┐ │
                                     │         │         │    │  │ Streamlit  │ │
                                     │  ┌──────▼───────┐ │    │  │ UI + Auth  │ │
                                     │  │ latest.json  │─┼───▶│  ├────────────┤ │
                                     │  │ sensor_log   │─┼───▶│  │ ML Model   │ │
                                     │  │   .csv       │ │    │  │ (sklearn)  │ │
                                     │  └──────────────┘ │    │  ├────────────┤ │
                                     └──────────────────┘    │  │ Chatbot    │ │
                                                              │  ├────────────┤ │
                                                              │  │ PDF Report │ │
                                                              │  └────────────┘ │
                                                              └────────────────┘
```

---

## Project Structure

```
smart_agri/
├── collector.py                 # MQTT subscriber + weather enrichment + CSV/JSON logger
├── dashboard.py                 # Streamlit dashboard (UI, ML, chatbot, PDF, auth)
├── train_model.py               # Basic Random Forest model trainer
├── train_model_v2.py            # Enhanced trainer with metrics & classification report
├── train_model_sensor_aligned.py# Sensor-aligned trainer with StandardScaler pipeline
├── test.py                      # Model testing & validation script
├── crop_data.csv                # Training dataset for crop classification
├── sensor_log.csv               # Historical sensor readings (auto-generated)
├── requirements.txt             # Python dependencies
├── .env.example                 # Template for environment variables
├── .env                         # Your actual credentials (git-ignored)
├── .gitignore                   # Git ignore rules
└── README.md                    # You are here!
```

> **Files generated at runtime** (git-ignored): `latest.json`, `crop_model.pkl`, `users.json`, `farm_report.pdf`

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **MQTT Broker** (e.g., [HiveMQ Cloud](https://www.hivemq.com/mqtt-cloud-broker/) - free tier available)
- **IoT sensor** publishing to your MQTT topic (or simulate with test data)

### 1. Clone the Repository

```bash
git clone https://github.com/rizzit17/SmartAgri.git
cd SmartAgri
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your MQTT broker details:

```env
MQTT_BROKER=your_broker_url_here
MQTT_PORT=8883
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password
MQTT_TOPIC=smartagri/data
LATITUDE=12.9676
LONGITUDE=79.1338
CITY=Vellore
```

### 4. Train the ML Model

```bash
python train_model_sensor_aligned.py
```

This creates `crop_model.pkl` using the data in `crop_data.csv`.

### 5. Start the Data Collector

```bash
python collector.py
```

This connects to your MQTT broker, listens for sensor data, enriches it with weather info, and writes to `latest.json` + `sensor_log.csv`.

### 6. Launch the Dashboard

In a separate terminal:

```bash
streamlit run dashboard.py
```

Open **http://localhost:8501** in your browser and choose **Create account**. Choose a username and a password of at least 8 characters. There are no default credentials. Existing plaintext entries in `users.json` migrate to salted PBKDF2 hashes after successful sign-in.

The navigation includes Overview, History (date filters and CSV export), Crops, Field notes (the rules-based helper), Reports (PDF snapshots and CSV export), and Account (password change and sign-out). Missing data and incompatible models show setup guidance rather than stopping the app. Reports remain downloadable while you navigate in the same session.

Accounts are local to this installation and share the same field data. This is a prototype account system without email recovery or production identity management; use an established authentication provider before a public deployment.

For an isolated data directory, set `SMARTAGRI_DATA_DIR` before starting the dashboard. It contains `latest.json`, `sensor_log.csv`, `crop_model.pkl` and `users.json`; the default is the directory containing `dashboard.py`. Both `moisture` and `soil_moisture` payload keys are accepted, and moisture must be a calibrated percentage for crop suggestions.

Dashboard regression checks (temporary data only):

```bash
python -m unittest discover -s tests
```

---

## ML Model Details

The crop recommendation system uses a **Random Forest Classifier** trained on agricultural data with three input features:

| Feature | Source |
|---|---|
| Soil Temperature (°C) | DHT11/DHT22 sensor |
| Soil Humidity (%) | DHT11/DHT22 sensor |
| Soil Moisture (%) | Capacitive soil moisture sensor |

Three model training scripts are provided:

| Script | Description |
|---|---|
| `train_model.py` | Basic trainer - quick and simple |
| `train_model_v2.py` | Enhanced with accuracy metrics and classification report |
| `train_model_sensor_aligned.py` | **Recommended** - includes StandardScaler pipeline for normalized predictions |

---

## Chatbot Capabilities

The built-in Smart Farming Assistant responds to natural language queries:

```
Supported Topics:
  • irrigation / watering    → Actionable advice based on live moisture levels
  • crop / plant / grow      → AI-backed crop recommendation with confidence
  • soil / moisture          → Soil health assessment with thresholds
  • temperature              → Heat stress analysis and advice
  • humidity                 → Fungal disease risk assessment
  • weather / wind           → Local weather impact on farming
  • alerts / warnings        → Active farm alerts
  • fertilizer / nutrients   → Context-aware fertilizer guidance
  • pest / disease           → Pest risk evaluation
  • harvest / yield          → Harvest readiness notes
  • summary                  → Full farm snapshot
  • tips                     → General smart farming best practices
```

---

## PDF Reports

Generate professional farm reports directly from the dashboard with a single click. Reports include:

- Current sensor readings in styled tables
- System status and recommended actions
- Weather conditions
- AI crop recommendation with Top 3 confidence scores
- Timestamped and branded footer

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit 1.37+ with responsive cream-and-sage styling |
| **Data Collection** | Paho MQTT (TLS-secured) |
| **Weather API** | [Open-Meteo](https://open-meteo.com/) (free, no API key needed) |
| **Machine Learning** | scikit-learn (Random Forest + StandardScaler pipeline) |
| **PDF Generation** | ReportLab |
| **Data Storage** | JSON + CSV (file-based, lightweight) |
| **Authentication** | JSON-based user/password system |
| **IoT Protocol** | MQTT over TLS (port 8883) |

---

## MQTT Message Format

The collector expects JSON payloads on the configured MQTT topic:

```json
{
  "temperature": 28.5,
  "humidity": 65.0,
  "moisture": 450,
  "status": "OK",
  "action": "No Action Needed"
}
```

The collector enriches this with weather data and writes the full payload to `latest.json`.

---

## Security

- All MQTT credentials are stored in `.env` (git-ignored)
- Salted PBKDF2 password hashes are stored in `users.json` (git-ignored)
- MQTT connection uses **TLS encryption** (port 8883)
- No API keys required for weather data (Open-Meteo is free and keyless)

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  <b>🌾 Smart Agriculture IoT System</b><br>
  <i>Making farming smarter, one sensor at a time.</i>
</p>
