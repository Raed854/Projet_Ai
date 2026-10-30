"""
Flask API Service - Dosage IA (courbes de titrage acido-basique)
Endpoints:
  POST  /predict                     -> analyse a curve, nothing saved
  POST  /api/users/<user_id>/dosage  -> analyse a curve, save result in 'dosage' table
  PATCH /api/dosages/<id>            -> update type_declare / a_revoir of a saved result
  GET   /health

Input (JSON):
  { "volumes": [...], "ph": [...], "c_titrant": 0.1, "v_prise": 20, "type_declare": "acide_faible" }
OR multipart/form-data with an Excel file in 'file' (columns 'volume' and 'ph')
plus optional form fields c_titrant, v_prise, type_declare.

Run from the project root:  python api_service.py
"""

import os
from pathlib import Path

import requests
from flask import Flask, jsonify, request

from ai_model.chemistry import TYPES
from ai_model.service import analyser_courbe, modele_actif

# ─── Config ──────────────────────────────────────────────────────────────────
MODELS_DIR = Path(__file__).resolve().parent / "ai_model" / "models_store"

# URL of the FastAPI backend (backend_ai) that owns the 'dosage' table.
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://localhost:8000")
# Frontend React allowed to call this service from the browser (CORS).
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://localhost:3000")

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# ─── Input parsing ────────────────────────────────────────────────────────────
class InputError(ValueError):
    pass


def optional_float(value, name):
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise InputError(f"'{name}' must be a number.")
    if number <= 0:
        raise InputError(f"'{name}' must be greater than 0.")
    return number


def read_curve():
    """Return (volumes, ph, c_titrant, v_prise, type_declare) from JSON or Excel upload."""
    if "file" in request.files:
        from ai_model.predire_excel import lire_courbe  # pandas + openpyxl only needed here

        try:
            volumes, ph = lire_courbe(request.files["file"])
        except ImportError:
            raise InputError("Excel support requires 'openpyxl' (pip install openpyxl).")
        params = request.form
    else:
        params = request.get_json(silent=True)
        if not isinstance(params, dict):
            raise InputError("Send JSON {volumes, ph, ...} or an Excel file in the 'file' field.")
        volumes, ph = params.get("volumes"), params.get("ph")

    if not isinstance(volumes, list) or not isinstance(ph, list):
        raise InputError("'volumes' and 'ph' must be lists of numbers.")
    if len(volumes) != len(ph):
        raise InputError("'volumes' and 'ph' must have the same length.")
    try:
        volumes = [float(v) for v in volumes]
        ph = [float(p) for p in ph]
    except (TypeError, ValueError):
        raise InputError("'volumes' and 'ph' must contain only numbers.")

    type_declare = params.get("type_declare") or None
    if type_declare is not None and type_declare not in TYPES:
        raise InputError(f"Invalid type_declare. Must be one of: {list(TYPES)}")

    return (
        volumes,
        ph,
        optional_float(params.get("c_titrant"), "c_titrant"),
        optional_float(params.get("v_prise"), "v_prise"),
        type_declare,
    )


def run_analysis():
    """Return (inputs, result, error_response)."""
    try:
        volumes, ph, c_titrant, v_prise, type_declare = read_curve()
        result = analyser_courbe(MODELS_DIR, volumes, ph, c_titrant, v_prise, type_declare)
    except ValueError as e:  # InputError, or curve rejected by the model (< 5 points...)
        return None, None, (jsonify({"error": str(e)}), 400)
    except Exception as e:
        return None, None, (jsonify({"error": f"Analysis failed: {str(e)}"}), 500)

    inputs = {
        "volumes": volumes,
        "ph": ph,
        "c_titrant": c_titrant,
        "v_prise": v_prise,
        "type_declare": type_declare,
    }
    return inputs, result, None


def backend_json(resp):
    try:
        return resp.json()
    except Exception:
        return resp.text


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/predict", methods=["POST"])
def predict_only():
    inputs, result, error = run_analysis()
    if error:
        return error
    return jsonify(result), 200


@app.route("/api/users/<int:user_id>/dosage", methods=["POST"])
def analyse_and_save(user_id):
    """Analyse the curve, then save inputs + result through the backend: POST /dosages."""
    inputs, result, error = run_analysis()
    if error:
        return error

    backend_url = f"{BACKEND_BASE_URL}/dosages"
    payload = {**inputs, **result, "user_id": user_id}

    try:
        resp = requests.post(backend_url, json=payload, timeout=10)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Could not connect to backend at {BACKEND_BASE_URL}"}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": "Backend request timed out"}), 504

    if resp.status_code != 201:
        return jsonify({
            "error": "Backend refused to save the result",
            **result,
            "backendStatus": resp.status_code,
            "backendResponse": backend_json(resp),
        }), resp.status_code if resp.status_code < 500 else 502

    return jsonify({"userId": user_id, **result, "dosage": backend_json(resp)}), 201


@app.route("/api/dosages/<int:dosage_id>", methods=["PATCH"])
def update_dosage(dosage_id):
    """Proxy endpoint: PATCH /dosages/{id} with {type_declare?, a_revoir?}."""
    body = request.get_json(silent=True) or {}
    update = {k: body[k] for k in ("type_declare", "a_revoir") if k in body}
    if not update:
        return jsonify({"error": "Nothing to update: send 'type_declare' and/or 'a_revoir'."}), 400
    if update.get("type_declare") not in (None, *TYPES):
        return jsonify({"error": f"Invalid type_declare. Must be one of: {list(TYPES)}"}), 400

    backend_url = f"{BACKEND_BASE_URL}/dosages/{dosage_id}"
    try:
        resp = requests.patch(backend_url, json=update, timeout=10)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Could not connect to backend at {BACKEND_BASE_URL}"}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": "Backend request timed out"}), 504
    return jsonify(backend_json(resp)), resp.status_code


@app.route("/health", methods=["GET"])
def health():
    bundle = modele_actif(MODELS_DIR)
    return jsonify({"status": "ok", "modele_version": bundle["version"], "types": list(TYPES)})


# ─── Load (or train once) the active model at startup ────────────────────────
print("Loading dosage model (first start trains it on 4000 synthetic curves, may take a few minutes)...")
print(f"Model ready: {modele_actif(MODELS_DIR)['version']}\n")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    print(f"Starting dosage API on port {port}")
    print(f"Backend URL: {BACKEND_BASE_URL}")
    app.run(host="0.0.0.0", port=port, debug=False)
