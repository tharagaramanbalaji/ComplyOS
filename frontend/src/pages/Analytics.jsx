import React from 'react';
import { motion } from 'framer-motion';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';

const trendData = [
  { name: 'Mon', pass: 400, fail: 24 },
  { name: 'Tue', pass: 300, fail: 13 },
  { name: 'Wed', pass: 550, fail: 48 },
  { name: 'Thu', pass: 278, fail: 39 },
  { name: 'Fri', pass: 189, fail: 48 },
  { name: 'Sat', pass: 239, fail: 38 },
  { name: 'Sun', pass: 349, fail: 43 },
];

const usageData = [
  { name: 'Required Fields', count: 4000, color: '#8b5cf6' },
  { name: 'Tax Rules', count: 3000, color: '#10b981' },
  { name: 'Calculations', count: 2000, color: '#f59e0b' },
  { name: 'Date Rules', count: 2780, color: '#f43f5e' },
  { name: 'Duplicates', count: 1890, color: '#06b6d4' },
];

export default function Analytics() {
  return (
    <div className="p-8 max-w-7xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-extrabold text-textMain">Analytics & Insights</h1>
        <p className="text-textMuted mt-2">Monitor validation trends, failure hotspots, and rule execution metrics.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Trend Chart */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6 bg-surface">
          <h2 className="text-xl font-bold mb-6 text-textMain">Weekly Validation Volume</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorPass" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorFail" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <RechartsTooltip contentStyle={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-textMain)', borderRadius: '12px', boxShadow: '0 10px 25px -5px rgb(0 0 0 / 0.1)' }} />
                <Area type="monotone" dataKey="pass" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorPass)" />
                <Area type="monotone" dataKey="fail" stroke="#f43f5e" strokeWidth={3} fillOpacity={1} fill="url(#colorFail)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Usage Bar Chart */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-panel p-6 bg-surface">
          <h2 className="text-xl font-bold mb-6 text-textMain">Rule Category Execution</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={usageData} layout="vertical" margin={{ top: 0, right: 0, left: 40, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} width={100} />
                <RechartsTooltip cursor={{fill: 'var(--color-background)'}} contentStyle={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-textMain)', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={24}>
                  {usageData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Structured Heatmap Analysis */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-panel p-6 bg-surface">
        <h2 className="text-xl font-bold mb-2 text-textMain">Failure Density Matrix</h2>
        <p className="text-sm text-textMuted mb-6">Analyze validation failures by Rule Category across the week.</p>
        
        <div className="overflow-x-auto">
          <div className="min-w-[600px]">
            {/* Header row (Days) */}
            <div className="flex mb-2">
              <div className="w-32 flex-shrink-0"></div>
              {trendData.map(d => (
                <div key={d.name} className="flex-1 text-center text-xs font-semibold text-textMuted uppercase tracking-wider">{d.name}</div>
              ))}
            </div>
            
            {/* Grid rows (Categories) */}
            <div className="space-y-2">
              {usageData.map((category) => (
                <div key={category.name} className="flex items-center">
                  <div className="w-32 flex-shrink-0 text-sm font-medium text-textMain truncate pr-4">{category.name}</div>
                  {trendData.map((day, i) => {
                    // Generate a deterministic but varied intensity based on category and day
                    const hash = category.name.length * day.fail;
                    const intensity = (hash % 100) / 100;
                    
                    let textClass = 'text-transparent';
                    let intensityClass = 'bg-background';
                    
                    if (intensity > 0.8) {
                      intensityClass = 'bg-accent';
                      textClass = 'text-white';
                    } else if (intensity > 0.6) {
                      intensityClass = 'bg-amber-400 dark:bg-warning';
                      textClass = 'text-amber-900 dark:text-white';
                    } else if (intensity > 0.3) {
                      intensityClass = 'bg-primary/40 dark:bg-primary';
                      textClass = 'text-primary dark:text-white';
                    }
                    
                    return (
                      <div key={`${category.name}-${day.name}`} className="flex-1 px-1">
                        <div 
                          className={`h-10 rounded-md flex items-center justify-center transition-transform hover:scale-110 cursor-pointer shadow-sm ${intensityClass} ${textClass}`}
                          title={`${category.name} on ${day.name}: ${Math.floor(intensity * 50)} failures`}
                        >
                          <span className="text-xs font-bold">{Math.floor(intensity * 50)}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="flex justify-end items-center gap-2 mt-6 text-xs font-medium text-textMuted">
          <span>Low</span>
          <div className="w-4 h-4 rounded-sm bg-background"></div>
          <div className="w-4 h-4 rounded-sm bg-primary/40 dark:bg-primary"></div>
          <div className="w-4 h-4 rounded-sm bg-amber-400 dark:bg-warning"></div>
          <div className="w-4 h-4 rounded-sm bg-accent"></div>
          <span>High (Failures)</span>
        </div>
      </motion.div>
    </div>
  );
}
