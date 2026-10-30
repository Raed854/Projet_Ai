"""Exploite une courbe de titrage stockée dans un fichier Excel.

Format attendu du fichier .xlsx : une feuille avec deux colonnes, nommées
"volume" et "ph" (insensible à la casse, les en-têtes peuvent être sur la
première ligne dans n'importe quel ordre). Chaque ligne = un point de mesure.

Usage :
    python -m ai_model.predire_excel chemin/vers/courbe.xlsx
    python -m ai_model.predire_excel chemin/vers/courbe.xlsx --titrant 0.1 --prise 20
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ai_model.service import analyser_courbe

MODELS_DIR = Path(__file__).parent / "models_store"


def lire_courbe(chemin_excel: str) -> tuple[list[float], list[float]]:
    df = pd.read_excel(chemin_excel)
    colonnes = {c.lower().strip(): c for c in df.columns}
    if "volume" not in colonnes or "ph" not in colonnes:
        raise ValueError(
            f"Le fichier doit contenir des colonnes 'volume' et 'ph' (trouvé : {list(df.columns)})"
        )
    volumes = df[colonnes["volume"]].astype(float).tolist()
    ph = df[colonnes["ph"]].astype(float).tolist()
    return volumes, ph


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fichier", help="Chemin du fichier Excel (.xlsx)")
    parser.add_argument("--titrant", type=float, default=None, help="Concentration du titrant (mol/L)")
    parser.add_argument("--prise", type=float, default=None, help="Volume de la prise d'essai (mL)")
    parser.add_argument("--type", type=str, default=None, help="Type de dosage déclaré (optionnel)")
    args = parser.parse_args()

    volumes, ph = lire_courbe(args.fichier)
    resultat = analyser_courbe(MODELS_DIR, volumes, ph, args.titrant, args.prise, args.type)
    print(json.dumps(resultat, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
