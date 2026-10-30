import glob
import joblib, pandas as pd, numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder

csv = glob.glob("data/*.csv")[0]
df = pd.read_csv(csv).drop_duplicates().reset_index(drop=True)
TARGET = "Diagnosis" if "Diagnosis" in df.columns else df.columns[-1]
X = df.drop(columns=[TARGET]).select_dtypes(include=np.number)
X = X.fillna(X.median())
le = LabelEncoder()
y = le.fit_transform(df[TARGET])
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
m = RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=42).fit(Xtr, ytr)
print(classification_report(yte, m.predict(Xte), target_names=le.classes_))
joblib.dump({"model": m, "label_encoder": le, "features": list(X.columns),
             "medians": X.median().to_dict()}, "model/cbc_model.joblib")
print("Modèle sauvegardé dans model/cbc_model.joblib")
