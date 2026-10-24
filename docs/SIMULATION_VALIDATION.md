# SmartAgri validation record

Submission checks repeated on 25 October 2026 (Asia/Calcutta), using Python 3.13.7. Archived experiment timestamps remain unchanged.

| Evidence | Observed result | Scope |
|---|---|---|
| Browser simulator automated tests | 8 passed, including 1,150 Python/C++ input comparisons | Engine, HTTP API, validation, persistence and parity |
| Browser scenario batch | 9 scenario exports; 17/17 built-in checks passed | Deterministic synthetic traces; CSV/JSON and source manifest |
| Dashboard automated tests | 3 passed | Account creation/login/logout, password flow, reports/helper and legacy account migration in temporary fixtures |
| Wokwi functional archive | 18 observed cases passed; 20 selected circuit-and-Serial screenshots | Original firmware session; not a newly repeated run |
| MQTT archive | 95 received payloads | Actual synthetic-data receipts, not a delivery-ratio or latency study |
| C++ host controller check | 520,251 integer-domain points plus consequents, boundaries, invalid inputs, filter, timer and millis wrap passed | Host compilation, distinct from ESP32 execution |
| Optional crop-model holdout | 415/440 correct; accuracy 0.9431818182; macro F1 0.9428923969; top-three 1.0 | One stratified public-dataset holdout, 1,760 training rows |

The recorded crop experiment fits proxy normalization and preprocessing on training records only. It uses 200 Random Forest trees, maximum depth 12 and minimum leaf size 3. Dataset hashes, settings and versions are in `simulator/model/metrics.json`. The rainfall/humidity proxy has no established calibration to physical soil moisture.

The final editable research paper has 51 pages, 34 figures and 11 tables. All pages were rendered and visually reviewed using Microsoft Word PDF export and PDF rasterization; the bundled LibreOffice executable was unavailable on this Windows host. The Review-1 draft is a separate three-page proposal and the editable presentation has 14 checked slides.

Browser figure manifests are in `simulation/`; the separate Wokwi protocol, commands, observations, source hashes and capture-timing disclosure are in `wokwi-evidence/`. One late TC11 screenshot attempt was excluded from the 20 published figures because its capture occurred after the dose ended; the successful active-dose case is retained.

These checks do not establish water savings, yield, physical pump safety, calibrated confidence, real-world crop suitability, field reliability, broker delivery guarantees or ESP32 timing performance.
