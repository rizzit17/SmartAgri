# Working on SmartAgri

SmartAgri is a Python IoT agriculture prototype for farmers, farm operators, and student demonstrators: an MQTT collector enriches sensor readings with weather, and a Streamlit dashboard displays trends, crop suggestions, alerts, a rules-based assistant, and downloadable reports. Treat agronomic advice as prototype heuristics, not validated field outcomes. Evidence: `README.md`, `collector.py`, `dashboard.py`.

## Stack and versions
- `README.md` advertises Python 3.10+ and Streamlit 1.30+; tested compatibility with those minimums is **UNVERIFIED**.
- `requirements.txt`: streamlit, pandas, numpy, scikit-learn, paho-mqtt, requests, reportlab, python-dotenv; all unpinned, with no lockfile.
- `collector.py` uses `mqtt.CallbackAPIVersion.VERSION2`: requires the Paho 2.x callback API. Exact deployed versions are unknown.
- RandomForestClassifier, optional StandardScaler pipeline, pickle serialization; MQTT over TLS, Open-Meteo HTTPS; JSON/CSV persistence. No separate JS frontend, SQL database, REST server, queue service, or container configuration is tracked.

## Install and run (repository root)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python train_model_sensor_aligned.py
python collector.py
# Separate terminal, same virtual environment:
python -m streamlit run dashboard.py
```
- Fill `.env` MQTT broker/username/password/topic and location values; default port is 8883, location Vellore (`.env.example`, `collector.py`). Use a configured broker and a publisher; hardware firmware is absent.
- Create `users.json` as a username-to-password JSON object. Missing or malformed files silently enable `admin` / `admin` (`dashboard.py:load_users`). This is demo authentication.
- Streamlit normally opens on localhost:8501 (`README.md`); actual launch has not been verified in this review.
- Train with the sensor-aligned script, not the basic trainer: all trainers overwrite `crop_model.pkl`, but their features differ.
- No build/package command exists. Training produces the model; Streamlit runs the application directly.

## Verification
- `python test.py` prints model/dependency diagnostics and runs one three-feature prediction; it contains no assertions and may report errors without failing the process.
- `test_mqtt.py` is empty. No automated test suite, CI, lint, formatting, or type-check configuration is tracked.
- Suggested syntax check: `python -m compileall collector.py dashboard.py train_model.py train_model_v2.py train_model_sensor_aligned.py test.py`.
- Manually verify login, missing-data handling, three-feature inference/top-three display, trends, alerts, assistant routing, and PDF generation/download after relevant edits.
- Collector imports connect to MQTT; training imports fit and overwrite the model. Do not import these scripts merely to inspect functions.

## Files and responsibilities
| Path | Role |
|---|---|
| `collector.py` | dotenv config, Paho callbacks, Open-Meteo calls, temporary-file JSON replacement, CSV append |
| `dashboard.py` | Single Streamlit script: inline CSS, auth, file loaders, inference, metrics, trends, alerts, ReportLab PDF, chatbot |
| `train_model_sensor_aligned.py` | Recommended three-feature training pipeline, stratified holdout evaluation |
| `train_model_v2.py` | Three-feature rainfall-proxy alternative; prints metrics/importances; does not train on sensor logs |
| `train_model.py` | Five-feature synthetic-data model; incompatible with dashboard input |
| `test.py` | Manual pickle/model environment diagnostic; stale suggested filename |
| `test_mqtt.py` | Empty placeholder |
| `crop_data.csv` | 2,200 labeled rows, 22 crop classes, eight columns |
| `sensor_log.csv` | 1,155 historical records; incomplete moisture data; tracked mutable file |
| `.env.example`, `.gitignore` | Configuration template and exclusions |
| `farm_report.pdf`, `Screenshot from 2026-09-04 *.png` | Tracked demonstration artifacts |
| `docs/PROJECT_CONTEXT.md` | Evidence-based architecture and portfolio context |

## Patterns actually used
- Four-space Python indentation, snake_case functions/locals, uppercase path/config constants, procedural module-level execution; no class/service framework (`*.py`).
- Paths use `os.path.dirname(os.path.abspath(__file__))`; keep runtime data relative to the repository, not the caller's working directory.
- Large section-divider comments and inline HTML/CSS in `dashboard.py`; retain local style for focused edits. No enforced style tool exists.
- Streamlit session state holds `logged_in`, `user`, and chat history; `cache_resource` loads the model, `cache_data(ttl=5)` loads CSV.
- Trainers use `random_state=42`; preserve feature order and document any model contract changes alongside dashboard inference.
- Broad exception handlers commonly return `None` or print errors; preserve graceful missing-file behavior but expose actionable diagnostics when refactoring.
- Do not commit `.env`, `users.json`, `latest.json`, or model pickles (`.gitignore`). `sensor_log.csv` and `farm_report.pdf` ARE tracked despite README runtime-artifact wording; avoid incidental changes.

## Known gotchas and prioritized debt
1. **Moisture contract mismatch:** collector CSV reads input `moisture`; live JSON preserves incoming keys; dashboard reads `soil_moisture`. README example only supplies `moisture`. Agree on one normalized schema before changing either side (`collector.py:on_message/write_to_csv`, `dashboard.py` VALUES).
2. Dashboard assumes percentage moisture; README example uses 450. Firmware/calibration and physical sensor semantics are **UNVERIFIED**; no conversion exists.
3. Sensor-aligned training uses globally normalized `0.6*rainfall + 0.4*humidity` as moisture. This is not measured soil moisture; preprocessing occurs before splitting. Field validity and calibrated confidence are **UNVERIFIED**.
4. Basic trainer expects five features; dashboard always passes `[temperature, humidity, moisture]`. V2 uses raw rainfall as the third feature. No artifact metadata/version contract exists (`train_model*.py`, `dashboard.py`).
5. Two blocking weather requests per MQTT message, each with five-second timeout; live JSON and CSV can contain different weather snapshots. No weather cache, HTTP status check, payload schema validation, explicit retry policy, or durable buffering (`collector.py`).
6. Snapshot uses a temporary file and `shutil.move`; replacement behavior under concurrent access is **UNVERIFIED**. CSV append has no locking/rotation. Latest JSON lacks collector timestamp/device ID/staleness checks.
7. No automatic refresh while waiting for live data: `st.stop()` precedes the final `sleep(2)`/`st.rerun()`. Model cache needs invalidation/restart after retraining (`dashboard.py`).
8. Plaintext passwords and fallback account, no roles/logout/rate limiting; never treat this as production auth. Only load trusted pickles (`dashboard.py`).
9. Chatbot substring matching can misroute (`hi` matches inside words); zero-valued sensor checks sometimes use truthiness. Thresholds differ across UI/chat. Critical alert string lacks f-string interpolation (`dashboard.py:bot`).
10. `generate_pdf(report_data, ...)` largely reads globals, writes one shared filename, uses Helvetica with emoji, and shows download inside a transient button branch; verify glyphs/download timing and concurrent sessions (`dashboard.py`).
11. `test.py` recommends nonexistent `train_model_fixed.py`; README links absent `LICENSE`. No explicit TODO/FIXME markers found; this list is review-derived debt, not a promised roadmap.

## Evidence boundary
Reviewed all tracked Python, configs, README, CSV structure/counts, and all eight commit summaries at `abd6a43bd10877fd3a7c7c9813cf1e12060b8e73`. Source was introduced in `8e2e7af`; later commits change README or add screenshots. No committed evaluation logs establish accuracy, latency, water savings, yield impact, or deployment scale. Report unknown values as **unknown** and uncertain interpretations as **UNVERIFIED**.
