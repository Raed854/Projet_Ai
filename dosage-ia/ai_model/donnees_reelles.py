"""Charge les dosages validés par un responsable depuis la base SQLite de
l'application, pour enrichir l'entraînement avec de vraies mesures en
complément des courbes synthétiques.

Seuls les dosages au statut 'valide' sont utilisés : un dosage juste "en
analyse" n'a pas de volume équivalent garanti fiable, alors qu'un dosage
validé par un responsable a été relu et confirmé.
"""
from __future__ import annotations

import sqlite3

import numpy as np

from .generateur import CourbeSimulee


def charger_dosages_valides(chemin_db: str) -> list[CourbeSimulee]:
    conn = sqlite3.connect(chemin_db)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, type_dosage, titrant_concentration, volume_prise, "
            "veq_retenu, concentration, pka_estime FROM dosages WHERE statut = 'valide'"
        )
        lignes = cur.fetchall()

        courbes: list[CourbeSimulee] = []
        for dosage_id, type_dosage, c_titrant, v_prise, veq, concentration, pka in lignes:
            if veq is None:
                continue
            cur.execute(
                "SELECT volume, ph FROM points_mesure WHERE dosage_id = ? ORDER BY volume",
                (dosage_id,),
            )
            points = cur.fetchall()
            if len(points) < 5:
                continue
            courbes.append(CourbeSimulee(
                type_dosage=type_dosage,
                volumes=np.array([p[0] for p in points], dtype=float),
                ph=np.array([p[1] for p in points], dtype=float),
                veq=float(veq),
                c_analyte=float(concentration) if concentration is not None else 0.0,
                v_prise=float(v_prise) if v_prise is not None else 0.0,
                c_titrant=float(c_titrant) if c_titrant is not None else 0.0,
                pka=float(pka) if pka is not None else None,
                bruit=0.0,
                anomalie=None,
            ))
        return courbes
    finally:
        conn.close()
