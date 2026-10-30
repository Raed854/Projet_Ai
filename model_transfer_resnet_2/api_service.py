"""
Flask API Service - Alzheimer Diagnostic AI
Endpoints:
  POST  /predict                          -> run AI only, nothing saved
  POST  /api/users/<user_id>/image        -> run AI, save result in 'alzheimer' table
  PATCH /api/alzheimers/<id>?etatIrm=VALUE -> correct a saved result
"""

import os
import io
import requests
from flask import Flask, request, jsonify
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

# ─── Config ──────────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_transfer_resnet")
NUM_CLASSES = 4
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CLASS_NAMES = [
    "No Impairment",
    "Very Mild Impairment",
    "Mild Impairment",
    "Moderate Impairment",
]

# URL of the FastAPI backend (backend_ai) that owns the 'alzheimer' table.
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

# ─── Build Model ──────────────────────────────────────────────────────────────
def build_model(num_classes=4):
    model = models.resnet18(weights=None)
    model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(in_features, 256),
        nn.BatchNorm1d(256),
        nn.ReLU(),
        nn.Dropout(0.5),
        nn.Linear(256, num_classes),
    )
    return model


def load_model(model_path, num_classes=4, device="cpu"):
    import zipfile

    pt_path = model_path + ".pt"
    if not os.path.exists(pt_path) and os.path.isdir(model_path):
        print("Repackaging model directory to .pt ...")
        with zipfile.ZipFile(pt_path, "w") as zf:
            for root, _, files in os.walk(model_path):
                for file in files:
                    fp = os.path.join(root, file)
                    arcname = os.path.relpath(fp, os.path.dirname(model_path))
                    info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
                    with open(fp, "rb") as f:
                        zf.writestr(info, f.read())

    state_dict = torch.load(pt_path, map_location=device, weights_only=False)
    model = build_model(num_classes)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    print(f"Model loaded on {device}")
    return model


# ─── Image Transform ──────────────────────────────────────────────────────────
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.Grayscale(num_output_channels=1),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485], std=[0.229]),
])


# ─── Predict ──────────────────────────────────────────────────────────────────
def predict_image(image_bytes: bytes):
    """Run inference on raw image bytes. Returns (class_name, confidence, all_probs)."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = transform(img).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = MODEL(tensor)
        probs = torch.softmax(outputs, dim=1)[0]
        predicted_idx = probs.argmax().item()
        confidence = probs[predicted_idx].item() * 100

    all_probs = {CLASS_NAMES[i]: round(probs[i].item() * 100, 2) for i in range(NUM_CLASSES)}
    return CLASS_NAMES[predicted_idx], confidence, all_probs


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/predict", methods=["POST"])
def predict_only():
    """
    Simple prediction endpoint called by the Java backend.
    Accepts multipart/form-data with 'image' field OR raw binary body.
    Returns: { etatIrm, confidence, allProbabilities }
    No callback to the backend - Java handles DB update itself.
    """
    if "image" in request.files:
        image_bytes = request.files["image"].read()
    elif request.data:
        image_bytes = request.data
    else:
        return jsonify({"error": "No image provided. Send file in 'image' field or raw body."}), 400

    if not image_bytes:
        return jsonify({"error": "Image is empty."}), 400

    try:
        etat_irm, confidence, all_probs = predict_image(image_bytes)
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

    return jsonify({
        "etatIrm": etat_irm,
        "confidence": round(confidence, 2),
        "allProbabilities": all_probs,
    }), 200


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


def backend_json(resp):
    try:
        return resp.json()
    except Exception:
        return resp.text


@app.route("/api/users/<int:user_id>/image", methods=["POST"])
def upload_image_and_save(user_id):
    """
    Receive an MRI image, run AI model, then save the result in the 'alzheimer'
    table through the FastAPI backend: POST /alzheimers {type, user_id, confidence}.

    Form-data field: 'image' (file)
    OR raw binary body with Content-Type: image/*
    """
    image_bytes, error = read_image_bytes()
    if error:
        return error

    # ── AI Prediction ─────────────────────────────────────────────────────────
    try:
        etat_irm, confidence, all_probs = predict_image(image_bytes)
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

    # ── Save in alzheimer table: POST /alzheimers ─────────────────────────────
    backend_url = f"{BACKEND_BASE_URL}/alzheimers"
    payload = {"type": etat_irm, "user_id": user_id, "confidence": round(confidence, 2)}

    try:
        resp = requests.post(backend_url, json=payload, timeout=10)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Could not connect to backend at {BACKEND_BASE_URL}"}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": "Backend request timed out"}), 504

    if resp.status_code != 201:
        return jsonify({
            "error": "Backend refused to save the result",
            "etatIrm": etat_irm,
            "confidence": round(confidence, 2),
            "backendStatus": resp.status_code,
            "backendResponse": backend_json(resp),
        }), resp.status_code if resp.status_code < 500 else 502

    return jsonify({
        "userId": user_id,
        "etatIrm": etat_irm,
        "confidence": round(confidence, 2),
        "allProbabilities": all_probs,
        "alzheimer": backend_json(resp),
    }), 201


@app.route("/api/alzheimers/<int:alzheimer_id>", methods=["PATCH"])
def update_alzheimer_type(alzheimer_id):
    """
    Proxy endpoint: manually correct a saved result.
    Query param: etatIrm=<value>  ->  PATCH /alzheimers/{id} {type}
    """
    etat_irm = request.args.get("etatIrm")
    if not etat_irm:
        return jsonify({"error": "Missing query parameter 'etatIrm'"}), 400

    if etat_irm not in CLASS_NAMES:
        return jsonify({
            "error": f"Invalid etatIrm value. Must be one of: {CLASS_NAMES}"
        }), 400

    backend_url = f"{BACKEND_BASE_URL}/alzheimers/{alzheimer_id}"
    try:
        resp = requests.patch(backend_url, json={"type": etat_irm}, timeout=10)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Could not connect to backend at {BACKEND_BASE_URL}"}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": "Backend request timed out"}), 504
    return jsonify(backend_json(resp)), resp.status_code


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "device": str(DEVICE), "classes": CLASS_NAMES})


# ─── Load model at startup ────────────────────────────────────────────────────
print("Loading AI model...")
MODEL = load_model(MODEL_PATH, num_classes=NUM_CLASSES, device=DEVICE)
print("Model ready.\n")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting API on port {port}")
    print(f"Backend URL: {BACKEND_BASE_URL}")
    app.run(host="0.0.0.0", port=port, debug=False)
