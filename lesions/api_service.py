"""
Flask API Service - Détection de lésions cutanées (EfficientNet-B0, 7 classes)
Endpoints:
  POST  /predict                         -> run AI only, nothing saved
  POST  /api/users/<user_id>/image       -> run AI, save result in 'lesion' table
  PATCH /api/lesions/<id>?type=VALUE     -> correct a saved result
  GET   /health
"""

import base64
import os

import cv2
import numpy as np
import requests
import timm
import torch
from flask import Flask, jsonify, request

# ─── Config ──────────────────────────────────────────────────────────────────
MODEL_NAME = "efficientnet_b0"
WEIGHTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "best.pth")
IMG = 224
MEL_FACTOR = 3.0                 # même valeur que app.py
TTA = True                       # moyenne de 4 vues (image + flips)
LOW, HIGH = 0.10, 0.30           # seuils de la jauge de vigilance

CLASS_NAMES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
LABELS = {"akiec": "Kératose actinique", "bcc": "Carcinome basocellulaire",
          "bkl": "Kératose bénigne", "df": "Dermatofibrome",
          "mel": "Mélanome", "nv": "Naevus", "vasc": "Lésion vasculaire"}
MEL = CLASS_NAMES.index("mel")
SUSPECT = [CLASS_NAMES.index(c) for c in ("mel", "bcc", "akiec")]

# URL of the FastAPI backend (backend_ai) that owns the 'lesion' table.
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
print("Loading lesion model...")
MODEL = timm.create_model(MODEL_NAME, pretrained=False, num_classes=len(CLASS_NAMES))
MODEL.load_state_dict(torch.load(WEIGHTS, map_location="cpu"))
MODEL.eval()
print(f"Model ready: {MODEL_NAME} | {IMG}px | TTA={TTA}\n")

mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
std = np.array([0.229, 0.224, 0.225], dtype=np.float32)


# ─── Predict ──────────────────────────────────────────────────────────────────
def preprocess(image_bytes: bytes):
    """Return (resized RGB image, input tensor)."""
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image file.")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (IMG, IMG), interpolation=cv2.INTER_AREA)
    x = torch.from_numpy(((img.astype(np.float32) / 255.0 - mean) / std)
                         .transpose(2, 0, 1)).unsqueeze(0)
    return img, x


def gradcam(x, idx):
    """Same Grad-CAM as app.py, on the last conv layer (conv_head)."""
    acts = {}
    h = MODEL.conv_head.register_forward_hook(lambda m, i, o: acts.__setitem__("a", o))
    with torch.enable_grad():
        out = MODEL(x)
        a = acts["a"]
        g = torch.autograd.grad(out[0, idx], a)[0]
    h.remove()
    w = g.mean(dim=(2, 3), keepdim=True)
    cam = torch.relu((w * a).sum(1))[0].detach().numpy()
    cam = cv2.resize(cam, (IMG, IMG))
    return (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)


def to_data_url(rgb_img) -> str:
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR),
                           [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        raise ValueError("Could not encode image.")
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


def vigilance_level(score: float) -> str:
    if score < LOW:
        return "faible"
    if score < HIGH:
        return "moderee"
    return "elevee"


def predict_image(image_bytes: bytes) -> dict:
    """Same logic as app.py: TTA average, mel boosted by MEL_FACTOR, renormalized."""
    img, x = preprocess(image_bytes)
    views = [x, x.flip(3), x.flip(2), x.flip((2, 3))] if TTA else [x]
    with torch.no_grad():
        ps = [torch.softmax(MODEL(v), 1)[0].numpy() for v in views]

    tops = []
    for q in ps:
        r = q.copy()
        r[MEL] *= MEL_FACTOR
        tops.append(int(r.argmax()))

    p = np.mean(ps, 0)
    p[MEL] *= MEL_FACTOR
    p = p / p.sum()
    top = int(p.argmax())
    score = float(p[SUSPECT].sum())

    cam = gradcam(x, top)
    heat = cv2.cvtColor(cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET),
                        cv2.COLOR_BGR2RGB)
    overlay = (0.6 * img + 0.4 * heat).astype(np.uint8)

    return {
        "type": CLASS_NAMES[top],
        "label": LABELS[CLASS_NAMES[top]],
        "confidence": round(float(p[top]) * 100, 2),
        "suspicion_score": round(score * 100, 2),
        "vigilance": vigilance_level(score),
        "coherence": f"{tops.count(top)}/{len(views)}",
        "probabilities": {c: round(float(p[i]) * 100, 2) for i, c in enumerate(CLASS_NAMES)},
        "image": to_data_url(img),
        "gradcam_image": to_data_url(overlay),
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
    except Exception:
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
    """
    Run the model, then save the result in the 'lesion' table through the
    FastAPI backend: POST /lesions.
    """
    result, error = run_prediction()
    if error:
        return error

    backend_url = f"{BACKEND_BASE_URL}/lesions"
    payload = {
        "type": result["type"],
        "user_id": user_id,
        "confidence": result["confidence"],
        "suspicion_score": result["suspicion_score"],
        "vigilance": result["vigilance"],
        "probabilities": result["probabilities"],
        "image": result["image"],
        "gradcam_image": result["gradcam_image"],
    }

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

    return jsonify({"userId": user_id, **result, "lesion": backend_json(resp)}), 201


@app.route("/api/lesions/<int:lesion_id>", methods=["PATCH"])
def update_lesion_type(lesion_id):
    """
    Proxy endpoint: manually correct a saved result.
    Query param: type=<code>  ->  PATCH /lesions/{id} {type}
    """
    lesion_type = request.args.get("type")
    if not lesion_type:
        return jsonify({"error": "Missing query parameter 'type'"}), 400

    if lesion_type not in CLASS_NAMES:
        return jsonify({"error": f"Invalid type value. Must be one of: {CLASS_NAMES}"}), 400

    backend_url = f"{BACKEND_BASE_URL}/lesions/{lesion_id}"
    try:
        resp = requests.patch(backend_url, json={"type": lesion_type}, timeout=10)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Could not connect to backend at {BACKEND_BASE_URL}"}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": "Backend request timed out"}), 504
    return jsonify(backend_json(resp)), resp.status_code


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": MODEL_NAME, "classes": CLASS_NAMES})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting lesion API on port {port}")
    print(f"Backend URL: {BACKEND_BASE_URL}")
    app.run(host="0.0.0.0", port=port, debug=False)
