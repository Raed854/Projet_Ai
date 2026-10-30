import { useState } from 'react';
import './sanguine.css';
import '../component/result_modal.css';
import SideBar from '../component/side_bar/side_bar';
import {
  GROUPES,
  PARAMETRES,
  PARAMETRES_PAR_CODE,
  formatPercent,
  formatValeur,
  libelleDiagnostic,
  lignesValeurs,
  probabilitesTriees,
} from './parametres';

// Service Flask du modèle NFS (projet_nfs_cbc/api_service.py) : prédiction + enregistrement en table sanguine
const MODEL_API_URL = process.env.REACT_APP_SANGUINE_API_URL || 'http://localhost:5003';

// Ligne réelle du jeu d'entraînement (diagnostic : Iron deficiency anemia)
const EXEMPLE = {
  WBC: '7.2', LYMp: '30.7', NEUTp: '60.7', LYMn: '2.2', NEUTn: '4.4', RBC: '3.97', HGB: '9',
  HCT: '30.5', MCV: '77', MCH: '22.6', MCHC: '29.5', PLT: '148', PDW: '14.3', PCT: '0.14',
};

const EMPTY_VALEURS = Object.fromEntries(PARAMETRES.map((p) => [p.code, '']));

function parseNumber(value) {
  return Number(String(value).trim().replace(',', '.'));
}

