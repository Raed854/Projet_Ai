# Explication du modèle — Alzheimer Diagnostic AI (ResNet-18)

## 1. Présentation du modèle

Ce projet contient un modèle d'intelligence artificielle capable d'analyser une image IRM du cerveau et de prédire le stade de la maladie d'Alzheimer. Le modèle reçoit une image en entrée et renvoie l'une des quatre classes suivantes : `No Impairment` (aucune altération), `Very Mild Impairment` (altération très légère), `Mild Impairment` (altération légère) et `Moderate Impairment` (altération modérée). En plus de la classe prédite, il fournit un score de confiance en pourcentage ainsi que la probabilité associée à chacune des quatre classes.

Le modèle est servi par une petite API Flask ([api_service.py](api_service.py)) qui joue le rôle d'intermédiaire entre le frontend (React), le modèle PyTorch et le backend FastAPI `backend_ai`, qui est responsable de la base de données et de la table `alzheimer`.

## 2. Quel type de modèle est-ce ? (ML, Deep Learning… ?)

Ce n'est pas un modèle de Machine Learning « classique » comme une régression logistique, un arbre de décision ou un SVM, qui travaillent sur des colonnes de données tabulaires. Il s'agit d'un modèle de **Deep Learning**, plus précisément un **réseau de neurones convolutif (CNN)**, qui est la famille de modèles adaptée aux images. Le Deep Learning reste une sous-branche du Machine Learning : on parle donc bien d'apprentissage automatique, mais avec un réseau profond qui apprend lui-même à extraire les caractéristiques visuelles de l'image, sans qu'on ait à les définir à la main.

Il s'agit d'un problème d'**apprentissage supervisé** de type **classification d'images multi-classes** (4 classes) : le modèle a appris à partir d'images IRM déjà étiquetées par leur stade de la maladie.

Enfin, le modèle utilise la technique du **Transfer Learning** (apprentissage par transfert). Au lieu de créer un réseau à partir de zéro, on part de l'architecture **ResNet-18**, un réseau célèbre conçu à l'origine pour reconnaître 1000 catégories d'objets (base ImageNet), et on l'adapte à notre problème médical. Cela permet d'obtenir de bonnes performances avec beaucoup moins de données et de temps d'entraînement.

## 3. Architecture du modèle

La base du modèle est ResNet-18, composé de 18 couches organisées en blocs résiduels. Les « connexions résiduelles » (raccourcis qui sautent certaines couches) permettent d'entraîner un réseau profond sans que l'apprentissage ne se bloque. Cette partie du réseau transforme l'image en un vecteur de 512 caractéristiques qui résume son contenu.

Deux modifications ont été apportées au ResNet-18 d'origine, visibles dans la fonction `build_model` :

- **La première couche (`conv1`) a été remplacée** pour accepter des images à **1 seul canal** (niveaux de gris) au lieu de 3 canaux couleur (RGB), car les IRM sont des images monochromes.
- **La dernière couche (`fc`) a été remplacée** par une tête de classification personnalisée : `Linear(512 → 256)`, puis `BatchNorm1d(256)` pour stabiliser l'apprentissage, `ReLU()` comme fonction d'activation, `Dropout(0.5)` pour limiter le surapprentissage, et enfin `Linear(256 → 4)` qui produit un score pour chacune des 4 classes.

À la sortie, une fonction **softmax** transforme ces 4 scores bruts en probabilités dont la somme vaut 100 %. La classe ayant la plus forte probabilité est la prédiction finale, et sa probabilité est la confiance.

## 4. Les étapes de création du modèle

La création d'un tel modèle suit plusieurs étapes. Les premières (collecte des données et entraînement) ont été réalisées en amont : le script d'entraînement ne fait pas partie de ce dossier, seuls les poids entraînés sont fournis (`model_transfer_resnet.pt` et sa version dézippée `model_transfer_resnet/`). Les étapes ci-dessous décrivent la démarche générale correspondant à l'architecture utilisée.

**Étape 1 — Collecte et préparation des données.** On rassemble un jeu d'images IRM cérébrales classées dans les 4 catégories. Les images sont ensuite séparées en un ensemble d'entraînement, un ensemble de validation et un ensemble de test, afin de pouvoir mesurer honnêtement les performances du modèle sur des images qu'il n'a jamais vues.

**Étape 2 — Prétraitement des images.** Toutes les images doivent avoir le même format pour être données au réseau. Elles sont redimensionnées en 224 × 224 pixels, converties en niveaux de gris, transformées en tenseurs PyTorch, puis normalisées (moyenne 0.485, écart-type 0.229). Ce même prétraitement est reproduit à l'identique au moment de la prédiction, dans la variable `transform`.

**Étape 3 — Construction de l'architecture.** On charge ResNet-18, on remplace la couche d'entrée pour accepter 1 canal, et on remplace la couche finale par la tête personnalisée à 4 sorties, comme décrit dans la partie précédente.

**Étape 4 — Entraînement.** Le modèle voit les images d'entraînement par lots, compare ses prédictions aux vraies étiquettes à l'aide d'une fonction de perte (généralement l'entropie croisée pour la classification), puis ajuste ses poids par rétropropagation du gradient grâce à un optimiseur. Cette opération est répétée sur plusieurs époques, en surveillant les performances sur l'ensemble de validation pour éviter le surapprentissage.

**Étape 5 — Évaluation.** Une fois entraîné, le modèle est évalué sur l'ensemble de test à l'aide de métriques comme la précision (accuracy), la matrice de confusion ou le F1-score, pour vérifier qu'il distingue correctement les quatre stades.

