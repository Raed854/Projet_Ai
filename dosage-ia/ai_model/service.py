"""Service d'inférence : charge le modèle actif et exploite une courbe de titrage.

Version autonome (sans backend web ni base de données) : le modèle actif est
repéré par un fichier pointeur `active.json` dans le dossier des modèles, et non
par une table SQL. Utilisable comme simple bibliothèque Python.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

import joblib
import numpy as np

from . import chemistry
from .entrainement import entrainer
from .features import VERSION_FEATURES, descripteurs_qualite, extraire

SEUIL_DISCORDANCE = 0.03
TRAINING_SAMPLES = 4000

LIBELLES_DEFAUT = {
    "pic": "Pic(s) de pH isolé(s) — bulle d'air, agitation ou mauvais contact d'électrode",
    "arret_premature": "Dosage arrêté avant ou trop près de l'équivalence",
    "electrode_defaillante": "Signal très bruité — électrode à vérifier ou réétalonner",
    "inversion": "Évolution du pH incohérente — erreur de saisie ou de séquence probable",
}

_verrou = threading.Lock()
_cache: dict = {"version": None, "bundle": None}


def _pointeur(dossier: Path) -> Path:
    return dossier / "active.json"


def _charger(chemin: str) -> dict:
    bundle = joblib.load(chemin)
    if bundle.get("version_features") != VERSION_FEATURES:
        raise RuntimeError("Modèle incompatible avec la version des caractéristiques — réentraîner")
    return bundle


def modele_actif(dossier: Path, n_echantillons: int = TRAINING_SAMPLES) -> dict:
    """Charge le modèle marqué actif dans `dossier`, en entraîne un nouveau si absent."""
    dossier = Path(dossier)
    with _verrou:
        pointeur = _pointeur(dossier)
        info = json.loads(pointeur.read_text()) if pointeur.exists() else None
        if info is None or not Path(info["chemin"]).exists():
            info = entrainer_et_activer(dossier, n_echantillons)
        if _cache["version"] != info["version"]:
            _cache["bundle"] = _charger(info["chemin"])
            _cache["version"] = info["version"]
        return _cache["bundle"]


def entrainer_et_activer(dossier: Path, n_echantillons: int, courbes_reelles: list | None = None) -> dict:
    """Entraîne un nouveau modèle, l'enregistre comme actif et renvoie ses métadonnées."""
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    resultat = entrainer(n_echantillons, dossier, courbes_reelles=courbes_reelles)
    _pointeur(dossier).write_text(json.dumps({
        "version": resultat["version"],
        "chemin": resultat["chemin"],
        "nb_echantillons": resultat["nb_echantillons"],
        "metriques": resultat["metriques"],
    }))
    _cache["version"] = None  # forcera le rechargement
    return resultat


def analyser_courbe(dossier: Path, volumes, ph, c_titrant: float | None = None,
                    v_prise: float | None = None, type_declare: str | None = None) -> dict:
    """Exploitation complète d'une courbe : méthode classique + IA + contrôle qualité."""
    bundle = modele_actif(dossier)
    vec, ctx = extraire(volumes, ph)
    X = vec.reshape(1, -1)
    v_max = ctx["v_max"]

    # 1) Volume équivalent — prédiction + incertitude (dispersion des arbres)
    reg = bundle["regresseur"]
    par_arbre = np.array([arbre.predict(X)[0] for arbre in reg.estimators_]) * v_max
    veq_ia = float(np.mean(par_arbre))
    incertitude = float(np.std(par_arbre))

    # 2) Type de dosage
    clf = bundle["classifieur"]
    proba = clf.predict_proba(X)[0]
    i_type = int(np.argmax(proba))
    type_predit = str(clf.classes_[i_type])
    type_confiance = float(proba[i_type])

    # 3) Contrôle qualité
    qualite = bundle["qualite"]
    pq = qualite.predict_proba(descripteurs_qualite(volumes, ph).reshape(1, -1))[0]
    classes_q = list(qualite.classes_)
    p_conforme = float(pq[classes_q.index("conforme")])
    defaut = str(classes_q[int(np.argmax(pq))])
    est_anomalie = defaut != "conforme"

    # 4) Méthode classique et arbitrage
    classique = chemistry.methode_derivee(volumes, ph)
    veq_der = classique.veq
    ecart_rel = abs(veq_ia - veq_der) / max(veq_ia, 1e-9)

    alertes: list[dict] = []
    if est_anomalie:
        alertes.append({"niveau": "critique", "code": defaut, "message": LIBELLES_DEFAUT[defaut]})
    if ecart_rel > SEUIL_DISCORDANCE:
        alertes.append({
            "niveau": "attention", "code": "discordance",
            "message": f"Écart de {ecart_rel * 100:.1f} % entre l'IA et la méthode dérivée — vérifier la courbe",
        })
    if incertitude / max(veq_ia, 1e-9) > 0.03:
        alertes.append({"niveau": "attention", "code": "incertitude",
                        "message": "Incertitude IA élevée — resserrer les incréments autour du saut"})
    if type_declare and type_declare != type_predit and type_confiance > 0.8:
        alertes.append({"niveau": "attention", "code": "type",
                        "message": f"Type déclaré « {type_declare} » ≠ type reconnu « {type_predit} »"})
    if veq_ia > 0.9 * v_max:
        alertes.append({"niveau": "attention", "code": "marge",
                        "message": "Équivalence proche du dernier point — prolonger le dosage"})

    # Volume retenu : l'IA, sauf si la courbe est jugée non conforme (on garde alors la
    # méthode classique, plus "explicable", et le dosage part en revue humaine).
    veq_retenu = veq_der if est_anomalie else veq_ia
    type_pour_pka = type_declare or type_predit
    resultat = {
        "veq_derivee": round(veq_der, 3),
        "veq_ia": round(veq_ia, 3),
        "veq_ia_incertitude": round(incertitude, 3),
        "veq_retenu": round(veq_retenu, 3),
        "type_predit": type_predit,
        "type_confiance": round(type_confiance, 3),
        "probabilites_type": {str(c): round(float(p), 3) for c, p in zip(clf.classes_, proba)},
        "score_qualite": round(p_conforme, 3),
        "est_anomalie": est_anomalie,
        "defaut_detecte": None if not est_anomalie else defaut,
        "pka_estime": chemistry.estimer_pka(volumes, ph, veq_retenu, type_pour_pka),
        "concentration": None,
        "alertes": alertes,
        "a_revoir": est_anomalie or any(a["niveau"] == "attention" for a in alertes),
        "derivee": {"v": classique.derivee_v, "d": classique.derivee},
        "modele_version": bundle["version"],
    }
    if c_titrant and v_prise:
        resultat["concentration"] = round(chemistry.concentration_analyte(veq_retenu, c_titrant, v_prise), 6)
    return resultat
