import { useState } from 'react';
import './cardiaque.css';
import '../component/result_modal.css';
import SideBar from '../component/side_bar/side_bar';

// Service Flask du modèle ECG (interface_ecg/web_app.py) : prédiction + enregistrement en table cardiaque
const MODEL_API_URL = process.env.REACT_APP_CARDIAQUE_API_URL || 'http://localhost:5004';

const SIGNAL_LENGTH = 187;

export const CLASSES = {
  N: 'Battement normal',
  S: 'Battement supraventriculaire',
  V: 'Contraction ventriculaire prématurée',
  F: 'Fusion normale et ventriculaire',
  Q: 'Battement non classifiable',
};

// Index MIT-BIH (188e colonne d'un CSV) -> code de classe
const CODES_PAR_INDEX = ['N', 'S', 'V', 'F', 'Q'];

// interface_ecg/test_simple.csv (battement normal, 187 valeurs)
const EXEMPLE = '0.98,0.91,0.72,0.46,0.19,-0.11,-0.37,-0.60,-0.77,-0.88,-0.94,-0.93,-0.86,-0.75,-0.59,-0.41,-0.20,0.01,0.22,0.41,0.57,0.71,0.80,0.86,0.89,0.88,0.85,0.78,0.69,0.59,0.46,0.33,0.19,0.06,-0.06,-0.17,-0.26,-0.34,-0.39,-0.42,-0.44,-0.44,-0.42,-0.40,-0.36,-0.32,-0.27,-0.22,-0.17,-0.12,-0.07,-0.03,0.01,0.04,0.07,0.09,0.11,0.13,0.14,0.14,0.14,0.13,0.12,0.11,0.10,0.08,0.07,0.05,0.03,0.01,-0.01,-0.03,-0.05,-0.06,-0.08,-0.09,-0.10,-0.10,-0.11,-0.11,-0.11,-0.11,-0.10,-0.10,-0.09,-0.08,-0.07,-0.06,-0.05,-0.04,-0.03,-0.02,-0.01,-0.01,0.00,0.01,0.02,0.03,0.04,0.04,0.05,0.05,0.06,0.06,0.06,0.06,0.06,0.06,0.06,0.05,0.05,0.05,0.04,0.04,0.03,0.03,0.02,0.02,0.01,0.01,0.00,0.00,-0.01,-0.01,-0.01,-0.02,-0.02,-0.02,-0.02,-0.03,-0.03,-0.03,-0.03,-0.03,-0.03,-0.03,-0.03,-0.03,-0.02,-0.02,-0.02,-0.02,-0.02,-0.01,-0.01,-0.01,-0.01,-0.01,-0.01,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00';

function parseValues(text) {
  return text
    .split(/[\s,;]+/)
    .filter((value) => value.trim() !== '')
    .map(Number);
}

function formatPercent(value, digits = 2) {
  return `${value.toLocaleString('fr-FR', { minimumFractionDigits: digits, maximumFractionDigits: digits })} %`;
}