**Étape 6 — Sauvegarde.** Les poids appris (le `state_dict`) sont enregistrés dans un fichier `.pt`. C'est ce fichier qui est livré dans ce projet. Pour l'utiliser, il faut reconstruire exactement la même architecture (`build_model`) puis y charger les poids (`load_model`) ; si l'architecture diffère, même légèrement, le chargement échoue.

**Étape 7 — Déploiement.** Le modèle est chargé une seule fois au démarrage de l'API, mis en mode évaluation avec `model.eval()` (ce qui désactive le Dropout et fige la BatchNorm), puis utilisé pour chaque requête avec `torch.no_grad()` afin d'accélérer l'inférence. Le script [test_model.py](test_model.py) permet de tester le modèle en ligne de commande, par exemple avec `python test_model.py model_transfer_resnet/1.jpg`.

## 5. Utilisation des API et relation avec `backend_ai`

### Rôle de chaque service

L'application est découpée en trois parties. Le **frontend React** (par défaut `http://localhost:3000`) envoie les images choisies par l'utilisateur. Le **service IA Flask** (ce projet, par défaut `http://localhost:5000`) reçoit l'image, exécute le modèle et renvoie le résultat. Le **backend FastAPI `backend_ai`** (par défaut `http://localhost:8000`) gère la base de données et la table `alzheimer`. Le service IA ne touche jamais directement à la base de données : il passe toujours par les routes HTTP de `backend_ai`.

```
Frontend React ──image──▶ Service IA Flask (:5000) ──JSON──▶ backend_ai FastAPI (:8000) ──▶ table alzheimer
                ◀─résultat─                        ◀─ligne créée─
```

Deux variables d'environnement configurent cette relation : `BACKEND_BASE_URL` indique l'adresse de `backend_ai` (par défaut `http://localhost:8000`), et `ALLOWED_ORIGIN` indique l'adresse du frontend autorisé à appeler le service depuis le navigateur grâce aux en-têtes CORS (par défaut `http://localhost:3000`). Le port du service IA peut être changé avec `PORT`.

```powershell
pip install -r requirements.txt
$env:BACKEND_BASE_URL = "http://localhost:8000"
$env:ALLOWED_ORIGIN = "http://localhost:3000"
python api_service.py
```

### `POST /predict` — prédiction seule

Cette route exécute uniquement le modèle et renvoie le résultat, sans rien enregistrer et sans contacter `backend_ai`. L'image peut être envoyée dans un champ de formulaire nommé `image` ou directement comme corps binaire.

```bash
curl -X POST http://localhost:5000/predict -F "image=@model_transfer_resnet/1.jpg"
```

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

### `POST /api/users/{userId}/image` — prédiction et enregistrement

C'est la route principale de la relation avec `backend_ai`. Le service IA reçoit l'image d'un utilisateur, exécute le modèle, puis appelle lui-même `backend_ai` avec `POST {BACKEND_BASE_URL}/alzheimers` et le corps `{"type": <classe prédite>, "user_id": <userId>, "confidence": <confiance>}`. Si `backend_ai` répond `201 Created`, le service IA renvoie au frontend la prédiction complète accompagnée de la ligne créée dans la table `alzheimer` (champ `alzheimer`).

```bash
curl -X POST http://localhost:5000/api/users/3/image -F "image=@model_transfer_resnet/1.jpg"
```

```json
{
  "userId": 3,
  "etatIrm": "Mild Impairment",
  "confidence": 87.52,
  "allProbabilities": { "No Impairment": 2.11, "Very Mild Impairment": 8.37, "Mild Impairment": 87.52, "Moderate Impairment": 2.0 },
  "alzheimer": { "id": 12, "type": "Mild Impairment", "confidence": 87.52, "date_creation": "2026-10-26T21:40:00", "user_id": 3 }
}
```

Si `backend_ai` refuse l'enregistrement (par exemple un utilisateur inexistant renvoie `404`), le service IA renvoie une erreur contenant malgré tout la prédiction, le code HTTP du backend et sa réponse. Si le backend est injoignable, la réponse est `502` ; s'il met plus de 10 secondes à répondre, la réponse est `504`.

### `PATCH /api/alzheimers/{id}?etatIrm=VALEUR` — correction manuelle

Cette route permet, par exemple à un médecin, de corriger un résultat déjà enregistré. Le service IA vérifie d'abord que la valeur fait bien partie des 4 classes (sinon `400`), puis la transmet à `backend_ai` avec `PATCH {BACKEND_BASE_URL}/alzheimers/{id}` et le corps `{"type": <valeur>}`. La réponse de `backend_ai` est renvoyée telle quelle au client.

```bash
curl -X PATCH "http://localhost:5000/api/alzheimers/12?etatIrm=Mild%20Impairment"
```

### `GET /health` — état du service

Cette route permet de vérifier que le service IA est démarré et que le modèle est chargé. Elle renvoie le statut, le périphérique utilisé (`cpu` ou `cuda`) et la liste des classes.

### Ce que `backend_ai` doit fournir

Pour que l'intégration fonctionne, le backend FastAPI doit exposer deux routes : `POST /alzheimers`, qui accepte `{type, user_id, confidence}` et répond `201` avec la ligne créée, et `PATCH /alzheimers/{id}`, qui accepte `{type}` et met à jour la ligne correspondante.

## 6. Avertissement

Ce modèle est un outil d'aide à la décision et de recherche. Il ne remplace en aucun cas le diagnostic d'un professionnel de santé qualifié.
