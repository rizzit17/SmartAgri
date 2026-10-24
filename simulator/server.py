"""Local-only SmartAgri simulation server. Python 3.10+, standard library."""
import argparse
import csv
import hashlib
import io
import json
import mimetypes
import pickle
import traceback
from functools import lru_cache
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from engine import PRESETS, RULES, Config, run, run_suite, VERSION

ROOT=Path(__file__).resolve().parent


def csv_trace(result):
    buf=io.StringIO(newline="")
    writer=csv.writer(buf)
    writer.writerow(["time_s","raw_moisture_pct","raw_temperature_c","raw_humidity_pct","filtered_moisture_pct","filtered_temperature_c","filtered_humidity_pct","fuzzy_command_min","fuzzy_pump_on","baseline_command_min","baseline_pump_on","sensor_ok","network_online","collector_sample_time_s","delivered","overwritten"])
    for r in result["frames"]:
        writer.writerow([r["time"],*r["raw"],*(r["fuzzy"]["filtered"] or [None]*3),r["fuzzy"]["command_minutes"],r["fuzzy"]["pump_on"],r["baseline"]["command_minutes"],r["baseline"]["pump_on"],r["fuzzy"]["sensor_ok"],r["network_online"],(r["collector"] or {}).get("sample_time"),r["delivered"],r["overwritten"]])
    return buf.getvalue()


def save_evidence(result, output, suite=False):
    payload=json.dumps(result,allow_nan=False,sort_keys=True).encode()
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder=output / (stamp+"-"+hashlib.sha256(payload).hexdigest()[:8])
    folder.mkdir(parents=True,exist_ok=False)
    (folder/("suite.json" if suite else "run.json")).write_bytes(payload)
    if suite:
        with (folder/"checks.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=["name","expected","actual","passed"]);w.writeheader();w.writerows(result["tests"])
    else:
        (folder/"trace.csv").write_text(csv_trace(result),encoding="utf-8")
    (folder/"README.txt").write_text("SmartAgri software simulation. Synthetic prescribed inputs; not field data.\nEngine: "+VERSION+"\nUTC: "+stamp+"\nSHA256 JSON: "+hashlib.sha256(payload).hexdigest()+"\n",encoding="utf-8")
    return folder.name


@lru_cache(maxsize=1)
def crop_model(modified_ns):
    import pickle
    import sklearn
    metrics=json.loads((ROOT/"model"/"metrics.json").read_text())
    if metrics.get("sklearn_version")!=sklearn.__version__:
        raise ValueError("Re-train the crop model using this Python environment.")
    with (ROOT/"model"/"crop_model.pkl").open("rb") as f:model=pickle.load(f)
    return model,metrics


def crop_prediction(values):
    """Optional, trusted local model only; core simulation never needs sklearn."""
    file=ROOT/"model"/"crop_model.pkl"
    if not file.exists():
        return {"available":False,"message":"Optional crop model not trained. Run simulator/train_model.py to use the repository dataset."}
    try:
        import pandas as pd
        model,metrics=crop_model(file.stat().st_mtime_ns)
        frame=pd.DataFrame([[values[1],values[2],values[0]]],columns=["temperature","humidity","moisture"])
        probabilities=model.predict_proba(frame)[0]
        indices=sorted(range(len(probabilities)),key=lambda i:probabilities[i],reverse=True)[:3]
        return {"available":True,"suggestions":[{"crop":str(model.classes_[i]),"score":float(probabilities[i])} for i in indices],"metrics":metrics}
    except (ImportError,OSError,ValueError,AttributeError,TypeError,EOFError,pickle.UnpicklingError) as e:
        return {"available":False,"message":"The optional model could not be loaded. Re-train with the installed Python environment.","error_type":type(e).__name__}


def make_handler(output):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass

        def respond(self,body,ctype="application/json",status=200):
            if not isinstance(body,bytes):body=json.dumps(body,allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type",ctype)
            self.send_header("Content-Length",str(len(body)))
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'")
            self.end_headers();self.wfile.write(body)

        def do_GET(self):
            path=urlsplit(self.path).path
            if path=="/api/info":
                self.respond({"version":VERSION,"presets":PRESETS,"rules":RULES,"model_ready":(ROOT/"model"/"crop_model.pkl").exists()})
            elif path in ["/","/index.html","/app.js","/style.css"]:
                file=ROOT/"static"/("index.html" if path=="/" else path[1:])
                self.respond(file.read_bytes(),mimetypes.guess_type(file)[0]+"; charset=utf-8")
            else:self.respond({"error":"Not found"},status=404)

        def do_POST(self):
            origin=self.headers.get("Origin")
            if origin and origin not in [f"http://127.0.0.1:{self.server.server_port}",f"http://localhost:{self.server.server_port}"]:
                self.respond({"error":"Use the local simulator page."},status=403);return
            try:
                length=int(self.headers.get("Content-Length","0"))
                if not 0<length<=16384 or self.headers.get("Content-Type","").split(";")[0]!="application/json":
                    raise ValueError("A small JSON request is required.")
                data=json.loads(self.rfile.read(length))
                path=urlsplit(self.path).path
                if path=="/api/run":
                    config=Config.parse(data)
                    result=run(config)
                    result["crop"]=crop_prediction([config.moisture,config.temperature,config.humidity])
                    result["evidence_id"]=save_evidence(result,output)
                    self.respond(result)
                elif path=="/api/suite":
                    result=run_suite()
                    result["evidence_id"]=save_evidence(result,output,True)
                    self.respond(result)
                else:self.respond({"error":"Not found"},status=404)
            except (ValueError,TypeError,OverflowError) as e:
                self.respond({"error":str(e)},status=400)
            except OSError:
                self.respond({"error":"The evidence folder could not be written. Check folder permissions."},status=500)
            except Exception:
                traceback.print_exc()
                self.respond({"error":"The engine could not finish. Check the simulator terminal for details."},status=500)
    return Handler


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port",type=int,default=8766)
    p.add_argument("--output",type=Path,default=ROOT/"results")
    p.add_argument("--suite",action="store_true",help="Run checks and save evidence without starting a server")
    args=p.parse_args()
    if args.suite:
        result=run_suite();folder=save_evidence(result,args.output,True)
        print(f"{result['passed']}/{result['total']} checks passed. Evidence: {args.output/folder}")
        raise SystemExit(0 if result["passed"]==result["total"] else 1)
    server=ThreadingHTTPServer(("127.0.0.1",args.port),make_handler(args.output))
    print(f"SmartAgri Lab: http://127.0.0.1:{args.port}\nSynthetic data only. Press Ctrl+C to stop.",flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=="__main__":main()
