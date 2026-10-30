"""
Flask API Service - NFS / CBC : classification du type d'anémie (scikit-learn)
Remplace le relais Kaggle (cv-projet/test_interface) : même port 5003, même route.
Endpoints:
  POST  /predict                          -> prédiction seule, rien n'est enregistré
  POST  /api/users/<user_id>/sanguine     -> prédiction + enregistrement en table 'sanguine'
  PATCH /api/sanguines/<id>               -> corriger le diagnostic d'une analyse enregistrée
  GET   /health                           -> paramètres attendus, médianes et classes

Entrée (JSON) : {"valeurs": {"HGB": 8.5, "MCV": 70, "RBC": 3.8, ...}}
Les paramètres absents sont complétés par la médiane du jeu d'entraînement (comme predict.py).
"""

import math
import os

import joblib
import pandas as pd
import requests
from flask import Flask, jsonify, request

# ─── Config ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = "cbc_model.joblib"

BUNDLE = joblib.load(os.path.join(BASE_DIR, "model", MODEL_FILE))
MODEL = BUNDLE["model"]
FEATURES = list(BUNDLE["features"])
MEDIANS = {k: float(v) for k, v in BUNDLE["medians"].items()}
CLASSES = [str(c) for c in BUNDLE["label_encoder"].classes_]

# Backend FastAPI (backend_ai) qui gère la table 'sanguine'
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://localhost:8000")
# Frontend React autorisé à appeler ce service depuis le navigateur (CORS)
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://localhost:3000")

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# ─── Predict ──────────────────────────────────────────────────────────────────
class InputError(ValueError):
    pass


def read_valeurs(data):
    """Validate {"valeurs": {...}} and return the provided values as floats."""
    valeurs = (data or {}).get("valeurs")
    if not isinstance(valeurs, dict) or not valeurs:
        raise InputError("Envoyez {\"valeurs\": {...}} avec au moins un paramètre de la NFS.")

    inconnus = sorted(set(valeurs) - set(FEATURES))
    if inconnus:
        raise InputError(f"Paramètres inconnus : {inconnus}. Attendus : {FEATURES}")

    propres = {}
    for nom, valeur in valeurs.items():
        if valeur is None or valeur == "":
            continue  # champ laissé vide -> médiane
        try:
            nombre = float(valeur)
        except (TypeError, ValueError):
            raise InputError(f"La valeur de {nom} doit être un nombre.")
        if not math.isfinite(nombre) or nombre < 0:
            raise InputError(f"La valeur de {nom} doit être un nombre positif.")
        propres[nom] = nombre

    if not propres:
        raise InputError("Renseignez au moins un paramètre de la NFS.")
    return propres


def predire(valeurs: dict) -> dict:
    """Same logic as predict.py: missing parameters take the training median."""
    utilisees = {**MEDIANS, **valeurs}
    x = pd.DataFrame([utilisees])[FEATURES]
    proba = MODEL.predict_proba(x)[0]
    probabilities = {CLASSES[i]: round(float(p) * 100, 2) for i, p in enumerate(proba)}
    diagnostic = max(probabilities, key=probabilities.get)

    return {
        "valeurs": valeurs,
        "valeurs_utilisees": {f: round(utilisees[f], 4) for f in FEATURES},
        "parametres_completes": [f for f in FEATURES if f not in valeurs],
        "diagnostic": diagnostic,
        "confidence": probabilities[diagnostic],
        "probabilities": dict(sorted(probabilities.items(), key=lambda kv: -kv[1])),
        "modele": MODEL_FILE,
    }


def run_prediction():
    """Return (result, error_response)."""
    try:
        return predire(read_valeurs(request.get_json(silent=True))), None
    except InputError as e:
        return None, (jsonify({"error": str(e)}), 400)
    except Exception as e:
        return None, (jsonify({"error": f"Prédiction impossible : {str(e)}"}), 500)


def backend_json(resp):
    try:
        return resp.json()
    except ValueError:
        return resp.text


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/predict", methods=["POST"])
def predict_only():
    result, error = run_prediction()
    if error:
        return error
    return jsonify(result), 200


@app.route("/api/users/<int:user_id>/sanguine", methods=["POST"])
def predict_and_save(user_id):
    """Predict the diagnosis, then save it through the backend: POST /sanguines."""
    result, error = run_prediction()
    if error:
        return error

    try:
        resp = requests.post(f"{BACKEND_BASE_URL}/sanguines", json={**result, "user_id": user_id}, timeout=10)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Backend non joignable ({BACKEND_BASE_URL})", **result}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": "Le backend a mis trop de temps à répondre", **result}), 504

    if resp.status_code != 201:
        return jsonify({
            "error": "Le backend a refusé l'enregistrement",
            **result,
            "backendStatus": resp.status_code,
            "backendResponse": backend_json(resp),
        }), resp.status_code if resp.status_code < 500 else 502

    return jsonify({"userId": user_id, **result, "sanguine": backend_json(resp)}), 201


@app.route("/api/sanguines/<int:sanguine_id>", methods=["PATCH"])
def update_sanguine(sanguine_id):
    """Proxy endpoint: PATCH /sanguines/{id} with {diagnostic}."""
    diagnostic = (request.get_json(silent=True) or {}).get("diagnostic")
    if diagnostic not in CLASSES:
        return jsonify({"error": f"Diagnostic invalide. Valeurs possibles : {CLASSES}"}), 400

    try:
        resp = requests.patch(f"{BACKEND_BASE_URL}/sanguines/{sanguine_id}", json={"diagnostic": diagnostic}, timeout=10)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Backend non joignable ({BACKEND_BASE_URL})"}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": "Le backend a mis trop de temps à répondre"}), 504
    return jsonify(backend_json(resp)), resp.status_code


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "modele": MODEL_FILE,
        "model_type": type(MODEL).__name__,
        "parametres": FEATURES,
        "medianes": MEDIANS,
        "classes": CLASSES,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))
    print(f"Starting NFS/CBC API on port {port} | model: {type(MODEL).__name__} | backend: {BACKEND_BASE_URL}")
    app.run(host="0.0.0.0", port=port, debug=False)
