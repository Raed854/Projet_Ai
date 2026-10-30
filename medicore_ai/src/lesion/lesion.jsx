import { useEffect, useState } from 'react';
import './lesion.css';
import '../component/result_modal.css';
import SideBar from '../component/side_bar/side_bar';

// Service Flask du modèle lésions (prédiction + enregistrement en table lesion)
const MODEL_API_URL = process.env.REACT_APP_LESION_API_URL || 'http://localhost:5001';
// Backend FastAPI (lecture de l'historique) : passe par le proxy React en dev
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

const VIGILANCE = {
  faible: {
    label: 'Vigilance faible',
    text: 'Le modèle ne détecte pas de signe de malignité, mais cela ne garantit rien.',
  },
  moderee: {
    label: 'Vigilance modérée',
    text: 'Le modèle hésite : une part non négligeable de la probabilité va vers une lésion suspecte. Un avis médical est conseillé en cas de doute.',
  },
  elevee: {
    label: 'Vigilance élevée',
    text: 'Le modèle détecte un type de lésion potentiellement malin ou précancéreux. Seul un dermatologue peut confirmer.',
  },
};

function formatDate(value) {
  return new Date(value).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' });
}

function Lesion({ account, onOpenHistory, onLogout, onSelectModule, selectedModule }) {
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
      const response = await fetch(`${BACKEND_API_URL}/lesions?user_id=${account.id}`);
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
      setError('Veuillez sélectionner une image de lésion au format JPG, JPEG ou PNG.');
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
      setError('Sélectionnez une image de lésion avant de lancer le test.');
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

      if (!responseData?.type || typeof responseData.confidence !== 'number') {
        throw new Error('La réponse de l’API ne contient pas un résultat valide.');
      }

      setResult(responseData);
      setShowResult(true);
      loadHistory();
    } catch (requestError) {
      setError(
        requestError.message === 'Failed to fetch'
          ? 'Impossible de contacter le modèle. Vérifiez que l’API lésions est démarrée sur le port 5001.'
          : requestError.message,
      );
    } finally {
      setIsLoading(false);
    }
  }

  const vigilance = result ? VIGILANCE[result.vigilance] : null;

  return (
    <main className="lesion-page">
      <SideBar onLogout={onLogout} onSelectModule={onSelectModule} selectedModule={selectedModule} />

      <section className="lesion-main">
        <header className="lesion-topbar">
          <div>
            <p className="lesion-eyebrow">IA médicale</p>
            <h1>Analyse des lésions cutanées</h1>
          </div>
          <button className="lesion-history-button" type="button" onClick={onOpenHistory}>
            Voir l’historique
          </button>
        </header>

        <div className="lesion-grid">
          <form className="lesion-form" onSubmit={handleSubmit}>
            <label className="lesion-image-upload" htmlFor="lesion-image">
              <span className="lesion-upload-icon" aria-hidden="true">↑</span>
              <strong>Importer une image de lésion</strong>
              <span>JPG, JPEG ou PNG · image dermoscopique de préférence</span>
              <input
                id="lesion-image"
                name="image"
                type="file"
                accept="image/jpeg,image/png"
                onChange={handleImageChange}
              />
            </label>

            {previewUrl && (
              <div className="lesion-image-preview">
                <img src={previewUrl} alt="Aperçu de la lésion sélectionnée" />
                <div><strong>{image.name}</strong><span>{Math.round(image.size / 1024)} Ko</span></div>
              </div>
            )}

            <div className="lesion-api-info">
              <span aria-hidden="true">✓</span>
              <span>L’image sera analysée par le modèle EfficientNet-B0 et le résultat sera enregistré dans votre historique.</span>
            </div>

            {error && <p className="lesion-api-error" role="alert">{error}</p>}

            <button className="lesion-submit" type="submit" disabled={isLoading}>
              {isLoading ? 'Test en cours…' : 'Tester'}
            </button>
          </form>

          {showResult && <div className="analysis-result-modal-backdrop" onClick={() => setShowResult(false)} />}
          <div className={`lesion-result${showResult ? ' analysis-result-modal' : ''}`} role={showResult ? 'dialog' : undefined} aria-modal={showResult ? 'true' : undefined}>
            <div className="lesion-result-header">
              <p className="lesion-eyebrow">Résultat du modèle</p>
              <h2>Diagnostic assisté</h2>
            </div>

            {result ? (
              <>
                <div className={`lesion-result-badge lesion-vigilance-${result.vigilance}`}>
                  {LABELS[result.type] || result.type}
                </div>
                <div className="lesion-result-metrics">
                  <div className="lesion-result-metric"><small>Classe prédite</small><strong>{result.type}</strong></div>
                  <div className="lesion-result-metric"><small>Confiance</small><strong>{result.confidence.toFixed(2)}%</strong></div>
                  <div className="lesion-result-metric"><small>Enregistré</small><strong>{result.lesion ? `#${result.lesion.id}` : '—'}</strong></div>
                </div>

                {result.gradcam_image && (
                  <div className="lesion-images">
                    <figure>
                      <img src={result.image} alt="Lésion analysée par le modèle" />
                      <figcaption>Image analysée</figcaption>
                    </figure>
                    <figure>
                      <img src={result.gradcam_image} alt="Carte Grad-CAM du modèle" />
                      <figcaption>Zone regardée par le modèle (Grad-CAM)</figcaption>
                    </figure>
                  </div>
                )}

                <div className="lesion-gauge">
                  <div className="lesion-gauge-head">
                    <span className={`lesion-vigilance-${result.vigilance}`}>{vigilance?.label}</span>
                    <span>{result.suspicion_score.toFixed(0)} %</span>
                  </div>
                  <div className="lesion-gauge-track">
                    <span className={`lesion-vigilance-${result.vigilance}`} style={{ width: `${result.suspicion_score}%` }} />
                  </div>
                  <p>{vigilance?.text}</p>
                  <p>Cohérence : {result.coherence} vues donnent le même résultat.</p>
                </div>

                <div className="lesion-probabilities-box">
                  <h3>Probabilités du modèle</h3>
                  {Object.entries(result.probabilities || {})
                    .sort(([, a], [, b]) => b - a)
                    .map(([code, probability]) => (
                      <div className="lesion-probability-row" key={code}>
                        <span>{LABELS[code] || code} ({code})</span>
                        <strong>{Number(probability).toFixed(2)}%</strong>
                        <div className="lesion-probability-track"><span style={{ width: `${probability}%` }} /></div>
                      </div>
                    ))}
                </div>
              </>
            ) : (
              <div className="lesion-empty-result">
                <div className="lesion-empty-icon">AI</div>
                <p>Les résultats du modèle apparaîtront ici après avoir cliqué sur « Tester ».</p>
              </div>
            )}

            <div className="lesion-history-box">
              <h3>Historique des analyses</h3>
              {historyError && <p className="lesion-api-error">{historyError}</p>}
              {!historyError && history.length === 0 && <p className="lesion-history-empty">Aucune analyse enregistrée.</p>}
              {history.map((item) => (
                <div className="lesion-history-row" key={item.id}>
                  <span>{formatDate(item.date_creation)}</span>
                  <strong>{LABELS[item.type] || item.type}</strong>
                  <small className={`lesion-vigilance-${item.vigilance}`}>{item.confidence.toFixed(2)}%</small>
                </div>
              ))}
            </div>
          </div>
        </div>

        <p className="lesion-disclaimer">
          Les pourcentages sont indicatifs et non calibrés (le score du mélanome est volontairement amplifié).
          Ce résultat ne remplace pas l’avis d’un dermatologue.
        </p>
      </section>
    </main>
  );
}

export default Lesion;
