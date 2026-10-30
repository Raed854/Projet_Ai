import { useEffect, useState } from 'react';
import './hsitoriquealzeimer.css';
import SideBar from '../../component/side_bar/side_bar';

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

function HistoriqueAlzheimer({ account, onBackToAlzheimer, onLogout, onSelectModule, selectedModule }) {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadHistory() {
      try {
        const response = await fetch(`${BACKEND_API_URL}/alzheimers?user_id=${account.id}`);
        if (!response.ok) {
          throw new Error(`Statut ${response.status}`);
        }

        const data = await response.json();
        const records = Array.isArray(data) ? data : data?.items;
        if (!Array.isArray(records)) {
          throw new Error('Format de réponse invalide');
        }

        setHistory([...records].reverse());
      } catch (requestError) {
        setError('Impossible de charger l’historique depuis le backend.');
      }
    }

    loadHistory();
  }, [account.id]);

  return (
    <main className="history-page">
      <SideBar onLogout={onLogout} onSelectModule={onSelectModule} selectedModule={selectedModule} />

      <section className="history-main">
        <header className="history-topbar">
          <div>
            <p className="history-eyebrow">Suivi médical</p>
            <h1>Historique Alzheimer</h1>
            <p>Retrouvez les résultats des analyses réalisées sur votre compte.</p>
          </div>
          <button className="history-back" type="button" onClick={onBackToAlzheimer}>
            ← Nouvelle analyse
          </button>
        </header>

        <section className="history-card" aria-labelledby="history-table-title">
          <div className="history-card-heading">
            <div>
              <p className="history-eyebrow">Résultats enregistrés</p>
              <h2 id="history-table-title">Vos tests</h2>
            </div>
            <span className="history-count">{history.length} test{history.length === 1 ? '' : 's'}</span>
          </div>

          {error && <p className="history-error" role="alert">{error}</p>}
          {!error && history.length > 0 && (
            <div className="history-table-wrapper">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>État détecté</th>
                    <th>Date du test</th>
                    <th>Nom</th>
                    <th>Prénom</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((test) => (
                    <tr key={test.id}>
                      <td><span className="state-badge">{test.type || test.etatIrm || '—'}</span></td>
                      <td>{formatTestDate(test.date_creation || test.dateTest)}</td>
                      <td>{account.nom}</td>
                      <td>{account.prenom}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {!error && history.length === 0 && (
            <div className="history-empty-state">
              <div className="history-empty-icon" aria-hidden="true">AI</div>
              <h3>Aucun test enregistré</h3>
              <p>Les résultats de vos prochaines analyses apparaîtront ici.</p>
              <button type="button" onClick={onBackToAlzheimer}>Lancer une analyse</button>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

export default HistoriqueAlzheimer;
