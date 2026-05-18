import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Activity, LayoutDashboard, FileCode2, BookOpen, Settings as SettingsIcon, Home as HomeIcon, PieChart, HelpCircle, Wand2 } from 'lucide-react';
import { AnimatePresence } from 'framer-motion';

import Dashboard from './pages/Dashboard';
import RuleStudio from './pages/RuleStudio';
import XMLValidator from './pages/XMLValidator';
import Home from './pages/Home';
import Settings from './pages/Settings';
import RuleTemplates from './pages/RuleTemplates';
import Analytics from './pages/Analytics';
import Onboarding from './components/Onboarding';

export const ThemeContext = createContext();
export const RuleContext = createContext();

function App() {
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem('complyos_theme') || 'light');
  
  const [ruleStore, setRuleStore] = useState([]);
  const [activeRuleId, setActiveRuleId] = useState(null);

  useEffect(() => {
    const hasSeenTour = localStorage.getItem('complyos_tour_completed');
    if (!hasSeenTour) {
      setShowOnboarding(true);
    }
  }, []);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('complyos_theme', theme);
  }, [theme]);

  const toggleTheme = (newTheme) => {
    setTheme(newTheme);
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      <RuleContext.Provider value={{ ruleStore, setRuleStore, activeRuleId, setActiveRuleId }}>
        <Router>
          <div className="flex h-screen bg-background overflow-hidden relative font-sans text-textMain selection:bg-primary/20">
            <Sidebar />
            
            {/* Main Content */}
            <main className="flex-1 overflow-y-auto bg-background/50 relative z-0">
              <AnimatePresence mode="wait">
                <Routes>
                  <Route path="/" element={<Home />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/studio" element={<RuleStudio />} />
                  <Route path="/validator" element={<XMLValidator />} />
                  <Route path="/templates" element={<RuleTemplates />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </AnimatePresence>
            </main>
            
            {/* Help button to restart tour */}
            <button 
              onClick={() => setShowOnboarding(true)}
              className="absolute bottom-6 right-6 w-12 h-12 bg-surface rounded-full shadow-xl border border-border flex items-center justify-center text-primary hover:scale-105 transition-transform z-50 group"
              title="Restart Tutorial"
            >
              <HelpCircle size={24} />
            </button>

            {showOnboarding && <Onboarding onComplete={() => setShowOnboarding(false)} />}
          </div>
        </Router>
      </RuleContext.Provider>
    </ThemeContext.Provider>
  );
}

function Sidebar() {
  const location = useLocation();
  const { theme } = useContext(ThemeContext);
  
  return (
    <aside className="w-64 border-r border-border bg-surface/70 backdrop-blur-xl flex flex-col z-10 relative shadow-sm">
      <div className="p-6">
        <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-br from-primary via-secondary to-accent bg-clip-text text-transparent drop-shadow-sm">
          ComplyOS
        </h1>
        <p className="text-xs text-textMuted mt-1 font-medium tracking-wide uppercase">Validation Engine</p>
      </div>
      
      <nav className="flex-1 px-4 space-y-1.5 mt-2">
        <NavItem to="/" icon={<HomeIcon size={18}/>} text="Home" current={location.pathname === "/"} />
        <NavItem to="/dashboard" icon={<LayoutDashboard size={18}/>} text="Dashboard" current={location.pathname === "/dashboard"} />
        <NavItem to="/studio" icon={<FileCode2 size={18}/>} text="Rule Studio" current={location.pathname === "/studio"} tourId="tour-studio" />
        <NavItem to="/validator" icon={<Activity size={18}/>} text="XML Validator" current={location.pathname === "/validator"} tourId="tour-validator" />
        <NavItem to="/templates" icon={<BookOpen size={18}/>} text="Rule Templates" current={location.pathname === "/templates"} />
        <NavItem to="/analytics" icon={<PieChart size={18}/>} text="Analytics" current={location.pathname === "/analytics"} tourId="tour-analytics" />
      </nav>
      
      <div className="p-4 border-t border-border mt-auto">
        <NavItem to="/settings" icon={<SettingsIcon size={18}/>} text="Settings" current={location.pathname === "/settings"} />
      </div>
    </aside>
  );
}

function NavItem({ to, icon, text, current, tourId }) {
  return (
    <Link 
      id={tourId}
      to={to} 
      className={`flex items-center gap-3 px-4 py-2.5 rounded-xl font-medium transition-all ${
        current 
          ? 'bg-primary/20 text-primary shadow-sm' 
          : 'text-textMuted hover:text-textMain hover:bg-background/80'
      }`}
    >
      {icon}
      <span className="text-sm">{text}</span>
      {current && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary" />}
    </Link>
  );
}

export default App;
