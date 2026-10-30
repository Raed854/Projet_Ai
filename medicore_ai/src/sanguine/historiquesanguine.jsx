import { Fragment, useEffect, useState } from 'react';
import './sanguine.css';
import './historiquesanguine.css';
import { DiagnosticResult } from './sanguine';
import { PARAMETRES, formatPercent, libelleDiagnostic } from './parametres';
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

function HistoriqueSanguine({ account, onBackToSanguine, onLogout, onSelectModule, selectedModule }) {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [openedId, setOpenedId] = useState(null);

  useEffect(() => {
    async function loadHistory() {
      try {
        const response = await fetch(`${BACKEND_API_URL}/sanguines?user_id=${account.id}`);
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

  const anomalies = history.filter((test) => test.diagnostic !== 'Healthy').length;

  return (
    <main className="historique-sanguine-page">
      <SideBar onLogout={onLogout} onSelectModule={onSelectModule} selectedModule={selectedModule} />

      <section className="historique-sanguine-main">
        <header className="historique-sanguine-topbar">
          <div>
            <p className="historique-sanguine-eyebrow">Suivi médical</p>
            <h1>Historique des NFS</h1>
            <p>Retrouvez tous les résultats des analyses sanguines réalisées sur votre compte.</p>
          </div>
          <button className="historique-sanguine-back" type="button" onClick={onBackToSanguine}>
            ← Nouvelle analyse
          </button>
        </header>

        <section className="historique-sanguine-card" aria-labelledby="historique-sanguine-title">
          <div className="historique-sanguine-card-heading">
            <div>
              <p className="historique-sanguine-eyebrow">Table sanguine</p>
              <h2 id="historique-sanguine-title">Vos analyses</h2>
            </div>
            <div className="historique-sanguine-counts">
              <span className="historique-sanguine-count">
                {history.length} analyse{history.length === 1 ? '' : 's'}
              </span>
              {anomalies > 0 && (
                <span className="historique-sanguine-count historique-sanguine-count-alert">
                  {anomalies} anomalie{anomalies === 1 ? '' : 's'}
                </span>
              )}
            </div>
          </div>

          {isLoading && <p className="historique-sanguine-loading">Chargement…</p>}
          {error && <p className="historique-sanguine-error" role="alert">{error}</p>}

          {!isLoading && !error && history.length > 0 && (
            <div className="historique-sanguine-table-wrapper">
              <table className="historique-sanguine-table">
                <thead>
                  <tr>
                    <th>N°</th>
                    <th>Date du test</th>
                    <th>Diagnostic prédit</th>
                    <th>Confiance</th>
                    <th>Paramètres saisis</th>
                    <th>Complétés (médiane)</th>
                    <th>Modèle</th>
                    <th>Utilisateur</th>
                    <th>Détails</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((test) => {
                    const isOpen = openedId === test.id;
                    const sain = test.diagnostic === 'Healthy';
                    return (
                      <Fragment key={test.id}>
                        <tr>
                          <td>#{test.id}</td>
                          <td>{formatTestDate(test.date_creation)}</td>
                          <td>
                            <span className={`sanguine-diagnostic ${sain ? 'sanguine-diagnostic-sain' : 'sanguine-diagnostic-anomalie'}`}>
                              <span aria-hidden="true">{sain ? '✓' : '!'}</span>
                              {libelleDiagnostic(test.diagnostic)}
                            </span>
                          </td>
                          <td>{formatPercent(test.confidence)}</td>
                          <td>{Object.keys(test.valeurs).length} / {PARAMETRES.length}</td>
                          <td>
                            {test.parametres_completes.length > 0
                              ? <span title={test.parametres_completes.join(', ')}>{test.parametres_completes.length}</span>
                              : 'Aucun'}
                          </td>
                          <td><code>{test.modele}</code></td>
                          <td>{account.prenom} {account.nom} (#{test.user_id})</td>
                          <td>
                            <button
                              className="historique-sanguine-toggle"
                              type="button"
                              onClick={() => setOpenedId(isOpen ? null : test.id)}
                              aria-expanded={isOpen}
                            >
                              {isOpen ? 'Masquer' : 'Afficher'}
                            </button>
                          </td>
                        </tr>
                        {isOpen && (
                          <tr className="historique-sanguine-details">
                            <td colSpan={9}>
                              <DiagnosticResult analyse={test} />
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
            <div className="historique-sanguine-empty-state">
              <div className="historique-sanguine-empty-icon" aria-hidden="true">AI</div>
              <h3>Aucune analyse enregistrée</h3>
              <p>Les résultats de vos prochaines analyses sanguines apparaîtront ici.</p>
              <button type="button" onClick={onBackToSanguine}>Lancer une analyse</button>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

export default HistoriqueSanguine;
