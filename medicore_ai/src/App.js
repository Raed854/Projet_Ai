import './App.css';
import { useState } from 'react';
import Login from './Login/login';
import Account from './component/account/account';
import Home from './Home/home';
import Alzheimer from './alzheimer/alzheimer';
import HistoriqueAlzheimer from './alzheimer/historiquealzeimer/historiquealzeimer';
import Lesion from './lesion/lesion';
import HistoriqueLesion from './lesion/historiquelesion/historiquelesion';
import Dosage from './dosage/dosage';
import Sanguine from './sanguine/sanguine';
import HistoriqueSanguine from './sanguine/historiquesanguine';
import Cardiaque from './cardiaque/cardiaque';
import HistoriqueCardiaque from './cardiaque/historiquecardiaque';
import Chest from './chest/chest';
import HistoriqueChest from './chest/historiquechest';
import Dashboard from './Dashboard/dashboard';

const MODULE_PAGES = { skin: 'lesion', general: 'dosage', blood: 'sanguine', cardio: 'cardiaque', alzheimer: 'alzheimer', pulmonary: 'chest' };
// Page d'analyse -> module de la barre latérale
const PAGE_MODULES = { alzheimer: 'alzheimer', lesion: 'skin', dosage: 'general', sanguine: 'blood', cardiaque: 'cardio', chest: 'pulmonary' };
const DASHBOARD_PAGES = {
  home: 'home',
  alzheimer: 'dashboard-alzheimer',
  pulmonary: 'dashboard-pulmonary',
  skin: 'dashboard-skin',
  blood: 'dashboard-blood',
  cardio: 'dashboard-cardio',
  general: 'dashboard-general',
};

