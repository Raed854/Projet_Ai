import { useEffect, useState } from 'react';
import './alzheimer.css';
import '../component/result_modal.css';
import SideBar from '../component/side_bar/side_bar';

// Service Flask du modèle (prédiction + enregistrement en table alzheimer)
const MODEL_API_URL = process.env.REACT_APP_ALZHEIMER_API_URL || 'http://localhost:5000';
// Backend FastAPI (lecture de l'historique) : passe par le proxy React en dev
const BACKEND_API_URL = process.env.REACT_APP_BACKEND_API_URL || '';

function formatDate(value) {
  return new Date(value).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' });
}

function Alzheimer({ account, onOpenHistory, onLogout, onSelectModule, selectedModule }) {
  const [image, setImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [historyError, setHistoryError] = useState('');
  const [showResult, setShowResult] = useState(false);

  async function loadHistory() {
    try {
      const response = await fetch(`${BACKEND_API_URL}/alzheimers?user_id=${account.id}`);
      if (!response.ok) {
        throw new Error(`Statut ${response.status}`);
      }
      const data = await response.json();
      setHistory([...data].reverse());
      setHistoryError('');
    } catch (requestError) {
      setHistoryError('Impossible de charger l’historique depuis le backend (port 8000).');
    }
  }

  useEffect(() => {
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [account.id]);

  useEffect(() => () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
  }, [previewUrl]);

  function handleImageChange(event) {
    const selectedImage = event.target.files[0];
    setError('');
    setResult(null);

    if (!selectedImage) {
      setImage(null);
      setPreviewUrl('');
      return;
    }

    if (!selectedImage.type.startsWith('image/')) {
      setImage(null);
      setPreviewUrl('');
      setError('Veuillez sélectionner une image IRM au format JPG, JPEG ou PNG.');
      return;
    }

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setImage(selectedImage);
    setPreviewUrl(URL.createObjectURL(selectedImage));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!image) {
      setError('Sélectionnez une image IRM avant de lancer l’analyse.');
      return;
    }

    const formData = new FormData();
    formData.append('image', image);
    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${MODEL_API_URL}/api/users/${account.id}/image`, {
        method: 'POST',
        body: formData,
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

      if (!responseData?.etatIrm || typeof responseData.confidence !== 'number') {
        throw new Error('La réponse de l’API ne contient pas un résultat valide.');
      }

      setResult(responseData);
      setShowResult(true);
      loadHistory();
    } catch (requestError) {
      setError(
        requestError.message ||
        'Impossible de contacter le modèle. Vérifiez que l’API Flask est démarrée sur le port 5000.',
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="alzheimer-page">
      <SideBar onLogout={onLogout} onSelectModule={onSelectModule} selectedModule={selectedModule} />

      <section className="alzheimer-main">
        <header className="alzheimer-topbar">
          <div>
            <p className="alzheimer-eyebrow">IA médicale</p>
            <h1>Analyse de la maladie d’Alzheimer</h1>
          </div>
          <button className="history-button" type="button" onClick={onOpenHistory}>
            Voir l’historique
          </button>
        </header>

        <div className="alzheimer-grid">
          <form className="alzheimer-form" onSubmit={handleSubmit}>
            <label className="irm-upload" htmlFor="irm-image">
              <span className="upload-icon" aria-hidden="true">↑</span>
              <strong>Importer une image IRM</strong>
              <span>JPG, JPEG ou PNG · sélectionnez une image cérébrale</span>
              <input
                id="irm-image"
                name="image"
                type="file"
                accept="image/jpeg,image/png"
                onChange={handleImageChange}
              />
            </label>

            {previewUrl && (
              <div className="irm-preview">
                <img src={previewUrl} alt="Aperçu de l'image IRM sélectionnée" />
                <div><strong>{image.name}</strong><span>{Math.round(image.size / 1024)} Ko</span></div>
              </div>
            )}

            <div className="api-info">
              <span aria-hidden="true">✓</span>
              <span>Cette image sera analysée par le modèle ResNet-18 via l’API Alzheimer.</span>
            </div>

            {error && <p className="api-error" role="alert">{error}</p>}

            <button className="alzheimer-submit" type="submit" disabled={isLoading}>
              {isLoading ? 'Analyse en cours…' : 'Envoyer l’image au modèle'}
            </button>
          </form>

          {showResult && <div className="analysis-result-modal-backdrop" onClick={() => setShowResult(false)} />}
          <div className={`alzheimer-result${showResult ? ' analysis-result-modal' : ''}`} role={showResult ? 'dialog' : undefined} aria-modal={showResult ? 'true' : undefined}>
            <div className="result-header">
              <p className="alzheimer-eyebrow">Résultat du modèle</p>
              <h2>Diagnostic assisté</h2>
            </div>

            {result ? (
              <>
                <div className="result-badge">{result.etatIrm}</div>
                <div className="result-metrics">
                  <div className="result-metric"><small>Classe prédite</small><strong>{result.etatIrm}</strong></div>
                  <div className="result-metric"><small>Confiance</small><strong>{result.confidence.toFixed(2)}%</strong></div>
                  <div className="result-metric"><small>Enregistré</small><strong>{result.alzheimer ? `#${result.alzheimer.id}` : '—'}</strong></div>
                </div>
                <div className="probabilities-box">
                  <h3>Probabilités du modèle</h3>
                  {Object.entries(result.allProbabilities || {}).map(([label, probability]) => (
                    <div className="probability-row" key={label}>
                      <span>{label}</span>
                      <strong>{Number(probability).toFixed(2)}%</strong>
                      <div className="probability-track"><span style={{ width: `${probability}%` }} /></div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="empty-result">
                <div className="empty-icon">AI</div>
                <p>Les résultats du modèle apparaîtront ici après soumission du formulaire.</p>
              </div>
            )}

            <div className="history-box">
              <h3>Historique des analyses</h3>
              {historyError && <p className="api-error">{historyError}</p>}
              {!historyError && history.length === 0 && <p className="history-empty">Aucune analyse enregistrée.</p>}
              {history.map((item) => (
                <div className="history-row" key={item.id}>
                  <span>{formatDate(item.date_creation)}</span>
                  <strong>{item.type}</strong>
                  <small>{typeof item.confidence === 'number' ? `${item.confidence.toFixed(2)}%` : '—'}</small>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

export default Alzheimer;
