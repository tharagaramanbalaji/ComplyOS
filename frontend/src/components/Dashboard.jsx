import React, { useState, useEffect, useRef } from 'react';
import { UploadCloud, CheckCircle2, XCircle, FileJson, Settings2, Play, Loader2, MessageSquare, Send, Trash2, ShoppingCart, ArrowRight, Download } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Dashboard = () => {
  const [sessionId] = useState(() => 'sess-' + Math.random().toString(36).substring(2, 9));
  const [messages, setMessages] = useState([
    { id: '1', role: 'bot', content: "👋 Welcome to ComplyOS Copilot! Tell me what compliance rules you'd like to build for your e-invoices. You can add multiple rules into a unified bundle.", quickReplies: [] }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loadingChat, setLoadingChat] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL 
    ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, "") 
    : (import.meta.env.DEV ? 'http://localhost:8000' : '');

  // Cart & Compiler State
  const [cart, setCart] = useState([]);
  const [xsltCode, setXsltCode] = useState(null);
  const [file, setFile] = useState(null);
  const [validationStatus, setValidationStatus] = useState(null);
  const [loadingExecute, setLoadingExecute] = useState(false);
  const [extractedData, setExtractedData] = useState(null);

  const messagesEndRef = useRef(null);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => { scrollToBottom(); }, [messages]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  // --- COPILOT CONVERSATIONAL HANDLERS ---
  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;
    const userMsg = inputMessage;
    setInputMessage('');
    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', content: userMsg }]);
    setLoadingChat(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/validate/chat/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, user_message: userMsg })
      });
      const data = await res.json();
      if (!res.ok) {
        setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', content: "❌ Error: " + (data.detail || "Server error") }]);
        setLoadingChat(false);
        return;
      }
      
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'bot',
        content: data.bot_message,
        quickReplies: data.quick_replies || []
      }]);
      
      if (data.cart) setCart(data.cart);
      if (data.compiled_xslt) {
        setXsltCode(data.compiled_xslt);
        setValidationStatus(null);
      }
    } catch (e) {
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', content: "❌ Could not connect to backend engine." }]);
    }
    setLoadingChat(false);
  };

  const handleQuickReply = async (reply) => {
    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', content: reply.label }]);
    setLoadingChat(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/validate/chat/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          user_choice: { action: reply.action, value: reply.value }
        })
      });
      const data = await res.json();
      
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'bot',
        content: data.bot_message,
        quickReplies: data.quick_replies || []
      }]);
      
      if (data.cart) setCart(data.cart);
      if (data.compiled_xslt) {
        setXsltCode(data.compiled_xslt);
        setValidationStatus(null);
      }
    } catch (e) {
      alert("Error confirming value.");
    }
    setLoadingChat(false);
  };

  const handleClearCart = async () => {
    setLoadingChat(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/validate/chat/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, action: 'clear_cart' })
      });
      const data = await res.json();
      setCart([]);
      setXsltCode(null);
      setValidationStatus(null);
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', content: data.bot_message }]);
    } catch (e) {
      alert("Error clearing cart.");
    }
    setLoadingChat(false);
  };

  const handleExecuteXML = async () => {
    if (!xsltCode || !file) return;
    setLoadingExecute(true);
    const formData = new FormData();
    formData.append('xslt_code', xsltCode);
    formData.append('invoice_file', file);

    try {
      const text = await file.text();
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(text, "text/xml");
      
      // If there are rules in cart, pick first field for demonstration trace
      const sampleRule = cart[0] || {};
      const targetField = sampleRule.field || "invoice_id";
      const cleanField = targetField.split('.').pop();
      
      const nodes = xmlDoc.getElementsByTagName(cleanField);
      let foundValue = "Not Found in Document";
      if (nodes && nodes.length > 0) {
        const uniqueVals = Array.from(new Set(Array.from(nodes).map(n => n.textContent.trim()).filter(Boolean)));
        foundValue = uniqueVals.join(", ");
      }
      
      setExtractedData({
        field: cleanField,
        value: foundValue
      });
    } catch (e) {
      console.log("Extraction error:", e);
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/validate/execute`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setValidationStatus(data.validation_status);
    } catch (e) {
      alert("Error executing validation.");
    }
    setLoadingExecute(false);
  };

  const handleExportXSLT = () => {
    if (!xsltCode) return;
    const blob = new Blob([xsltCode], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `complyos_master_bundle_${Date.now()}.xslt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Helper to parse granular validation output
  let isPass = validationStatus === 'PASS';
  let bannerStatus = validationStatus;
  let ruleBreakdowns = [];

  if (validationStatus && validationStatus.includes('BUNDLE_')) {
    const lines = validationStatus.split('\n').map(l => l.trim()).filter(Boolean);
    isPass = lines[0] === 'BUNDLE_PASS';
    bannerStatus = isPass ? 'BUNDLE PASS' : 'BUNDLE FAIL';
    ruleBreakdowns = lines.slice(1);
  }

  return (
    <div className="pipeline-view" style={{ paddingBottom: '60px' }}>
      <div className="grid-2">
        {/* LEFT COLUMN: INTERACTIVE COPILOT CHAT */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '650px', padding: 0 }}>
          <div className="card-header" style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MessageSquare size={18} color="var(--primary)" />
              <span style={{ fontWeight: 600 }}>1. Rule Copilot (Interactive Builder)</span>
            </div>
            {cart.length > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '12px', backgroundColor: 'var(--primary-bg)', color: 'var(--primary)', padding: '4px 10px', borderRadius: '20px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShoppingCart size={14} /> Bundle Cart: {cart.length}
                </span>
                <button onClick={handleClearCart} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--error-text)', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '13px' }} title="Clear Rule Cart">
                  <Trash2 size={16} /> Clear
                </button>
              </div>
            )}
          </div>

          {/* Chat Messages Timeline */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', backgroundColor: '#f8fafc' }}>
            {messages.map((msg, idx) => (
              <motion.div
                key={msg.id || idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}
              >
                <div
                  style={{
                    backgroundColor: msg.role === 'user' ? 'var(--primary)' : '#fff',
                    color: msg.role === 'user' ? '#fff' : 'var(--text-main)',
                    padding: '12px 16px',
                    borderRadius: msg.role === 'user' ? '16px 16px 0 16px' : '16px 16px 16px 0',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                    border: msg.role === 'user' ? 'none' : '1px solid #e2e8f0',
                    fontSize: '14px',
                    lineHeight: '1.5'
                  }}
                >
                  {msg.content}
                </div>

                {/* Render Quick-Reply Verification Pills */}
                {msg.quickReplies && msg.quickReplies.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '4px' }}>
                    {msg.quickReplies.map((reply, rIdx) => (
                      <button
                        key={rIdx}
                        onClick={() => handleQuickReply(reply)}
                        style={{
                          backgroundColor: '#fff',
                          border: '1px solid var(--primary)',
                          color: 'var(--primary)',
                          padding: '6px 12px',
                          borderRadius: '20px',
                          fontSize: '13px',
                          fontWeight: 500,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                          transition: 'all 0.2s'
                        }}
                        onMouseOver={(e) => { e.currentTarget.style.backgroundColor = 'var(--primary)'; e.currentTarget.style.color = '#fff'; }}
                        onMouseOut={(e) => { e.currentTarget.style.backgroundColor = '#fff'; e.currentTarget.style.color = 'var(--primary)'; }}
                      >
                        {reply.label} <ArrowRight size={14} />
                      </button>
                    ))}
                  </div>
                )}
              </motion.div>
            ))}
            {loadingChat && (
              <div style={{ alignSelf: 'flex-start', backgroundColor: '#fff', padding: '12px 16px', borderRadius: '16px 16px 16px 0', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Loader2 size={16} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
                <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>ComplyOS Copilot is thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Bar */}
          <div style={{ padding: '16px', borderTop: '1px solid var(--border-color)', backgroundColor: '#fff', display: 'flex', gap: '12px' }}>
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleSendMessage(); }}
              placeholder="Type your compliance rule (e.g., 'The tax category must be XYZ')..."
              style={{ flex: 1, padding: '12px 16px', border: '1px solid #cbd5e1', borderRadius: '24px', outline: 'none', fontSize: '14px' }}
            />
            <button
              className="btn-primary"
              onClick={handleSendMessage}
              disabled={loadingChat || !inputMessage.trim()}
              style={{ borderRadius: '50%', width: '48px', height: '48px', padding: 0, display: 'flex', justifyContent: 'center', alignItems: 'center' }}
            >
              <Send size={18} />
            </button>
          </div>
        </div>

        {/* RIGHT COLUMN: ACCUMULATED IR CART & COMPILED XSLT */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="card" style={{ height: '310px', display: 'flex', flexDirection: 'column', padding: 0 }}>
            <div className="card-header" style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ fontWeight: 600 }}>2. Bundle Rule Cart (JSON IR)</span>
              <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 500 }}>{cart.length} active rules</span>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: 0, margin: 0, backgroundColor: '#1e293b', color: '#f8fafc' }}>
              <pre style={{ border: 'none', borderRadius: 0, margin: 0, padding: '16px', fontSize: '13px', height: '100%', backgroundColor: 'transparent', color: 'inherit' }}>
                {cart.length > 0 ? JSON.stringify(cart, null, 2) : "// Your rule shopping cart is empty.\n// Type a rule in the chat to begin."}
              </pre>
            </div>
          </div>

          <div className="card" style={{ height: '310px', display: 'flex', flexDirection: 'column', padding: 0 }}>
            <div className="card-header" style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 600 }}>3. Unified Master XSLT Bundle</span>
              {xsltCode && (
                <button 
                  onClick={handleExportXSLT} 
                  style={{ backgroundColor: '#f0fdf4', border: '1px solid #22c55e', color: '#166534', padding: '6px 14px', borderRadius: '20px', fontSize: '12px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', transition: 'all 0.2s', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}
                  onMouseOver={(e) => { e.currentTarget.style.backgroundColor = '#22c55e'; e.currentTarget.style.color = '#fff'; }}
                  onMouseOut={(e) => { e.currentTarget.style.backgroundColor = '#f0fdf4'; e.currentTarget.style.color = '#166534'; }}
                  title="Download Compiled XSLT File"
                >
                  <Download size={14} /> Export .xslt
                </button>
              )}
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: 0, margin: 0, backgroundColor: '#0f172a', color: '#38bdf8' }}>
              <pre style={{ border: 'none', borderRadius: 0, margin: 0, padding: '16px', fontSize: '13px', height: '100%', backgroundColor: 'transparent', color: 'inherit' }}>
                {xsltCode ? xsltCode : "<!-- Compiled multi-rule XSLT engine bundle will appear here -->"}
              </pre>
            </div>
          </div>
        </div>
      </div>

      {/* STEP 4: EXECUTION ZONE */}
      <div className="card" style={{ marginTop: '24px' }}>
        <div className="card-header">
          4. Execution Trace Validation (Upload Invoice)
        </div>
        <div className="card-body">
          <div className="upload-zone" onClick={() => document.getElementById('file-upload').click()} style={{ cursor: 'pointer' }}>
            <UploadCloud size={32} color={file ? "var(--success-text)" : "var(--primary)"} style={{ marginBottom: '12px' }} />
            <p style={{ fontWeight: 500, color: file ? 'var(--success-text)' : 'var(--text-main)' }}>
              {file ? file.name : "Click to upload an XML invoice file"}
            </p>
            <input 
              id="file-upload" 
              type="file" 
              accept=".xml" 
              style={{ display: 'none' }} 
              onChange={handleFileChange} 
            />
          </div>
          <button 
            className="btn-primary" 
            style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', marginTop: '16px' }}
            onClick={handleExecuteXML}
            disabled={loadingExecute || !xsltCode || !file}
          >
            {loadingExecute ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={16} />}
            {loadingExecute ? "Evaluating XML Invoice..." : "Run Validation Suite"}
          </button>
        </div>
      </div>

      {/* FINAL EXECUTION TRACE BOX */}
      <AnimatePresence>
        {validationStatus && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }} 
            animate={{ opacity: 1, y: 0 }} 
            style={{ display: 'flex', gap: '24px', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '24px', backgroundColor: '#fff', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)', marginTop: '24px' }}
          >
            <div style={{ flex: '0 0 300px', backgroundColor: isPass ? 'var(--success-bg)' : 'var(--error-bg)', border: `1px solid ${isPass ? 'var(--success-border)' : 'var(--error-border)'}`, borderRadius: '8px', padding: '32px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px', textOverflow: 'ellipsis', overflow: 'hidden' }}>
              {isPass ? <CheckCircle2 size={64} color="var(--success-text)" /> : <XCircle size={64} color="var(--error-text)" />}
              <h2 style={{ fontSize: '28px', fontWeight: 700, color: isPass ? 'var(--success-text)' : 'var(--error-text)', margin: 0, textAlign: 'center' }}>
                {bannerStatus}
              </h2>
            </div>

            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>Execution Trace Lineage</h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px' }}>
                  <span style={{ fontSize: '14px', color: 'var(--text-main)' }}>1. Rules Loaded: {cart.length} Active Rules in Compliance Bundle</span>
                  <CheckCircle2 size={16} color="var(--success-text)" />
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px' }}>
                  <span style={{ fontSize: '14px', color: 'var(--text-main)' }}>2. Master XSLT 1.0 Document Compiled with Granular Tracing</span>
                  <CheckCircle2 size={16} color="var(--success-text)" />
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px' }}>
                  <span style={{ fontSize: '14px', color: 'var(--text-main)' }}>3. XML Evaluated via lxml Engine (<span style={{ color: 'var(--primary)', fontWeight: 600 }}>&lt; 15ms</span>)</span>
                  <CheckCircle2 size={16} color="var(--success-text)" />
                </div>

                {extractedData && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px', backgroundColor: '#f8fafc', padding: '12px', borderRadius: '6px' }}>
                    <span style={{ fontSize: '14px', color: 'var(--text-main)' }}>
                      ↳ <strong>Sample Extracted Data:</strong> <code>&lt;{extractedData.field}&gt;</code> = <strong style={{ color: 'var(--primary)' }}>{extractedData.value}</strong>
                    </span>
                    <CheckCircle2 size={16} color="var(--success-text)" />
                  </div>
                )}
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '8px', marginTop: '4px' }}>
                  <span style={{ fontSize: '14px', fontWeight: 500 }}>4. Bundle Compliance Status</span>
                  {isPass ? <CheckCircle2 size={16} color="var(--success-text)" /> : <XCircle size={16} color="var(--error-text)" />}
                </div>

                {ruleBreakdowns.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px', borderTop: '1px solid #e2e8f0', paddingTop: '12px' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)' }}>Granular Rule Breakdown:</h4>
                    {ruleBreakdowns.map((rb, rIdx) => {
                      const passed = rb.startsWith('[PASS]');
                      return (
                        <div key={rIdx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: passed ? '#f0fdf4' : '#fef2f2', padding: '10px 14px', borderRadius: '6px', border: `1px solid ${passed ? '#bbf7d0' : '#fecaca'}` }}>
                          <span style={{ fontSize: '13px', fontWeight: 500, color: passed ? '#166534' : '#991b1b' }}>{rb}</span>
                          {passed ? <CheckCircle2 size={16} color="var(--success-text)" /> : <XCircle size={16} color="var(--error-text)" />}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default Dashboard;
