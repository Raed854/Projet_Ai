import { useState } from 'react';
import './dosage.css';
import '../component/result_modal.css';
import SideBar from '../component/side_bar/side_bar';

// Service Flask du modèle dosage (analyse + enregistrement en table dosage)
const MODEL_API_URL = process.env.REACT_APP_DOSAGE_API_URL || 'http://localhost:5002';

const TYPE_LABELS = {
  acide_fort: 'Acide fort',
  acide_faible: 'Acide faible',
  base_forte: 'Base forte',
  base_faible: 'Base faible',
};

const DEFAUT_LABELS = {
  pic: 'Pic de pH isolé',
  arret_premature: 'Arrêt prématuré',
  electrode_defaillante: 'Électrode défaillante',
  inversion: 'Inversion du pH',
};

// Courbe d'exemple du README de dosage-ia (acide faible, C_titrant 0,1 mol/L, prise 20 mL)
const EXEMPLE = {
  volumes: [0, 2, 4, 6, 8, 9, 9.5, 10, 10.5, 11, 12, 14, 16],
  ph: [2.9, 3.9, 4.3, 4.7, 5.2, 5.6, 6.0, 8.7, 11.3, 11.6, 11.9, 12.2, 12.3],
  cTitrant: '0.1',
  vPrise: '20',
  typeDeclare: 'acide_faible',
};

const EMPTY_ROWS = Array.from({ length: 5 }, () => ({ volume: '', ph: '' }));

function formatNumber(value, digits = 3) {
  return typeof value === 'number' ? value.toLocaleString('fr-FR', { maximumFractionDigits: digits }) : '—';
}

function parseNumber(value) {
  return Number(String(value).trim().replace(',', '.'));
}

// Lit deux colonnes (volume, pH) collées depuis Excel ou un fichier texte
function parsePastedRows(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim().split(/[\t;]+|\s+/))
    .filter((cells) => cells.length >= 2)
    .map(([volume, ph]) => ({ volume: volume.replace(',', '.'), ph: ph.replace(',', '.') }))
    .filter((row) => Number.isFinite(parseNumber(row.volume)) && Number.isFinite(parseNumber(row.ph)));
}

function niceTicks(min, max, count = 5) {
  const span = max - min || 1;
  const rawStep = span / count;
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= rawStep);
  const ticks = [];
  for (let t = Math.ceil(min / step) * step; t <= max + step * 1e-6; t += step) {
    ticks.push(Number(t.toFixed(10)));
  }
  return ticks;
}

function CurveChart({ title, points, xLabel, yLabel, markerX, markerLabel, yDigits = 2 }) {
  const [hoverIndex, setHoverIndex] = useState(null);
  const width = 560;
  const height = 240;
  const pad = { top: 16, right: 18, bottom: 40, left: 48 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;

  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  const xTicks = niceTicks(Math.min(...xs, markerX ?? Infinity), Math.max(...xs, markerX ?? -Infinity));
  const yTicks = niceTicks(Math.min(0, ...ys), Math.max(...ys));
  const [x0, x1] = [xTicks[0], xTicks[xTicks.length - 1]];
  const [y0, y1] = [yTicks[0], yTicks[yTicks.length - 1]];
  const sx = (x) => pad.left + ((x - x0) / (x1 - x0 || 1)) * innerW;
  const sy = (y) => pad.top + innerH - ((y - y0) / (y1 - y0 || 1)) * innerH;
  const path = points.map((p, i) => `${i ? 'L' : 'M'}${sx(p.x).toFixed(1)},${sy(p.y).toFixed(1)}`).join(' ');
  const hovered = hoverIndex !== null ? points[hoverIndex] : null;

  function handleMove(event) {
    const box = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - box.left) / box.width) * width;
    let best = 0;
    points.forEach((p, i) => {
      if (Math.abs(sx(p.x) - x) < Math.abs(sx(points[best].x) - x)) best = i;
    });
    setHoverIndex(best);
  }

  return (
    <figure className="dosage-chart">
      <figcaption>{title}</figcaption>
      <div className="dosage-chart-frame">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label={`${title} : ${points.length} points`}
          onMouseMove={handleMove}
          onMouseLeave={() => setHoverIndex(null)}
        >
          {yTicks.map((t) => (
            <g key={`y${t}`}>
              <line className="dosage-chart-grid" x1={pad.left} x2={width - pad.right} y1={sy(t)} y2={sy(t)} />
              <text className="dosage-chart-tick" x={pad.left - 8} y={sy(t) + 4} textAnchor="end">{formatNumber(t, 2)}</text>
            </g>
          ))}
          {xTicks.map((t) => (
            <text key={`x${t}`} className="dosage-chart-tick" x={sx(t)} y={height - pad.bottom + 18} textAnchor="middle">{formatNumber(t, 2)}</text>
          ))}
          <text className="dosage-chart-axis" x={pad.left + innerW / 2} y={height - 4} textAnchor="middle">{xLabel}</text>
          <text className="dosage-chart-axis" x={12} y={pad.top + innerH / 2} textAnchor="middle" transform={`rotate(-90 12 ${pad.top + innerH / 2})`}>{yLabel}</text>

          {typeof markerX === 'number' && (
            <g>
              <line className="dosage-chart-marker" x1={sx(markerX)} x2={sx(markerX)} y1={pad.top} y2={pad.top + innerH} />
              <text className="dosage-chart-marker-label" x={sx(markerX) + 6} y={pad.top + 12}>{markerLabel}</text>
            </g>
          )}

          <path className="dosage-chart-line" d={path} />
          {points.map((p, i) => (
            <circle key={i} className="dosage-chart-dot" cx={sx(p.x)} cy={sy(p.y)} r={hoverIndex === i ? 5 : 3} />
          ))}

          {hovered && (
            <line className="dosage-chart-crosshair" x1={sx(hovered.x)} x2={sx(hovered.x)} y1={pad.top} y2={pad.top + innerH} />
          )}
        </svg>
        {hovered && (
          <div
            className="dosage-chart-tooltip"
            style={{
              left: `${(sx(hovered.x) / width) * 100}%`,
              top: `${(sy(hovered.y) / height) * 100}%`,
            }}
          >
            <span>V = {formatNumber(hovered.x, 3)} mL</span>
            <strong>{yLabel.split(' ')[0]} = {formatNumber(hovered.y, yDigits)}</strong>
          </div>
        )}
      </div>
    </figure>
  );
}

