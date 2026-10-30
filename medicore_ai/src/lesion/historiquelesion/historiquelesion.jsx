import { Fragment, useEffect, useState } from 'react';
import './historiquelesion.css';
import SideBar from '../../component/side_bar/side_bar';

const BACKEND_API_URL = process.env.REACT_APP_BACKEND_API_URL || '';

const LABELS = {
  akiec: 'Kératose actinique',
  bcc: 'Carcinome basocellulaire',
  bkl: 'Kératose bénigne',
  df: 'Dermatofibrome',
  mel: 'Mélanome',
  nv: 'Naevus',
  vasc: 'Lésion vasculaire',
};

const VIGILANCE_LABELS = {
  faible: 'Faible',
  moderee: 'Modérée',
  elevee: 'Élevée',
};

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
  return typeof value === 'number' ? `${value.toFixed(2)} %` : '—';
}

function HistoriqueLesion({ account, onBackToLesion, onLogout, onSelectModule, selectedModule }) {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [openedId, setOpenedId] = useState(null);

  useEffect(() => {
    async function loadHistory() {
      try {
        const response = await fetch(`${BACKEND_API_URL}/lesions?user_id=${account.id}`);
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

  return (
    <main className="historique-lesion-page">
      <SideBar onLogout={onLogout} onSelectModule={onSelectModule} selectedModule={selectedModule} />

      <section className="historique-lesion-main">
        <header className="historique-lesion-topbar">
          <div>
            <p className="historique-lesion-eyebrow">Suivi médical</p>
            <h1>Historique des lésions</h1>
            <p>Retrouvez tous les résultats des analyses de lésions réalisées sur votre compte.</p>
          </div>
          <button className="historique-lesion-back" type="button" onClick={onBackToLesion}>
            ← Nouvelle analyse
          </button>
        </header>

        <section className="historique-lesion-card" aria-labelledby="historique-lesion-title">
          <div className="historique-lesion-card-heading">
            <div>
              <p className="historique-lesion-eyebrow">Table lesion</p>
              <h2 id="historique-lesion-title">Vos analyses</h2>
            </div>
            <span className="historique-lesion-count">
              {history.length} analyse{history.length === 1 ? '' : 's'}
            </span>
          </div>

          {isLoading && <p className="historique-lesion-loading">Chargement…</p>}
          {error && <p className="historique-lesion-error" role="alert">{error}</p>}

          {!isLoading && !error && history.length > 0 && (
            <div className="historique-lesion-table-wrapper">
              <table className="historique-lesion-table">
                <thead>
                  <tr>
                    <th>N°</th>
                    <th>Image</th>
                    <th>Type</th>
                    <th>Lésion détectée</th>
                    <th>Confiance</th>
                    <th>Score de suspicion</th>
                    <th>Vigilance</th>
                    <th>Date du test</th>
                    <th>Utilisateur</th>
                    <th>Détails</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((test) => (
                    <Fragment key={test.id}>
                      <tr>
                        <td>#{test.id}</td>
                        <td>
                          {test.gradcam_image || test.image ? (
                            <img
                              className="historique-lesion-thumb"
                              src={test.gradcam_image || test.image}
                              alt={`Analyse #${test.id}`}
                            />
                          ) : '—'}
                        </td>
                        <td><code>{test.type}</code></td>
                        <td>
                          <span className={`historique-lesion-badge historique-lesion-${test.vigilance}`}>
                            {LABELS[test.type] || test.type}
                          </span>
                        </td>
                        <td>{formatPercent(test.confidence)}</td>
                        <td>{formatPercent(test.suspicion_score)}</td>
                        <td>
                          <span className={`historique-lesion-vigilance historique-lesion-${test.vigilance}`}>
                            {VIGILANCE_LABELS[test.vigilance] || test.vigilance}
                          </span>
                        </td>
                        <td>{formatTestDate(test.date_creation)}</td>
                        <td>{account.prenom} {account.nom} (#{test.user_id})</td>
                        <td>
                          {test.probabilities || test.image ? (
                            <button
                              className="historique-lesion-toggle"
                              type="button"
                              onClick={() => setOpenedId(openedId === test.id ? null : test.id)}
                              aria-expanded={openedId === test.id}
                            >
                              {openedId === test.id ? 'Masquer' : 'Afficher'}
                            </button>
                          ) : '—'}
                        </td>
                      </tr>
                      {openedId === test.id && (
                        <tr className="historique-lesion-details">
                          <td colSpan={10}>
                            {(test.image || test.gradcam_image) && (
                              <div className="historique-lesion-images">
                                {test.image && (
                                  <figure>
                                    <img src={test.image} alt={`Lésion analysée #${test.id}`} />
                                    <figcaption>Image analysée</figcaption>
                                  </figure>
                                )}
                                {test.gradcam_image && (
                                  <figure>
                                    <img src={test.gradcam_image} alt={`Carte Grad-CAM #${test.id}`} />
                                    <figcaption>Zone regardée par le modèle (Grad-CAM)</figcaption>
                                  </figure>
                                )}
                              </div>
                            )}
                            <div className="historique-lesion-probabilities">
                              {Object.entries(test.probabilities || {})
                                .sort(([, a], [, b]) => b - a)
                                .map(([code, probability]) => (
                                  <div className="historique-lesion-probability" key={code}>
                                    <span>{LABELS[code] || code} ({code})</span>
                                    <strong>{formatPercent(probability)}</strong>
                                    <div className="historique-lesion-track">
                                      <span style={{ width: `${probability}%` }} />
                                    </div>
                                  </div>
                                ))}
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!isLoading && !error && history.length === 0 && (
            <div className="historique-lesion-empty-state">
              <div className="historique-lesion-empty-icon" aria-hidden="true">AI</div>
              <h3>Aucune analyse enregistrée</h3>
              <p>Les résultats de vos prochaines analyses de lésions apparaîtront ici.</p>
              <button type="button" onClick={onBackToLesion}>Lancer une analyse</button>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

export default HistoriqueLesion;
