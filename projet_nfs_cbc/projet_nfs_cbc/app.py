import subprocess
import sys

import joblib
import pandas as pd
import streamlit as st
from streamlit.runtime import exists

# Si on lance "python app.py", on démarre Streamlit automatiquement
if __name__ == "__main__" and not exists():
    subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
    sys.exit()

st.set_page_config(page_title="NFS / CBC", page_icon="🩸", layout="wide")

d = joblib.load("model/cbc_model.joblib")

st.title("🩸 Analyse NFS / CBC - type d'anémie")
st.caption("Outil d'étude, ne remplace pas un diagnostic médical.")

st.subheader("Saisie des paramètres")
vals = {}
cols = st.columns(4)
for i, f in enumerate(d["features"]):
    vals[f] = cols[i % 4].number_input(
        f, value=float(round(d["medians"][f], 2)), format="%.2f"
    )

if st.button("Prédire", type="primary"):
    x = pd.DataFrame([vals])[d["features"]]
    p = pd.Series(
        d["model"].predict_proba(x)[0], index=d["label_encoder"].classes_
    ).sort_values(ascending=False)

    st.success(f"Diagnostic probable : **{p.index[0]}** ({p.iloc[0]:.0%})")

    c1, c2 = st.columns([1, 2])
    c1.dataframe(p.rename("Probabilité").map("{:.1%}".format))
    c2.bar_chart(p)