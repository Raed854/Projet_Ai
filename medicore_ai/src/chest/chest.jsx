import { useEffect, useState } from 'react';
import './chest.css';
import SideBar from '../component/side_bar/side_bar';

// Service Flask du modèle chest (DenseNet121) : prédiction + enregistrement en table chest
const MODEL_API_URL = process.env.REACT_APP_CHEST_API_URL || 'http://localhost:5005';

export const CLASSES = {
  NORMAL: { label: 'Normal', text: 'Aucun signe de pneumonie détecté par le modèle.', icon: '✓' },
  PNEUMONIA: { label: 'Pneumonie', text: 'Le modèle détecte des signes compatibles avec une pneumonie. Seul un médecin peut confirmer.', icon: '!' },
};

export function formatPercent(value) {
  return typeof value === 'number'
    ? `${value.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} %`
    : '—';
}

// Jauge du score de pneumonie avec la position du seuil de décision
export function ScoreGauge({ score, seuil, classe }) {
  return (
    <div className="chest-gauge">
      <div className="chest-gauge-head">
        <span>Score de pneumonie</span>
        <strong className={`chest-text-${classe}`}>{formatPercent(score)}</strong>
      </div>
      <div className="chest-gauge-track">
        <span className={`chest-fill-${classe}`} style={{ width: `${score}%` }} />
        <i className="chest-gauge-seuil" style={{ left: `${seuil}%` }} aria-hidden="true" />
      </div>
      <div className="chest-gauge-scale">
        <span>0 % · Normal</span>
        <span>Seuil {formatPercent(seuil)}</span>
        <span>Pneumonie · 100 %</span>
      </div>
    </div>
  );
}

function Chest({ account, onOpenHistory, onLogout, onSelectModule, selectedModule }) {
  const [image, setImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

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
      setError('Veuillez sélectionner une radiographie au format JPG, JPEG ou PNG.');
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
      setError('Sélectionnez une radiographie thoracique avant de lancer le test.');
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

      if (!responseData?.classe || typeof responseData.score_pneumonie !== 'number') {
        throw new Error('La réponse de l’API ne contient pas un résultat valide.');
      }

      setResult(responseData);
    } catch (requestError) {
      setError(
        requestError.message === 'Failed to fetch'
          ? 'Impossible de contacter le modèle. Vérifiez que l’API chest est démarrée sur le port 5005.'
          : requestError.message,
      );
    } finally {
      setIsLoading(false);
    }
  }

  const classe = result ? CLASSES[result.classe] : null;

  return (
    <main className="chest-page">
      <SideBar onLogout={onLogout} onSelectModule={onSelectModule} selectedModule={selectedModule} />

      <section className="chest-main">
        <header className="chest-topbar">
          <div>
            <p className="chest-eyebrow">IA pneumologie</p>
            <h1>Détection de pneumonie (radiographie thoracique)</h1>
          </div>
          <button className="chest-history-button" type="button" onClick={onOpenHistory}>
            Voir l’historique
          </button>
        </header>

        <div className="chest-grid">
          <form className="chest-form" onSubmit={handleSubmit}>
            <label className="chest-upload" htmlFor="chest-image">
              <span className="chest-upload-icon" aria-hidden="true">↑</span>
              <strong>Importer une radiographie thoracique</strong>
              <span>JPG, JPEG ou PNG · vue de face de préférence</span>
              <input
                id="chest-image"
                name="image"
                type="file"
                accept="image/jpeg,image/png"
                onChange={handleImageChange}
              />
            </label>

            {previewUrl && (
              <div className="chest-preview">
                <img src={previewUrl} alt="Aperçu de la radiographie sélectionnée" />
                <div><strong>{image.name}</strong><span>{Math.round(image.size / 1024)} Ko</span></div>
              </div>
            )}

            <div className="chest-api-info">
              <span aria-hidden="true">✓</span>
              <span>La radiographie sera analysée par le modèle DenseNet121 et le résultat enregistré dans votre historique.</span>
            </div>

            {error && <p className="chest-api-error" role="alert">{error}</p>}

            <button className="chest-submit" type="submit" disabled={isLoading}>
              {isLoading ? 'Test en cours…' : 'Tester'}
            </button>
          </form>

          <div className="chest-result">
            <div className="chest-result-header">
              <p className="chest-eyebrow">Résultat du modèle</p>
              <h2>Diagnostic assisté</h2>
            </div>

            {result ? (
              <>
                <div className="chest-badges">
                  <span className={`chest-badge chest-badge-${result.classe}`}>
                    <span aria-hidden="true">{classe.icon}</span>
                    {classe.label}
                  </span>
                  {result.chest && <span className="chest-saved">Enregistré #{result.chest.id}</span>}
                </div>
                <p className="chest-result-text">{classe.text}</p>

                <div className="chest-metrics">
                  <div className="chest-metric"><small>Classe prédite</small><strong>{result.classe}</strong></div>
                  <div className="chest-metric"><small>Confiance</small><strong>{formatPercent(result.confidence)}</strong></div>
                  <div className="chest-metric"><small>Seuil de décision</small><strong>{formatPercent(result.seuil)}</strong></div>
                </div>

                <ScoreGauge score={result.score_pneumonie} seuil={result.seuil} classe={result.classe} />

                {result.image && (
                  <figure className="chest-analysed">
                    <img src={result.image} alt="Radiographie analysée par le modèle" />
                    <figcaption>Image analysée (224 × 224) · {result.modele}</figcaption>
                  </figure>
                )}
              </>
            ) : (
              <div className="chest-empty-result">
                <div className="chest-empty-icon">AI</div>
                <p>Les résultats du modèle apparaîtront ici après avoir cliqué sur « Tester ».</p>
              </div>
            )}
          </div>
        </div>

        <p className="chest-disclaimer">
          Outil d’apprentissage et de recherche : ce résultat ne constitue pas un diagnostic médical.
        </p>
      </section>
    </main>
  );
}

export default Chest;
