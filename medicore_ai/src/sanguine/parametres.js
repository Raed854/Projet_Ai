// Paramètres du modèle NFS / CBC (projet_nfs_cbc/model/cbc_model.joblib), dans l'ordre du modèle.
// mediane : valeur utilisée par le modèle quand le champ est laissé vide.
// reference : plage adulte indicative, affichée comme aide à la saisie (non utilisée par le modèle).
export const GROUPES = [
  {
    titre: 'Globules blancs',
    parametres: [
      { code: 'WBC', label: 'Globules blancs', unite: '10⁹/L', mediane: 7.4, reference: [4, 10] },
      { code: 'LYMp', label: 'Lymphocytes', unite: '%', mediane: 25.84, reference: [20, 40] },
      { code: 'NEUTp', label: 'Neutrophiles', unite: '%', mediane: 77.51, reference: [40, 75] },
      { code: 'LYMn', label: 'Lymphocytes', unite: '10⁹/L', mediane: 1.88, reference: [1, 4] },
      { code: 'NEUTn', label: 'Neutrophiles', unite: '10⁹/L', mediane: 5.14, reference: [1.8, 7.5] },
    ],
  },
  {
    titre: 'Globules rouges',
    parametres: [
      { code: 'RBC', label: 'Globules rouges', unite: '10¹²/L', mediane: 4.6, reference: [4, 5.9] },
      { code: 'HGB', label: 'Hémoglobine', unite: 'g/dL', mediane: 12.2, reference: [12, 17] },
      { code: 'HCT', label: 'Hématocrite', unite: '%', mediane: 46.15, reference: [36, 52] },
      { code: 'MCV', label: 'VGM', unite: 'fL', mediane: 86.55, reference: [80, 100] },
      { code: 'MCH', label: 'TCMH', unite: 'pg', mediane: 27.7, reference: [27, 32] },
      { code: 'MCHC', label: 'CCMH', unite: 'g/dL', mediane: 32, reference: [32, 36] },
    ],
  },
  {
    titre: 'Plaquettes',
    parametres: [
      { code: 'PLT', label: 'Plaquettes', unite: '10⁹/L', mediane: 211, reference: [150, 400] },
      { code: 'PDW', label: 'Indice de distribution', unite: '%', mediane: 14.31, reference: [10, 18] },
      { code: 'PCT', label: 'Plaquettocrite', unite: '%', mediane: 0.26, reference: [0.15, 0.4] },
    ],
  },
];

export const PARAMETRES = GROUPES.flatMap((groupe) => groupe.parametres);

export const PARAMETRES_PAR_CODE = Object.fromEntries(PARAMETRES.map((p) => [p.code, p]));

// Classes prédites par le modèle -> libellé français
export const DIAGNOSTICS = {
  Healthy: 'Sain (aucune anomalie)',
  'Iron deficiency anemia': 'Anémie ferriprive',
  Leukemia: 'Leucémie',
  'Leukemia with thrombocytopenia': 'Leucémie avec thrombopénie',
  'Macrocytic anemia': 'Anémie macrocytaire',
  'Normocytic hypochromic anemia': 'Anémie normocytaire hypochrome',
  'Normocytic normochromic anemia': 'Anémie normocytaire normochrome',
  'Other microcytic anemia': 'Autre anémie microcytaire',
  Thrombocytopenia: 'Thrombopénie',
};

export function libelleDiagnostic(diagnostic) {
  return DIAGNOSTICS[diagnostic] || diagnostic;
}

export function formatValeur(value) {
  return typeof value === 'number' ? value.toLocaleString('fr-FR', { maximumFractionDigits: 2 }) : '—';
}

export function formatPercent(value) {
  return typeof value === 'number'
    ? `${value.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} %`
    : '—';
}

// Probabilités triées de la plus forte à la plus faible
export function probabilitesTriees(probabilities = {}) {
  return Object.entries(probabilities).sort(([, a], [, b]) => b - a);
}

// Tableau des 14 valeurs envoyées au modèle, avec leur origine (saisie ou médiane)
export function lignesValeurs(analyse) {
  return PARAMETRES.map((parametre) => ({
    ...parametre,
    valeur: analyse.valeurs_utilisees?.[parametre.code],
    completee: (analyse.parametres_completes || []).includes(parametre.code),
  }));
}
