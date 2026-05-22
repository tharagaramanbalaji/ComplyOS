import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import LandingPage from './components/LandingPage';

function App() {
  const [view, setView] = useState('landing'); // 'landing' or 'dashboard'

  if (view === 'landing') {
    return <LandingPage onStart={() => setView('dashboard')} />;
  }

  return (
    <div className="app-container">
      <Sidebar onLogoClick={() => setView('landing')} />
      <div className="main-content">
        <div className="header">
          <h1>Validate Invoice</h1>
        </div>
        <Dashboard />
      </div>
    </div>
  );
}

export default App;
