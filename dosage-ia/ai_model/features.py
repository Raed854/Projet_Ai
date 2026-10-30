"""Extraction de caractéristiques à partir d'une courbe de titrage brute.

Une courbe réelle a un nombre de points variable et un pas irrégulier. On la ramène
à un vecteur de taille fixe :
  * volume normalisé x = V / V_max, pH rééchantillonné sur une grille de N_GRILLE points ;
  * dérivée de la courbe rééchantillonnée ;
  * descripteurs scalaires (pH initial/final, amplitude, bruit estimé, densité de points,
    estimation par la méthode dérivée — l'IA corrige la méthode classique plutôt que
    de l'ignorer : approche hybride).
"""
from __future__ import annotations

import numpy as np

from .chemistry import _nettoyer, methode_derivee

N_GRILLE = 64
VERSION_FEATURES = "f2"


def bruit_estime(v: np.ndarray, p: np.ndarray) -> float:
    """Écart-type des résidus par rapport à une moyenne glissante sur 3 points,
    calculé hors de la zone de saut (où la pente domine)."""
    if len(p) < 7:
        return 0.0
    residus = p[1:-1] - (p[:-2] + p[2:]) / 2
    pente = np.abs(np.gradient(p, v))[1:-1]
    masque = pente < np.quantile(pente, 0.7)
    r = residus[masque] if masque.sum() >= 3 else residus
    return float(np.std(r) * np.sqrt(2 / 3))


def extraire(volumes, ph) -> tuple[np.ndarray, dict]:
    """Retourne (vecteur de caractéristiques, contexte utile au post-traitement)."""
    v, p = _nettoyer(volumes, ph)
    if len(v) < 5:
        raise ValueError("Au moins 5 points distincts sont nécessaires")
    v_max = float(v[-1])
    if v_max <= 0:
        raise ValueError("Le volume maximal doit être positif")
    x = v / v_max

    grille = np.linspace(0, 1, N_GRILLE)
    p_grille = np.interp(grille, x, p)
    d_grille = np.gradient(p_grille, grille)
    signe = 1.0 if p[-1] >= p[0] else -1.0

    res = methode_derivee(v, p)
    x_derivee = res.veq / v_max

    pas = np.diff(x)
    # densité de points autour de l'estimation classique (±10 % de V_max)
    proche = np.abs(x - x_derivee) < 0.10
    scalaires = np.array(
        [
            p[0],
            p[-1],
            p[-1] - p[0],
            signe,
            x_derivee,
            res.pente_max * v_max / 14.0,
            bruit_estime(v, p),
            len(v) / 60.0,
            float(pas.max()),
            float(proche.sum()) / len(v),
            float(np.mean(np.diff(p) * signe < -0.02)),  # part de non-monotonie
            p_grille[N_GRILLE // 4] - p[0],                # forme de la zone tampon
        ]
    )
    vecteur = np.concatenate([p_grille, d_grille * signe / 100.0, scalaires])
    contexte = {"v_max": v_max, "veq_derivee": res.veq, "signe": signe}
    return vecteur, contexte


def descripteurs_qualite(volumes, ph) -> np.ndarray:
    """Petit vecteur dédié à la détection d'anomalies (Isolation Forest)."""
    v, p = _nettoyer(volumes, ph)
    x = v / v[-1]
    signe = 1.0 if p[-1] >= p[0] else -1.0
    res = methode_derivee(v, p)
    x_eq = res.veq / v[-1]
    pas = np.diff(x)
    dp = np.diff(p) * signe
    return np.array(
        [
            bruit_estime(v, p),
            float(np.mean(dp < -0.03)),         # inversions de tendance
            float(np.max(np.abs(np.diff(dp))) if len(dp) > 1 else 0.0),  # pics isolés
            abs(p[-1] - p[0]),                    # amplitude totale
            x_eq,                                 # position du saut dans la plage versée
            float(pas.max()),                     # plus grand trou de mesure
            1.0 - x_eq,                           # marge après l'équivalence
        ]
    )
