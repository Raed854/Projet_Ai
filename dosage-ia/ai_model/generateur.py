"""Générateur de courbes de titrage synthétiques réalistes.

Pourquoi des données synthétiques ? Un laboratoire n'a généralement pas des milliers
de courbes annotées avec le "vrai" volume équivalent. La chimie, elle, est connue :
on simule donc des courbes exactes, puis on leur ajoute les défauts d'une mesure réelle
(bruit d'électrode, dérive d'étalonnage, erreur de lecture de burette, pas irrégulier,
courbes peu denses). Le modèle apprend à retrouver le volume vrai malgré ces défauts.
Les courbes réelles validées par un responsable peuvent ensuite enrichir l'entraînement.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .chemistry import TYPES, simuler_ph, volume_equivalence_theorique


@dataclass
class CourbeSimulee:
    type_dosage: str
    volumes: np.ndarray
    ph: np.ndarray
    veq: float
    c_analyte: float
    v_prise: float
    c_titrant: float
    pka: float | None
    bruit: float
    anomalie: str | None = None


def _log_uniforme(rng, a, b):
    return float(np.exp(rng.uniform(np.log(a), np.log(b))))


def generer_courbe(rng: np.random.Generator, type_dosage: str | None = None,
                   bruit: float | None = None, nb_points: int | None = None) -> CourbeSimulee:
    type_dosage = type_dosage or str(rng.choice(TYPES))
    # Tirage des conditions opératoires avec un volume équivalent raisonnable (3–30 mL)
    while True:
        c_analyte = _log_uniforme(rng, 0.005, 0.2)
        v_prise = float(rng.choice([5.0, 10.0, 20.0, 25.0]))
        c_titrant = _log_uniforme(rng, 0.01, 0.2)
        veq = volume_equivalence_theorique(c_analyte, v_prise, c_titrant)
        if 3.0 <= veq <= 30.0:
            break

    pka = None
    if type_dosage == "acide_faible":
        pka = float(rng.uniform(3.0, 7.5))
    elif type_dosage == "base_faible":
        pka = float(rng.uniform(6.5, 10.5))  # pKa du couple BH+/B (ex. NH4+/NH3 : 9,25)

    v_max = veq * float(rng.uniform(1.35, 2.2))
    n = nb_points or int(rng.integers(12, 61))
    # Pratique de laboratoire : incréments resserrés autour du saut (une fois sur deux)
    if rng.random() < 0.5:
        n_large = max(n // 2, 4)
        larges = np.linspace(0, v_max, n_large)
        serres = veq + rng.uniform(-0.12, 0.12) * veq + np.linspace(-0.15, 0.15, n - n_large) * veq
        volumes = np.sort(np.clip(np.concatenate([larges, serres]), 0, v_max))
    else:
        volumes = np.sort(np.concatenate([[0.0], rng.uniform(0, v_max, n - 2), [v_max]]))

    ph = simuler_ph(type_dosage, volumes, c_analyte, v_prise, c_titrant, pka)

    sigma = float(rng.uniform(0.003, 0.06)) if bruit is None else bruit
    decalage = float(rng.normal(0, 0.05))                 # étalonnage de l'électrode
    lecture = rng.normal(0, 0.02, size=volumes.shape)     # lecture de burette (mL)
    volumes_mesures = np.clip(volumes + lecture, 0, None)
    volumes_mesures[0] = 0.0
    ph_mesure = np.clip(ph + decalage + rng.normal(0, sigma, size=ph.shape), 0, 14)

    return CourbeSimulee(type_dosage, volumes_mesures.round(3), ph_mesure.round(3), veq,
                         c_analyte, v_prise, c_titrant, pka, sigma)


def injecter_anomalie(rng: np.random.Generator, c: CourbeSimulee) -> CourbeSimulee:
    """Dégrade une courbe pour simuler une mesure non conforme."""
    v, p = c.volumes.copy(), c.ph.copy()
    genre = str(rng.choice(["pic", "arret_premature", "electrode_defaillante", "inversion"]))
    if genre == "pic":
        idx = rng.choice(len(p), size=max(1, len(p) // 10), replace=False)
        p[idx] = np.clip(p[idx] + rng.choice([-1, 1], size=len(idx)) * rng.uniform(1.5, 3.5, size=len(idx)), 0, 14)
    elif genre == "arret_premature":
        garde = v <= c.veq * rng.uniform(0.6, 0.95)
        if garde.sum() >= 6:
            v, p = v[garde], p[garde]
        else:
            p = p + rng.normal(0, 0.6, size=p.shape)
    elif genre == "electrode_defaillante":
        p = p + rng.normal(0, rng.uniform(0.3, 0.8), size=p.shape)
    else:
        i = len(p) // 2
        p[i:] = p[i:][::-1]
    c.volumes, c.ph, c.anomalie = v, np.clip(p, 0, 14), genre
    return c
