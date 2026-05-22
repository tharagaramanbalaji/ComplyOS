import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, CheckCircle2, Zap, Code, FileSearch } from 'lucide-react';
import './LandingPage.css';

const LandingPage = ({ onStart }) => {
  return (
    <div className="landing-container">
      {/* Ambient background glows */}
      <div className="glow-orb orb-1"></div>
      <div className="glow-orb orb-2"></div>

      <nav className="landing-navbar">
        <div className="landing-logo">
          <CheckCircle2 size={28} className="logo-icon" />
          <span>ComplyOS</span>
        </div>
        <div className="navbar-tag">
          <span className="pill">v1.0.0 Stable</span>
        </div>
      </nav>

      <main className="landing-main">
        <motion.div 
          className="hero-section"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >

          <h1 className="hero-title">
            Validate E-Invoices with <span className="gradient-text">Natural Language</span>
          </h1>

          <p className="hero-subtitle">
            ComplyOS instantly translates plain English business rules into optimized XSLT validation scripts. Validate XML invoices deterministically with zero code overhead.
          </p>

          <motion.button 
            className="cta-btn"
            onClick={onStart}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.98 }}
          >
            Launch App Dashboard
            <ArrowRight size={20} className="arrow-icon" />
          </motion.button>
        </motion.div>

        <motion.div 
          className="features-grid"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
        >
          <div className="feature-card">
            <div className="feature-icon-wrapper blue">
              <Zap size={24} />
            </div>
            <h3>NLP Parser</h3>
            <p>Automatically extract rule operators, variables, and numerical thresholds from fuzzy English sentences.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper purple">
              <Code size={24} />
            </div>
            <h3>XSLT Compiler</h3>
            <p>Compile rule trees directly into high-speed XSLT sheets executable natively on standard XML parsers.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon-wrapper green">
              <FileSearch size={24} />
            </div>
            <h3>Diagnostic Trace</h3>
            <p>Receive detailed element traces and reports mapping rule violations directly to specific XML elements.</p>
          </div>
        </motion.div>
      </main>

      <footer className="landing-footer">
        <p>© 2026 ComplyOS. Automated E-Invoice Compliance Engine.</p>
      </footer>
    </div>
  );
};

export default LandingPage;
