"""Entraînement et évaluation des trois modèles du module IA.

  1. Régression du volume équivalent (Random Forest) — cible : V_eq / V_max.
     L'incertitude est estimée par la dispersion des prédictions des arbres.
  2. Classification du type de dosage (Random Forest, 4 classes).
  3. Contrôle qualité de la mesure (Random Forest multi-classes) : "conforme" ou type de
     défaut (pic parasite, arrêt avant l'équivalence, électrode défaillante, inversion).
     Entraîné sur des courbes conformes et des courbes dégradées volontairement.

Chaque entraînement produit un rapport de métriques comparant l'IA à la méthode
dérivée classique sur un jeu de test tenu à l'écart.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split

from .chemistry import TYPES
from .features import VERSION_FEATURES, descripteurs_qualite, extraire
from .generateur import generer_courbe, injecter_anomalie


def _jeu(courbes):
    X, y_frac, y_type, veq, v_max, veq_der, bruits, n_pts = [], [], [], [], [], [], [], []
    for c in courbes:
        vec, ctx = extraire(c.volumes, c.ph)
        X.append(vec)
        y_frac.append(c.veq / ctx["v_max"])
        y_type.append(c.type_dosage)
        veq.append(c.veq)
        v_max.append(ctx["v_max"])
        veq_der.append(ctx["veq_derivee"])
        bruits.append(c.bruit)
        n_pts.append(len(c.volumes))
    return (np.array(X), np.array(y_frac), np.array(y_type), np.array(veq), np.array(v_max),
            np.array(veq_der), np.array(bruits), np.array(n_pts))


def entrainer(n_echantillons: int, dossier: Path, graine: int = 42,
             courbes_reelles: list | None = None) -> dict:
    t0 = time.perf_counter()
    rng = np.random.default_rng(graine)
    courbes = [generer_courbe(rng) for _ in range(n_echantillons)]
    courbes += courbes_reelles or []
    X, y_frac, y_type, veq, v_max, veq_der, bruits, n_pts = _jeu(courbes)

    idx = np.arange(len(X))
    i_tr, i_te = train_test_split(idx, test_size=0.2, random_state=graine, stratify=y_type)

    reg = RandomForestRegressor(n_estimators=200, min_samples_leaf=2, max_features=0.4,
                                n_jobs=-1, random_state=graine)
    reg.fit(X[i_tr], y_frac[i_tr])

    clf = RandomForestClassifier(n_estimators=200, min_samples_leaf=1, n_jobs=-1, random_state=graine)
    clf.fit(X[i_tr], y_type[i_tr])

    # --- Contrôle qualité : courbes conformes + courbes dégradées (1 sur 3)
    rng_q = np.random.default_rng(graine + 7)
    q_courbes = [courbes[i] for i in i_tr]
    q_courbes += [injecter_anomalie(rng_q, generer_courbe(rng_q)) for _ in range(len(i_tr) // 2)]
    Q = np.array([descripteurs_qualite(c.volumes, c.ph) for c in q_courbes])
    y_q = np.array([c.anomalie or "conforme" for c in q_courbes])
    qualite = RandomForestClassifier(n_estimators=200, min_samples_leaf=2, n_jobs=-1,
                                     class_weight="balanced", random_state=graine)
    qualite.fit(Q, y_q)

    # --- Évaluation
    pred_frac = reg.predict(X[i_te])
    veq_ia = pred_frac * v_max[i_te]
    err_ia = np.abs(veq_ia - veq[i_te]) / veq[i_te] * 100
    err_der = np.abs(veq_der[i_te] - veq[i_te]) / veq[i_te] * 100
    pred_type = clf.predict(X[i_te])

    def _par_tranche(masques):
        lignes = []
        for libelle, m in masques:
            if m.sum() == 0:
                continue
            lignes.append({
                "tranche": libelle, "n": int(m.sum()),
                "erreur_ia_pct": round(float(np.median(err_ia[m])), 3),
                "erreur_derivee_pct": round(float(np.median(err_der[m])), 3),
            })
        return lignes

    b, n = bruits[i_te], n_pts[i_te]
    par_bruit = _par_tranche([
        ("σ < 0,015", b < 0.015), ("0,015 – 0,03", (b >= 0.015) & (b < 0.03)),
        ("0,03 – 0,045", (b >= 0.03) & (b < 0.045)), ("σ ≥ 0,045", b >= 0.045),
    ])
    par_points = _par_tranche([
        ("< 20 points", n < 20), ("20 – 35", (n >= 20) & (n < 35)),
        ("35 – 50", (n >= 35) & (n < 50)), ("≥ 50 points", n >= 50),
    ])

    rng_a = np.random.default_rng(graine + 1)
    tests_ok = [generer_courbe(rng_a) for _ in range(400)]
    tests_ko = [injecter_anomalie(rng_a, generer_courbe(rng_a)) for _ in range(400)]
    Q_test = np.array([descripteurs_qualite(c.volumes, c.ph) for c in tests_ok + tests_ko])
    y_ano = np.array([0] * 400 + [1] * 400)
    genres = np.array(["conforme"] * 400 + [c.anomalie for c in tests_ko])
    pred_q = qualite.predict(Q_test)
    pred_ano = (pred_q != "conforme").astype(int)
    detection_par_genre = {
        str(g): round(float(pred_ano[genres == g].mean() * 100), 1)
        for g in sorted(set(genres)) if g != "conforme"
    }

    version = datetime.now(timezone.utc).strftime("rf-%Y%m%d-%H%M%S")
    metriques = {
        "volume_equivalence": {
            "mae_relative_ia_pct": round(float(np.mean(err_ia)), 3),
            "mae_relative_derivee_pct": round(float(np.mean(err_der)), 3),
            "mediane_ia_pct": round(float(np.median(err_ia)), 3),
            "mediane_derivee_pct": round(float(np.median(err_der)), 3),
            "p95_ia_pct": round(float(np.percentile(err_ia, 95)), 3),
            "p95_derivee_pct": round(float(np.percentile(err_der, 95)), 3),
            "part_ia_meilleure_pct": round(float(np.mean(err_ia < err_der) * 100), 1),
            "par_bruit": par_bruit,
            "par_nombre_points": par_points,
        },
        "type_dosage": {
            "exactitude": round(float(accuracy_score(y_type[i_te], pred_type)), 4),
            "classes": list(TYPES),
            "matrice_confusion": confusion_matrix(y_type[i_te], pred_type, labels=list(TYPES)).tolist(),
        },
        "anomalies": {
            "f1": round(float(f1_score(y_ano, pred_ano)), 4),
            "taux_detection_pct": round(float(pred_ano[y_ano == 1].mean() * 100), 1),
            "faux_positifs_pct": round(float(pred_ano[y_ano == 0].mean() * 100), 1),
            "detection_par_type_pct": detection_par_genre,
        },
        "jeu": {"entrainement": int(len(i_tr)), "test": int(len(i_te))},
        "duree_s": round(time.perf_counter() - t0, 1),
    }

    chemin = dossier / f"{version}.joblib"
    joblib.dump({
        "version": version,
        "version_features": VERSION_FEATURES,
        "regresseur": reg,
        "classifieur": clf,
        "qualite": qualite,
    }, chemin, compress=3)
    return {"version": version, "chemin": str(chemin), "metriques": metriques,
            "nb_echantillons": n_echantillons}
