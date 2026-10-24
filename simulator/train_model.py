"""Optional crop experiment; training-only proxy normalization, stratified holdout."""
import hashlib
import json
import pickle
import platform
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import sklearn

ROOT=Path(__file__).resolve().parent


def main():
    source=ROOT.parent/"crop_data.csv"
    df=pd.read_csv(source)
    train,test=train_test_split(df,test_size=.2,stratify=df.label,random_state=42)
    proxy=.6*train.rainfall+.4*train.humidity
    lo,hi=float(proxy.min()),float(proxy.max())
    def features(frame):
        return frame[["temperature","humidity"]].assign(moisture=100*(.6*frame.rainfall+.4*frame.humidity-lo)/(hi-lo))
    model=make_pipeline(StandardScaler(),RandomForestClassifier(n_estimators=200,max_depth=12,min_samples_leaf=3,random_state=42,n_jobs=-1))
    model.fit(features(train),train.label)
    predicted=model.predict(features(test))
    probs=model.predict_proba(features(test));indices=np.argsort(probs,axis=1)[:,-3:]
    metrics={"python_version":platform.python_version(),"sklearn_version":sklearn.__version__,"pandas_version":pd.__version__,"numpy_version":np.__version__,
             "dataset_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"train_rows":len(train),"test_rows":len(test),
             "random_state":42,"accuracy":float(accuracy_score(test.label,predicted)),"macro_f1":float(f1_score(test.label,predicted,average="macro")),
             "top3_accuracy":float(np.mean([label in model.classes_[ii] for label,ii in zip(test.label,indices)])),
             "proxy_train_min":lo,"proxy_train_max":hi,
             "scope":"Held-out public dataset with engineered rainfall/humidity moisture proxy; not measured-soil or field accuracy."}
    (ROOT/"model").mkdir(exist_ok=True)
    (ROOT/"model"/"crop_model.pkl").write_bytes(pickle.dumps(model))
    (ROOT/"model"/"metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
    print(json.dumps(metrics,indent=2))


if __name__=="__main__":main()