export function SignalChart({ signal }) {
  const [hoverIndex, setHoverIndex] = useState(null);
  const width = 640;
  const height = 220;
  const pad = { top: 14, right: 16, bottom: 36, left: 44 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;

  const min = Math.min(...signal);
  const max = Math.max(...signal);
  const span = max - min || 1;
  const yMin = min - span * 0.08;
  const yMax = max + span * 0.08;
  const sx = (i) => pad.left + (i / (signal.length - 1)) * innerW;
  const sy = (v) => pad.top + innerH - ((v - yMin) / (yMax - yMin)) * innerH;
  const path = signal.map((v, i) => `${i ? 'L' : 'M'}${sx(i).toFixed(1)},${sy(v).toFixed(1)}`).join(' ');
  const yTicks = [yMin, (yMin + yMax) / 2, yMax];
  const xTicks = [0, 50, 100, 150, signal.length - 1];

  function handleMove(event) {
    const box = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - box.left) / box.width) * width;
    const index = Math.round(((x - pad.left) / innerW) * (signal.length - 1));
    setHoverIndex(Math.min(signal.length - 1, Math.max(0, index)));
  }

  return (
    <figure className="cardiaque-chart">
      <figcaption>Signal ECG analysé (1 battement, {signal.length} échantillons)</figcaption>
      <div className="cardiaque-chart-frame">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label={`Signal ECG de ${signal.length} valeurs, de ${min.toFixed(2)} à ${max.toFixed(2)}`}
          onMouseMove={handleMove}
          onMouseLeave={() => setHoverIndex(null)}
        >
          {yTicks.map((t) => (
            <g key={t}>
              <line className="cardiaque-chart-grid" x1={pad.left} x2={width - pad.right} y1={sy(t)} y2={sy(t)} />
              <text className="cardiaque-chart-tick" x={pad.left - 8} y={sy(t) + 4} textAnchor="end">{t.toFixed(2)}</text>
            </g>
          ))}
          {xTicks.map((t) => (
            <text key={t} className="cardiaque-chart-tick" x={sx(t)} y={height - pad.bottom + 18} textAnchor="middle">{t}</text>
          ))}
          <text className="cardiaque-chart-axis" x={pad.left + innerW / 2} y={height - 2} textAnchor="middle">Échantillon</text>
          <path className="cardiaque-chart-line" d={path} />
          {hoverIndex !== null && (
            <>
              <line className="cardiaque-chart-crosshair" x1={sx(hoverIndex)} x2={sx(hoverIndex)} y1={pad.top} y2={pad.top + innerH} />
              <circle className="cardiaque-chart-dot" cx={sx(hoverIndex)} cy={sy(signal[hoverIndex])} r={5} />
            </>
          )}
        </svg>
        {hoverIndex !== null && (
          <div
            className="cardiaque-chart-tooltip"
            style={{ left: `${(sx(hoverIndex) / width) * 100}%`, top: `${(sy(signal[hoverIndex]) / height) * 100}%` }}
          >
            <span>Échantillon {hoverIndex}</span>
            <strong>Amplitude {signal[hoverIndex].toFixed(3)}</strong>
          </div>
        )}
      </div>
    </figure>
  );
}

