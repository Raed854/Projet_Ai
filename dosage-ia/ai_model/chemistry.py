"""Chimie des dosages acido-basiques : simulation théorique et méthodes classiques.

Simulation : résolution exacte de l'équation d'électroneutralité (pas d'approximation
de Henderson), valable sur toute la courbe, y compris près de l'équivalence.

Méthodes classiques d'exploitation :
  * dérivée première (maximum de |dpH/dV|), affinée par interpolation parabolique ;
  * lissage Savitzky-Golay optionnel quand la courbe est dense ;
  * estimation du pKa à la demi-équivalence (couples faibles).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq
from scipy.signal import savgol_filter

KW = 1e-14
KA_FORT = 1e3  # un acide "fort" est modélisé par un Ka très grand

TYPES = ("acide_fort", "acide_faible", "base_forte", "base_faible")


def _ph_monoprotique(c_analyte: float, c_titrant_ajoute: float, ka: float) -> float:
    """pH d'un mélange acide HA (conc. totale c_analyte) + base forte (c_titrant_ajoute).

    Électroneutralité : h + Na = Kw/h + C·Ka/(Ka+h)
    """

    def f(log_h: float) -> float:
        h = 10.0 ** log_h
        return h + c_titrant_ajoute - KW / h - c_analyte * ka / (ka + h)

    log_h = brentq(f, -14.5, 1.0, xtol=1e-10)
    return -log_h


def simuler_ph(
    type_dosage: str,
    volumes_ml: np.ndarray,
    c_analyte: float,
    v_prise_ml: float,
    c_titrant: float,
    pka: float | None = None,
) -> np.ndarray:
    """pH théorique pour chaque volume de titrant versé.

    Les dosages d'une base par un acide sont traités par symétrie (on calcule le pOH).
    """
    if type_dosage not in TYPES:
        raise ValueError(f"type_dosage inconnu : {type_dosage}")
    faible = type_dosage.endswith("faible")
    if faible and pka is None:
        raise ValueError("pKa requis pour un couple faible")
    # Pour une base faible B, on travaille sur le couple conjugué en "pOH" : pKb = 14 - pKa
    if type_dosage == "acide_faible":
        k = 10.0 ** (-pka)
    elif type_dosage == "base_faible":
        k = 10.0 ** (-(14.0 - pka))
    else:
        k = KA_FORT

    ph = np.empty_like(np.asarray(volumes_ml, dtype=float))
    for i, vb in enumerate(volumes_ml):
        v_tot = v_prise_ml + vb
        ca = c_analyte * v_prise_ml / v_tot
        cb = c_titrant * vb / v_tot
        p = _ph_monoprotique(ca, cb, k)
        ph[i] = p if type_dosage.startswith("acide") else 14.0 - p
    return ph


def volume_equivalence_theorique(c_analyte: float, v_prise_ml: float, c_titrant: float) -> float:
    return c_analyte * v_prise_ml / c_titrant


# ---------------------------------------------------------------------------
# Méthodes classiques
# ---------------------------------------------------------------------------
@dataclass
class ResultatClassique:
    veq: float
    pente_max: float
    derivee_v: list[float]
    derivee: list[float]
    pka: float | None


def _nettoyer(volumes, ph):
    v = np.asarray(volumes, dtype=float)
    p = np.asarray(ph, dtype=float)
    ordre = np.argsort(v)
    v, p = v[ordre], p[ordre]
    # Fusion des volumes dupliqués (moyenne des pH)
    v_u, inv = np.unique(v, return_inverse=True)
    p_u = np.bincount(inv, weights=p) / np.bincount(inv)
    return v_u, p_u


def _regrouper_points_proches(v: np.ndarray, p: np.ndarray, pas_min: float):
    """Fusionne les points séparés de moins de `pas_min` mL.

    Deux lectures très rapprochées divisent le bruit de pH par un dV minuscule et
    créent un faux pic de dérivée : c'est la première cause d'erreur de la méthode.
    """
    groupes_v, groupes_p = [v[0]], [[p[0]]]
    debut = v[0]
    for vi, pi in zip(v[1:], p[1:]):
        if vi - debut < pas_min:
            groupes_p[-1].append(pi)
        else:
            groupes_v.append(vi)
            groupes_p.append([pi])
            debut = vi
    return np.array(groupes_v), np.array([np.mean(g) for g in groupes_p])


def methode_derivee(volumes, ph, lissage: bool = True) -> ResultatClassique:
    """Volume équivalent par maximum de la dérivée première |dpH/dV|."""
    v, p = _nettoyer(volumes, ph)
    if len(v) < 5:
        raise ValueError("Au moins 5 points distincts sont nécessaires")

    if lissage:
        v, p = _regrouper_points_proches(v, p, pas_min=0.004 * v[-1])
    p_travail = p
    pas = np.diff(v)
    # Savitzky-Golay suppose un pas régulier : on ne l'applique que dans ce cas
    if lissage and len(v) >= 15 and pas.std() / pas.mean() < 0.15:
        p_travail = savgol_filter(p, 5, 2)

    dv = np.diff(v)
    d = np.diff(p_travail) / dv
    v_mid = (v[:-1] + v[1:]) / 2
    signe = 1.0 if p[-1] >= p[0] else -1.0  # saut montant (acide) ou descendant (base)
    d_abs = d * signe

    i = int(np.argmax(d_abs))
    veq = float(v_mid[i])
    # Interpolation parabolique sur les trois points autour du maximum
    if 0 < i < len(d_abs) - 1:
        x0, x1, x2 = v_mid[i - 1 : i + 2]
        y0, y1, y2 = d_abs[i - 1 : i + 2]
        denom = (x0 - x1) * (x0 - x2) * (x1 - x2)
        if abs(denom) > 1e-12:
            a = (x2 * (y1 - y0) + x1 * (y0 - y2) + x0 * (y2 - y1)) / denom
            b = (x2**2 * (y0 - y1) + x1**2 * (y2 - y0) + x0**2 * (y1 - y2)) / denom
            if a < 0:
                sommet = -b / (2 * a)
                if x0 <= sommet <= x2:
                    veq = float(sommet)

    return ResultatClassique(
        veq=veq,
        pente_max=float(d_abs[i]),
        derivee_v=v_mid.round(4).tolist(),
        derivee=(d_abs).round(4).tolist(),
        pka=None,
    )


def estimer_pka(volumes, ph, veq: float, type_dosage: str | None) -> float | None:
    """pKa ≈ pH à la demi-équivalence (pour une base faible : pKa du couple BH+/B)."""
    if type_dosage not in ("acide_faible", "base_faible"):
        return None
    v, p = _nettoyer(volumes, ph)
    demi = veq / 2
    if demi < v[0] or demi > v[-1]:
        return None
    return round(float(np.interp(demi, v, p)), 2)


def concentration_analyte(veq_ml: float, c_titrant: float, v_prise_ml: float) -> float:
    """C_analyte = C_titrant × V_eq / V_prise (stœchiométrie 1:1)."""
    return c_titrant * veq_ml / v_prise_ml
