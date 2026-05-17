import React from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <div className="app-container">
      <Sidebar />
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
