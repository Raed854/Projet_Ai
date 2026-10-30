import { Fragment, useEffect, useState } from 'react';
import './cardiaque.css';
import './historiquecardiaque.css';
import { CLASSES, SignalChart } from './cardiaque';
import SideBar from '../component/side_bar/side_bar';

const BACKEND_API_URL = process.env.REACT_APP_BACKEND_API_URL || '';

function formatTestDate(value) {
  if (!value) {
    return '—';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }

  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function formatPercent(value) {
  return typeof value === 'number'
    ? `${value.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} %`
    : '—';
}

// Miniature du battement pour la colonne « Signal »
function Sparkline({ signal }) {
  const width = 110;
  const height = 32;
  const min = Math.min(...signal);
  const max = Math.max(...signal);
  const span = max - min || 1;
  const points = signal
    .map((v, i) => `${((i / (signal.length - 1)) * width).toFixed(1)},${(height - 2 - ((v - min) / span) * (height - 4)).toFixed(1)}`)
    .join(' ');

  return (
    <svg className="historique-cardiaque-sparkline" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Aperçu du signal ECG">
      <polyline points={points} />
    </svg>
  );
}

function HistoriqueCardiaque({ account, onBackToCardiaque, onLogout, onSelectModule, selectedModule }) {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [openedId, setOpenedId] = useState(null);

  useEffect(() => {
    async function loadHistory() {
      try {
        const response = await fetch(`${BACKEND_API_URL}/cardiaques?user_id=${account.id}`);
        if (!response.ok) {
          throw new Error(`Statut ${response.status}`);
        }

        const data = await response.json();
        if (!Array.isArray(data)) {
          throw new Error('Format de réponse invalide');
        }

        setHistory([...data].reverse());
      } catch (requestError) {
        setError('Impossible de charger l’historique depuis le backend.');
      } finally {
        setIsLoading(false);
      }
    }

    loadHistory();
  }, [account.id]);

  const anormaux = history.filter((test) => test.classe !== 'N').length;

  return (
    <main className="historique-cardiaque-page">
      <SideBar onLogout={onLogout} onSelectModule={onSelectModule} selectedModule={selectedModule} />

      <section className="historique-cardiaque-main">
        <header className="historique-cardiaque-topbar">
          <div>
            <p className="historique-cardiaque-eyebrow">Suivi médical</p>
            <h1>Historique cardiaque</h1>
            <p>Retrouvez tous les battements ECG analysés sur votre compte.</p>
          </div>
          <button className="historique-cardiaque-back" type="button" onClick={onBackToCardiaque}>
            ← Nouvelle analyse
          </button>
        </header>

        <section className="historique-cardiaque-card" aria-labelledby="historique-cardiaque-title">
          <div className="historique-cardiaque-card-heading">
            <div>
              <p className="historique-cardiaque-eyebrow">Table cardiaque</p>
              <h2 id="historique-cardiaque-title">Vos analyses</h2>
            </div>
            <div className="historique-cardiaque-counts">
              <span className="historique-cardiaque-count">
                {history.length} analyse{history.length === 1 ? '' : 's'}
              </span>
              {anormaux > 0 && (
                <span className="historique-cardiaque-count historique-cardiaque-count-anormal">
                  {anormaux} non normal{anormaux === 1 ? '' : 'es'}
                </span>
              )}
            </div>
          </div>

          {isLoading && <p className="historique-cardiaque-loading">Chargement…</p>}
          {error && <p className="historique-cardiaque-error" role="alert">{error}</p>}

          {!isLoading && !error && history.length > 0 && (
            <div className="historique-cardiaque-table-wrapper">
              <table className="historique-cardiaque-table">
                <thead>
                  <tr>
                    <th>N°</th>
                    <th>Signal</th>
                    <th>Classe prédite</th>
                    <th>Confiance</th>
                    <th>Classe réelle</th>
                    <th>Prédiction</th>
                    <th>Date du test</th>
                    <th>Modèle</th>
                    <th>Utilisateur</th>
                    <th>Détails</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((test) => {
                    const isOpen = openedId === test.id;
                    return (
                      <Fragment key={test.id}>
                        <tr>
                          <td>#{test.id}</td>
                          <td><Sparkline signal={test.signal} /></td>
                          <td>
                            <span className={`historique-cardiaque-badge ${test.classe === 'N' ? 'historique-cardiaque-normal' : 'historique-cardiaque-anormal'}`}>
                              <span aria-hidden="true">{test.classe === 'N' ? '✓' : '!'}</span>
                              {test.classe} — {CLASSES[test.classe]}
                            </span>
                          </td>
                          <td>{formatPercent(test.confidence)}</td>
                          <td>{test.classe_reelle ? `${test.classe_reelle} — ${CLASSES[test.classe_reelle]}` : '—'}</td>
                          <td>
                            {test.prediction_correcte === null
                              ? <span className="historique-cardiaque-muted">Non vérifiée</span>
                              : test.prediction_correcte
                                ? <span className="historique-cardiaque-correct">✓ Correcte</span>
                                : <span className="historique-cardiaque-incorrect">✕ Incorrecte</span>}
                          </td>
                          <td>{formatTestDate(test.date_creation)}</td>
                          <td><code>{test.modele}</code></td>
                          <td>{account.prenom} {account.nom} (#{test.user_id})</td>
                          <td>
                            <button
                              className="historique-cardiaque-toggle"
                              type="button"
                              onClick={() => setOpenedId(isOpen ? null : test.id)}
                              aria-expanded={isOpen}
                            >
                              {isOpen ? 'Masquer' : 'Afficher'}
                            </button>
                          </td>
                        </tr>
                        {isOpen && (
                          <tr className="historique-cardiaque-details">
                            <td colSpan={10}>
                              <div className="historique-cardiaque-details-grid">
                                <SignalChart signal={test.signal} />
                                <div className="historique-cardiaque-probabilities">
                                  <h3>Probabilités par classe</h3>
                                  {Object.entries(test.probabilities)
                                    .sort(([, a], [, b]) => b - a)
                                    .map(([code, probability]) => (
                                      <div className="cardiaque-probability-row" key={code}>
                                        <span>{code} — {CLASSES[code]}</span>
                                        <strong>{formatPercent(probability)}</strong>
                                        <div className="cardiaque-probability-track"><span style={{ width: `${probability}%` }} /></div>
                                      </div>
                                    ))}
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {!isLoading && !error && history.length === 0 && (
            <div className="historique-cardiaque-empty-state">
              <div className="historique-cardiaque-empty-icon" aria-hidden="true">AI</div>
              <h3>Aucune analyse enregistrée</h3>
              <p>Les résultats de vos prochaines analyses ECG apparaîtront ici.</p>
              <button type="button" onClick={onBackToCardiaque}>Lancer une analyse</button>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

export default HistoriqueCardiaque;
