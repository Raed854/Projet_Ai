import json, sys
import joblib, pandas as pd

d = joblib.load("model/cbc_model.joblib")

def predire(valeurs: dict):
    x = pd.DataFrame([{**d["medians"], **valeurs}])[d["features"]]
    p = d["model"].predict_proba(x)[0]
    return pd.Series(p, index=d["label_encoder"].classes_).sort_values(ascending=False)

if __name__ == "__main__":
    vals = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {"HGB": 8.5, "MCV": 70, "RBC": 3.8}
    print("Colonnes :", d["features"])
    print(predire(vals).round(3).to_string())
