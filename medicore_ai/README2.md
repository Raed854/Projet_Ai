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

Le backend Java/Spring utilisé par les endpoints de mise à jour est
configuré avec `BACKEND_BASE_URL`. Sa valeur par défaut est
`http://localhost:8080`.

```powershell
$env:BACKEND_BASE_URL = "http://localhost:8080"
python api_service.py
```

## Configuration CORS avec le frontend React

En développement, le frontend React utilise le proxy défini dans
`package.json` et appelle l'API avec l'URL relative `/predict`. Le proxy
redirige cette requête vers `http://localhost:5000`, ce qui évite une requête
cross-origin dans le navigateur.

Pour un déploiement séparé du frontend et de l'API, la réponse Flask doit
retourner une origine explicite et valide, par exemple :

```http
Access-Control-Allow-Origin: http://localhost:3000
```

Ne pas utiliser plusieurs origines séparées par des virgules dans cette
valeur. Si les cookies ou les identifiants sont activés, ne pas utiliser
`*` : l'origine du frontend doit être configurée explicitement et
`Access-Control-Allow-Credentials: true` doit être ajouté.

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

## 2. Prédiction et mise à jour du diagnostic

### Requête

```http
POST /api/diagnostics/{diagnosticId}/image
```

Exemple :

```http
POST /api/diagnostics/25/image
```

Cette API reçoit une image, exécute la prédiction, puis transmet
automatiquement le résultat au backend Java/Spring.

### Entrée

Le paramètre de chemin `diagnosticId` est un entier.

L'image doit être envoyée dans le champ `image` :

```bash
curl -X POST http://localhost:5000/api/diagnostics/25/image ^
  -F "image=@model_transfer_resnet/1.jpg"
```

Un corps binaire brut est également accepté :

```bash
curl -X POST http://localhost:5000/api/diagnostics/25/image ^
  -H "Content-Type: image/jpeg" ^
  --data-binary "@model_transfer_resnet/1.jpg"
```

### Appel interne au backend

L'API Python appelle ensuite :

```http
PUT http://localhost:8080/api/diagnostics/25/etat-irm?etatIrm=Mild%20Impairment
```

La valeur `http://localhost:8080` peut être remplacée avec la variable
`BACKEND_BASE_URL`.

### Sortie en cas de succès — HTTP `200`

```json
{
  "diagnosticId": 25,
  "etatIrm": "Mild Impairment",
  "confidence": 87.52,
  "allProbabilities": {
    "No Impairment": 2.11,
    "Very Mild Impairment": 8.37,
    "Mild Impairment": 87.52,
    "Moderate Impairment": 2.0
  },
  "backendUpdate": {
    "url": "http://localhost:8080/api/diagnostics/25/etat-irm",
    "status": 200,
    "response": {}
  }
}
```

Le champ `backendUpdate` indique le résultat de la communication avec le
backend Java :

| Champ | Description |
|---|---|
| `url` | URL appelée par le service Python |
| `status` | Code HTTP retourné par le backend, ou `null` si la connexion échoue |
| `response` | Réponse JSON ou texte du backend |

---

## 3. Mise à jour manuelle de l'état IRM

### Requête

```http
PUT /api/diagnostics/{diagnosticId}/etat-irm?etatIrm=VALUE
```

Exemple :

```bash
curl -X PUT "http://localhost:5000/api/diagnostics/25/etat-irm?etatIrm=Mild%20Impairment"
```

### Paramètres

| Paramètre | Emplacement | Type | Obligatoire | Description |
|---|---|---|---|---|
| `diagnosticId` | URL | `integer` | Oui | Identifiant du diagnostic |
| `etatIrm` | Query string | `string` | Oui | État IRM à enregistrer |

Les valeurs acceptées pour `etatIrm` sont :

```text
No Impairment
Very Mild Impairment
Mild Impairment
Moderate Impairment
```

Cette API transmet la requête au backend Java et renvoie sa réponse.

### Erreur : paramètre absent — HTTP `400`

```json
{
  "error": "Missing query parameter 'etatIrm'"
}
```

### Erreur : valeur invalide — HTTP `400`

```json
{
  "error": "Invalid etatIrm value. Must be one of: ['No Impairment', 'Very Mild Impairment', 'Mild Impairment', 'Moderate Impairment']"
}
```

### Erreur : backend inaccessible — HTTP `502`

```json
{
  "error": "Could not connect to backend at http://localhost:8080"
}
```

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
| `POST` | `/api/diagnostics/{id}/image` | Image IRM et identifiant | Retourne la prédiction et met à jour le backend |
| `PUT` | `/api/diagnostics/{id}/etat-irm` | `etatIrm` dans la query string | Transmet manuellement l'état au backend |
| `GET` | `/health` | Aucune | Vérifie que le service est opérationnel |

## Avertissement médical

Ce modèle est un outil d'aide à la décision et de recherche. Il ne remplace
pas le diagnostic d'un professionnel de santé qualifié.
