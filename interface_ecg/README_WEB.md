# Application Web ECG - Guide d'utilisation

## Description
Application web simple pour tester votre modèle de classification de battements cardiaques (ECG) avec une interface moderne et intuitive.

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Lancement de l'application

### Option 1 : Application Web (Flask)
```bash
python web_app.py
```
Puis ouvrir votre navigateur à : http://localhost:5000

### Option 2 : Application Streamlit (existante)
```bash
streamlit run app.py
```

## Utilisation de l'application web

1. **Saisir un signal ECG** :
   - Coller 187 valeurs séparées par des virgules, espaces ou retours à la ligne
   - Ou cliquer sur "Charger un exemple" pour tester rapidement

2. **Lancer la prédiction** :
   - Cliquer sur "Lancer la prédiction"
   - Les résultats s'afficheront automatiquement

3. **Interpréter les résultats** :
   - Classe prédite : le type de battement détecté
   - Confiance : niveau de certitude du modèle (en %)
   - Graphique du signal : visualisation du signal ECG analysé
   - Probabilités : distribution des probabilités pour chaque classe

## Classes ECG

- **0 - N** : Battement normal
- **1 - S** : Battement supraventriculaire
- **2 - V** : Contraction ventriculaire prématurée
- **3 - F** : Fusion normale et ventriculaire
- **4 - Q** : Battement non classifiable

## Structure des fichiers

```
.
├── web_app.py              # Backend Flask
├── app.py                  # Application Streamlit (existante)
├── templates/
│   └── index.html         # Page HTML principale
├── static/
│   ├── style.css          # Styles CSS
│   └── script.js          # Logique JavaScript
├── ecg_cnn_final.keras    # Modèle entraîné
└── requirements.txt       # Dépendances Python
```

## Notes importantes

⚠️ **Cette application est pédagogique uniquement**. Les résultats ne constituent pas un diagnostic médical.
