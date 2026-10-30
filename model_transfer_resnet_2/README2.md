# API du modèle ResNet — Alzheimer Diagnostic AI

Ce projet expose une API REST Flask pour analyser une image IRM cérébrale
avec un modèle ResNet-18 entraîné par transfer learning.

Le modèle prédit l'un des quatre états suivants :

| Classe (`etatIrm`) | Signification |
|---|---|
| `No Impairment` | Aucun signe d'altération |
| `Very Mild Impairment` | Altération très légère |
| `Mild Impairment` | Altération légère |
| `Moderate Impairment` | Altération modérée |

## Adresse de l'API

Par défaut, le service démarre à l'adresse suivante :

```text
http://localhost:5000
```

Pour démarrer le service :

```bash
python api_service.py
```

La variable `PORT` permet de modifier le port :

```powershell
$env:PORT = "5000"
python api_service.py
```

Le backend FastAPI (`backend_ai`) qui gère la table `alzheimer` est
configuré avec `BACKEND_BASE_URL`. Sa valeur par défaut est
`http://localhost:8000`.

```powershell
$env:BACKEND_BASE_URL = "http://localhost:8000"
python api_service.py
```

## Prétraitement de l'image

Chaque image reçue est :

1. redimensionnée en `224 x 224` ;
2. convertie en niveaux de gris ;
3. convertie en tenseur PyTorch ;
4. normalisée ;
5. envoyée au modèle ResNet-18.

Les formats d'image supportés dépendent de Pillow, notamment JPEG et PNG.

---

## 1. Prédiction simple

### Requête

```http
POST /predict
```

Cette API prédit l'état IRM sans modifier la base de données.

### Entrée avec `multipart/form-data`

Le nom du champ fichier doit être `image`.

```bash
curl -X POST http://localhost:5000/predict ^
  -F "image=@model_transfer_resnet/1.jpg"
```

### Entrée avec un corps binaire brut

```bash
curl -X POST http://localhost:5000/predict ^
  -H "Content-Type: image/jpeg" ^
  --data-binary "@model_transfer_resnet/1.jpg"
```

### Sortie en cas de succès — HTTP `200`

```json
{
  "etatIrm": "No Impairment",
  "confidence": 96.4,
  "allProbabilities": {
    "No Impairment": 96.4,
    "Very Mild Impairment": 2.1,
    "Mild Impairment": 1.0,
    "Moderate Impairment": 0.5
  }
}
```

### Description de la sortie

| Champ | Type | Description |
|---|---|---|
| `etatIrm` | `string` | Classe prédite |
| `confidence` | `number` | Confiance de la classe prédite, en pourcentage |
| `allProbabilities` | `object` | Probabilité de chaque classe, en pourcentage |

Les valeurs de `allProbabilities` sont calculées avec `softmax` et leur somme
est normalement égale à environ `100`.

---

## 2. Prédiction et enregistrement dans la table `alzheimer`

### Requête

```http
POST /api/users/{userId}/image
```

Cette API reçoit une image, exécute la prédiction, puis enregistre le
résultat dans la table `alzheimer` via le backend FastAPI (`backend_ai`).

### Entrée

```bash
curl -X POST http://localhost:5000/api/users/3/image ^
  -F "image=@model_transfer_resnet/1.jpg"
```

Un corps binaire brut (`Content-Type: image/jpeg`) est également accepté.

### Appel interne au backend

```http
POST http://localhost:8000/alzheimers
{ "type": "Mild Impairment", "user_id": 3, "confidence": 87.52 }
```

L'URL `http://localhost:8000` peut être remplacée avec `BACKEND_BASE_URL`.

### Sortie en cas de succès — HTTP `201`

```json
{
  "userId": 3,
  "etatIrm": "Mild Impairment",
  "confidence": 87.52,
  "allProbabilities": {
    "No Impairment": 2.11,
    "Very Mild Impairment": 8.37,
    "Mild Impairment": 87.52,
    "Moderate Impairment": 2.0
  },
  "alzheimer": {
    "id": 12,
    "type": "Mild Impairment",
    "confidence": 87.52,
    "date_creation": "2026-10-26T21:40:00",
    "user_id": 3
  }
}
```

### Erreurs

| Code | Cas |
|---|---|
| `404` | Utilisateur introuvable (renvoyé par le backend) |
| `502` | Backend inaccessible |
| `504` | Backend trop lent |

---

## 3. Correction manuelle d'un résultat enregistré

```http
PATCH /api/alzheimers/{alzheimerId}?etatIrm=VALUE
```

```bash
curl -X PATCH "http://localhost:5000/api/alzheimers/12?etatIrm=Mild%20Impairment"
```

Transmis au backend sous la forme `PATCH /alzheimers/{id}` avec
`{ "type": "..." }`. `etatIrm` doit être l'une des quatre classes ; sinon
HTTP `400`.

---

## 4. Vérification de l'état du service

### Requête

```http
GET /health
```

Exemple :

```bash
curl http://localhost:5000/health
```

### Sortie — HTTP `200`

```json
{
  "status": "ok",
  "device": "cpu",
  "classes": [
    "No Impairment",
    "Very Mild Impairment",
    "Mild Impairment",
    "Moderate Impairment"
  ]
}
```

Le champ `device` peut être `cpu` ou un périphérique CUDA, selon la machine
utilisée.

---

## Gestion des erreurs de prédiction

### Image absente — HTTP `400`

```json
{
  "error": "No image provided. Send file in 'image' field or raw body."
}
```

### Image vide — HTTP `400`

```json
{
  "error": "Image is empty."
}
```

### Image invalide ou erreur du modèle — HTTP `500`

```json
{
  "error": "Prediction failed: ..."
}
```

---

## Résumé des endpoints

| Méthode | Endpoint | Entrée | Fonction |
|---|---|---|---|
| `POST` | `/predict` | Image IRM | Retourne la prédiction sans modifier la base |
| `POST` | `/api/users/{userId}/image` | Image IRM et identifiant utilisateur | Prédit et enregistre dans la table `alzheimer` |
| `PATCH` | `/api/alzheimers/{id}` | `etatIrm` dans la query string | Corrige un résultat enregistré |
| `GET` | `/health` | Aucune | Vérifie que le service est opérationnel |

## Avertissement médical

Ce modèle est un outil d'aide à la décision et de recherche. Il ne remplace
pas le diagnostic d'un professionnel de santé qualifié.
