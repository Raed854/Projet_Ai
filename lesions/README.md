# Détection de lésions cutanées

Application de classification d'images dermoscopiques basée sur PyTorch et
EfficientNet-B0.

> **Avertissement médical :** ce projet est expérimental. Il ne remplace pas
> l'avis d'un dermatologue et ne doit pas être utilisé pour établir seul un
> diagnostic médical.

## Fonctionnalités

- Classification d'une image de lésion cutanée.
- Interface web avec Gradio.
- Prédiction en ligne de commande.
- Affichage des probabilités pour les 7 classes reconnues.
- Visualisation Grad-CAM de la zone observée par le modèle.
- Test-time augmentation avec quatre vues de l'image dans l'interface web.
- Jauge de vigilance basée sur les classes potentiellement suspectes.

## Classes reconnues

| Code | Signification |
|---|---|
| `akiec` | Kératose actinique |
| `bcc` | Carcinome basocellulaire |
| `bkl` | Kératose bénigne |
| `df` | Dermatofibrome |
| `mel` | Mélanome |
| `nv` | Naevus |
| `vasc` | Lésion vasculaire |

## Structure du projet

```text
lesions/
├── app.py
├── predict.py
├── best.pth
├── examples/
│   ├── ISIC_0025384.jpg
│   ├── ISIC_0025843.jpg
│   ├── ISIC_0028069.jpg
│   ├── ISIC_0028579.jpg
│   ├── ISIC_0030417.jpg
│   └── ISIC_0032212.jpg
└── venv/
```

## Prérequis

- Windows 10 ou Windows 11
- Python 3.10 ou plus récent
- Le fichier `best.pth` doit rester dans le même dossier que les scripts

Les bibliothèques utilisées sont :

- PyTorch
- timm
- OpenCV
- NumPy
- Gradio

## Installation

Ouvrir PowerShell dans le dossier du projet :

```powershell
cd "C:\Users\DELL\Desktop\Ai\lesions"
```

### Créer et utiliser l'environnement virtuel recommandé

L'ancien dossier `venv` peut pointer vers une installation Python qui n'est
plus présente sur la machine. Utiliser plutôt `.venv` :

```powershell
py -3.13 -m venv --system-site-packages .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install timm opencv-python gradio
```

Si PowerShell bloque l'activation :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Le paramètre `--system-site-packages` permet de réutiliser PyTorch déjà installé
sur cette machine. Si PyTorch n'est pas installé, ajouter `torch` et
`torchvision` à la commande d'installation :

```powershell
python -m pip install torch torchvision timm opencv-python numpy gradio
```

## Lancer l'interface web

Depuis le dossier racine du projet :

```powershell
python app.py
```

Une adresse locale sera affichée dans le terminal, généralement :

```text
http://127.0.0.1:7860
```

Ouvrir cette adresse dans un navigateur.

### Utiliser l'interface

1. Importer une image de lésion.
2. Cliquer sur **Analyser**.
3. Lire la classe prédite et les probabilités.
4. Consulter la carte Grad-CAM.
5. Examiner le niveau de vigilance affiché.

Des images d'exemple sont disponibles dans le dossier `examples/`.

## Utiliser la prédiction en ligne de commande

Activer l'environnement virtuel, puis exécuter :

```powershell
python predict.py "examples\ISIC_0025384.jpg"
```

Pour analyser une autre image :

```powershell
python predict.py "C:\chemin\vers\mon-image.jpg"
```

Les formats JPG et PNG sont recommandés.

## Fonctionnement technique

Les images sont :

1. Converties en RGB.
2. Redimensionnées en `224 × 224` pixels.
3. Normalisées avec les valeurs ImageNet.
4. Passées dans un modèle EfficientNet-B0.
5. Converties en probabilités avec Softmax.

Dans `app.py`, quatre vues sont utilisées :

- image originale ;
- retournement horizontal ;
- retournement vertical ;
- retournement horizontal et vertical.

Les résultats sont ensuite moyennés.

Le score de la classe `mel` est volontairement amplifié par un facteur `×3`
avant la normalisation finale. Les probabilités affichées ne sont donc pas
calibrées comme des probabilités médicales.

## Paramètres principaux

Les paramètres sont définis au début de `app.py` et `predict.py` :

```python
MODEL_NAME = "efficientnet_b0"
WEIGHTS = "best.pth"
IMG = 224
MEL_FACTOR = 3.0
```

Dans `app.py` :

```python
TTA = True
LOW, HIGH = 0.10, 0.30
```

- `TTA` active ou désactive les quatre vues.
- `LOW` définit le seuil de vigilance modérée.
- `HIGH` définit le seuil de vigilance élevée.
- Le score de vigilance additionne les probabilités de `mel`, `bcc` et
  `akiec`.

## Performances indiquées par l'application

| Métrique | Résultat |
|---|---:|
| Accuracy | 0.83 |
| F1 moyen sur 7 classes | 0.71 |
| Recall mélanome | 0.64 |
| Recall mélanome avec facteur ×3 | 0.77 |
| Précision mélanome | 0.56 |
| Précision mélanome avec facteur ×3 | 0.49 |

Ces chiffres sont indicatifs. Le projet précise que le même jeu de validation
a servi à choisir le meilleur epoch, ce qui peut rendre les performances
légèrement optimistes.

## Avertissement médical

Ce modèle peut produire des erreurs, notamment :

- faux positifs ;
- faux négatifs ;
- mauvaise interprétation d'une image de mauvaise qualité ;
- confusion entre des lésions visuellement similaires.

Une lésion nouvelle, qui change, saigne, démange ou présente une évolution
inhabituelle doit être examinée par un professionnel de santé, quel que soit le
résultat du modèle.

## Limites actuelles

- Aucun script d'entraînement n'est fourni.
- Aucun fichier `requirements.txt` n'est présent.
- Aucun test automatisé n'est présent.
- Le modèle dépend exactement de l'architecture EfficientNet-B0 et de ses
  7 classes.
- Le fichier `best.pth` est indispensable.
- Les chemins des exemples sont relatifs : il faut lancer `app.py` depuis le
  dossier racine du projet.
