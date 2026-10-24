# SmartAgri Lab verification

Verified on 25 October 2026 (Asia/Calcutta). This record concerns the new local browser/Python simulation.

- Eight automated tests passed with Python 3.13.7. They cover the built-in bench, invalid settings, repeatability and seed changes, dose windows, raw-wet shutdown, CSV/JSON persistence, local HTTP responses and rejection of invalid/foreign requests.
- All 17 built-in functional checks passed. Observed outcomes and expected values are preserved in each suite export.
- The C++ bridge compiled the bundled controller.h with g++ and compared both policies with Python at 1,150 input points: 1,000 seed-42 random inputs plus 150 boundary combinations. Fuzzy tolerance was 0.00002 command minutes; reference outputs matched exactly.
- The nine-preset batch completed and saved each scenario as per-second CSV and full JSON, with comparison CSV, checks and source hashes in a timestamped experiment directory.
- Browser checks exercised field view, parameter/preset selection, timer replay, timeline scrubbing, signals/rules, the regression bench and optional crop model. No browser errors were recorded in the checked run. A 390-pixel viewport showed no horizontal document overflow; desktop figures used a 1280-pixel viewport.
- Eleven actual paper figure captures cover nine scenarios, the executed test bench and the independent crop model. The paper preserves the source formatting and filename and has 30 pages after insertion. Every rendered page was visually reviewed. Microsoft Word PDF export and bundled Python PDF rasterization were used because the packaged LibreOffice renderer could not find a Windows LibreOffice executable.
- The optional Random Forest used 1,760 training / 440 test rows, a stratified seed-42 holdout, training-only proxy normalization, StandardScaler, 200 trees, max depth 12 and minimum leaf size 3. Recorded holdout accuracy: 0.9431818182; macro F1: 0.9428923969; top-three accuracy: 1.0. Runtime/model versions and dataset hash are in model/metrics.json.

These are software checks and a single public-dataset holdout. They do not establish physical actuation safety, water volume, yield, MQTT transit performance, ESP32 execution latency, geographical transfer, calibrated confidence or agronomic validity. The earlier Wokwi smoke-run record remains a separate experiment.
