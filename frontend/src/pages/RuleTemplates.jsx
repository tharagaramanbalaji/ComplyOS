import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Copy, Heart, BookOpen } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const TEMPLATES = [
  { id: 1, category: 'Required Fields', text: 'issue date is required', type: 'required_field', color: 'bg-indigo-100 text-indigo-700' },
  { id: 2, category: 'Required Fields', text: 'currency code is required', type: 'required_field', color: 'bg-indigo-100 text-indigo-700' },
  { id: 3, category: 'Tax Rules', text: 'tax category must be valid', type: 'tax_category_validation', color: 'bg-emerald-100 text-emerald-700' },
  { id: 4, category: 'Tax Rules', text: 'If tax amount > 0 tax category required', type: 'conditional_required_field', color: 'bg-emerald-100 text-emerald-700' },
  { id: 5, category: 'Calculations', text: 'payable amount must equal taxable amount + tax amount', type: 'amount_calculation', color: 'bg-amber-100 text-amber-700' },
  { id: 6, category: 'Date Rules', text: 'issue date cannot be in the future', type: 'date_validation', color: 'bg-rose-100 text-rose-700' },
  { id: 7, category: 'Calculations', text: 'Tax amount should be greater than 0', type: 'numeric_comparison', color: 'bg-amber-100 text-amber-700' },
  { id: 8, category: 'Duplicate Checks', text: 'invoice identifier must be unique', type: 'duplicate_field_check', color: 'bg-purple-100 text-purple-700' },
  { id: 9, category: 'Currency Rules', text: 'currency must be consistent', type: 'currency_consistency', color: 'bg-blue-100 text-blue-700' },
];

export default function RuleTemplates() {
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  const navigate = useNavigate();

  const categories = ['All', ...new Set(TEMPLATES.map(t => t.category))];

  const filtered = TEMPLATES.filter(t => 
    (activeCategory === 'All' || t.category === activeCategory) &&
    t.text.toLowerCase().includes(search.toLowerCase())
  );

  const handleUseTemplate = (text) => {
    // Pass via state to RuleStudio
    navigate('/studio', { state: { templateText: text } });
  };

  return (
    <div className="p-8 h-full flex flex-col">
      <header className="mb-8">
        <h1 className="text-3xl font-extrabold text-textMain">Rule Library</h1>
        <p className="text-textMuted mt-2">Browse, copy, and modify pre-built deterministic compliance rules.</p>
      </header>

      <div className="flex flex-col md:flex-row gap-4 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 text-textMuted" size={20} />
          <input 
            type="text" 
            placeholder="Search templates..." 
            className="input-field pl-10"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
          {categories.map(c => (
            <button 
              key={c} 
              onClick={() => setActiveCategory(c)}
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition ${
                activeCategory === c ? 'bg-primary text-white shadow-md' : 'bg-surface text-textMuted border border-border hover:bg-background'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 flex-1 overflow-y-auto pb-10">
        {filtered.map((t, i) => (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            key={t.id} 
            className="glass-panel p-6 bg-surface hover:shadow-xl transition-shadow flex flex-col h-full group"
          >
            <div className="flex justify-between items-start mb-4">
              <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${t.color}`}>
                {t.category}
              </span>
              <button className="text-border hover:text-accent transition">
                <Heart size={18} />
              </button>
            </div>
            
            <p className="text-lg font-medium text-textMain mb-6 flex-1">
              "{t.text}"
            </p>
            
            <div className="flex items-center gap-3 pt-4 border-t border-border">
              <button onClick={() => handleUseTemplate(t.text)} className="btn-primary py-1.5 flex-1 text-sm shadow">
                Use Template
              </button>
              <button onClick={() => navigator.clipboard.writeText(t.text)} className="btn-secondary py-1.5 px-3 text-textMuted hover:text-textMain">
                <Copy size={16} />
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
