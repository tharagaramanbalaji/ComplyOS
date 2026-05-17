import React, { useState } from 'react';
import { UploadCloud, CheckCircle2, XCircle, FileJson, Settings2, Play, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Dashboard = () => {
  const [ruleText, setRuleText] = useState('');
  const [file, setFile] = useState(null);
  
  // Step-by-step State
  const [jsonIr, setJsonIr] = useState(null);
  const [xsltCode, setXsltCode] = useState(null);
  const [validationStatus, setValidationStatus] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  
  // Loading states
  const [loadingParse, setLoadingParse] = useState(false);
  const [loadingCompile, setLoadingCompile] = useState(false);
  const [loadingExecute, setLoadingExecute] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleParse = async () => {
    if (!ruleText) return alert("Please enter a rule.");
    setLoadingParse(true);
    try {
      const response = await fetch('http://localhost:8000/api/validate/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rule_text: ruleText })
      });
      const data = await response.json();
      if (!response.ok) {
        alert("❌ NLP Engine Error: " + data.detail);
        setLoadingParse(false);
        return;
      }
      setJsonIr(data.json_ir);
      setXsltCode(null);
      setValidationStatus(null);
    } catch (e) {
      alert("Error connecting to backend.");
    }
    setLoadingParse(false);
  };

  const handleCompile = async () => {
    if (!jsonIr) return;
    setLoadingCompile(true);
    try {
      const response = await fetch('http://localhost:8000/api/validate/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ json_ir: jsonIr })
      });
      const data = await response.json();
      setXsltCode(data.xslt_code);
      setValidationStatus(null);
    } catch (e) {
      alert("Error compiling XSLT.");
    }
    setLoadingCompile(false);
  };

  const handleExecuteXML = async () => {
    if (!xsltCode || !file) return;
    setLoadingExecute(true);
    const formData = new FormData();
    formData.append('xslt_code', xsltCode);
    formData.append('json_ir_str', JSON.stringify(jsonIr));
    formData.append('invoice_file', file);

    // --- CLIENT-SIDE XML EXTRACTION FOR XAI TRACEABILITY ---
    try {
      const text = await file.text();
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(text, "text/xml");
      
      const targetField = jsonIr.field || jsonIr.condition_field || "invoice_id";
      // Strip array syntax (e.g. line_items[*].tax_amount -> tax_amount)
      const cleanField = targetField.split('.').pop(); 
      
      const nodes = xmlDoc.getElementsByTagName(cleanField);
      let foundValue = "Not Found in Document";
      if (nodes && nodes.length > 0) {
        foundValue = nodes[0].textContent;
      }
      
      setExtractedData({
        field: cleanField,
        value: foundValue
      });
    } catch (e) {
      console.log("Client-side extraction failed:", e);
    }

    try {
      const response = await fetch('http://localhost:8000/api/validate/execute', {
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

  return (
    <div className="pipeline-view">
      <div className="grid-2">
        {/* Step 1: Rule Input */}
        <div className="card">
          <div className="card-header">
            1. Natural Language Rule
            <FileJson size={16} color="var(--text-muted)"/>
          </div>
          <div className="card-body">
            <textarea 
              value={ruleText}
              onChange={(e) => setRuleText(e.target.value)}
              placeholder="Write your compliance rule in simple English..."
            />
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <span style={{fontSize: '13px', color: 'var(--text-muted)'}}>
                💡 Ex: 'The total amount must be > 0'
              </span>
              <button className="btn-primary" onClick={handleParse} disabled={loadingParse}>
                {loadingParse ? <Loader2 size={16} className="spin" style={{animation: 'spin 1s linear infinite'}} /> : "Parse to JSON"}
              </button>
            </div>
          </div>
        </div>

        {/* Step 2: Parsed Rule IR */}
        <div className="card">
          <div className="card-header">
            2. Parsed Rule (JSON IR)
            {jsonIr && (
              <button className="btn-primary" style={{padding: '6px 12px', fontSize: '12px'}} onClick={handleCompile} disabled={loadingCompile}>
                {loadingCompile ? "Compiling..." : "Compile to XSLT"}
              </button>
            )}
          </div>
          <div className="card-body" style={{padding: 0, position: 'relative'}}>
            <AnimatePresence mode="wait">
              {jsonIr ? (
                <motion.pre key="json" initial={{opacity: 0, y: 10}} animate={{opacity: 1, y: 0}} style={{border: 'none', borderRadius: 0, height: '100%', margin: 0}}>
                  {JSON.stringify(jsonIr, null, 2)}
                </motion.pre>
              ) : (
                <pre key="empty-json" style={{border: 'none', borderRadius: 0, height: '100%', margin: 0, color: 'var(--text-muted)'}}>
                  {"{\n  // Awaiting parsing...\n}"}
                </pre>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Step 3: XSLT Code */}
        <div className="card">
          <div className="card-header">
            3. Compiled XSLT Engine Code
            <Settings2 size={16} color="var(--text-muted)"/>
          </div>
          <div className="card-body" style={{padding: 0}}>
            <AnimatePresence mode="wait">
              {xsltCode ? (
                <motion.pre key="xslt" initial={{opacity: 0, y: 10}} animate={{opacity: 1, y: 0}} style={{border: 'none', borderRadius: 0, height: '100%', margin: 0}}>
                  {xsltCode}
                </motion.pre>
              ) : (
                <pre key="empty-xslt" style={{border: 'none', borderRadius: 0, height: '100%', margin: 0, color: 'var(--text-muted)'}}>
                  {"<!-- Auto-generated XSLT will appear here -->"}
                </pre>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Step 4: Upload & Execute */}
        <div className="card">
          <div className="card-header">
            4. Execution (Upload XML)
          </div>
          <div className="card-body">
            <div className="upload-zone" onClick={() => document.getElementById('file-upload').click()}>
              <UploadCloud size={32} color={file ? "var(--success-text)" : "var(--primary)"} style={{marginBottom: '12px'}} />
              <p style={{fontWeight: 500, color: file ? 'var(--success-text)' : 'var(--text-main)'}}>
                {file ? file.name : "Click to select an XML invoice"}
              </p>
              <input 
                id="file-upload" 
                type="file" 
                accept=".xml" 
                style={{display: 'none'}} 
                onChange={handleFileChange} 
              />
            </div>
            <button 
              className="btn-primary" 
              style={{width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px'}}
              onClick={handleExecuteXML}
              disabled={loadingExecute || !xsltCode || !file}
            >
              {loadingExecute ? <Loader2 size={16} style={{animation: 'spin 1s linear infinite'}} /> : <Play size={16} />}
              {loadingExecute ? "Evaluating XML..." : "Run Validation"}
            </button>
          </div>
        </div>
      </div>

      {/* FINAL RESULT UI (MATCHING COMPYL REFERENCE) */}
      <AnimatePresence>
        {validationStatus && (
          <motion.div 
            initial={{opacity: 0, y: 20}} 
            animate={{opacity: 1, y: 0}} 
            style={{display: 'flex', gap: '24px', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '24px', backgroundColor: '#fff', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'}}
          >
            {/* Big Pass/Fail Box */}
            <div style={{flex: '0 0 300px', backgroundColor: validationStatus === 'PASS' ? 'var(--success-bg)' : 'var(--error-bg)', border: `1px solid ${validationStatus === 'PASS' ? 'var(--success-border)' : 'var(--error-border)'}`, borderRadius: '8px', padding: '32px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px'}}>
              {validationStatus === 'PASS' ? <CheckCircle2 size={64} color="var(--success-text)" /> : <XCircle size={64} color="var(--error-text)" />}
              <h2 style={{fontSize: '32px', color: validationStatus === 'PASS' ? 'var(--success-text)' : 'var(--error-text)', margin: 0}}>
                {validationStatus}
              </h2>
            </div>

            {/* Execution Trace */}
            <div style={{flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
              <h3 style={{fontSize: '18px', fontWeight: 600, marginBottom: '16px'}}>Execution Trace</h3>
              
              <div style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px'}}>
                  <span style={{fontSize: '14px', color: 'var(--text-main)'}}>1. Rule Extracted: {jsonIr?.rule_type}</span>
                  <CheckCircle2 size={16} color="var(--success-text)" />
                </div>
                
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px'}}>
                  <span style={{fontSize: '14px', color: 'var(--text-main)'}}>2. XSLT Engine Compiled Targeting: {jsonIr?.field || jsonIr?.condition_field || 'Invoice Array'}</span>
                  <CheckCircle2 size={16} color="var(--success-text)" />
                </div>
                
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px'}}>
                  <span style={{fontSize: '14px', color: 'var(--text-main)'}}>3. XML Evaluated via lxml</span>
                  <CheckCircle2 size={16} color="var(--success-text)" />
                </div>

                {extractedData && (
                  <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px', backgroundColor: '#f8fafc', padding: '12px', borderRadius: '6px'}}>
                    <span style={{fontSize: '14px', color: 'var(--text-main)'}}>
                      ↳ <strong>Data Extracted:</strong> <code>&lt;{extractedData.field}&gt;</code> = <strong style={{color: 'var(--primary)'}}>{extractedData.value}</strong>
                    </span>
                    <CheckCircle2 size={16} color="var(--success-text)" />
                  </div>
                )}
                
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '8px', marginTop: '4px'}}>
                  <span style={{fontSize: '14px', fontWeight: 500}}>4. Condition Verified</span>
                  {validationStatus === 'PASS' ? <CheckCircle2 size={16} color="var(--success-text)" /> : <XCircle size={16} color="var(--error-text)" />}
                </div>
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
