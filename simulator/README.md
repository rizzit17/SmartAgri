# SmartAgri Lab

A local, interactive software simulation for the SmartAgri research prototype. It follows the same pattern as the SoundScape simulator: a Python calculation engine, browser replay, reproducible presets and exportable evidence. Rishit & Siddharth.

## Open it

On this computer, open a terminal in the project directory and run:

```powershell
python simulator/server.py
```

Then open **http://127.0.0.1:8766**. Keep the terminal running. You can also double-click **Start-Simulator.cmd** in the project root, then open that address. Stop the server with Ctrl+C. If the port is in use, use `python simulator/server.py --port 8767` and open that port.

The core controller and UI need only Python 3.10 or newer. No Wokwi account, MQTT broker, Node.js, Streamlit or Internet connection is required. Do not open `static/index.html` directly; it needs the Python API.

## Use the simulator

1. Wait for **Python engine connected** in the header.
2. Choose a **Test case**. A preset fills the input sliders and resets the seed and duration.
3. Adjust moisture, air temperature or humidity if desired. **Experiment settings** contains duration, seed and moisture-noise amplitude.
4. Click **Run this scene**. Settings are applied only when a run is calculated. The trace is saved under `simulator/results/<run-id>/`.
5. In **Field view**, inspect the virtual node display, filtered readings, logical pump indicators, collector snapshot and alert text.
6. Click **Play**, choose 1×/4×/10× replay, pause or drag the timeline. Replay does not change the numerical experiment. The timeline starts paused at zero so the initial decision can be inspected.
7. Open **Signals & rules** for the raw/filtered moisture plot, pump-output intervals, membership strengths, active rules and event log. Move the same timeline to inspect an instant.
8. Open **Test bench**, then **Run all checks**. Python executes the checks and shows actual outcomes, including failures, plus a same-input comparison across all nine presets.
9. Open **Crop model** for the optional Random Forest experiment. This uses the run's initial inputs, independently of replay time and the irrigation controller.
10. Download **Run JSON** and **Trace CSV**. The test bench has separate suite JSON and checks CSV exports. **Print this view** opens the browser print dialog; select Save as PDF if wanted.

Slider changes do not silently modify a running experiment. The left-side inputs are the prescribed source values; the cards show the most recent filtered observation. Fault frames show unavailable readings. Command duration and current pump state are separate: a command can be nonzero while a dose has finished or a safety stop is active.

## Demonstrate these cases

All presets use 120 simulation seconds and seed 7. Outputs below are controller expectations checked by the included tests, not physical measurements.

| Scene | Inspect at | Expected demonstration |
|---|---:|---|
| Everyday conditions | 0, 7, 8 s | 50% / 27 °C / 60% RH → fuzzy command 8 min; indicator ON at 7 s, OFF at 8 s. Reference command 0. |
| Hot & dry | 0, 20, 40 s | 10% / 45 °C / 20% RH → fuzzy 40 min, reference 10 min. The two timers expire independently. |
| Already wet | 0 s | 85% → both commands zero, both outputs off. |
| At the boundary | 0 s | 30% → low-moisture alert true, fuzzy 20 min, reference zero because its comparison is strictly `<30`. |
| Sudden wet reading | 14, 15 s | Raw moisture becomes 90% at 15 s; average is still 30%, but raw-wet safety immediately stops the fuzzy output at that sampling tick. |
| Sensor fault & recovery | 11, 12, 27, 30 s | Both outputs stop at 12 s. Fault clears at 27 s; a fresh valid sample at 30 s resets filtering and begins a new scheduled dose. |
| Connection lost | 9, 20, 35, 40 s | Offline 10–39 s. Local fuzzy output still on at 20 s; collector retains its 5 s sample. By 35 s it is stale. Latest snapshot delivered on reconnection at 40 s. |
| Noisy sensor | Signals & rules | Seeded ±10 percentage-point moisture noise, unless an explicit nonzero noise setting is supplied. Compare the raw signal and five-sample average. |
| Gradual drying | Signals & rules | A prescribed 65→10% ramp; the controllers react to the same filtered input at dose windows. |

The low-moisture alert uses raw input `<=30`. The reference dose uses filtered input `<30`. The difference at exactly 30% is intentional and is tested. Noise is uniform, independent at each five-second sample, clamped to 0–100%. For a new random trace, change the seed and run again.

## Timing and controller contract

