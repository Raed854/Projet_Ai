import SideBar from '../component/side_bar/side_bar';
import './dashboard.css';

const DASHBOARDS = {
  global: {
    title: 'Vue globale',
    eyebrow: 'Tableau de bord principal',
    description: 'Retrouvez en un seul endroit l’activité de vos six modules d’analyse.',
    action: 'Voir les modules',
    metrics: [
      ['128', 'Analyses réalisées', '+12%'],
      ['96%', 'Précision moyenne', '+2,4%'],
      ['24', 'Rapports disponibles', '+8'],
      ['08', 'Alertes à consulter', 'À voir'],
    ],
    highlights: [
      ['Alzheimer', 'Analyse IRM et suivi cognitif', 'alzheimer', '✦'],
      ['Maladies pulmonaires', 'Analyse respiratoire', 'pulmonary', '♧'],
      ['Lésions cutanées', 'Classification dermoscopique', 'skin', '◌'],
      ['Numération sanguine', 'Lecture des paramètres NFS/CBC', 'blood', '▦'],
      ['Rythme cardiaque', 'Classification du signal ECG', 'cardio', '♡'],
      ['Dosage', 'Interprétation des courbes de pH', 'general', '⌁'],
    ],
  },
  alzheimer: {
    title: 'Dashboard Alzheimer',
    eyebrow: 'Suivi neurologique',
    description: 'Suivez vos analyses IRM et les résultats du modèle Alzheimer.',
    action: 'Lancer une analyse IRM',
    metrics: [['12', 'IRM analysées', '+3'], ['91%', 'Confiance moyenne', '+1,8%'], ['2', 'Alertes à consulter', 'À voir'], ['12', 'Rapports disponibles', '+2']],
  },
  pulmonary: {
    title: 'Dashboard maladies pulmonaires',
    eyebrow: 'Suivi respiratoire',
    description: 'Détectez une pneumonie sur radiographie thoracique et suivez vos résultats.',
    action: 'Analyser une radiographie',
    metrics: [['—', 'Radiographies analysées', '—'], ['—', 'Confiance moyenne', '—'], ['—', 'Pneumonies détectées', '—'], ['—', 'Rapports disponibles', '—']],
  },
  skin: {
    title: 'Dashboard lésions cutanées',
    eyebrow: 'Suivi dermatologique',
    description: 'Visualisez vos classifications de lésions et les niveaux de vigilance.',
    action: 'Analyser une lésion',
    metrics: [['28', 'Images analysées', '+6'], ['94%', 'Confiance moyenne', '+2,1%'], ['3', 'Vigilances élevées', 'À voir'], ['8', 'Rapports disponibles', '+1']],
  },
  blood: {
    title: 'Dashboard numération sanguine',
    eyebrow: 'Suivi hématologique',
    description: 'Consultez l’évolution de vos paramètres NFS/CBC.',
    action: 'Lancer une NFS',
    metrics: [['34', 'NFS analysées', '+5'], ['89%', 'Paramètres dans la norme', '+3,2%'], ['4', 'Valeurs à surveiller', 'À voir'], ['9', 'Rapports disponibles', '+2']],
  },
  cardio: {
    title: 'Dashboard rythme cardiaque',
    eyebrow: 'Suivi cardiologique',
    description: 'Suivez les classifications de vos signaux ECG.',
    action: 'Analyser un ECG',
    metrics: [['41', 'ECG analysés', '+7'], ['97%', 'Battements normaux', '+1,1%'], ['5', 'Anomalies à consulter', 'À voir'], ['11', 'Rapports disponibles', '+3']],
  },
  general: {
    title: 'Dashboard dosage',
    eyebrow: 'Suivi des dosages',
    description: 'Retrouvez vos courbes de dosage, points d’équivalence et rapports.',
    action: 'Lancer un dosage',
    metrics: [['13', 'Dosages réalisés', '+2'], ['92%', 'Courbes exploitables', '+4,5%'], ['1', 'Alerte à consulter', 'À voir'], ['6', 'Rapports disponibles', '+1']],
  },
};

const ANALYSIS_MODULES = {
  alzheimer: 'alzheimer',
  skin: 'lesion',
  blood: 'sanguine',
  cardio: 'cardiaque',
  general: 'dosage',
  pulmonary: 'chest',
};

const CHART_POINTS = {
  alzheimer: '4,64 22,58 40,62 58,45 76,49 94,31 112,37 130,24',
  pulmonary: '4,64 22,64 40,64 58,64 76,64 94,64 112,64 130,64',
  skin: '4,58 22,54 40,61 58,42 76,48 94,32 112,38 130,22',
  blood: '4,55 22,48 40,52 58,36 76,42 94,29 112,34 130,20',
  cardio: '4,49 22,37 40,54 58,27 76,45 94,31 112,40 130,18',
  general: '4,60 22,52 40,56 58,41 76,45 94,30 112,35 130,25',
};

