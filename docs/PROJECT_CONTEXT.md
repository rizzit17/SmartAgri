# SmartAgri — project context

Evidence baseline: repository `rizzit17/SmartAgri`, HEAD `abd6a43bd10877fd3a7c7c9813cf1e12060b8e73`, reviewed 19 October 2026. Paths below are relative to the repository. This describes implemented code, not a claim of production deployment. All tracked Python, configuration, README, dataset structures, and git history were inspected; screenshot/PDF contents were not used to establish quantitative results.

## Problem, solution, significance

Farm operators need to interpret local sensor readings together with weather and crop requirements. SmartAgri combines MQTT ingestion, weather enrichment, file-backed history, crop classification, threshold alerts, and reports in one Python dashboard. Its value is an integrated decision-support prototype that makes readings easier to inspect; demonstrated water savings, improved yield, adoption, and economic benefit are **unknown**. Target users are farmers/operators and educational IoT demonstrators; actual user research is **UNVERIFIED**. Sources: `README.md` Overview/Features; `collector.py`; `dashboard.py`.

## Architecture and data flow

```text
External sensor publisher / firmware [not tracked]
     | JSON on smartagri/data (configurable)
     v
MQTT broker -- TLS, default 8883 --> collector.py / Paho callback
                                      |        |
                     Open-Meteo <-----+        +--> latest.json
                     HTTP GET twice/message    +--> sensor_log.csv
                                                      |
crop_data.csv --> sensor-aligned trainer --> crop_model.pkl
                                                      |
users.json -------------------------------------------v
                       dashboard.py / Streamlit
                       login + session state
                       live metrics + weather + history
                       Random Forest top-three crop scores
                       threshold alerts + keyword assistant
                       ReportLab --> farm_report.pdf --> download
```

The collector decodes MQTT JSON, requests current weather, merges `outside_temp`, `wind_speed`, and `city` into the live payload, and replaces the snapshot via a temporary file. Its CSV logger fetches weather again and appends a timestamped row. Streamlit reads the snapshot on rerun, caches historical CSV for five seconds, and caches the pickle as a resource. Inference receives three numeric values. The logged-in page sleeps two seconds before requesting another full rerun; this is configured polling, not measured end-to-end latency. Sources: `collector.py:get_weather/write_latest_json/write_to_csv/on_message`; `dashboard.py:load_model/read_latest/read_csv` and AUTO REFRESH.

Important integration break: input `moisture` is used for CSV logging, but dashboard live inference reads `soil_moisture`. An input with only one of those keys leaves the other consumer without moisture. No automatic normalization resolves it. Sources: `README.md` MQTT Message Format; `collector.py:write_to_csv/on_message`; `dashboard.py` VALUES.

## Stack and technical decisions

| Decision / technology | Benefit | Cost or limitation | Evidence |
|---|---|---|---|
| Python + Streamlit monolith | UI, analytics, inference, report generation in one runtime | Full reruns; coupled globals and large UI file | `dashboard.py` |
| Separate MQTT collector process | Ingestion runs separately from browser interaction | Shared-file coordination and process supervision left to operator | `collector.py`, `README.md` Quick Start |
| JSON latest snapshot + CSV history | Simple local operation without database provisioning | No transactions across files, locking, indexes, retention, or tenant isolation | `collector.py`, `dashboard.py:read_csv` |
| Random Forest on three approximated sensor features | Tabular classification and class ranking without external AI service | Missing nutrient/pH inputs, moisture domain mismatch, no field validation | `train_model_sensor_aligned.py` |
| StandardScaler before forest | Single reusable preprocessing/inference pipeline | Tree splits generally do not require scaling; no ablation proves benefit | `train_model_sensor_aligned.py` |
| Keyword-based assistant | Deterministic local responses using current readings | Substring collisions and duplicated thresholds; no LLM/NLP evaluation | `dashboard.py:bot` |
| Cached model / five-second CSV TTL | Avoid repeated deserialization and continuous CSV reads | Stale model after retraining; entire history still loaded | `dashboard.py:load_model/read_csv` |
| TLS MQTT + dotenv credentials | Encrypted broker transport and external configuration | Web login still uses plaintext passwords and default fallback | `collector.py`, `.env.example`, `dashboard.py:load_users` |

Versions: README advertises Python 3.10+ and Streamlit 1.30+; minimum-version compatibility is **UNVERIFIED**. `requirements.txt` lists eight unpinned packages: streamlit, pandas, numpy, scikit-learn, paho-mqtt, requests, reportlab, python-dotenv. Paho's VERSION2 callback API requires a compatible 2.x release (`collector.py`). Exact development/deployment versions are **unknown**; no lockfile or Python runtime pin exists.

## ML: data, features, models, evaluation

`crop_data.csv` contains **2,200 records**, **22 labels**, **100 examples per label**, and columns `N,P,K,temperature,humidity,ph,rainfall,label` (counts computed directly from the tracked CSV). Scripts call it a Kaggle dataset, but a precise source URL, license, collection protocol, and geographic coverage are absent: dataset provenance is **UNVERIFIED**. Nutrients and pH are not used by either CSV-based trainer.