- One-second discrete software clock; a trace includes both endpoints 0 and duration.
- Sensors sampled every 5 seconds; filter is the mean of up to five valid samples. It resets on a fault.
- Zero-order Sugeno fuzzy controller: minimum antecedent firing, weighted singleton average, all 27 consequents in `engine.py` and `firmware/controller.h`.
- Moisture dry/normal/wet shoulders 20–50 / 50–80, normal triangle 20/50/80; temperature shoulders 15–27 / 27–39, normal triangle 15/27/39; humidity shoulders 30–60 / 60–90, normal triangle 30/60/90.
- Accepted inputs: moisture 0–100%, air temperature 0–50 °C, humidity 0–100%. Invalid readings produce zero command and an off output.
- Initial dose plus 60-second dose windows; **one command minute = one simulation second**. These are accelerated logical output intervals, not pump-flow or real-duration measurements.
- Raw moisture >=80% or zero command stops the current dose at a sampling tick. A scripted sensor fault stops it immediately on the software tick.
- At recovery the browser model resumes on the next five-second sample. Wokwi's `FAULT OFF` can request an immediate sample; the two scheduling implementations are not cycle-equivalent.
- Summary pump-on seconds count intervals `[0,duration)`; doses beginning at the final endpoint are excluded from summary dose counts. Endpoint frames remain visible in replay.
- Transport is an in-process online/offline surrogate. One pending snapshot overwrites older unsent snapshots. It is not an MQTT network emulator or a latency benchmark.
- Inputs are prescribed. The pump does not change simulated moisture. There is no hydrological, water-balance, soil, crop-growth or yield model.

The `app/dashboard.py` UI is kept separate and retains its existing alert thresholds; these research-simulation rules do not silently alter the main dashboard or collector. No production data, credentials or sensor logs are modified.

## Optional crop experiment

The current computer has a locally trained model. On a new installation:

```powershell
python -m pip install -r simulator/requirements-ml.txt
python simulator/train_model.py
python simulator/server.py
```

Use the same Python environment for training and serving. A model-version mismatch shows a retraining message. Core simulation works without these packages. Only load a trusted locally trained pickle.

Training reads the repository's `crop_data.csv`: 2,200 rows, 22 labels. A seed-42 stratified split holds out 440 rows; 1,760 rows train a StandardScaler / Random Forest pipeline. The moisture proxy is `0.6*rainfall + 0.4*humidity`, normalized using **training-subset** min/max. This is an engineered proxy, not measured soil moisture. The scaler and classifier fit on training data only. The training script saves dataset SHA256, versions, split size, accuracy, macro F1 and top-three accuracy in `simulator/model/metrics.json`.

Crop scores are independent of irrigation control and are not calibrated confidence or recommendations verified for a real field. The dataset experiment does not validate physical moisture inputs or eliminate the omitted nutrients/pH/season limitation.

## Verification and repeatable exports

```powershell
python -m unittest discover -s simulator/tests -v
python simulator/server.py --suite
python simulator/run_experiments.py
```

The first command runs engine, validation, export and HTTP API tests. If g++ is available, it also compiles `tests/cpp_bridge.cpp` and compares Python against the actual C++ header on **1,150 input points** (1,000 seeded random points plus 150 boundaries), with a 0.00002-minute tolerance for float differences. That optional check reports a skip if the compiler is absent.

The second command executes and saves the 17 built-in controller/system checks without opening a browser. The third writes all nine runs as JSON + CSV, `checks.json`, `summary.csv` and a manifest of source SHA256 values and Python version. Each experiment gets a unique timestamped folder. These nine cases are deterministic scenario demonstrations, not independent repeated field trials. Changing the seed affects noisy input traces; it does not create independent evidence for deterministic cases.

## Wokwi counterpart

`firmware/` preserves the earlier implementation used by the Python/C++ parity bridge. The subsequently tested Wokwi project is in [`../wokwi/`](../wokwi/), with its 18-case protocol, 20 published screenshots and received MQTT records in [`../docs/wokwi-evidence/`](../docs/wokwi-evidence/). Its shared fuzzy-controller header matches the host-tested header. Browser checks and firmware runs are separate evidence; their scheduling and dose-window settings are documented independently.

## For the paper

Use the screenshot plan in `docs/SIMULATION_GUIDE.md`. Always caption these as **software simulation with synthetic inputs**. Report saved observed outcomes and source settings. Do not reuse legacy water-saving percentages, physical response times or field-performance claims as outcomes of this software experiment.
