# SmartAgri Wokwi simulation

Open https://wokwi.com/projects/478323582523545601 and click Start Simulation.

The saved project runs Arduino/C++ on an ESP32. To recreate it, paste `sketch.ino`, `controller.h`, `diagram.json` and `libraries.txt` into four matching Wokwi files. Python is optional and runs on your computer only to receive MQTT telemetry.

The complete step-by-step instructions, commands, expected outcomes and evidence limits are in [the test protocol](../docs/wokwi-evidence/README.md). Follow its `test-cases.csv` in order; wait for a complete Serial report before capturing the circuit and Serial Monitor together.

From the repository root:

```powershell
python -m pip install -r wokwi/requirements.txt
python wokwi/collector.py --topic smartagri/23bct0157/demo-v1/data --out runs/my-wokwi-capture
```

This receiver matches the demonstration broker on port 1883. The root application's legacy collector defaults to TLS on 8883 and is configured separately. See the main README before connecting the two.

DHT22 and a potentiometer supply synthetic inputs; the GPIO2 LED represents logical pump state. Timers are accelerated. Neither the circuit nor the screenshots measure water volume or crop outcomes.