| Trainer | Data and ordered features | Estimator | Evaluation / compatibility |
|---|---|---|---|
| `train_model_sensor_aligned.py` | CSV; `temperature, humidity, moisture`; moisture = min-max-to-100 of `0.6*rainfall + 0.4*humidity` | StandardScaler → RandomForestClassifier: 200 trees, depth 12, leaf minimum 3, seed 42 | Stratified 80/20 split, seed 42; prints accuracy and per-class precision/recall/F1/support. Three-feature dashboard path, subject to proxy mismatch |
| `train_model_v2.py` | CSV; `soil_temp, humidity, moisture_proxy` where proxy is raw rainfall | RandomForestClassifier: 300 trees, depth 12, seed 42 | Unstratified 80/20 split; prints accuracy, classification report, importances. Reads sensor logs but explicitly does not train on unlabeled readings |
| `train_model.py` | Synthetic uniform ranges: 300 samples each for Wheat/Rice/Maize/Cotton/Barley; `soil_temp, soil_moisture, humidity, outside_temp, wind_speed` | RandomForestClassifier: 200 trees, depth 12, seed 42 | Fits all 1,500 generated rows; no held-out evaluation. Incompatible with dashboard's three inputs |

All write the same ignored `crop_model.pkl`. The recommended split yields **1,760 train / 440 test examples** by code and dataset size. Moisture normalization uses the complete dataset before splitting, allowing test-set extrema to influence feature preparation. Rainfall/humidity-derived moisture is not calibrated to physical sensor percentage; translating environmental dataset temperature into “soil temperature” is also **UNVERIFIED**. Sources: `train_model_sensor_aligned.py`, `train_model_v2.py`, `train_model.py`, `.gitignore`.

Dashboard uses `predict_proba([[t,h,m]])`, sorts descending, and displays the top three classes and rounded percentages. These are model scores; calibration, field accuracy, top-three accuracy, cross-validation, robustness across seasons/locations, and uncertainty estimation are **unknown**. No evaluation output or trained artifact is committed. Printed accuracy code is evidence of an evaluation procedure, not an achieved accuracy result. `test.py` is a manual diagnostic with one sample, not an assertion-based evaluation suite. No LLM, embeddings, RAG, neural network, or generative AI integration exists in the tracked Python. Sources: `dashboard.py` SMART AI + LOGIC / `bot`; `test.py`; trainers.

## Backend, persistence, interfaces, security

- **MQTT ingress:** configurable broker, port (8883 default), credentials, topic (`smartagri/data` default). VERSION2 connection callback subscribes; message callback parses JSON. README payload fields are `temperature`, `humidity`, `moisture`, `status`, `action`; no enforced schema, units, range checks, device ID, or publisher firmware exists. `collector.py`, `.env.example`, `README.md`.
- **Weather API:** `GET https://api.open-meteo.com/v1/forecast?latitude=...&longitude=...&current_weather=true`, five-second timeout; reads `current_weather.temperature/windspeed`, returns null values on exception. No HTTP status validation or cache. Coordinates default to 12.9676, 79.1338, city Vellore. `collector.py:get_weather`.
- **Snapshot:** `latest.json` is incoming fields plus weather/city. Collector does not add an ingestion timestamp; stale data is indistinguishable from fresh data in the dashboard. `collector.py:on_message`.
- **Historical schema:** `timestamp,soil_temp,soil_humidity,soil_moisture,status,action,outside_temp,wind_speed,city`. Local timestamps have no explicit timezone; file includes ISO and space-separated formats. No database tables, migrations, API routing layer, workers, task queues, or durable replay machinery are tracked. `collector.py:write_to_csv`, `sensor_log.csv`.
- **Authentication:** `users.json` maps usernames to plaintext passwords. Missing/invalid file falls back to `admin:admin`; equality comparison sets Streamlit session state. No roles, account provisioning API, logout control, password hashing, or login throttling appears. MQTT transport authentication is separate. `dashboard.py:load_users/login_ui`; `collector.py`.
- **Caching/concurrency:** model cached with `st.cache_resource`; history with `st.cache_data(ttl=5)`; latest JSON uncached. Concurrent CSV read/write is uncoordinated. PDF generation writes one shared `farm_report.pdf`; concurrent downloads may contend. Pickle must be trusted. `dashboard.py`, `collector.py`.

## Frontend and reporting

There is a login view and one wide Streamlit dashboard, not a separate SPA. Inline CSS uses dark green variables, Google Fonts Inter, metric cards, status badges, recommendation cards, and internal Streamlit DOM selectors. State lives in `st.session_state` (`logged_in`, `user`, `chat`); no Redux or other client state framework. Internal selector styling may break across unpinned Streamlit upgrades. Source: `dashboard.py` CONFIG/CUSTOM CSS/AUTH/CHATBOT.

