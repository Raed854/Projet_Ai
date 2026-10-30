"""Exemple d'utilisation autonome du module IA (sans frontend ni backend web)."""
from pathlib import Path

import numpy as np

from ai_model.generateur import generer_courbe
from ai_model.service import analyser_courbe, entrainer_et_activer

MODELS_DIR = Path(__file__).parent / "models_store"

if __name__ == "__main__":
    print("Entraînement du modèle...")
    info = entrainer_et_activer(MODELS_DIR, n_echantillons=1500)
    print(f"Modèle {info['version']} entraîné sur {info['nb_echantillons']} courbes.")

    print("\nGénération d'une courbe de test...")
    rng = np.random.default_rng(0)
    courbe = generer_courbe(rng)

    resultat = analyser_courbe(MODELS_DIR, courbe.volumes, courbe.ph,
                               courbe.c_titrant, courbe.v_prise, courbe.type_dosage)

    print(f"Veq vrai        : {courbe.veq:.3f} mL")
    print(f"Veq IA          : {resultat['veq_ia']:.3f} mL (± {resultat['veq_ia_incertitude']:.3f})")
    print(f"Veq dérivée     : {resultat['veq_derivee']:.3f} mL")
    print(f"Type prédit     : {resultat['type_predit']} ({resultat['type_confiance']:.1%})")
    print(f"Score qualité   : {resultat['score_qualite']:.3f}")
    print(f"Alertes         : {resultat['alertes']}")
