import './side_bar.css';

const modules = [
  { id: 'alzheimer', label: 'Maladie Alzheimer', icon: '✦' },
  { id: 'pulmonary', label: 'Maladies pulmonaires', icon: '♧' },
  { id: 'skin', label: 'Analyse des lésions cutanées', icon: '◌' },
  { id: 'blood', label: 'Analyse de la numération sanguine (NFS/CBC)', icon: '▦' },
  { id: 'cardio', label: 'Analyse du rythme cardiaque', icon: '♡' },
  { id: 'general', label: 'Dosage', icon: '⌁' },
];

function SideBar({ onLogout, onSelectModule, selectedModule }) {
  return (
    <aside className="side-bar">
      <div className="side-bar-brand"><span className="side-bar-mark" aria-hidden="true">+</span><span>MediCore <strong>AI</strong></span></div>
      <div className="side-bar-caption">Modules d’analyse</div>
      <nav aria-label="Modules médicaux">
        <button
          className={`side-bar-item${selectedModule === 'home' ? ' active' : ''}`}
          type="button"
          onClick={() => onSelectModule('home')}
        >
          <span className="side-bar-icon" aria-hidden="true">⌂</span>
          <span>Vue globale</span>
        </button>
        {modules.map((module) => (
          <button
            className={`side-bar-item${selectedModule === module.id ? ' active' : ''}`}
            type="button"
            key={module.label}
            onClick={() => onSelectModule(module.id)}
          >
            <span className="side-bar-icon" aria-hidden="true">{module.icon}</span>
            <span>{module.label}</span>
          </button>
        ))}
      </nav>
      <div className="side-bar-footer"><div className="side-bar-secure"><span>✓</span><div><strong>Données sécurisées</strong><small>Confidentialité médicale</small></div></div><button className="side-bar-logout" type="button" onClick={onLogout}>↪ <span>Se déconnecter</span></button></div>
    </aside>
  );
}

export default SideBar;
