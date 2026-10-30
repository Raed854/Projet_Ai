"""Entraîne le modèle avec les courbes synthétiques + les dosages réels validés
stockés dans la base SQLite de l'application (dosage.db).

Usage :
    python -m ai_model.entrainer_avec_db
    python -m ai_model.entrainer_avec_db --db chemin/vers/dosage.db --n 4000
"""
from __future__ import annotations

import argparse
from pathlib import Path

from ai_model.donnees_reelles import charger_dosages_valides
from ai_model.service import entrainer_et_activer

MODELS_DIR = Path(__file__).parent / "models_store"
DB_PAR_DEFAUT = Path(__file__).parent / "dosage.db"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DB_PAR_DEFAUT), help="Chemin du fichier dosage.db")
    parser.add_argument("--n", type=int, default=4000, help="Nombre de courbes synthétiques")
    args = parser.parse_args()

    reelles = charger_dosages_valides(args.db)
    print(f"{len(reelles)} dosage(s) validé(s) chargé(s) depuis {args.db}")

    info = entrainer_et_activer(MODELS_DIR, args.n, courbes_reelles=reelles)
    print(f"Modèle {info['version']} entraîné sur {info['nb_echantillons']} courbes synthétiques "
          f"+ {len(reelles)} courbe(s) réelle(s).")
    print(f"Sauvegardé dans : {info['chemin']}")

    m = info["metriques"]
    print("\n--- Métriques (jeu de test tenu à l'écart) ---")
    print(f"Volume équivalent — erreur médiane IA : {m['volume_equivalence']['mediane_ia_pct']}% "
          f"vs méthode dérivée : {m['volume_equivalence']['mediane_derivee_pct']}%")
    print(f"IA meilleure que la méthode dérivée dans {m['volume_equivalence']['part_ia_meilleure_pct']}% des cas")
    print(f"Type de dosage — exactitude : {m['type_dosage']['exactitude'] * 100:.1f}%")
    print(f"Anomalies — F1 : {m['anomalies']['f1']}, détection : {m['anomalies']['taux_detection_pct']}%, "
          f"faux positifs : {m['anomalies']['faux_positifs_pct']}%")
    print(f"\nMétriques complètes : {Path(info['chemin']).parent / 'active.json'}")


if __name__ == "__main__":
    main()
