# 🧠 Alzheimer Diagnostic AI — ResNet-18 (Transfer Learning)

Modèle d'intelligence artificielle qui analyse une **image IRM cérébrale** et prédit le **stade de la maladie d'Alzheimer** parmi 4 classes. Le projet expose le modèle via une **API REST Flask** intégrée à un backend Java/Spring.

---

## 📑 Sommaire

1. [À quoi sert ce modèle](#-1-à-quoi-sert-ce-modèle)
2. [Architecture du modèle](#-2-architecture-du-modèle)
3. [Le pipeline étape par étape](#-3-le-pipeline-étape-par-étape)
4. [Structure du projet](#-4-structure-du-projet)
5. [Installation](#-5-installation)
6. [Utilisation](#-6-utilisation)
7. [L'API REST](#-7-lapi-rest)
8. [Pourquoi ce modèle est performant](#-8-pourquoi-ce-modèle-est-performant)

---

## 🎯 1. À quoi sert ce modèle

Le modèle classe une image IRM dans l'une de ces **4 catégories** :

| Index | Classe (`etatIrm`)        | Signification                       |
|-------|---------------------------|-------------------------------------|
| 0     | `No Impairment`           | Aucun signe d'altération            |
| 1     | `Very Mild Impairment`    | Altération très légère              |
| 2     | `Mild Impairment`         | Altération légère                   |
| 3     | `Moderate Impairment`     | Altération modérée                  |

En sortie, le modèle donne **la classe prédite + un score de confiance (%) + la probabilité de chaque classe**.

---

## 🏗️ 2. Architecture du modèle

Le modèle repose sur **ResNet-18** (réseau de neurones convolutif pré-entraîné) adapté par **Transfer Learning** au cas médical.

```
Entrée : image IRM 224×224 en niveaux de gris (1 canal)
   │
   ▼
┌─────────────────────────────────────────────┐
│  ResNet-18 (backbone CNN)                     │
│  • conv1 modifié : 1 canal au lieu de 3       │  ← images IRM = grayscale
│  • 4 blocs résiduels → extraction de features │
│  • sortie : vecteur de 512 features           │
└─────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────┐
│  Tête de classification personnalisée (fc)    │
│  Linear(512 → 256)                            │
│  BatchNorm1d(256)                             │
│  ReLU()                                       │
│  Dropout(0.5)        ← régularisation         │
│  Linear(256 → 4)     ← 4 classes              │
└─────────────────────────────────────────────┘
   │
   ▼
Softmax → probabilités des 4 classes
```

**Modifications clés par rapport au ResNet-18 standard :**

- **`conv1` remplacée** : `Conv2d(1, 64, kernel_size=7, ...)` — le réseau accepte des images **1 canal** (niveaux de gris) car les IRM sont monochromes, au lieu de 3 canaux (RGB).
- **Couche `fc` remplacée** : la dernière couche (1000 classes ImageNet) est remplacée par une tête sur-mesure avec `BatchNorm`, `ReLU` et `Dropout` qui réduit à **4 classes**.

---

## 🔄 3. Le pipeline étape par étape

### Étape 1 — Construire l'architecture (`build_model`)
On recrée la structure exacte du réseau (ResNet-18 + conv1 modifiée + tête personnalisée). Cette structure doit être **identique** à celle utilisée pendant l'entraînement, sinon les poids ne peuvent pas être chargés.

### Étape 2 — Charger les poids (`load_model`)
- Si le modèle est fourni sous forme de **dossier dézippé** (`model_transfer_resnet/`), le code le **re-zippe** en un fichier `.pt` reproductible (dates fixées à 1980 pour un hash déterministe).
- Les poids (`state_dict`) sont chargés via `torch.load(...)` puis injectés dans l'architecture avec `model.load_state_dict(...)`.
- Le modèle est mis en mode **évaluation** (`model.eval()`) — désactive Dropout/BatchNorm en mode training.

### Étape 3 — Prétraitement de l'image (`transform`)
Chaque image entrante passe par une chaîne de transformations :

```python
Resize((224, 224))                       # redimensionne à la taille attendue
Grayscale(num_output_channels=1)         # force 1 canal (niveaux de gris)
ToTensor()                               # convertit en tenseur PyTorch [0,1]
Normalize(mean=[0.485], std=[0.229])     # normalise les valeurs des pixels
```

### Étape 4 — Inférence (`predict` / `predict_image`)
- L'image transformée est passée au modèle (`outputs = model(tensor)`).
- `torch.softmax(...)` convertit les scores bruts (logits) en **probabilités** sommant à 100 %.
- `argmax()` sélectionne la classe la plus probable → **classe prédite** + **confiance**.
- Toutes les probabilités par classe sont aussi renvoyées.

### Étape 5 — Servir / Intégrer (`api_service.py`)
Le résultat est :
- soit renvoyé en **JSON** au client (endpoint `/predict`),
- soit automatiquement **transmis au backend Java/Spring** pour mettre à jour la base de données du diagnostic (endpoint `/api/diagnostics/<id>/image`).

---

## 📁 4. Structure du projet

```
model_transfer_resnet_2/
├── api_service.py             # API REST Flask (production)
├── test_model.py              # Script CLI pour tester le modèle sur une image
├── requirements.txt           # Dépendances Python
├── model_transfer_resnet.pt   # Modèle entraîné (poids, ~45 Mo)
├── model_transfer_resnet/     # Version dézippée du modèle
│   ├── data.pkl               #   métadonnées / structure du state_dict
│   ├── byteorder, version ... #   fichiers internes du format PyTorch
│   └── 1.jpg, 7.jpg, 9.jpg    #   images IRM d'exemple pour tester
└── README.md                  # Ce fichier
```

---

## ⚙️ 5. Installation

```bash
# 1. (recommandé) créer un environnement virtuel
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# 2. installer les dépendances
pip install -r requirements.txt
```

**Dépendances** : `flask`, `torch`, `torchvision`, `Pillow`, `requests`.

---

## 🚀 6. Utilisation

### A) Tester en ligne de commande

```bash
# Affiche l'architecture du modèle (sans image)
python test_model.py

# Prédit la classe d'une image IRM
python test_model.py model_transfer_resnet/1.jpg
```

Exemple de sortie :

```
Image: 1.jpg
Prédiction: classe 0 (No Impairment) - Confiance: 96.4%

Probabilités par classe:
  No Impairment   :  96.4% ███████████████████
  Very Mild       :   2.1% 
  Mild Impairment :   1.0% 
  Moderate        :   0.5% 
```

### B) Lancer l'API REST

```bash
# (optionnel) définir l'URL du backend Java
set BACKEND_BASE_URL=http://localhost:8080    # Windows
set PORT=5000

python api_service.py
```

L'API démarre sur `http://localhost:5000`.

---

## 🌐 7. L'API REST

| Méthode | Endpoint                                  | Rôle                                                                 |
|---------|-------------------------------------------|----------------------------------------------------------------------|
| `POST`  | `/predict`                                | Prédit la classe d'une image. Renvoie le JSON, sans toucher la DB.   |
| `POST`  | `/api/diagnostics/<id>/image`             | Prédit **et** met à jour le diagnostic côté backend Java.            |
| `PUT`   | `/api/diagnostics/<id>/etat-irm?etatIrm=` | Proxy : transmet la valeur au backend.                              |
| `GET`   | `/health`                                 | Vérifie que le service tourne (statut, device, classes).            |

### Exemple — `POST /predict`

```bash
curl -X POST http://localhost:5000/predict \
     -F "image=@model_transfer_resnet/1.jpg"
```

Réponse :

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

L'image peut être envoyée soit comme **fichier** (champ `image`), soit comme **corps binaire brut**.

---

## ⭐ 8. Pourquoi ce modèle est performant

- **Transfer Learning** : il part d'un ResNet-18, donc il bénéficie de filtres visuels déjà efficaces, et n'a besoin que d'un petit jeu de données médicales pour être spécialisé → entraînement rapide et meilleure précision.
- **Connexions résiduelles (ResNet)** : permettent d'entraîner un réseau profond sans problème de gradient qui s'évanouit → extraction de features riches.
- **Adapté aux IRM** : `conv1` reconfiguré pour 1 canal (grayscale), évitant de gaspiller des paramètres sur la couleur inutile.
- **Tête régularisée** : `BatchNorm` (stabilise l'apprentissage) + `Dropout(0.5)` (réduit le surapprentissage) → meilleure généralisation sur de nouvelles IRM.
- **Sortie probabiliste** : `softmax` fournit un **score de confiance** exploitable cliniquement, pas juste une étiquette brute.
- **Prêt pour la production** : `model.eval()` + `torch.no_grad()` pour une inférence rapide et déterministe, et une API REST directement branchable sur le backend Java/Spring.

---

> ⚠️ **Avertissement médical** : Ce modèle est un outil d'aide à la décision et de recherche. Il ne remplace pas le diagnostic d'un professionnel de santé qualifié.