function Dosage({ account, onLogout, onSelectModule, selectedModule }) {
  const [rows, setRows] = useState(EMPTY_ROWS);
  const [cTitrant, setCTitrant] = useState('');
  const [vPrise, setVPrise] = useState('');
  const [typeDeclare, setTypeDeclare] = useState('');
  const [pasteText, setPasteText] = useState('');
  const [result, setResult] = useState(null);
  const [curve, setCurve] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showResult, setShowResult] = useState(false);

  function updateRow(index, field, value) {
    setRows((current) => current.map((row, i) => (i === index ? { ...row, [field]: value } : row)));
  }

  function removeRow(index) {
    setRows((current) => (current.length > 1 ? current.filter((_, i) => i !== index) : current));
  }

  function loadExample() {
    setRows(EXEMPLE.volumes.map((volume, i) => ({ volume: String(volume), ph: String(EXEMPLE.ph[i]) })));
    setCTitrant(EXEMPLE.cTitrant);
    setVPrise(EXEMPLE.vPrise);
    setTypeDeclare(EXEMPLE.typeDeclare);
    setError('');
  }

  function importPasted() {
    const parsed = parsePastedRows(pasteText);
    if (parsed.length === 0) {
      setError('Aucun point lu : collez deux colonnes (volume puis pH), une ligne par mesure.');
      return;
    }
    setRows(parsed);
    setPasteText('');
    setError('');
  }

  function resetForm() {
    setRows(EMPTY_ROWS);
    setCTitrant('');
    setVPrise('');
    setTypeDeclare('');
    setResult(null);
    setCurve(null);
    setError('');
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const filled = rows.filter((row) => String(row.volume).trim() !== '' || String(row.ph).trim() !== '');
    const points = filled.map((row) => ({ volume: parseNumber(row.volume), ph: parseNumber(row.ph) }));
    if (points.some((p) => !Number.isFinite(p.volume) || !Number.isFinite(p.ph))) {
      setError('Chaque point doit avoir un volume et un pH numériques.');
      return;
    }
    if (points.length < 5) {
      setError('Saisissez au moins 5 points de mesure (volume, pH).');
      return;
    }

    const body = {
      volumes: points.map((p) => p.volume),
      ph: points.map((p) => p.ph),
      c_titrant: cTitrant ? parseNumber(cTitrant) : null,
      v_prise: vPrise ? parseNumber(vPrise) : null,
      type_declare: typeDeclare || null,
    };

    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${MODEL_API_URL}/api/users/${account.id}/dosage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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

      if (typeof responseData?.veq_retenu !== 'number') {
        throw new Error('La réponse de l’API ne contient pas un résultat valide.');
      }

      setResult(responseData);
      setShowResult(true);
      setCurve([...points].sort((a, b) => a.volume - b.volume));
    } catch (requestError) {
      setError(
        requestError.message === 'Failed to fetch'
          ? 'Impossible de contacter le modèle. Vérifiez que l’API dosage est démarrée sur le port 5002.'
          : requestError.message,
      );
    } finally {
      setIsLoading(false);
    }
  }

  const derivativePoints = result?.derivee
    ? result.derivee.v.map((v, i) => ({ x: v, y: result.derivee.d[i] }))
    : [];

  return (
    <main className="dosage-page">
      <SideBar onLogout={onLogout} onSelectModule={onSelectModule} selectedModule={selectedModule} />

      <section className="dosage-main">
        <header className="dosage-topbar">
          <div>
            <p className="dosage-eyebrow">IA chimie analytique</p>
            <h1>Analyse d’une courbe de titrage</h1>
          </div>
        </header>

        <div className="dosage-grid">
          <form className="dosage-form" onSubmit={handleSubmit}>
            <div className="dosage-section-head">
              <h2>Points de mesure</h2>
              <div className="dosage-head-actions">
                <button type="button" className="dosage-link-button" onClick={loadExample}>Charger l’exemple</button>
                <button type="button" className="dosage-link-button" onClick={resetForm}>Vider</button>
              </div>
            </div>

            <div className="dosage-points">
              <div className="dosage-points-header">
                <span>#</span><span>Volume (mL)</span><span>pH</span><span />
              </div>
              {rows.map((row, index) => (
                <div className="dosage-point-row" key={index}>
                  <span className="dosage-point-index">{index + 1}</span>
                  <input
                    type="text"
                    inputMode="decimal"
                    aria-label={`Volume du point ${index + 1}`}
                    placeholder="0.0"
                    value={row.volume}
                    onChange={(event) => updateRow(index, 'volume', event.target.value)}
                  />
                  <input
                    type="text"
                    inputMode="decimal"
                    aria-label={`pH du point ${index + 1}`}
                    placeholder="7.00"
                    value={row.ph}
                    onChange={(event) => updateRow(index, 'ph', event.target.value)}
                  />
                  <button
                    type="button"
                    className="dosage-remove"
                    aria-label={`Supprimer le point ${index + 1}`}
                    onClick={() => removeRow(index)}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
            <button
              type="button"
              className="dosage-add"
              onClick={() => setRows((current) => [...current, { volume: '', ph: '' }])}
            >
              + Ajouter un point
            </button>

            <details className="dosage-paste">
              <summary>Coller des points depuis Excel</summary>
              <textarea
                rows={5}
                placeholder={'0\t2.9\n2\t3.9\n4\t4.3'}
                value={pasteText}
                onChange={(event) => setPasteText(event.target.value)}
              />
              <button type="button" className="dosage-link-button" onClick={importPasted}>Importer ces points</button>
            </details>

            <h2 className="dosage-section-title">Paramètres du dosage</h2>
            <div className="dosage-params">
              <label>
                Concentration du titrant (mol/L)
                <input type="text" inputMode="decimal" placeholder="0.1" value={cTitrant} onChange={(event) => setCTitrant(event.target.value)} />
              </label>
              <label>
                Volume de la prise d’essai (mL)
                <input type="text" inputMode="decimal" placeholder="20" value={vPrise} onChange={(event) => setVPrise(event.target.value)} />
              </label>
              <label className="dosage-param-wide">
                Type de dosage déclaré (optionnel)
                <select value={typeDeclare} onChange={(event) => setTypeDeclare(event.target.value)}>
                  <option value="">Non précisé</option>
                  {Object.entries(TYPE_LABELS).map(([code, label]) => (
                    <option key={code} value={code}>{label}</option>
                  ))}
                </select>
              </label>
            </div>

            <div className="dosage-api-info">
              <span aria-hidden="true">✓</span>
              <span>La concentration de l’analyte n’est calculée que si le titrant et la prise d’essai sont renseignés.</span>
            </div>

            {error && <p className="dosage-api-error" role="alert">{error}</p>}

            <button className="dosage-submit" type="submit" disabled={isLoading}>
              {isLoading ? 'Test en cours…' : 'Tester'}
            </button>
          </form>

          {showResult && <div className="analysis-result-modal-backdrop" onClick={() => setShowResult(false)} />}
          <div className={`dosage-result${showResult ? ' analysis-result-modal' : ''}`} role={showResult ? 'dialog' : undefined} aria-modal={showResult ? 'true' : undefined}>
            <div className="dosage-result-header">
              <p className="dosage-eyebrow">Résultat du modèle</p>
              <h2>Exploitation de la courbe</h2>
            </div>

            {result ? (
              <>
                <div className="dosage-badges">
                  <span className="dosage-type-badge">{TYPE_LABELS[result.type_predit] || result.type_predit}</span>
                  <span className={`dosage-status ${result.a_revoir ? 'dosage-status-warning' : 'dosage-status-good'}`}>
                    <span aria-hidden="true">{result.a_revoir ? '!' : '✓'}</span>
                    {result.a_revoir ? 'À revoir par un opérateur' : 'Dosage conforme'}
                  </span>
                  {result.dosage && <span className="dosage-saved">Enregistré #{result.dosage.id}</span>}
                </div>

                <div className="dosage-hero">
                  <small>Volume équivalent retenu</small>
                  <strong>{formatNumber(result.veq_retenu)} <span>mL</span></strong>
                  <p>{result.est_anomalie ? 'Méthode dérivée retenue (anomalie détectée)' : 'Valeur prédite par l’IA'}</p>
                </div>

                <div className="dosage-metrics">
                  <div className="dosage-metric"><small>V_eq IA</small><strong>{formatNumber(result.veq_ia)} mL</strong><span>± {formatNumber(result.veq_ia_incertitude)} mL</span></div>
                  <div className="dosage-metric"><small>V_eq dérivée</small><strong>{formatNumber(result.veq_derivee)} mL</strong><span>Méthode classique</span></div>
                  <div className="dosage-metric"><small>pKa estimé</small><strong>{formatNumber(result.pka_estime, 2)}</strong><span>Couples faibles</span></div>
                  <div className="dosage-metric"><small>Concentration</small><strong>{formatNumber(result.concentration, 6)}</strong><span>mol/L</span></div>
                  <div className="dosage-metric"><small>Score qualité</small><strong>{formatNumber(result.score_qualite * 100, 1)} %</strong><span>Probabilité conforme</span></div>
                  <div className="dosage-metric"><small>Défaut détecté</small><strong>{result.defaut_detecte ? DEFAUT_LABELS[result.defaut_detecte] || result.defaut_detecte : 'Aucun'}</strong><span>Contrôle qualité</span></div>
                </div>

                <div className="dosage-box">
                  <h3>Alertes</h3>
                  {result.alertes.length === 0 && <p className="dosage-muted">Aucune alerte : la courbe ne nécessite pas de revue.</p>}
                  {result.alertes.map((alerte) => (
                    <div className={`dosage-alert dosage-alert-${alerte.niveau}`} key={alerte.code}>
                      <span className="dosage-alert-icon" aria-hidden="true">{alerte.niveau === 'critique' ? '✕' : '!'}</span>
                      <div>
                        <strong>{alerte.niveau === 'critique' ? 'Critique' : 'Attention'} · {alerte.code}</strong>
                        <p>{alerte.message}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="dosage-box">
                  <h3>Type de dosage reconnu</h3>
                  {Object.entries(result.probabilites_type || {})
                    .sort(([, a], [, b]) => b - a)
                    .map(([code, probability]) => (
                      <div className="dosage-probability-row" key={code}>
                        <span>{TYPE_LABELS[code] || code}</span>
                        <strong>{formatNumber(probability * 100, 1)} %</strong>
                        <div className="dosage-probability-track"><span style={{ width: `${probability * 100}%` }} /></div>
                      </div>
                    ))}
                </div>

                <p className="dosage-version">Modèle {result.modele_version}</p>
              </>
            ) : (
              <div className="dosage-empty-result">
                <div className="dosage-empty-icon">AI</div>
                <p>Saisissez les points de la courbe puis cliquez sur « Tester ».</p>
              </div>
            )}
          </div>
        </div>

        {result && curve && (
          <section className="dosage-charts">
            <CurveChart
              title="Courbe de titrage pH = f(V)"
              points={curve.map((p) => ({ x: p.volume, y: p.ph }))}
              xLabel="Volume de titrant (mL)"
              yLabel="pH"
              markerX={result.veq_retenu}
              markerLabel={`V_eq = ${formatNumber(result.veq_retenu)} mL`}
            />
            {derivativePoints.length > 0 && (
              <CurveChart
                title="Dérivée |dpH/dV|"
                points={derivativePoints}
                xLabel="Volume de titrant (mL)"
                yLabel="|dpH/dV| (mL⁻¹)"
                markerX={result.veq_derivee}
                markerLabel={`V_eq dérivée = ${formatNumber(result.veq_derivee)} mL`}
                yDigits={3}
              />
            )}
          </section>
        )}

        <p className="dosage-disclaimer">
          Modèle entraîné principalement sur des courbes synthétiques (dosages monoprotiques 1:1).
          Un dosage marqué « à revoir » doit être vérifié par un opérateur.
        </p>
      </section>
    </main>
  );
}

export default Dosage;
