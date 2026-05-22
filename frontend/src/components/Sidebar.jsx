import React from 'react';
import { CheckCircle } from 'lucide-react';

const Sidebar = ({ onLogoClick }) => {
  return (
    <div className="sidebar">
      <div className="logo" onClick={onLogoClick} style={{ cursor: 'pointer' }}>
        <CheckCircle size={24} color="#2563eb" className="logo-icon" />
        ComplyOS
      </div>
      <div className="nav-menu">
        <div className="nav-item active"><CheckCircle size={18} /> Validate Invoice</div>
      </div>
    </div>
  );
};

export default Sidebar;