The main page presents welcome/time, ranked crop suggestions, soil temperature/humidity/moisture, status/action, outside temperature/wind/city, alerts, historical line charts, PDF controls, and chat. Alerts use moisture <25/<40 and wind >12; assistant rules include additional heat/humidity/pest heuristics with differing thresholds. These rules are not evaluated agronomic models. Status/action are displayed or heuristically derived; there is no outgoing pump-control publish call. Source: `dashboard.py` VALUES, SMART ALERTS, TRENDS, `bot`.

ReportLab builds an A4 report with sensor/status/weather tables, recommended crop, optional top-three scores, and timestamps. `generate_pdf(report_data, ...)` mostly reads global values instead of its data argument. Helvetica/emoji rendering and the download button's lifetime under two-second reruns need manual verification: **UNVERIFIED**. Source: `dashboard.py:generate_pdf` and Farm Report button block.

## Evidenced outcomes and limits

| Measure | Evidence-based result |
|---|---|
| Labeled data coverage | 2,200 rows, 22 classes, 100/class (`crop_data.csv`) |
| Historical telemetry artifact | 1,155 rows; only 319 have nonempty moisture; nonempty moisture range 0–100 (`sensor_log.csv`, direct CSV inspection) |
| UI ranking | Three highest class scores implemented (`dashboard.py`) |
| Refresh/cache configuration | Two-second sleep per successful full rerun; five-second historical-data cache TTL; actual freshness/latency **unknown** (`dashboard.py`) |
| Achieved ML accuracy/F1 | **unknown**; scripts print metrics, no saved results (`train_model_sensor_aligned.py`, `train_model_v2.py`) |
| Water savings, yield gain, cost savings, active users, throughput, uptime | **unknown**; no benchmark or field-trial evidence in tracked code/README/history |
| Operational verification in this review | All seven Python files parsed with Python AST; dependency installation, model training, broker connection, UI execution, and PDF rendering were not performed |

History has eight commits. `8e2e7af` (11 April 2026) introduces source/data/report; `948515b` adds README; intervening changes edit README; September commits `8bc672f` and `abd6a43` add screenshots. This establishes repository evolution, not deployment or performance evidence. Source: `git log --stat --oneline`, `git log --format`.

## Resume-ready bullets

- Built a Python IoT agriculture prototype with Paho MQTT over TLS and Open-Meteo enrichment, connecting incoming sensor telemetry to a Streamlit monitoring dashboard (`collector.py`, `dashboard.py`).
- Implemented a scikit-learn crop recommendation pipeline over 2,200 labeled examples spanning 22 crops, with stratified holdout evaluation and top-three class-score presentation (`crop_data.csv`, `train_model_sensor_aligned.py`, `dashboard.py`).
- Added CSV-backed historical charts, moisture/wind alerts, and a context-aware rules assistant to make farm readings and suggested actions accessible in one interface (`dashboard.py`).
- Created downloadable ReportLab farm reports combining sensor readings, weather context, system status, and ranked crop recommendations (`dashboard.py:generate_pdf`).

These describe capabilities and artifacts; do not append accuracy, savings, deployment, or adoption claims without new evidence.

## Interview talking points

- **Hardest technical issue visible in code:** reconciling sensor semantics with a crop dataset, particularly rainfall-derived moisture versus measured soil moisture, plus the incompatible live/CSV field names. **UNVERIFIED** whether this was the author's personally hardest task. Explain the current mismatch candidly and propose a versioned payload/feature schema and sensor calibration (`collector.py`, `dashboard.py`, trainers).
- **First improvements:** normalize and validate incoming payloads; unify moisture units; preserve timestamps/device IDs; remove fallback auth; hash passwords; add focused ingestion/inference tests; pin dependencies and persist model metadata. These are proposed changes, not implemented features.
- **ML improvement:** fit preprocessing on training data, evaluate on labeled field measurements with temporal/geographic holdouts, compare a simple baseline, report per-class and top-three metrics, and calibrate scores before calling them confidence. Proxy validity is a larger risk than forest hyperparameter tuning.
- **Scale limits:** single blocking MQTT callback performs two sequential weather calls (up to roughly ten seconds of configured request timeouts, not a measured latency bound); history grows without rotation and is reread in full; no cross-process file locks; one location, snapshot, and shared PDF path. No supported device/user capacity is measured (`collector.py`, `dashboard.py`).
- **Growth path:** cache weather by location, decouple ingestion from enrichment, use timestamped per-device records in a database, add bounded queries/retention, generate per-session reports in memory, and replace full-page polling with targeted refresh. Introduce queues only when throughput/reliability measurements justify them.
- **Maintainability:** extract auth, inference, advisory rules, and reports from the 1,418-line dashboard; remove duplicate `safe_float`, broad silent handlers, and stale `train_model_fixed.py` advice. Add schema/feature-contract tests before restructuring (`dashboard.py`, `test.py`).

## Skill tags

[IoT, ML, SDE, Python, Streamlit, MQTT, TLS, scikit-learn, Random-Forest, Feature-Engineering, Pandas, Analytics, Data-Visualization, API-Integration, ReportLab, Prototype-Full-stack]

AI applies here to conventional ML classification and deterministic assistance; generative AI experience is not evidenced.