export function DiagnosticResult({ analyse }) {
  const nbCompletes = analyse.parametres_completes?.length || 0;
  return (
    <>
      <div className="sanguine-badges">
        <span className={`sanguine-diagnostic ${analyse.diagnostic === 'Healthy' ? 'sanguine-diagnostic-sain' : 'sanguine-diagnostic-anomalie'}`}>
          <span aria-hidden="true">{analyse.diagnostic === 'Healthy' ? '✓' : '!'}</span>
          {libelleDiagnostic(analyse.diagnostic)}
        </span>
      </div>
      <p className="sanguine-diagnostic-code">Classe du modèle : {analyse.diagnostic}</p>

      <div className="sanguine-metrics">
        <div className="sanguine-metric"><small>Confiance</small><strong>{formatPercent(analyse.confidence)}</strong></div>
        <div className="sanguine-metric"><small>Paramètres saisis</small><strong>{PARAMETRES.length - nbCompletes} / {PARAMETRES.length}</strong></div>
        <div className="sanguine-metric"><small>Complétés par la médiane</small><strong>{nbCompletes}</strong></div>
      </div>

      {nbCompletes > 0 && (
        <p className="sanguine-warning">
          {nbCompletes} paramètre{nbCompletes > 1 ? 's' : ''} non saisi{nbCompletes > 1 ? 's ont' : ' a'} été remplacé{nbCompletes > 1 ? 's' : ''} par
          la médiane du jeu d’entraînement : plus il y en a, moins le résultat est fiable.
        </p>
      )}

      <div className="sanguine-box">
        <h3>Probabilités par diagnostic</h3>
        {probabilitesTriees(analyse.probabilities).map(([diagnostic, probability]) => (
          <div className="sanguine-probability-row" key={diagnostic}>
            <span>{libelleDiagnostic(diagnostic)}</span>
            <strong>{formatPercent(probability)}</strong>
            <div className="sanguine-probability-track"><span style={{ width: `${probability}%` }} /></div>
          </div>
        ))}
      </div>

      <div className="sanguine-table-wrapper">
        <table className="sanguine-table">
          <thead>
            <tr><th>Paramètre</th><th>Valeur utilisée</th><th>Réf. indicative</th><th>Origine</th></tr>
          </thead>
          <tbody>
            {lignesValeurs(analyse).map((ligne) => (
              <tr key={ligne.code} className={ligne.completee ? 'sanguine-row-mediane' : ''}>
                <td><strong>{ligne.code}</strong> · {ligne.label}</td>
                <td><strong>{formatValeur(ligne.valeur)}</strong> {ligne.unite}</td>
                <td>{formatValeur(ligne.reference[0])} – {formatValeur(ligne.reference[1])}</td>
                <td>{ligne.completee ? <span className="sanguine-origine-mediane">Médiane</span> : <span className="sanguine-origine-saisie">Saisie</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function Sanguine({ account, onOpenHistory, onLogout, onSelectModule, selectedModule }) {
  const [valeurs, setValeurs] = useState(EMPTY_VALEURS);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showResult, setShowResult] = useState(false);

  function loadExample() {
    setValeurs(EXEMPLE);
    setError('');
  }

  function resetForm() {
    setValeurs(EMPTY_VALEURS);
    setResult(null);
    setError('');
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const saisies = Object.entries(valeurs).filter(([, value]) => String(value).trim() !== '');
    if (saisies.length === 0) {
      setError('Renseignez au moins un paramètre de la NFS.');
      return;
    }
    const invalide = saisies.find(([, value]) => !Number.isFinite(parseNumber(value)) || parseNumber(value) < 0);
    if (invalide) {
      setError(`La valeur de « ${invalide[0]} (${PARAMETRES_PAR_CODE[invalide[0]].label}) » doit être un nombre positif.`);
      return;
    }

    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${MODEL_API_URL}/api/users/${account.id}/sanguine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          valeurs: Object.fromEntries(saisies.map(([code, value]) => [code, parseNumber(value)])),
        }),
      });
      const responseData = await response.json().catch(() => null);

      if (!response.ok) {
        const backendDetail = responseData?.backendResponse?.detail;
        throw new Error(
          (typeof backendDetail === 'string' && backendDetail)
          || responseData?.error
          || `L’API a répondu avec le statut ${response.status}.`,
        );
      }

      if (!responseData?.diagnostic || typeof responseData.confidence !== 'number') {
        throw new Error('La réponse de l’API ne contient pas un résultat valide.');
      }

      setResult(responseData);
      setShowResult(true);
    } catch (requestError) {
      setError(
        requestError.message === 'Failed to fetch'
          ? 'Impossible de contacter le modèle NFS. Vérifiez que l’API est démarrée sur le port 5003.'
          : requestError.message,
      );
    } finally {
      setIsLoading(false);
    }
  }

  const nbSaisis = Object.values(valeurs).filter((value) => String(value).trim() !== '').length;

  return (
    <main className="sanguine-page">
      <SideBar onLogout={onLogout} onSelectModule={onSelectModule} selectedModule={selectedModule} />

      <section className="sanguine-main">
        <header className="sanguine-topbar">
          <div>
            <p className="sanguine-eyebrow">IA hématologie</p>
            <h1>Analyse de la NFS / CBC</h1>
          </div>
          <button className="sanguine-history-button" type="button" onClick={onOpenHistory}>
            Voir l’historique
          </button>
        </header>

        <div className="sanguine-grid">
          <form className="sanguine-form" onSubmit={handleSubmit}>
            <div className="sanguine-section-head">
              <h2>Paramètres de la NFS <span className="sanguine-count">{nbSaisis} / {PARAMETRES.length}</span></h2>
              <div className="sanguine-head-actions">
                <button type="button" className="sanguine-link-button" onClick={loadExample}>Charger l’exemple</button>
                <button type="button" className="sanguine-link-button" onClick={resetForm}>Vider</button>
              </div>
            </div>

            {GROUPES.map((groupe) => (
              <fieldset className="sanguine-groupe" key={groupe.titre}>
                <legend>{groupe.titre}</legend>
                <div className="sanguine-params">
                  {groupe.parametres.map((parametre) => (
                    <label key={parametre.code}>
                      <span className="sanguine-param-label"><strong>{parametre.code}</strong> · {parametre.label}</span>
                      <div className="sanguine-input-unit">
                        <input
                          type="text"
                          inputMode="decimal"
                          placeholder={formatValeur(parametre.mediane)}
                          value={valeurs[parametre.code]}
                          onChange={(event) => setValeurs((current) => ({ ...current, [parametre.code]: event.target.value }))}
                        />
                        <span>{parametre.unite}</span>
                      </div>
                      <small>Réf. {formatValeur(parametre.reference[0])} – {formatValeur(parametre.reference[1])} · vide = médiane</small>
                    </label>
                  ))}
                </div>
              </fieldset>
            ))}

            <div className="sanguine-api-info">
              <span aria-hidden="true">✓</span>
              <span>
                Les champs vides sont remplacés par la médiane du jeu d’entraînement (valeur grisée).
                Le modèle prédit le type d’anémie et le résultat est enregistré dans votre historique.
              </span>
            </div>

            {error && <p className="sanguine-api-error" role="alert">{error}</p>}

            <button className="sanguine-submit" type="submit" disabled={isLoading}>
              {isLoading ? 'Analyse en cours…' : 'Tester'}
            </button>
          </form>

          {showResult && <div className="analysis-result-modal-backdrop" onClick={() => setShowResult(false)} />}
          <div className={`sanguine-result${showResult ? ' analysis-result-modal' : ''}`} role={showResult ? 'dialog' : undefined} aria-modal={showResult ? 'true' : undefined}>
            <div className="sanguine-result-header">
              <p className="sanguine-eyebrow">Résultat du modèle</p>
              <h2>Type d’anémie prédit</h2>
              {result?.sanguine && <span className="sanguine-saved">Enregistré #{result.sanguine.id}</span>}
            </div>

            {result ? (
              <>
                <DiagnosticResult analyse={result} />
                <p className="sanguine-avertissement">Outil d’étude : ce résultat ne remplace pas un diagnostic médical.</p>
              </>
            ) : (
              <div className="sanguine-empty-result">
                <div className="sanguine-empty-icon">AI</div>
                <p>{isLoading ? 'Le modèle analyse la NFS…' : 'Renseignez les valeurs de la NFS puis cliquez sur « Tester ».'}</p>
              </div>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}

export default Sanguine;