function App() {
  const [page, setPage] = useState('login');
  const [account, setAccount] = useState(null);
  const [selectedModule, setSelectedModule] = useState('home');

  async function handleAccountCreated(accountData) {
    const response = await fetch('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(accountData),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Impossible de créer le compte.');
    }
    setAccount(data);
    setSelectedModule('home');
    setPage('home');
  }

  async function handleLogin(email, password, rememberMe) {
    const response = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Impossible de se connecter.');
    }
    setAccount(data);
    if (rememberMe) {
      localStorage.setItem('medicore_user', JSON.stringify(data));
    } else {
      localStorage.removeItem('medicore_user');
    }
    setSelectedModule('home');
    setPage('home');
  }

  function handleLogout() {
    setAccount(null);
    setSelectedModule('home');
    setPage('login');
  }

  function handleModuleSelect(moduleId) {
    setSelectedModule(moduleId);
    setPage(DASHBOARD_PAGES[moduleId] || 'home');
  }

  // Accepte une page d'analyse ('lesion', 'chest'…) ou un module de la barre latérale ('skin', 'pulmonary'…)
  function handleStartAnalysis(id) {
    const analysisPage = PAGE_MODULES[id] ? id : MODULE_PAGES[id] || 'alzheimer';
    setSelectedModule(PAGE_MODULES[analysisPage]);
    setPage(analysisPage);
  }

  function handleOpenHistory() {
    setPage('historique-alzheimer');
  }

  if (page === 'account') {
    return <Account onAccountCreated={handleAccountCreated} onBackToLogin={() => setPage('login')} />;
  }

  if (page === 'dashboard-alzheimer' && account) {
    return <Dashboard account={account} onLogout={handleLogout} onSelectModule={handleModuleSelect} selectedModule={selectedModule} moduleId="alzheimer" onStartAnalysis={handleStartAnalysis} />;
  }

  if (page === 'dashboard-pulmonary' && account) {
    return <Dashboard account={account} onLogout={handleLogout} onSelectModule={handleModuleSelect} selectedModule={selectedModule} moduleId="pulmonary" onStartAnalysis={handleStartAnalysis} />;
  }

  if (page === 'dashboard-skin' && account) {
    return <Dashboard account={account} onLogout={handleLogout} onSelectModule={handleModuleSelect} selectedModule={selectedModule} moduleId="skin" onStartAnalysis={handleStartAnalysis} />;
  }

  if (page === 'dashboard-blood' && account) {
    return <Dashboard account={account} onLogout={handleLogout} onSelectModule={handleModuleSelect} selectedModule={selectedModule} moduleId="blood" onStartAnalysis={handleStartAnalysis} />;
  }

  if (page === 'dashboard-cardio' && account) {
    return <Dashboard account={account} onLogout={handleLogout} onSelectModule={handleModuleSelect} selectedModule={selectedModule} moduleId="cardio" onStartAnalysis={handleStartAnalysis} />;
  }

  if (page === 'dashboard-general' && account) {
    return <Dashboard account={account} onLogout={handleLogout} onSelectModule={handleModuleSelect} selectedModule={selectedModule} moduleId="general" onStartAnalysis={handleStartAnalysis} />;
  }

  if (page === 'alzheimer' && account) {
    return (
      <Alzheimer
        account={account}
        onOpenHistory={handleOpenHistory}
        onLogout={handleLogout}
        onSelectModule={handleModuleSelect}
        selectedModule={selectedModule}
      />
    );
  }

  if (page === 'chest' && account) {
    return (
      <Chest
        account={account}
        onLogout={handleLogout}
        onSelectModule={handleModuleSelect}
        selectedModule={selectedModule}
        onOpenHistory={() => setPage('historique-chest')}
      />
    );
  }

  if (page === 'historique-chest' && account) {
    return (
      <HistoriqueChest
        account={account}
        onBackToChest={() => setPage('chest')}
        onLogout={handleLogout}
        onSelectModule={handleModuleSelect}
        selectedModule={selectedModule}
      />
    );
  }

  if (page === 'cardiaque' && account) {
    return (
      <Cardiaque
        account={account}
        onOpenHistory={() => setPage('historique-cardiaque')}
        onLogout={handleLogout}
        onSelectModule={handleModuleSelect}
        selectedModule={selectedModule}
      />
    );
  }

  if (page === 'historique-cardiaque' && account) {
    return (
      <HistoriqueCardiaque
        account={account}
        onBackToCardiaque={() => setPage('cardiaque')}
        onLogout={handleLogout}
        onSelectModule={handleModuleSelect}
        selectedModule={selectedModule}
      />
    );
  }

  if (page === 'sanguine' && account) {
    return (
      <Sanguine
        account={account}
        onOpenHistory={() => setPage('historique-sanguine')}
        onLogout={handleLogout}
        onSelectModule={handleModuleSelect}
        selectedModule={selectedModule}
      />
    );
  }

  if (page === 'historique-sanguine' && account) {
    return (
      <HistoriqueSanguine
        account={account}
        onBackToSanguine={() => setPage('sanguine')}
        onLogout={handleLogout}
        onSelectModule={handleModuleSelect}
        selectedModule={selectedModule}
      />
    );
  }

  if (page === 'dosage' && account) {
    return <Dosage account={account} onLogout={handleLogout} onSelectModule={handleModuleSelect} selectedModule={selectedModule} />;
  }

  if (page === 'lesion' && account) {
    return (
      <Lesion
        account={account}
        onOpenHistory={() => setPage('historique-lesion')}
        onLogout={handleLogout}
        onSelectModule={handleModuleSelect}
        selectedModule={selectedModule}
      />
    );
  }

  if (page === 'historique-lesion' && account) {
    return (
      <HistoriqueLesion
        account={account}
        onBackToLesion={() => setPage('lesion')}
        onLogout={handleLogout}
        onSelectModule={handleModuleSelect}
        selectedModule={selectedModule}
      />
    );
  }

  if (page === 'historique-alzheimer' && account) {
    return (
      <HistoriqueAlzheimer
        account={account}
        onBackToAlzheimer={() => setPage('alzheimer')}
        onLogout={handleLogout}
        onSelectModule={handleModuleSelect}
        selectedModule={selectedModule}
      />
    );
  }

  if (page === 'home' && account) {
    return <Home account={account} onLogout={handleLogout} onSelectModule={handleModuleSelect} selectedModule={selectedModule} />;
  }

  return <Login onCreateAccount={() => setPage('account')} onLogin={handleLogin} />;
}

export default App;
