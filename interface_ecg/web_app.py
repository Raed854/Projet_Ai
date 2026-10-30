"""
Flask API - Classification de battements ECG (CNN 1D, 187 valeurs, 5 classes)
Endpoints:
  GET   /                                  -> interface de test (templates/index.html)
  GET   /model-info
  POST  /predict                           -> prédiction seule, rien n'est enregistré
  POST  /api/users/<user_id>/cardiaque     -> prédiction + enregistrement en table 'cardiaque'
  PATCH /api/cardiaques/<id>               -> renseigner la classe réelle d'une analyse enregistrée
"""

from flask import Flask, render_template, request, jsonify
import numpy as np
import requests
import tensorflow as tf
import os

app = Flask(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "ecg_cnn_final.keras")
BEST_MODEL_PATH = os.path.join(BASE_DIR, "best_ecg_cnn.keras")
SIGNAL_LENGTH = 187

CLASS_NAMES = {
    0: "N - Battement normal",
    1: "S - Battement supraventriculaire",
    2: "V - Contraction ventriculaire prématurée",
    3: "F - Fusion normale et ventriculaire",
    4: "Q - Battement non classifiable",
}
CLASS_CODES = {i: name.split(" - ")[0] for i, name in CLASS_NAMES.items()}  # 0 -> "N", ...

# Backend FastAPI (backend_ai) qui gère la table 'cardiaque'
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://localhost:8000")
# Frontend React autorisé à appeler ce service depuis le navigateur (CORS)
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://localhost:3000")


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# Chargement du modèle
def load_model():
    if os.path.exists(MODEL_PATH):
        path = MODEL_PATH
    elif os.path.exists(BEST_MODEL_PATH):
        path = BEST_MODEL_PATH
    else:
        raise FileNotFoundError("Aucun fichier de modèle .keras trouvé.")
    return tf.keras.models.load_model(path, compile=False), os.path.basename(path)

model, model_file = load_model()


def predict_signal(signal):
    """Return (predicted_class, probs) for a 187-value signal."""
    x = np.array(signal, dtype='float32')
    if len(model.input_shape) == 3:
        x = x.reshape(1, -1, 1)
    else:
        x = x.reshape(1, -1)
    probs = model.predict(x, verbose=0)[0]
    return int(np.argmax(probs)), probs


def read_signal(data):
    """Return (signal, error_response)."""
    signal = (data or {}).get('signal', [])
    if not isinstance(signal, list) or len(signal) != SIGNAL_LENGTH:
        return None, (jsonify({
            'error': f'Le signal doit contenir exactement {SIGNAL_LENGTH} valeurs'
        }), 400)
    try:
        signal = [float(v) for v in signal]
    except (TypeError, ValueError):
        return None, (jsonify({'error': 'Le signal ne doit contenir que des nombres'}), 400)
    if not all(np.isfinite(signal)):
        return None, (jsonify({'error': 'Le signal contient des valeurs invalides (NaN ou infini)'}), 400)
    return signal, None


def read_classe_reelle(value):
    """Accept 0-4 (MIT-BIH label) or a class code N/S/V/F/Q. Return (code, error_response)."""
    if value in (None, ''):
        return None, None
    if str(value).upper() in CLASS_CODES.values():
        return str(value).upper(), None
    try:
        index = int(float(value))
    except (TypeError, ValueError):
        index = None
    if index in CLASS_CODES:
        return CLASS_CODES[index], None
    return None, (jsonify({'error': 'classe_reelle doit être 0-4 ou N, S, V, F, Q'}), 400)


