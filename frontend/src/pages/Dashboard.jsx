import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, ShieldCheck, AlertTriangle, FileText, CheckCircle } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export default function Dashboard() {
  const [stats, setStats] = useState({ total_rules: 0, rule_types: [] });

  useEffect(() => {
    axios.get(`${API_URL}/stats`).then(res => setStats(res.data)).catch(console.error);
  }, []);

  const mockData = [
    { name: 'Passed', value: 85, color: '#10b981' },
    { name: 'Failed', value: 15, color: '#f43f5e' }
  ];

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-extrabold text-textMain">Platform Overview</h1>
        <p className="text-textMuted mt-2 font-medium">Real-time compliance validation metrics.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard title="Active Rules" value={stats.total_rules || 150} icon={<ShieldCheck size={24} className="text-primary"/>} color="bg-primary/5" border="border-primary/20" />
        <StatCard title="Invoices Processed" value="1,204" icon={<FileText size={24} className="text-secondary"/>} color="bg-secondary/10" border="border-secondary/20" />
        <StatCard title="Validation Errors" value="182" icon={<AlertTriangle size={24} className="text-warning"/>} color="bg-warning/10" border="border-warning/20" trend="+12% this week" />
        <StatCard title="System Status" value="Online" icon={<Activity size={24} className="text-success"/>} color="bg-success/10" border="border-success/20" subtitle="99.9% uptime" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6 bg-surface">
          <h2 className="text-xl font-bold mb-6 text-textMain">Validation Outcome</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={mockData} innerRadius={70} outerRadius={90} paddingAngle={5} dataKey="value" stroke="none">
                  {mockData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip contentStyle={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-textMain)', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-8 mt-4">
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-success shadow-sm"></div><span className="text-sm font-semibold text-textMuted">Passed (85%)</span></div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-accent shadow-sm"></div><span className="text-sm font-semibold text-textMuted">Failed (15%)</span></div>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-panel p-6 bg-surface">
          <h2 className="text-xl font-bold mb-6 text-textMain">Recent Validation Traces</h2>
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-background rounded-xl border border-border hover:border-primary/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-full ${i % 3 === 0 ? 'bg-accent/10 text-accent' : 'bg-success/10 text-success'}`}>
                    {i % 3 === 0 ? <AlertTriangle size={16} /> : <CheckCircle size={16} />}
                  </div>
                  <div>
                    <p className="font-bold text-sm text-textMain">INV-2023-{1000 + i}</p>
                    <p className="text-xs text-textMuted mt-0.5">Processed {i * 2} mins ago</p>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-bold tracking-wide ${i % 3 === 0 ? 'bg-accent/10 text-accent' : 'bg-success/10 text-success'}`}>
                  {i % 3 === 0 ? 'FAIL' : 'PASS'}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, subtitle, trend, color, border }) {
  return (
    <motion.div whileHover={{ y: -5 }} className={`glass-panel p-6 flex flex-col justify-between relative overflow-hidden ${color} border ${border}`}>
      <div className="flex justify-between items-start mb-4 relative z-10">
        <div>
          <p className="text-textMuted text-sm font-bold uppercase tracking-wider">{title}</p>
          <h3 className="text-4xl font-black mt-2 text-textMain">{value}</h3>
        </div>
        <div className="p-3 bg-surface rounded-2xl shadow-sm border border-border">
          {icon}
        </div>
      </div>
      {trend && <p className="text-xs text-accent font-bold relative z-10">{trend}</p>}
      {subtitle && <p className="text-xs text-success font-bold relative z-10">{subtitle}</p>}
      
      {/* Decorative gradient blob */}
      <div className="absolute -bottom-6 -right-6 w-32 h-32 bg-background/40 rounded-full blur-2xl"></div>
    </motion.div>
  );
}
