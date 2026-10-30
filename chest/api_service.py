"""
Flask API Service - Détection de pneumonie sur radiographie thoracique (DenseNet121)
Endpoints:
  POST  /predict                        -> run AI only, nothing saved
  POST  /api/users/<user_id>/image      -> run AI, save result in 'chest' table
  PATCH /api/chests/<id>?classe=VALUE   -> correct a saved result (NORMAL / PNEUMONIA)
  GET   /health
"""

import base64
import io
import json
import os

import numpy as np
import requests
import tensorflow as tf
from flask import Flask, jsonify, request
from PIL import Image, UnidentifiedImageError

# ─── Config ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = "lung_model.keras"
SEUIL = 0.5  # score > SEUIL -> PNEUMONIA (comme predict.py)

with open(os.path.join(BASE_DIR, "classes.json"), encoding="utf-8") as f:
    _classes = json.load(f)
CLASS_NAMES = [_classes["0"], _classes["1"]]  # ["NORMAL", "PNEUMONIA"]
IMG_SIZE = tuple(_classes.get("image_size", [224, 224]))

# URL of the FastAPI backend (backend_ai) that owns the 'chest' table.
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


# ─── Model ────────────────────────────────────────────────────────────────────
print("Loading chest model...")
MODEL = tf.keras.models.load_model(os.path.join(BASE_DIR, MODEL_FILE))
print(f"Model ready: {MODEL_FILE} | input {MODEL.input_shape}\n")


# ─── Predict ──────────────────────────────────────────────────────────────────
def to_data_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def predict_image(image_bytes: bytes) -> dict:
    """Same preprocessing as predict.py: RGB, 224x224, raw 0-255 values (normalisation is in the model)."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise ValueError("Invalid image file.")
    img = img.resize(IMG_SIZE)
    x = np.expand_dims(np.asarray(img, dtype="float32"), 0)

    score = float(MODEL.predict(x, verbose=0)[0][0])  # probabilité de pneumonie
    classe = CLASS_NAMES[int(score > SEUIL)]
    probabilities = {CLASS_NAMES[0]: round((1 - score) * 100, 2), CLASS_NAMES[1]: round(score * 100, 2)}

    return {
        "classe": classe,
        "score_pneumonie": round(score * 100, 2),
        "confidence": probabilities[classe],
        "probabilities": probabilities,
        "seuil": SEUIL * 100,
        "modele": MODEL_FILE,
        "image": to_data_url(img),
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────
def read_image_bytes():
    """Return (image_bytes, error_response) from multipart 'image' field or raw body."""
    if "image" in request.files:
        image_bytes = request.files["image"].read()
    elif request.data:
        image_bytes = request.data
    else:
        return None, (jsonify({"error": "No image provided. Send file in 'image' field or raw body."}), 400)

    if not image_bytes:
        return None, (jsonify({"error": "Image is empty."}), 400)
    return image_bytes, None


def run_prediction():
    """Return (result, error_response)."""
    image_bytes, error = read_image_bytes()
    if error:
        return None, error
    try:
        return predict_image(image_bytes), None
    except ValueError as e:
        return None, (jsonify({"error": str(e)}), 400)
    except Exception as e:
        return None, (jsonify({"error": f"Prediction failed: {str(e)}"}), 500)


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


@app.route("/api/users/<int:user_id>/image", methods=["POST"])
def upload_image_and_save(user_id):
    """Run the model, then save the result in the 'chest' table: POST /chests."""
    result, error = run_prediction()
    if error:
        return error

    backend_url = f"{BACKEND_BASE_URL}/chests"
    try:
        resp = requests.post(backend_url, json={**result, "user_id": user_id}, timeout=10)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Could not connect to backend at {BACKEND_BASE_URL}", **result}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": "Backend request timed out", **result}), 504

    if resp.status_code != 201:
        return jsonify({
            "error": "Backend refused to save the result",
            **result,
            "backendStatus": resp.status_code,
            "backendResponse": backend_json(resp),
        }), resp.status_code if resp.status_code < 500 else 502

    return jsonify({"userId": user_id, **result, "chest": backend_json(resp)}), 201


@app.route("/api/chests/<int:chest_id>", methods=["PATCH"])
def update_chest(chest_id):
    """
    Proxy endpoint: manually correct a saved result.
    Query param: classe=NORMAL|PNEUMONIA  ->  PATCH /chests/{id} {classe}
    """
    classe = (request.args.get("classe") or "").upper()
    if classe not in CLASS_NAMES:
        return jsonify({"error": f"Invalid classe. Must be one of: {CLASS_NAMES}"}), 400

    try:
        resp = requests.patch(f"{BACKEND_BASE_URL}/chests/{chest_id}", json={"classe": classe}, timeout=10)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Could not connect to backend at {BACKEND_BASE_URL}"}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": "Backend request timed out"}), 504
    return jsonify(backend_json(resp)), resp.status_code


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": MODEL_FILE, "classes": CLASS_NAMES, "seuil": SEUIL})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    print(f"Starting chest API on port {port}")
    print(f"Backend URL: {BACKEND_BASE_URL}")
    app.run(host="0.0.0.0", port=port, debug=False)