def backend_json(resp):
    try:
        return resp.json()
    except ValueError:
        return resp.text


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/model-info')
def model_info():
    """Retourner les informations sur le modèle"""
    try:
        # Charger les prédictions si disponibles pour calculer l'accuracy
        predictions_path = os.path.join(BASE_DIR, 'predictions_ecg.csv')
        accuracy = 'N/A'

        if os.path.exists(predictions_path):
            import pandas as pd
            df = pd.read_csv(predictions_path)
            if 'classe_reelle' in df.columns and 'classe_predite' in df.columns:
                acc = (df['classe_reelle'] == df['classe_predite']).mean()
                accuracy = f'{acc * 100:.2f}%'

        return jsonify({
            'accuracy': accuracy,
            'model_type': 'CNN 1D',
            'input_size': SIGNAL_LENGTH,
            'num_classes': len(CLASS_NAMES)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    signal, error = read_signal(request.get_json(silent=True))
    if error:
        return error

    try:
        predicted_class, probs = predict_signal(signal)
        return jsonify({
            'predicted_class': predicted_class,
            'class_name': CLASS_NAMES[predicted_class],
            'confidence': float(probs[predicted_class]),
            'probabilities': {CLASS_NAMES[i]: float(probs[i]) for i in range(len(probs))}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<int:user_id>/cardiaque', methods=['POST'])
def predict_and_save(user_id):
    """Predict the beat class, then save it through the backend: POST /cardiaques."""
    data = request.get_json(silent=True)
    signal, error = read_signal(data)
    if error:
        return error
    classe_reelle, error = read_classe_reelle((data or {}).get('classe_reelle'))
    if error:
        return error

    try:
        predicted_class, probs = predict_signal(signal)
    except Exception as e:
        return jsonify({'error': f'Prédiction impossible : {str(e)}'}), 500

    result = {
        'classe': CLASS_CODES[predicted_class],
        'class_name': CLASS_NAMES[predicted_class],
        'confidence': round(float(probs[predicted_class]) * 100, 2),
        'probabilities': {CLASS_CODES[i]: round(float(probs[i]) * 100, 2) for i in range(len(probs))},
        'classe_reelle': classe_reelle,
        'prediction_correcte': None if classe_reelle is None else CLASS_CODES[predicted_class] == classe_reelle,
        'modele': model_file,
    }

    backend_url = f"{BACKEND_BASE_URL}/cardiaques"
    payload = {
        'signal': signal,
        **{k: v for k, v in result.items() if k != 'class_name'},
        'user_id': user_id,
    }

    try:
        resp = requests.post(backend_url, json=payload, timeout=10)
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'Backend non joignable ({BACKEND_BASE_URL})', **result}), 502
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Le backend a mis trop de temps à répondre', **result}), 504

    if resp.status_code != 201:
        return jsonify({
            'error': "Le backend a refusé l'enregistrement",
            **result,
            'backendStatus': resp.status_code,
            'backendResponse': backend_json(resp),
        }), resp.status_code if resp.status_code < 500 else 502

    return jsonify({'userId': user_id, **result, 'cardiaque': backend_json(resp)}), 201


@app.route('/api/cardiaques/<int:cardiaque_id>', methods=['PATCH'])
def update_cardiaque(cardiaque_id):
    """Proxy endpoint: PATCH /cardiaques/{id} with {classe_reelle} (0-4, N/S/V/F/Q or null)."""
    body = request.get_json(silent=True) or {}
    if 'classe_reelle' not in body:
        return jsonify({'error': 'Envoyez "classe_reelle" (0-4, N/S/V/F/Q ou null)'}), 400
    classe_reelle, error = read_classe_reelle(body['classe_reelle'])
    if error:
        return error

    try:
        resp = requests.patch(
            f"{BACKEND_BASE_URL}/cardiaques/{cardiaque_id}",
            json={'classe_reelle': classe_reelle},
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'Backend non joignable ({BACKEND_BASE_URL})'}), 502
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Le backend a mis trop de temps à répondre'}), 504
    return jsonify(backend_json(resp)), resp.status_code


if __name__ == '__main__':
    # 5000 est déjà utilisé par le service Alzheimer : 5004 par défaut
    port = int(os.environ.get('PORT', 5004))
    print(f"Starting ECG API on port {port} | model: {model_file} | backend: {BACKEND_BASE_URL}")
    app.run(debug=True, port=port)
