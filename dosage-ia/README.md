# Dosage IA — exploitation intelligente des courbes de titrage acido-basique

Module Python autonome (`ai_model/`) qui analyse une courbe de titrage pH = f(V) et en extrait :

- le **volume équivalent** (V_eq) par IA, avec une incertitude, comparé à la méthode classique de la dérivée ;
- le **type de dosage** (acide fort, acide faible, base forte, base faible) ;
- un **contrôle qualité** de la mesure (courbe conforme ou défaut détecté) ;
- le **pKa** estimé (couples faibles) et la **concentration** de l'analyte ;
- des **alertes** expliquant pourquoi un dosage doit être revu par un humain.

L'approche est **hybride** : l'IA ne remplace pas la méthode dérivée, elle s'en sert comme caractéristique d'entrée et la corrige. Si la courbe est jugée non conforme, c'est la méthode classique (plus explicable) qui est retenue.

---

## Sommaire

1. [Installation](#installation)
2. [Structure du projet](#structure-du-projet)
3. [Fonctionnalités](#fonctionnalités)
4. [Entrées (inputs)](#entrées-inputs)
5. [Sorties (outputs)](#sorties-outputs)
6. [Utilisation](#utilisation)
7. [Fonctionnement interne](#fonctionnement-interne)
8. [Limites connues](#limites-connues)

---

## Installation

Python ≥ 3.10 (le code utilise la syntaxe `float | None`).

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS : source .venv/bin/activate)
pip install -r ai_model/requirements.txt
```

Dépendances : `numpy`, `scipy`, `scikit-learn`, `joblib`, `pandas`, `openpyxl`.

> Le package utilise des imports relatifs : lancez toujours les scripts **depuis la racine du projet** avec `python -m ai_model.<script>`.

---

## Structure du projet

| Fichier | Rôle |
|---|---|
| `ai_model/chemistry.py` | Chimie : simulation exacte du pH, méthode dérivée, estimation du pKa, calcul de concentration |
| `ai_model/generateur.py` | Génération de courbes synthétiques réalistes (bruit, dérive, pas irrégulier) et injection d'anomalies |
| `ai_model/features.py` | Transformation d'une courbe brute en vecteur de caractéristiques de taille fixe |
| `ai_model/entrainement.py` | Entraînement et évaluation des 3 modèles Random Forest, rapport de métriques |
| `ai_model/service.py` | Service d'inférence : chargement du modèle actif, analyse complète d'une courbe |
| `ai_model/donnees_reelles.py` | Lecture des dosages **validés** dans la base SQLite `dosage.db` |
| `ai_model/entrainer_avec_db.py` | CLI : entraînement synthétique + données réelles de la base |
| `ai_model/predire_excel.py` | CLI : analyse d'une courbe contenue dans un fichier Excel |
| `ai_model/example.py` | Exemple de bout en bout (entraînement + prédiction sur une courbe simulée) |
| `ai_model/dosage.db` | Base SQLite de l'application (dosages, points de mesure, utilisateurs…) |
| `ai_model/models_store/` | Modèles entraînés (`rf-AAAAMMJJ-HHMMSS.joblib`) + pointeur `active.json` (créé automatiquement, ignoré par git) |

---

## Fonctionnalités

### 1. Prédiction du volume équivalent
- Random Forest régresseur (200 arbres) qui prédit `V_eq / V_max`, remis à l'échelle en mL.
- **Incertitude** = écart-type des prédictions des 200 arbres.

### 2. Reconnaissance du type de dosage
- Random Forest classifieur à 4 classes : `acide_fort`, `acide_faible`, `base_forte`, `base_faible`.
- Renvoie la classe prédite, sa confiance et la probabilité de chaque classe.

### 3. Contrôle qualité de la mesure
Random Forest multi-classes qui renvoie `conforme` ou l'un des défauts suivants :

| Code | Signification |
|---|---|
| `pic` | Pic(s) de pH isolé(s) — bulle d'air, agitation ou mauvais contact d'électrode |
| `arret_premature` | Dosage arrêté avant ou trop près de l'équivalence |
| `electrode_defaillante` | Signal très bruité — électrode à vérifier ou réétalonner |
| `inversion` | Évolution du pH incohérente — erreur de saisie ou de séquence |

### 4. Méthode classique (dérivée)
- Maximum de |dpH/dV|, affiné par interpolation parabolique.
- Fusion des points trop rapprochés (< 0,4 % de V_max) pour éviter les faux pics de dérivée.
- Lissage Savitzky-Golay si la courbe est dense (≥ 15 points) et à pas régulier.

### 5. Grandeurs chimiques
- **pKa** ≈ pH à la demi-équivalence (uniquement pour `acide_faible` / `base_faible` ; pour une base faible, c'est le pKa du couple BH⁺/B).
- **Concentration de l'analyte** : `C = C_titrant × V_eq / V_prise` (stœchiométrie 1:1).

### 6. Système d'alertes et arbitrage
| Code | Niveau | Déclenchement |
|---|---|---|
| `pic`, `arret_premature`, `electrode_defaillante`, `inversion` | critique | Le contrôle qualité détecte un défaut |
| `discordance` | attention | Écart IA / dérivée > 3 % |
| `incertitude` | attention | Incertitude IA > 3 % de V_eq |
| `type` | attention | Type déclaré ≠ type reconnu (confiance > 80 %) |
| `marge` | attention | V_eq > 90 % du dernier volume versé |

**Volume retenu** : V_eq IA, sauf en cas d'anomalie critique → V_eq dérivée.
**`a_revoir = true`** dès qu'il y a une anomalie ou au moins une alerte « attention ».

### 7. Entraînement
- Sur **courbes synthétiques** (4000 par défaut) simulées par la chimie exacte puis dégradées comme une vraie mesure.
- Optionnellement enrichi par les **dosages réels validés** (`statut = 'valide'`) de `dosage.db`.
- Chaque modèle est versionné et produit un **rapport de métriques** sur un jeu de test tenu à l'écart (20 %).

---

## Entrées (inputs)

### Analyse d'une courbe — `service.analyser_courbe(...)`

| Paramètre | Type | Obligatoire | Unité | Description |
|---|---|---|---|---|
| `dossier` | `Path` | oui | — | Dossier des modèles (`ai_model/models_store`) |
| `volumes` | liste / `np.ndarray` de float | oui | mL | Volumes de titrant versés |
| `ph` | liste / `np.ndarray` de float | oui | — | pH mesuré pour chaque volume |
| `c_titrant` | float | non | mol/L | Concentration du titrant (nécessaire au calcul de concentration) |
| `v_prise` | float | non | mL | Volume de la prise d'essai (nécessaire au calcul de concentration) |
| `type_declare` | str | non | — | Type déclaré par l'opérateur : `acide_fort`, `acide_faible`, `base_forte`, `base_faible` |

Contraintes sur la courbe :
- **au moins 5 volumes distincts** (sinon `ValueError`) ;
- volume maximal > 0 ;
- l'ordre n'importe pas (les points sont triés) ; les volumes dupliqués sont fusionnés (moyenne des pH) ;
- pour une bonne estimation, la courbe doit **dépasser nettement l'équivalence**.

### Fichier Excel — `predire_excel.py`

Une feuille `.xlsx` avec deux colonnes nommées `volume` et `ph` (casse et ordre indifférents), une ligne par point :

| volume | ph |
|---|---|
| 0.0 | 2.87 |
| 1.0 | 3.65 |
| … | … |

Options CLI : `--titrant` (mol/L), `--prise` (mL), `--type` (type déclaré).

### Base SQLite — `entrainer_avec_db.py`

Lit les tables `dosages` (colonnes `type_dosage`, `titrant_concentration`, `volume_prise`, `veq_retenu`, `concentration`, `pka_estime`, `statut`) et `points_mesure` (`dosage_id`, `volume`, `ph`).
Seuls les dosages `statut = 'valide'` avec `veq_retenu` renseigné et ≥ 5 points sont utilisés.

Options CLI : `--db` (chemin de la base, défaut `ai_model/dosage.db`), `--n` (nombre de courbes synthétiques, défaut 4000).

### Entraînement — `service.entrainer_et_activer(...)`

| Paramètre | Type | Description |
|---|---|---|
| `dossier` | `Path` | Dossier où enregistrer le modèle |
| `n_echantillons` | int | Nombre de courbes synthétiques générées |
| `courbes_reelles` | `list[CourbeSimulee]` ou `None` | Courbes réelles additionnelles (cf. `charger_dosages_valides`) |

---

## Sorties (outputs)

### Résultat d'analyse — dictionnaire renvoyé par `analyser_courbe`

| Clé | Type | Description |
|---|---|---|
| `veq_derivee` | float (mL) | V_eq par la méthode dérivée classique |
| `veq_ia` | float (mL) | V_eq prédit par l'IA |
| `veq_ia_incertitude` | float (mL) | Écart-type des prédictions des arbres |
| `veq_retenu` | float (mL) | Volume finalement retenu (IA, ou dérivée si anomalie) |
| `type_predit` | str | Type de dosage reconnu |
| `type_confiance` | float [0–1] | Probabilité du type prédit |
| `probabilites_type` | dict | Probabilité de chacun des 4 types |
| `score_qualite` | float [0–1] | Probabilité que la courbe soit conforme |
| `est_anomalie` | bool | `true` si un défaut est détecté |
| `defaut_detecte` | str \| null | Code du défaut (`pic`, `arret_premature`, …) |
| `pka_estime` | float \| null | pKa estimé (couples faibles uniquement) |
| `concentration` | float \| null (mol/L) | Concentration de l'analyte, si `c_titrant` et `v_prise` sont fournis |
| `alertes` | liste de `{niveau, code, message}` | Alertes détaillées (voir tableau plus haut) |
| `a_revoir` | bool | Le dosage nécessite une revue humaine |
| `derivee` | `{v: [...], d: [...]}` | Courbe dérivée (volumes milieux, \|dpH/dV\|) pour tracé |
| `modele_version` | str | Version du modèle utilisé (ex. `rf-20261026-101500`) |

Exemple :

```json
{
  "veq_derivee": 12.48,
  "veq_ia": 12.531,
  "veq_ia_incertitude": 0.087,
  "veq_retenu": 12.531,
  "type_predit": "acide_faible",
  "type_confiance": 0.94,
  "probabilites_type": {"acide_faible": 0.94, "acide_fort": 0.05, "base_faible": 0.0, "base_forte": 0.01},
  "score_qualite": 0.97,
  "est_anomalie": false,
  "defaut_detecte": null,
  "pka_estime": 4.78,
  "concentration": 0.062655,
  "alertes": [],
  "a_revoir": false,
  "derivee": {"v": [0.5, 1.5, "..."], "d": [0.21, 0.18, "..."]},
  "modele_version": "rf-20261026-101500"
}
```
*(valeurs illustratives)*

### Entraînement — fichiers produits

- `models_store/rf-AAAAMMJJ-HHMMSS.joblib` : bundle contenant `regresseur`, `classifieur`, `qualite`, `version`, `version_features`.
- `models_store/active.json` : pointeur vers le modèle actif + métriques :

| Bloc | Métriques |
|---|---|
| `volume_equivalence` | MAE relative, médiane, P95 (IA vs dérivée, en %), part des cas où l'IA est meilleure, erreurs par tranche de bruit et par nombre de points |
| `type_dosage` | Exactitude, matrice de confusion 4×4 |
| `anomalies` | F1, taux de détection, faux positifs, détection par type de défaut |
| `jeu` | Taille des jeux d'entraînement et de test |
| `duree_s` | Durée de l'entraînement |

La CLI `entrainer_avec_db` affiche aussi un résumé de ces métriques dans la console.

---

## Utilisation

Toutes les commandes se lancent depuis la racine du projet.

**Exemple complet** (entraîne un petit modèle puis analyse une courbe simulée) :
```bash
python -m ai_model.example
```

**Entraîner avec les données réelles de la base** :
```bash
python -m ai_model.entrainer_avec_db
python -m ai_model.entrainer_avec_db --db chemin/vers/dosage.db --n 4000
```

**Analyser une courbe Excel** (résultat JSON sur la sortie standard) :
```bash
python -m ai_model.predire_excel courbe.xlsx
python -m ai_model.predire_excel courbe.xlsx --titrant 0.1 --prise 20 --type acide_faible
```

**Depuis Python** :
```python
from pathlib import Path
from ai_model.service import analyser_courbe

resultat = analyser_courbe(
    Path("ai_model/models_store"),
    volumes=[0, 2, 4, 6, 8, 9, 9.5, 10, 10.5, 11, 12, 14, 16],
    ph=[2.9, 3.9, 4.3, 4.7, 5.2, 5.6, 6.0, 8.7, 11.3, 11.6, 11.9, 12.2, 12.3],
    c_titrant=0.1, v_prise=20,
)
print(resultat["veq_retenu"], resultat["alertes"])
```

> Si aucun modèle actif n'existe, le premier appel à `analyser_courbe` **entraîne automatiquement** un modèle sur 4000 courbes synthétiques (compter de quelques dizaines de secondes à quelques minutes).

---

## Fonctionnement interne

```
Courbe brute (V, pH)
      │
      ▼
features.extraire ──► vecteur de 140 valeurs :
      │                 • 64 pH rééchantillonnés sur V/V_max ∈ [0, 1]
      │                 • 64 valeurs de dérivée
      │                 • 12 descripteurs (pH initial/final, amplitude, sens du saut,
      │                   V_eq dérivée, pente max, bruit, densité de points, …)
      ├──► Régresseur RF ──► V_eq IA ± incertitude
      ├──► Classifieur RF ──► type de dosage
features.descripteurs_qualite (7 valeurs) ──► Classifieur qualité RF ──► conforme / défaut
chemistry.methode_derivee ──► V_eq dérivée
      │
      ▼
Arbitrage + alertes ──► V_eq retenu, pKa, concentration, a_revoir
```

**Données synthétiques** (`generateur.py`) : C_analyte 0,005–0,2 mol/L, C_titrant 0,01–0,2 mol/L, prise 5/10/20/25 mL, V_eq entre 3 et 30 mL, pKa 3–7,5 (acides faibles) ou 6,5–10,5 (bases faibles), 12 à 60 points, bruit pH σ 0,003–0,06, décalage d'étalonnage, erreur de lecture de burette (σ 0,02 mL), incréments resserrés autour du saut une fois sur deux.

**Simulation chimique** : résolution exacte de l'électroneutralité (pas d'approximation de Henderson), valable sur toute la courbe.

**Versionnage** : `VERSION_FEATURES = "f2"`. Un modèle entraîné avec une autre version des caractéristiques est refusé (`RuntimeError`) — il faut réentraîner.

---

## Limites connues

- Dosages **monoprotiques** à stœchiométrie **1:1** uniquement (pas de polyacides, pas de dosages rédox/complexométriques).
- Le pKa n'est estimé que pour les couples faibles et si la demi-équivalence est dans la plage mesurée.
- Le modèle est entraîné majoritairement sur des données synthétiques : ses performances sur un appareil réel dépendent de la représentativité de la simulation — d'où l'intérêt de réentraîner avec les dosages validés.
- Le cache du modèle est global au processus (un seul dossier de modèles actif à la fois).
