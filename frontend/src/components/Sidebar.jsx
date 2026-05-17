import React from 'react';
import { LayoutDashboard, FileText, CheckCircle, Database, BarChart, BookOpen, Settings } from 'lucide-react';

const Sidebar = () => {
  return (
    <div className="sidebar">
      <div className="logo">
        <CheckCircle size={24} color="#2563eb" />
        ComplyOS
      </div>
      <div className="nav-menu">
        <div className="nav-item active"><CheckCircle size={18} /> Validate Invoice</div>
      </div>
    </div>
  );
};

export default Sidebar;
