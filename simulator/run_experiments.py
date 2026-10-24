"""Save all nine prescribed scenarios and actual regression outcomes."""
import argparse
import csv
import hashlib
import json
import platform
from datetime import datetime,timezone
from pathlib import Path

from engine import PRESETS, preset_config, run, run_suite, VERSION
from server import csv_trace, crop_prediction, ROOT


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=ROOT/"results")
    args=p.parse_args()
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder=args.output/("experiment-"+stamp)
    folder.mkdir(parents=True,exist_ok=False)
    summaries=[]
    for preset in PRESETS:
        config=preset_config(preset["id"])
        result=run(config)
        result["crop"]=crop_prediction([config.moisture,config.temperature,config.humidity])
        (folder/(preset["id"]+".json")).write_text(json.dumps(result,indent=2,allow_nan=False),encoding="utf-8")
        (folder/(preset["id"]+".csv")).write_text(csv_trace(result),encoding="utf-8",newline="")
        summaries.append({"scenario":preset["id"],**result["summary"]})
    suite=run_suite()
    (folder/"checks.json").write_text(json.dumps(suite,indent=2),encoding="utf-8")
    with (folder/"summary.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
    files=[ROOT/"engine.py",ROOT/"server.py",ROOT/"train_model.py",ROOT/"firmware"/"controller.h",*sorted((ROOT/"static").iterdir())]
    manifest={"engine":VERSION,"created_utc":stamp,"python":platform.python_version(),"scenarios":len(summaries),
              "checks_passed":suite["passed"],"checks_total":suite["total"],"source_sha256":{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},
              "scope":"Deterministic synthetic traces, one seed per preset. This is not an independent repeated field-trial dataset."}
    (folder/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(f"Saved {len(summaries)} scenario traces and {suite['passed']}/{suite['total']} passed checks to {folder}")
    raise SystemExit(0 if suite["passed"]==suite["total"] else 1)


if __name__=="__main__":main()
