import React, { useState, useContext } from 'react';
import { motion } from 'framer-motion';
import { Save, RefreshCw, Moon, Sun, Bell, Shield, Database } from 'lucide-react';
import { ThemeContext } from '../App';

export default function Settings() {
  const [saved, setSaved] = useState(false);
  const { theme, toggleTheme } = useContext(ThemeContext);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto h-full overflow-y-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-extrabold text-textMain tracking-tight">Settings</h1>
        <p className="text-textMuted mt-2">Manage your platform preferences and validation configurations.</p>
      </header>

      <div className="space-y-6">
        <SettingsSection title="Appearance" icon={<Sun size={20} className="text-amber-500"/>}>
          <div className="flex items-center justify-between p-4 bg-surface rounded-xl border border-border">
            <div>
              <p className="font-semibold text-textMain">Theme Preference</p>
              <p className="text-sm text-textMuted">Choose between Light and Dark mode.</p>
            </div>
            <div className="flex gap-2">
              <button 
                onClick={() => toggleTheme('light')}
                className={`px-4 py-2 rounded-lg font-medium shadow-sm border transition-colors ${theme === 'light' ? 'bg-white border-primary text-primary' : 'bg-transparent border-border text-textMuted hover:text-textMain'}`}
              >Light</button>
              <button 
                onClick={() => toggleTheme('dark')}
                className={`px-4 py-2 rounded-lg font-medium shadow-sm border transition-colors ${theme === 'dark' ? 'bg-slate-800 border-primary text-white' : 'bg-transparent border-border text-textMuted hover:text-textMain'}`}
              >Dark</button>
            </div>
          </div>
        </SettingsSection>

        {/* Validation */}
        <SettingsSection title="Validation Rules" icon={<Shield size={20} className="text-primary"/>}>
          <div className="flex items-center justify-between p-4 bg-background rounded-xl border border-border mb-3">
            <div>
              <p className="font-semibold text-textMain">Default Severity</p>
              <p className="text-sm text-textMuted">Set the default severity when parsing new rules.</p>
            </div>
            <select className="input-field w-32 bg-surface border border-border text-textMain rounded-lg px-2 py-1">
              <option>ERROR</option>
              <option>WARNING</option>
              <option>FATAL</option>
            </select>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-background rounded-xl border border-border">
            <div>
              <p className="font-semibold text-textMain">Strict Namespace Checking</p>
              <p className="text-sm text-textMuted">Require exact UBL namespaces instead of fallback generalization.</p>
            </div>
            <Toggle />
          </div>
        </SettingsSection>

        {/* Data & Cache */}
        <SettingsSection title="Data & Caching" icon={<Database size={20} className="text-success"/>}>
          <div className="flex items-center justify-between p-4 bg-background rounded-xl border border-border">
            <div>
              <p className="font-semibold text-textMain">Duplicate Invoice Cache</p>
              <p className="text-sm text-textMuted">Maintain a local cache to reject duplicate invoice identifiers instantly.</p>
            </div>
            <Toggle defaultChecked />
          </div>
        </SettingsSection>
        
        {/* Notifications */}
        <SettingsSection title="Notifications" icon={<Bell size={20} className="text-accent"/>}>
          <div className="flex items-center justify-between p-4 bg-background rounded-xl border border-border">
            <div>
              <p className="font-semibold text-textMain">Email Alerts on Fatal Errors</p>
              <p className="text-sm text-textMuted">Get notified when a FATAL validation failure occurs.</p>
            </div>
            <Toggle />
          </div>
        </SettingsSection>

        <div className="flex items-center gap-4 pt-6 mt-6 border-t border-border">
          <button onClick={handleSave} className="btn-primary shadow-lg">
            <Save size={18} /> Save Changes
          </button>
          <button className="btn-secondary text-accent hover:bg-accent/10 border-accent/20">
            <RefreshCw size={18} /> Reset Defaults
          </button>
          
          {saved && <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-sm font-medium text-success ml-auto">Settings saved successfully!</motion.span>}
        </div>
      </div>
    </div>
  );
}

function SettingsSection({ title, icon, children }) {
  return (
    <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6 bg-surface">
      <h2 className="text-lg font-bold text-textMain flex items-center gap-3 mb-6 pb-4 border-b border-border">
        {icon} {title}
      </h2>
      <div>{children}</div>
    </motion.section>
  );
}

function Toggle({ defaultChecked = false }) {
  const [checked, setChecked] = useState(defaultChecked);
  return (
    <button 
      onClick={() => setChecked(!checked)}
      className={`w-12 h-6 rounded-full transition-colors relative ${checked ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-600'}`}
    >
      <div className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${checked ? 'left-7' : 'left-1'}`} />
    </button>
  );
}