function Cardiaque({ account, onOpenHistory, onLogout, onSelectModule, selectedModule }) {
  const [signalText, setSignalText] = useState('');
  const [classeReelle, setClasseReelle] = useState('');
  const [csvRows, setCsvRows] = useState([]);
  const [csvName, setCsvName] = useState('');
  const [csvIndex, setCsvIndex] = useState(0);
  const [result, setResult] = useState(null);
  const [signal, setSignal] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showResult, setShowResult] = useState(false);

  const values = parseValues(signalText);
  const countIsValid = values.length === SIGNAL_LENGTH;

  function selectCsvRow(rows, index) {
    const row = rows[index];
    setCsvIndex(index);
    setSignalText(row.slice(0, SIGNAL_LENGTH).map((v) => v.toFixed(2)).join(', '));
    setClasseReelle(row.length === SIGNAL_LENGTH + 1 ? CODES_PAR_INDEX[row[SIGNAL_LENGTH]] || '' : '');
  }

  function handleCsvChange(event) {
    const file = event.target.files[0];
    setError('');
    setCsvRows([]);
    setCsvName('');
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const rows = String(reader.result)
        .split(/\r?\n/)
        .filter((line) => line.trim() !== '')
        .map((line) => line.split(/[,;]/).map(Number))
        .filter((row) => row.every(Number.isFinite));
      const valid = rows.filter((row) => row.length === SIGNAL_LENGTH || row.length === SIGNAL_LENGTH + 1);

      if (valid.length === 0) {
        setError(`Aucune ligne valide dans ${file.name} : chaque ligne doit contenir ${SIGNAL_LENGTH} valeurs (ou ${SIGNAL_LENGTH + 1} avec la classe réelle).`);
        return;
      }
      if (valid.length < rows.length) {
        setError(`${rows.length - valid.length} ligne(s) ignorée(s) : nombre de valeurs différent de ${SIGNAL_LENGTH}.`);
      }
      setCsvRows(valid);
      setCsvName(file.name);
      selectCsvRow(valid, 0);
    };
    reader.readAsText(file);
    event.target.value = '';
  }

  function loadExample() {
    setSignalText(EXEMPLE.split(',').join(', '));
    setClasseReelle('');
    setCsvRows([]);
    setCsvName('');
    setError('');
  }

  function resetForm() {
    setSignalText('');
    setClasseReelle('');
    setCsvRows([]);
    setCsvName('');
    setResult(null);
    setSignal(null);
    setError('');
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (values.some((value) => !Number.isFinite(value))) {
      setError('Le signal ne doit contenir que des nombres (séparés par des virgules, espaces ou retours à la ligne).');
      return;
    }
    if (!countIsValid) {
      setError(`Le signal doit contenir exactement ${SIGNAL_LENGTH} valeurs (${values.length} saisies).`);
      return;
    }

    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${MODEL_API_URL}/api/users/${account.id}/cardiaque`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signal: values, classe_reelle: classeReelle || null }),
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

      if (!responseData?.classe || typeof responseData.confidence !== 'number') {
        throw new Error('La réponse de l’API ne contient pas un résultat valide.');
      }

      setResult(responseData);
      setShowResult(true);
      setSignal(values);
    } catch (requestError) {
      setError(
        requestError.message === 'Failed to fetch'
          ? 'Impossible de contacter le modèle ECG. Vérifiez que l’API est démarrée sur le port 5004.'
          : requestError.message,
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="cardiaque-page">
      <SideBar onLogout={onLogout} onSelectModule={onSelectModule} selectedModule={selectedModule} />

      <section className="cardiaque-main">
        <header className="cardiaque-topbar">
          <div>
            <p className="cardiaque-eyebrow">IA cardiologie</p>
            <h1>Analyse du rythme cardiaque (ECG)</h1>
          </div>
          <button className="cardiaque-history-button" type="button" onClick={onOpenHistory}>
            Voir l’historique
          </button>
        </header>

        <div className="cardiaque-grid">
          <form className="cardiaque-form" onSubmit={handleSubmit}>
            <div className="cardiaque-section-head">
              <h2>Signal ECG</h2>
              <div className="cardiaque-head-actions">
                <button type="button" className="cardiaque-link-button" onClick={loadExample}>Charger l’exemple</button>
                <button type="button" className="cardiaque-link-button" onClick={resetForm}>Vider</button>
              </div>
            </div>

            <label className="cardiaque-field" htmlFor="cardiaque-signal">
              {SIGNAL_LENGTH} valeurs d’un battement, séparées par des virgules, espaces ou retours à la ligne
              <textarea
                id="cardiaque-signal"
                rows={8}
                placeholder="0.98, 0.91, 0.72, 0.46, …"
                value={signalText}
                onChange={(event) => setSignalText(event.target.value)}
              />
            </label>
            <p className={`cardiaque-counter ${signalText && !countIsValid ? 'cardiaque-counter-bad' : ''}`}>
              {values.length} / {SIGNAL_LENGTH} valeurs {countIsValid ? '✓' : ''}
            </p>

            <div className="cardiaque-csv">
              <label className="cardiaque-csv-button" htmlFor="cardiaque-csv">
                Importer un fichier CSV
                <input id="cardiaque-csv" type="file" accept=".csv,text/csv" onChange={handleCsvChange} />
              </label>
              <span>Format MIT-BIH : une ligne = un battement ({SIGNAL_LENGTH} valeurs, + classe réelle en option).</span>
            </div>

            {csvRows.length > 0 && (
              <label className="cardiaque-field">
                Battement de « {csvName} » à analyser ({csvRows.length} ligne{csvRows.length > 1 ? 's' : ''})
                <select value={csvIndex} onChange={(event) => selectCsvRow(csvRows, Number(event.target.value))}>
                  {csvRows.map((row, index) => (
                    <option key={index} value={index}>
                      Ligne {index + 1}{row.length === SIGNAL_LENGTH + 1 ? ` — classe réelle ${CODES_PAR_INDEX[row[SIGNAL_LENGTH]] || '?'}` : ''}
                    </option>
                  ))}
                </select>
              </label>
            )}

            <label className="cardiaque-field">
              Classe réelle (optionnel, si connue)
              <select value={classeReelle} onChange={(event) => setClasseReelle(event.target.value)}>
                <option value="">Inconnue</option>
                {Object.entries(CLASSES).map(([code, label]) => (
                  <option key={code} value={code}>{code} — {label}</option>
                ))}
              </select>
            </label>

            <div className="cardiaque-api-info">
              <span aria-hidden="true">✓</span>
              <span>Le battement sera classé par le CNN 1D et le résultat enregistré dans votre historique.</span>
            </div>

            {error && <p className="cardiaque-api-error" role="alert">{error}</p>}

            <button className="cardiaque-submit" type="submit" disabled={isLoading}>
              {isLoading ? 'Test en cours…' : 'Tester'}
            </button>
          </form>

          {showResult && <div className="analysis-result-modal-backdrop" onClick={() => setShowResult(false)} />}
          <div className={`cardiaque-result${showResult ? ' analysis-result-modal' : ''}`} role={showResult ? 'dialog' : undefined} aria-modal={showResult ? 'true' : undefined}>
            <div className="cardiaque-result-header">
              <p className="cardiaque-eyebrow">Résultat du modèle</p>
              <h2>Classification du battement</h2>
            </div>

            {result ? (
              <>
                <div className="cardiaque-badges">
                  <span className={`cardiaque-classe-badge ${result.classe === 'N' ? 'cardiaque-normal' : 'cardiaque-anormal'}`}>
                    <span aria-hidden="true">{result.classe === 'N' ? '✓' : '!'}</span>
                    {result.classe} — {CLASSES[result.classe]}
                  </span>
                  {result.cardiaque && <span className="cardiaque-saved">Enregistré #{result.cardiaque.id}</span>}
                </div>

                <div className="cardiaque-metrics">
                  <div className="cardiaque-metric"><small>Classe prédite</small><strong>{result.classe}</strong></div>
                  <div className="cardiaque-metric"><small>Confiance</small><strong>{formatPercent(result.confidence)}</strong></div>
                  <div className="cardiaque-metric">
                    <small>Classe réelle</small>
                    <strong>{result.classe_reelle || '—'}</strong>
                    {result.prediction_correcte !== null && (
                      <span className={result.prediction_correcte ? 'cardiaque-correct' : 'cardiaque-incorrect'}>
                        {result.prediction_correcte ? '✓ Correct' : '✕ Incorrect'}
                      </span>
                    )}
                  </div>
                </div>

                <div className="cardiaque-box">
                  <h3>Probabilités par classe</h3>
                  {Object.entries(result.probabilities)
                    .sort(([, a], [, b]) => b - a)
                    .map(([code, probability]) => (
                      <div className="cardiaque-probability-row" key={code}>
                        <span>{code} — {CLASSES[code]}</span>
                        <strong>{formatPercent(probability)}</strong>
                        <div className="cardiaque-probability-track"><span style={{ width: `${probability}%` }} /></div>
                      </div>
                    ))}
                </div>

                <p className="cardiaque-version">Modèle {result.modele}</p>
              </>
            ) : (
              <div className="cardiaque-empty-result">
                <div className="cardiaque-empty-icon">AI</div>
                <p>Saisissez ou importez un battement ECG puis cliquez sur « Tester ».</p>
              </div>
            )}
          </div>
        </div>

        {result && signal && <SignalChart signal={signal} />}

        <p className="cardiaque-disclaimer">
          Application pédagogique : les résultats ne constituent pas un diagnostic médical.
        </p>
      </section>
    </main>
  );
}

export default Cardiaque;
