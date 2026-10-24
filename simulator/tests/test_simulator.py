import csv
import io
import json
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine import Config, evaluate, run, run_suite, preset_config
from server import csv_trace, save_evidence, make_handler


class ControllerTests(unittest.TestCase):
    def test_bench(self):
        suite=run_suite()
        self.assertEqual(suite["passed"],suite["total"],suite["tests"])

    def test_validation(self):
        for config in [{"moisture":float('nan')},{"duration":601},{"noise":-1},{"seed":True},{"preset":"unknown"},{"humidity":None},{"extra":1}]:
            with self.assertRaises((ValueError,TypeError)):Config.parse(config)

    def test_seed_changes_noisy_trace(self):
        config=preset_config("noisy")
        a=run(config);config.seed=8;b=run(config)
        self.assertNotEqual(a["frames"],b["frames"])

    def test_dose_windows_and_wet_safety(self):
        frames=run(preset_config("dry_hot"))["frames"]
        self.assertTrue(frames[0]["fuzzy"]["pump_on"])
        self.assertFalse(frames[40]["fuzzy"]["pump_on"])
        self.assertTrue(frames[60]["fuzzy"]["pump_on"])
        frames=run(preset_config("wet_stop"))["frames"]
        self.assertTrue(all(not f["fuzzy"]["pump_on"] for f in frames[15:]))

    def test_exports(self):
        result=run(preset_config("sensor_fault"))
        rows=list(csv.DictReader(io.StringIO(csv_trace(result))))
        self.assertEqual(len(rows),121)
        self.assertEqual(rows[12]["filtered_moisture_pct"],"")
        self.assertEqual(rows[12]["fuzzy_pump_on"],"False")
        with tempfile.TemporaryDirectory() as folder:
            name=save_evidence(result,Path(folder))
            self.assertEqual(json.loads((Path(folder)/name/"run.json").read_text()),result)
            self.assertTrue((Path(folder)/name/"trace.csv").exists())

    @unittest.skipUnless(shutil.which("g++"),"g++ optional for C++ equivalence check")
    def test_cpp_equivalence(self):
        rng=random.Random(42)
        values=[(rng.uniform(0,100),rng.uniform(0,50),rng.uniform(0,100)) for _ in range(1000)]
        values += [(m,t,h) for m in [0,20,30,50,80,100] for t in [0,15,27,39,50] for h in [0,30,60,90,100]]
        with tempfile.TemporaryDirectory() as folder:
            binary=Path(folder)/"controller.exe"
            subprocess.run([shutil.which("g++"),"-std=c++11","-O2",str(ROOT/"tests"/"cpp_bridge.cpp"),"-o",str(binary)],check=True,capture_output=True)
            source="".join(f"{m:.8f} {t:.8f} {h:.8f}\n" for m,t,h in values)
            output=subprocess.run([str(binary)],input=source,text=True,capture_output=True,check=True).stdout.splitlines()
        self.assertEqual(len(output),len(values))
        for row,v in zip(output,values):
            f,b=map(float,row.split())
            self.assertAlmostEqual(f,evaluate(*v)["minutes"],delta=2e-5)
            self.assertEqual(b,evaluate(*v,True)["minutes"])


class APITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.server=ThreadingHTTPServer(("127.0.0.1",0),make_handler(Path(self.tmp.name)))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()

    def request(self,path,data,origin=None):
        headers={"Content-Type":"application/json"}
        if origin:headers["Origin"]=origin
        return urlopen(Request(self.base+path,json.dumps(data).encode(),headers),timeout=10)

    def test_browser_assets_and_run(self):
        for path in ["/","/style.css","/app.js","/api/info"]:
            with urlopen(self.base+path,timeout=5) as response:self.assertEqual(response.status,200)
        with self.request("/api/run",{"preset":"normal"}) as response:
            value=json.load(response)
        self.assertEqual(value["frames"][0]["fuzzy"]["command_minutes"],8)
        self.assertTrue((Path(self.tmp.name)/value["evidence_id"]/"trace.csv").exists())

    def test_reject_invalid_or_foreign_request(self):
        for data,origin,status in [({"moisture":-1},None,400),({},"http://untrusted.example",403)]:
            with self.assertRaises(HTTPError) as error:self.request("/api/run",data,origin)
            self.assertEqual(error.exception.code,status)


if __name__=="__main__":unittest.main()
