import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, ShieldCheck, Zap, Database, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Decorative background blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-3xl opacity-50" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent/10 rounded-full blur-3xl opacity-50" />
      <div className="absolute top-[20%] right-[20%] w-[20%] h-[20%] bg-emerald-400/10 rounded-full blur-3xl opacity-50" />

      <div className="max-w-6xl mx-auto px-6 py-20 relative z-10">
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-4xl mx-auto mt-10"
        >
          <span className="px-4 py-1.5 rounded-full bg-surface shadow-sm border border-border text-primary text-sm font-semibold tracking-wide uppercase mb-6 inline-block">
            Compliance 2.0
          </span>
          <h1 className="text-5xl md:text-7xl font-extrabold text-textMain tracking-tight leading-tight mb-8">
            Natural Language <br/>
            <span className="bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
              Compliance Engine
            </span>
          </h1>
          <p className="text-xl text-textMuted mb-10 max-w-2xl mx-auto leading-relaxed">
            Write XML validation rules in plain English. Automatically generate deterministic XSLT mappings and validate your invoices instantly with zero hardcoding.
          </p>
          
          <div className="flex items-center justify-center gap-4">
            <Link to="/studio" className="btn-primary px-8 py-3 text-lg shadow-lg shadow-primary/25">
              Start Writing Rules <ArrowRight size={20} />
            </Link>
            <Link to="/validator" className="btn-secondary px-8 py-3 text-lg bg-surface shadow-sm hover:shadow">
              Validate XML
            </Link>
          </div>
        </motion.div>

        {/* Workflow Animation Section */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="mt-24"
        >
          <div className="glass-panel p-8 bg-surface">
            <h3 className="text-center text-lg font-semibold text-textMuted mb-8 uppercase tracking-widest">How it works</h3>
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <WorkflowStep icon={<Zap className="text-amber-500" />} title="1. Natural Language" desc="Write 'Tax amount > 0'" />
              <ArrowRight className="hidden md:block text-gray-300" />
              <WorkflowStep icon={<Database className="text-primary" />} title="2. IR Mapping" desc="Deterministic structured rules" />
              <ArrowRight className="hidden md:block text-gray-300" />
              <WorkflowStep icon={<FileCode2 className="text-accent" />} title="3. Generate XSLT" desc="Engine creates mappings" />
              <ArrowRight className="hidden md:block text-gray-300" />
              <WorkflowStep icon={<ShieldCheck className="text-emerald-500" />} title="4. Validate XML" desc="Explainable PASS/FAIL" />
            </div>
          </div>
        </motion.div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mt-24">
          <FeatureCard 
            title="Schema Independent" 
            desc="Built-in generalization layer dynamically extracts data from any standard structure using XPath fallbacks."
            icon={<CheckCircle2 size={24} className="text-primary"/>}
          />
          <FeatureCard 
            title="Explainable Traces" 
            desc="Every validation generates a deterministic log telling you exactly why an invoice passed or failed."
            icon={<CheckCircle2 size={24} className="text-emerald-500"/>}
          />
          <FeatureCard 
            title="Evaluator Ready" 
            desc="Produces strict XSLT mapping scripts, satisfying enterprise compliance constraints instantly."
            icon={<CheckCircle2 size={24} className="text-accent"/>}
          />
        </div>
      </div>
    </div>
  );
}

function WorkflowStep({ icon, title, desc }) {
  return (
    <div className="flex flex-col items-center text-center p-4 bg-background rounded-2xl shadow-sm border border-border flex-1 w-full">
      <div className="w-12 h-12 rounded-full bg-surface flex items-center justify-center mb-4">
        {icon}
      </div>
      <h4 className="font-bold text-textMain">{title}</h4>
      <p className="text-sm text-textMuted mt-1">{desc}</p>
    </div>
  );
}

function FeatureCard({ title, desc, icon }) {
  return (
    <div className="glass-panel p-8 bg-surface hover:bg-background transition-colors cursor-default">
      <div className="w-10 h-10 rounded-xl bg-background flex items-center justify-center mb-6 shadow-sm border border-border">
        {icon}
      </div>
      <h3 className="text-xl font-bold mb-3 text-textMain">{title}</h3>
      <p className="text-textMuted leading-relaxed">{desc}</p>
    </div>
  );
}

// Ensure icons used above are imported. FileCode2 is missing in the import list of Home.
// Will add it via standard lucide-react import
import { FileCode2 } from 'lucide-react';
