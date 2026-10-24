# SmartAgri research figures and demonstration checklist

The simulator is local at http://127.0.0.1:8766. Start it using `Start-Simulator.cmd` or `python simulator/server.py`. See `simulator/README.md` for the full protocol.

## Suggested figure set

| Figure | Preset / view | Replay instant | What the screenshot establishes |
|---|---|---:|---|
| System demonstration | Hot & dry / Field view | 0 s | Synthetic inputs, controller command, reference command and logical pump indication. |
| Wet-input safety | Sudden wet reading / Field view | 15 s | Raw 90%, filtered 30%, fuzzy command 34 min but pump OFF due to raw-wet shutdown. |
| Sensor fail-safe | Sensor fault & recovery / Field view | 15 s | Missing readings, zero commands and both outputs OFF. |
| Offline autonomy | Connection lost / Field view | 35 s | Local pump ON; collector's last sample is 5 s and stale. Network is an injected transport surrogate. |
| Signal processing | Noisy sensor / Signals & rules | Any, use 0 s for repeatable rule view | Full raw/average trace and same-input pump lanes; current memberships and fired rules. |
| Software verification | Test bench after Run all checks | Not applicable | Actual 17-check outcome and controller comparison table. |
| Optional ML result | Crop model | Initial inputs shown by chosen preset | Real held-out dataset scores; engineered proxy and independent model scope visible. |

Prefer desktop width for paper figures and keep **SYNTHETIC INPUTS**, input values, time and scope labels visible. Use Run JSON and Trace CSV to keep the matching raw record. The final endpoint can start the next dose window, so use 119 s when illustrating the completed 120-second interval and 120 s when explicitly illustrating the new window.

The preliminary captured images are in `docs/simulation/`. `screenshots.json` records their captions, clock values and matching saved run IDs. They are actual browser captures, not drawings of fabricated results. The test-bench capture's own suite ID is shown in its table footer; its general export footer still identifies the previously selected scene.

## Example caption wording

“SmartAgri software simulator under a prescribed 10% moisture, 45 °C air-temperature and 20% RH input. The Sugeno controller issues a 40-minute command and the threshold reference issues 10 minutes. Output timers are accelerated at one software second per command minute; logical pump indicators do not measure irrigation volume.”

“Injected sensor failure at software time 15 s. Both controllers expose invalid readings, zero command and an off output. This tests software fail-safe behaviour and does not measure physical sensor-fault latency.”

The research Word document now includes 11 captured figures in Appendix B, with updated methods, the full 27-rule specification, nine observed scenario rows, controller comparison and separate crop-model results. Its original filename is preserved. The figure manifest is `docs/simulation/paper-screenshots.json`; those run IDs point to the archived trace folders.
