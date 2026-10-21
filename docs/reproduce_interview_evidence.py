"""Reproduce existing trainers in a temporary directory; leave runtime models alone.

Run from the repository: python docs/reproduce_interview_evidence.py
Outputs are preparation-session evidence, not historical deployment results.
"""
import contextlib
import hashlib
import io
import json
import platform
import runpy
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, top_k_accuracy_score


def main():
    root = Path(__file__).resolve().parents[1]
    out = root / "docs" / "interview_evidence"
    out.mkdir(exist_ok=True)
    data = pd.read_csv(root / "crop_data.csv")
    evidence = {
        "purpose": "New preparation-session reproduction, not original project metrics or field validation",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "versions": {"python": platform.python_version(), "sklearn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__},
        "dataset_sha256": hashlib.sha256((root / "crop_data.csv").read_bytes()).hexdigest(),
        "rows": len(data), "columns": list(data.columns),
        "label_counts": {str(k): int(v) for k, v in data.label.value_counts().sort_index().items()},
        "missing_cells": int(data.isna().sum().sum()),
        "duplicate_rows": int(data.duplicated().sum()),
        "experiments": {},
    }
    for script in ("train_model_v2.py", "train_model_sensor_aligned.py"):
        with tempfile.TemporaryDirectory(prefix="smartagri-interview-") as temp:
            target = Path(temp)
            for name in (script, "crop_data.csv", "sensor_log.csv"):
                shutil.copy2(root / name, target / name)
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                scope = runpy.run_path(str(target / script), run_name="__main__")
            (out / f"{Path(script).stem}_stdout.txt").write_text(captured.getvalue(), encoding="utf-8")
            model = scope.get("pipeline", scope.get("model"))
            xt, yt = scope["X_test"], scope["y_test"]
            prediction = model.predict(xt)
            probabilities = model.predict_proba(xt)
            dummy = DummyClassifier(strategy="most_frequent").fit(scope["X_train"], scope["y_train"])
            classes = model.classes_
            evidence["experiments"][script] = {
                "train_rows": len(scope["X_train"]), "test_rows": len(xt),
                "features": list(scope["X"].columns),
                "accuracy": accuracy_score(yt, prediction),
                "correct": int(np.sum(np.asarray(yt) == prediction)),
                "macro_f1": f1_score(yt, prediction, average="macro"),
                "top3_accuracy": top_k_accuracy_score(yt, probabilities, k=3, labels=classes),
                "majority_baseline_accuracy": accuracy_score(yt, dummy.predict(xt)),
                "classification_report": classification_report(yt, prediction, output_dict=True, zero_division=0),
                "feature_importances": dict(zip(scope["X"].columns, (model.named_steps["rf"] if hasattr(model, "named_steps") else model).feature_importances_.tolist())),
            }
            pd.DataFrame(confusion_matrix(yt, prediction, labels=classes), index=classes, columns=classes).to_csv(out / f"{Path(script).stem}_confusion.csv")
            pd.DataFrame({"dataset_row_index": xt.index, "actual": np.asarray(yt), "predicted": prediction}).to_csv(out / f"{Path(script).stem}_predictions.csv", index=False)
    (out / "metrics.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in evidence.items() if k != "experiments"}, indent=2))
    for name, result in evidence["experiments"].items():
        print(name, {k: result[k] for k in ("accuracy", "correct", "macro_f1", "top3_accuracy", "majority_baseline_accuracy")})


if __name__ == "__main__":
    main()
