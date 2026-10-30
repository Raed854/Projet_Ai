import { Fragment, useEffect, useState } from 'react';
import './chest.css';
import './historiquechest.css';
import { CLASSES, ScoreGauge, formatPercent } from './chest';
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

function HistoriqueChest({ account, onBackToChest, onLogout, onSelectModule, selectedModule }) {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [openedId, setOpenedId] = useState(null);

  useEffect(() => {
    async function loadHistory() {
      try {
        const response = await fetch(`${BACKEND_API_URL}/chests?user_id=${account.id}`);
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

  const pneumonies = history.filter((test) => test.classe === 'PNEUMONIA').length;

  return (
    <main className="historique-chest-page">
      <SideBar onLogout={onLogout} onSelectModule={onSelectModule} selectedModule={selectedModule} />

      <section className="historique-chest-main">
        <header className="historique-chest-topbar">
          <div>
            <p className="historique-chest-eyebrow">Suivi médical</p>
            <h1>Historique des radiographies</h1>
            <p>Retrouvez toutes les radiographies thoraciques analysées sur votre compte.</p>
          </div>
          <button className="historique-chest-back" type="button" onClick={onBackToChest}>
            ← Nouvelle analyse
          </button>
        </header>

        <section className="historique-chest-card" aria-labelledby="historique-chest-title">
          <div className="historique-chest-card-heading">
            <div>
              <p className="historique-chest-eyebrow">Table chest</p>
              <h2 id="historique-chest-title">Vos analyses</h2>
            </div>
            <div className="historique-chest-counts">
              <span className="historique-chest-count">
                {history.length} analyse{history.length === 1 ? '' : 's'}
              </span>
              {pneumonies > 0 && (
                <span className="historique-chest-count historique-chest-count-alert">
                  {pneumonies} pneumonie{pneumonies === 1 ? '' : 's'}
                </span>
              )}
            </div>
          </div>

          {isLoading && <p className="historique-chest-loading">Chargement…</p>}
          {error && <p className="historique-chest-error" role="alert">{error}</p>}

          {!isLoading && !error && history.length > 0 && (
            <div className="historique-chest-table-wrapper">
              <table className="historique-chest-table">
                <thead>
                  <tr>
                    <th>N°</th>
                    <th>Image</th>
                    <th>Résultat</th>
                    <th>Score de pneumonie</th>
                    <th>Confiance</th>
                    <th>Seuil</th>
                    <th>Date du test</th>
                    <th>Modèle</th>
                    <th>Utilisateur</th>
                    <th>Détails</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((test) => {
                    const isOpen = openedId === test.id;
                    const classe = CLASSES[test.classe];
                    return (
                      <Fragment key={test.id}>
                        <tr>
                          <td>#{test.id}</td>
                          <td>
                            {test.image
                              ? <img className="historique-chest-thumb" src={test.image} alt={`Radiographie #${test.id}`} />
                              : '—'}
                          </td>
                          <td>
                            <span className={`chest-badge chest-badge-${test.classe}`}>
                              <span aria-hidden="true">{classe?.icon}</span>
                              {classe?.label || test.classe}
                            </span>
                          </td>
                          <td className={`chest-text-${test.classe}`}><strong>{formatPercent(test.score_pneumonie)}</strong></td>
                          <td>{formatPercent(test.confidence)}</td>
                          <td>{formatPercent(test.seuil)}</td>
                          <td>{formatTestDate(test.date_creation)}</td>
                          <td><code>{test.modele}</code></td>
                          <td>{account.prenom} {account.nom} (#{test.user_id})</td>
                          <td>
                            <button
                              className="historique-chest-toggle"
                              type="button"
                              onClick={() => setOpenedId(isOpen ? null : test.id)}
                              aria-expanded={isOpen}
                            >
                              {isOpen ? 'Masquer' : 'Afficher'}
                            </button>
                          </td>
                        </tr>
                        {isOpen && (
                          <tr className="historique-chest-details">
                            <td colSpan={10}>
                              <div className="historique-chest-details-grid">
                                {test.image && (
                                  <figure className="chest-analysed">
                                    <img src={test.image} alt={`Radiographie analysée #${test.id}`} />
                                    <figcaption>Image analysée (224 × 224)</figcaption>
                                  </figure>
                                )}
                                <div>
                                  <p className="chest-result-text">{classe?.text}</p>
                                  <ScoreGauge score={test.score_pneumonie} seuil={test.seuil} classe={test.classe} />
                                  <div className="historique-chest-probabilities">
                                    {Object.entries(test.probabilities).map(([code, probability]) => (
                                      <div key={code}>
                                        <small>{CLASSES[code]?.label || code}</small>
                                        <strong>{formatPercent(probability)}</strong>
                                      </div>
                                    ))}
                                  </div>
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
            <div className="historique-chest-empty-state">
              <div className="historique-chest-empty-icon" aria-hidden="true">AI</div>
              <h3>Aucune analyse enregistrée</h3>
              <p>Les résultats de vos prochaines radiographies apparaîtront ici.</p>
              <button type="button" onClick={onBackToChest}>Lancer une analyse</button>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

export default HistoriqueChest;
