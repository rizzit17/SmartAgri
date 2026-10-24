# Response to the supplied paper comments

The revised paper preserves the existing section headings and canonical filename. The main paper has 22 pages and five selected figures; the complete screenshot evidence is moved to a separate supplementary Word document. Its evidence is limited to what was actually implemented, archived and tested.

| Comment | Revision / supporting evidence |
|---|---|
| Simulation presented as field validation | Abstract, methods, results and conclusion explicitly identify synthetic browser/Wokwi inputs, accelerated timers and an LED output. The DHT11 assembly is not the source of reported outcomes. |
| Unsupported decision accuracy, water efficiency and yield figures | Removed as project results. The separately computed 415/440 crop classification score is tied to the public-dataset experiment, training/test split and metrics files. No water or yield improvement is claimed. |
| Single runs treated as scientific validation | Nine browser demonstrations and 18 firmware cases are described as functional checks. Screenshot reframing is not counted as an independent trial; no mean/variance or reliability estimate is fabricated. |
| Crop-model feature mismatch | The three-feature rainfall/humidity proxy, training-only preprocessing, omitted soil chemistry and unresolved proxy-to-sensor calibration are explicit. Dataset scores do not establish integrated field recommendation accuracy. |
| Unverifiable references | Literature is replaced with identifiable publications and complete bibliographic details/DOIs. The selected base paper is supplied unchanged with Q1 category/year verification. |
| MQTT and DHT contradictions | Current demonstration topic and broker are identified; physical DHT11, simulated DHT22 and root collector TLS defaults are distinguished. The tested files and source hashes are archived. |
| Credentials in figures | The obsolete code screenshot was replaced with current demonstration documentation. Private credentials are not required in the paper or submission archive. |
| Unsupported latency comparison | No physical inference-latency or ESP32 performance comparison is claimed. Software command durations are distinguished from execution latency. |
| Baseline not actually run | Both browser policies receive identical prescribed traces; results, JSON/CSV exports and parity checks are archived. Wokwi also includes threshold-reference cases. |
| Missing validity threats | Methods and discussion address simulator substitutes, deterministic scenarios, field calibration, sensor degradation, transport scope, model transfer and missing physical trials. |
| Incomplete fuzzy specification | The complete 27-rule zero-order Sugeno specification and weighted-average equation are supplied with source. |
| Unsupported SHAP / chatbot claims | SHAP is future work. The implemented helper is identified as deterministic keyword rules, with limited scope and tested interactions. |
| Unsupported node cost | No substantiated bill-of-materials or affordability result is claimed. |
| Data available only on request | Source, synthetic traces, screenshots, test records, MQTT observations, model metrics and dataset are included in the repository/archive. |

Physical prototype trials, replicated agronomic experiments, measured water delivery and crop outcomes remain future work. The revision addresses those comments by narrowing claims honestly; it does not represent these unperformed experiments as completed or claim Q1 publication readiness.