function TrendChart({ moduleId }) {
  return (
    <div className="dashboard-chart">
      <div className="dashboard-chart-heading"><span>Évolution des analyses</span><strong>8 dernières périodes</strong></div>
      <svg viewBox="0 0 134 72" role="img" aria-label="Graphique d’évolution des analyses">
        <line x1="4" y1="64" x2="130" y2="64" className="dashboard-chart-axis" />
        <line x1="4" y1="42" x2="130" y2="42" className="dashboard-chart-gridline" />
        <line x1="4" y1="20" x2="130" y2="20" className="dashboard-chart-gridline" />
        <polyline points={CHART_POINTS[moduleId]} className="dashboard-chart-line" />
        {CHART_POINTS[moduleId].split(' ').map((point) => {
          const [cx, cy] = point.split(',');
          return <circle key={point} cx={cx} cy={cy} r="2.2" className="dashboard-chart-dot" />;
        })}
      </svg>
    </div>
  );
}

function Dashboard({ account, onLogout, onSelectModule, selectedModule, moduleId = 'global', onStartAnalysis }) {
  const dashboard = DASHBOARDS[moduleId] || DASHBOARDS.global;
  const roleLabel = account.role === 'docteur' ? 'Docteur' : 'Patient';
  const initials = `${account.prenom.charAt(0)}${account.nom.charAt(0)}`;

  function handleAction() {
    if (moduleId === 'global') {
      document.querySelector('.dashboard-modules')?.scrollIntoView({ behavior: 'smooth' });
      return;
    }
    if (dashboard.unavailable) return;
    onStartAnalysis(ANALYSIS_MODULES[moduleId]);
  }

  function openModuleAnalysis(id) {
    if (DASHBOARDS[id].unavailable) return;
    if (onStartAnalysis) {
      onStartAnalysis(ANALYSIS_MODULES[id]);
      return;
    }
    onSelectModule(id);
  }

  return (
    <main className="dashboard-page">
      <SideBar onLogout={onLogout} onSelectModule={onSelectModule} selectedModule={selectedModule} />
      <section className="dashboard-main">
        <header className="dashboard-topbar">
          <div>
            <p className="dashboard-breadcrumb">Tableau de bord / {dashboard.title}</p>
            <h1>Bonjour, {account.prenom} <span aria-hidden="true">👋</span></h1>
          </div>
          <div className="dashboard-user">
            <div className="dashboard-avatar">{initials}</div>
            <div><strong>{account.prenom} {account.nom}</strong><span>{roleLabel}</span></div>
          </div>
        </header>

        <div className="dashboard-content">
          <section className="dashboard-intro">
            <div>
              <p className="dashboard-eyebrow">{dashboard.eyebrow}</p>
              <h2>{dashboard.title}</h2>
              <p>{dashboard.description}</p>
            </div>
            <button type="button" className="dashboard-action" onClick={handleAction} disabled={dashboard.unavailable}>
              {dashboard.action}
            </button>
          </section>

          <section className="dashboard-section" aria-labelledby="metrics-title">
            <div className="dashboard-section-heading"><div><p className="dashboard-eyebrow">En un coup d’œil</p><h2 id="metrics-title">Vos statistiques</h2></div><span>Dernières données</span></div>
            <div className="dashboard-metrics">
              {dashboard.metrics.map(([value, label, change]) => (
                <article className="dashboard-metric" key={label}>
                  <div><span className="dashboard-metric-icon">✦</span><span className="dashboard-change">{change}</span></div>
                  <strong>{value}</strong><span>{label}</span>
                </article>
              ))}
            </div>
          </section>

          {moduleId === 'global' && (
            <section className="dashboard-section dashboard-modules" aria-labelledby="modules-title">
              <div className="dashboard-section-heading"><div><p className="dashboard-eyebrow">Vue consolidée</p><h2 id="modules-title">Les 6 dashboards d’analyse</h2></div><span>Accès rapide</span></div>
              <div className="dashboard-overview-grid">
                {dashboard.highlights.map(([title, description, id, icon]) => {
                  const moduleDashboard = DASHBOARDS[id];
                  return (
                    <article className="dashboard-overview-card" key={id}>
                      <button type="button" className="dashboard-overview-title" onClick={() => onSelectModule(id)}>
                        <span className="dashboard-module-icon">{icon}</span>
                        <span><strong>{title}</strong><small>{description}</small></span>
                        <b>→</b>
                      </button>
                      <div className="dashboard-overview-metrics">
                        {moduleDashboard.metrics.slice(0, 2).map(([value, label]) => <div key={label}><strong>{value}</strong><span>{label}</span></div>)}
                      </div>
                      <TrendChart moduleId={id} />
                      <button type="button" className="dashboard-overview-action" disabled={moduleDashboard.unavailable} onClick={() => openModuleAnalysis(id)}>
                        {moduleDashboard.unavailable ? 'Service bientôt disponible' : moduleDashboard.action}
                      </button>
                    </article>
                  );
                })}
              </div>
            </section>
          )}

          {moduleId !== 'global' && (
            <section className={`dashboard-empty${dashboard.unavailable ? ' unavailable' : ''}`}>
              <span aria-hidden="true">{dashboard.unavailable ? '…' : '✓'}</span>
              <div><h2>{dashboard.unavailable ? 'Module en préparation' : 'Aucune nouvelle analyse'}</h2><p>{dashboard.unavailable ? 'Le dashboard est prêt. Le service d’analyse pulmonaire sera connecté prochainement.' : 'Lancez une analyse pour afficher vos prochains résultats dans cet espace.'}</p></div>
            </section>
          )}
        </div>
      </section>
    </main>
  );
}

export default Dashboard;
