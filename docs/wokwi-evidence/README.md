# SmartAgri Wokwi evidence

Tested project: https://wokwi.com/projects/478323582523545601

18/18 prescribed functional scenarios passed on the ESP32 firmware in Wokwi. These are one-session functional observations with per-case resets, not 18 independent experimental replications. See `test-cases.csv` for input, command, expected behavior and screenshot/serial file mapping. Source is in `wokwi/` in the companion ZIP (`app/wokwi/` in the workspace checkout). A fresh browser view after SAVE matched the local sketch and diagram exactly (after line-ending normalization). TC18 was repeated to improve screenshot framing; it is counted once.

## What was exercised

Normal, wet, hot/dry and cold/dry control; valid domain endpoints; alert boundaries; injected fault shutdown and recovery; offline local dosing and broker reconnection; threshold reference; dose expiry; invalid command rejection; raw-wet shutdown before filter convergence; and the five-sample step response. An additional LIVE capture uses Wokwi's DHT22 and potentiometer models, rather than serial overrides.

Each screenshot is an unaltered browser screenshot with the circuit and Serial Monitor visible together. GPIO2 is read back by the firmware; the green LED represents the logical pump output. It is not a motor, hydraulic model or measured water flow. The OLED can look dithered while paused because the simulator is frozen during a display refresh; numerical records are in Serial and MQTT exports.

## Reproduce in Wokwi

1. Open the project URL in Chrome. The saved project already contains `sketch.ino`, `controller.h`, `diagram.json` and `libraries.txt`.
2. If recreating it, create an ESP32 Arduino project, replace `sketch.ino` and `diagram.json`, and add `controller.h` and `libraries.txt` using the file menu. Paste each local file into the matching Wokwi tab. Keep all four names unchanged.
3. Click the green Start Simulation button. Wait for compilation and sensor initialization. The Serial Monitor opens automatically. Input commands into its bottom text field and press Enter (LF newline).
4. Run the commands in `test-cases.csv` in order. Enter one command at a time. Semicolons in the CSV describe sequential actions; do not paste a whole semicolon-separated line.
5. Each `CASE n` selects inputs/policy and resets filters and the pending dose. Wait for a complete `[TCnn]` block before judging the case. The scheduled sample interval is 5000 ESP32 milliseconds. `STATUS` only reports the current state; it does not take a fresh sensor sample.
6. For TC09, issue `FAULT ON` while the preceding report says PUMP=ON. TC10 clears the fault. TC11 disables networking, and TC12 enables it; allow time for broker reconnection.
7. For TC15, observe PUMP=ON first, then PUMP=OFF once the 8000 ms dose expires. Observe subsequent samples before the 60000 ms next-dose window.
8. For TC17, issue `STEP 90 45 20` while the 40-second dose is active. `STEP` preserves the existing filter and dose. Check raw moisture 90%, filtered moisture below 80%, and pump OFF in the same record.
9. For TC18, allow at least five 100% moisture samples before `STEP 0 27 60`. Observe five successive averages 80, 60, 40, 20, 0%. TC18 does not request immediate pump restart; a nonzero command and pump OFF can coexist between dose windows.
10. For screenshots, narrow the editor by dragging the vertical divider left. Resize the Serial Monitor to show a complete report. Focus the circuit, press F to fit, and + to enlarge if needed. Pause only after the desired report appears. Include both the whole circuit and report; save the raw serial text too.
11. Type `LIVE` to return to DHT22/potentiometer readings. Click DHT22 to set temperature/humidity; turn the potentiometer for synthetic soil moisture. The red and blue buttons are HOLD inputs for fault/offline, respectively. `FAULT OFF`, `NET ON` and `MODE FUZZY` restore normal control. The TC label persists when using LIVE, so use the explicit `/ LIVE` input-source field.

## Optional Python MQTT receiver

The ESP32 itself runs C++/Arduino. Python is only needed to archive received messages, not to operate the circuit. From the repository root, install the receiver dependency and run:

```powershell
python -m pip install -r wokwi/requirements.txt
python wokwi/collector.py --topic smartagri/23bct0157/demo-v1/data --out work/my-wokwi-capture
```

The same commands work from the extracted implementation source folder. The demonstration uses broker.hivemq.com:1883 with a synthetic-data topic. Do not publish account credentials or private data. `mqtt/telemetry.jsonl` and `.csv` are actual receiver observations. Offline samples are not replayed: the firmware maintains a one-entry latest-snapshot queue. The receiver was stopped after the main suite and LIVE check; the TC18 framing repeat is evidenced by Serial rather than a second receiver log.

## Evidence limits

The timer is accelerated: one commanded irrigation minute equals 1000 simulator milliseconds. Wall-clock duration varies with simulator speed and pauses. No physical timing, real water savings, measured yield, field sensor calibration, classifier accuracy or statistical reliability is established by these cases. Forced sensor faults and forced network outages are deliberate test hooks; they do not establish physical failure coverage. Screenshots are selected states; the serial records contain the transitions. The master session includes pilot framing attempts; only the 18 entries in observations.json count toward the result. A late TC11 capture attempt is separately disclosed and excluded from the published evidence set.

Separately, the shared C++ controller passed a host sweep of 520251 integer-domain points, the 27 consequents, boundaries, invalid inputs, filter, timer and millis wrap. This is not an additional Wokwi run.

Official UI references: https://docs.wokwi.com/guides/serial-monitor and https://docs.wokwi.com/guides/diagram-editor.
