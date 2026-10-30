# Projet NFS / CBC - classification du type d'anémie

Dataset Kaggle : Anemia Types Classification (ehababoelnaga).

## Lancer en local
    python -m venv .venv
    .venv\Scripts\activate        (Windows)   |   source .venv/bin/activate   (Linux/Mac)
    pip install -r requirements.txt
    python train.py                 (ré-entraîne le modèle)
    python predict.py               (test en ligne de commande)
    streamlit run app.py            (interface web)
    python api_service.py           (API Flask sur http://localhost:5003)

Pour l'interface cliente qui utilise l'API, démarrez `api_service.py` dans un
terminal séparé, puis lancez l'interface. Vérification :

    Invoke-WebRequest http://localhost:5003/health

Modèle exporté depuis Kaggle avec scikit-learn 1.6.1.
Outil d'étude uniquement, ne remplace pas un diagnostic médical.
