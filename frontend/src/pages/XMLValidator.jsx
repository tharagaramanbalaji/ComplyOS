import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, CheckCircle2, XCircle, FileCode2, Info, Activity, Network } from 'lucide-react';
import axios from 'axios';
import { RuleContext } from '../App';

const API_URL = 'http://localhost:8000/api';

export default function XMLValidator() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const { ruleStore, setRuleStore, activeRuleId, setActiveRuleId } = React.useContext(RuleContext);

  React.useEffect(() => {
    const fetchRules = async () => {
      try {
        const res = await axios.get(`${API_URL}/rules`);
        setRuleStore(res.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchRules();
  }, [setRuleStore]);

  const activeRule = ruleStore.find(r => r.rule_id === activeRuleId);

  const handleUpload = async (fileToUpload) => {
    if (!activeRule) {
      alert("No active rule selected");
      return;
    }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', fileToUpload);
      formData.append('rule_id', activeRule.rule_id);
      formData.append('rule_text', activeRule.rule_text);
      formData.append('severity', activeRule.severity);
      formData.append('rule_type', activeRule.rule_type);
      formData.append('structured_IR', JSON.stringify(activeRule.structured_IR));

      const res = await axios.post(`${API_URL}/validate`, formData);
      setResult(res.data);
    } catch (error) {
      console.error(error);
      setResult({
        pass_fail: 'FAIL',
        validation_errors: [{ message: 'Failed to process file' }],
        trace: []
      });
    }
    setLoading(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="p-8 h-full flex flex-col">
      <header className="mb-8">
        <h1 className="text-3xl font-extrabold text-textMain">XML Validator</h1>
        <p className="text-textMuted mt-2 font-medium">Execute generated rules against physical XML files.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 flex-1 min-h-0">
        <div className="flex flex-col gap-6">
          {/* Rule Selection Dropdown */}
          <div className="glass-panel p-6 bg-surface">
            <h3 className="font-bold text-textMain mb-4">Select Active Rule</h3>
            {ruleStore.length === 0 ? (
              <p className="text-sm text-textMuted bg-background p-3 rounded-lg border border-border">No rules found. Please parse a rule in the Rule Studio first.</p>
            ) : (
              <select 
                className="w-full bg-background border border-border p-3 rounded-xl text-textMain outline-none focus:ring-2 focus:ring-primary/50"
                value={activeRuleId || ''}
                onChange={(e) => setActiveRuleId(e.target.value)}
              >
                <option value="" disabled>Select a rule...</option>
                {ruleStore.map(r => (
                  <option key={r.rule_id} value={r.rule_id}>[{r.rule_id}] {r.rule_text}</option>
                ))}
              </select>
            )}
            
            {activeRule && (
              <div className="mt-4 p-4 bg-primary/5 border border-primary/20 rounded-xl">
                <p className="text-xs font-bold text-primary uppercase tracking-widest mb-2">Rule Preview</p>
                <p className="text-sm text-textMain">{activeRule.rule_text}</p>
                <div className="flex gap-2 mt-3">
                  <span className="text-xs bg-background border border-border px-2 py-1 rounded text-textMuted">{activeRule.rule_type}</span>
                  <span className="text-xs bg-background border border-border px-2 py-1 rounded text-textMuted">{activeRule.severity}</span>
                </div>
              </div>
            )}
          </div>

          {/* Upload Zone */}
          <div 
            className={`glass-panel border-2 border-dashed rounded-2xl flex flex-col items-center justify-center p-10 transition-colors bg-surface ${
              isDragging ? 'border-primary bg-primary/10' : 'border-border'
            }`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={onDrop}
          >
            <div className="w-20 h-20 rounded-full bg-primary/5 flex items-center justify-center mb-6 shadow-inner border border-primary/10">
              <UploadCloud size={40} className="text-primary" />
            </div>
            <h3 className="text-xl font-bold text-textMain mb-2">Upload XML Invoice</h3>
            <p className="text-textMuted text-sm mb-8 text-center max-w-xs">Drag and drop your file here, or click to browse</p>
            
            <input 
              type="file" 
              id="file-upload" 
              className="hidden" 
              accept=".xml"
              onChange={(e) => setFile(e.target.files[0])}
            />
            <label htmlFor="file-upload" className="btn-secondary cursor-pointer shadow-sm">
              Browse File
            </label>
            {file && <p className="mt-4 text-sm text-primary font-bold">{file.name}</p>}
          </div>

          <div className="flex justify-end">
            <button 
              onClick={() => handleUpload(file)} 
              disabled={!file || !activeRule || loading}
              className={`btn-primary w-full py-3 text-lg shadow-lg shadow-primary/20 ${(!file || !activeRule) && 'opacity-50 cursor-not-allowed'}`}
            >
              {loading ? 'Processing...' : 'Run Validation'}
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div className="glass-panel p-0 flex flex-col h-full overflow-hidden bg-surface">
          <div className="p-6 border-b border-border flex justify-between items-center bg-surface/50">
            <h2 className="font-bold text-textMain flex items-center gap-2">
              <FileCode2 size={18} className="text-secondary"/> Validation Output
            </h2>
            {result && (
              <span className={`px-4 py-1 rounded-full text-sm font-bold tracking-widest uppercase shadow-sm ${
                result.pass_fail === 'PASS' ? 'bg-success/20 text-success' : 'bg-accent/20 text-accent'
              }`}>
                {result.pass_fail}
              </span>
            )}
          </div>
          
          <div className="flex-1 overflow-auto p-6 bg-background/50">
            <AnimatePresence>
              {!result && !loading && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full flex flex-col items-center justify-center text-textMuted">
                  <Info size={40} className="mb-4 opacity-50" />
                  <p>Results will appear here after validation</p>
                </motion.div>
              )}
              
              {result && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
                  {/* Execution Summary Cards */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-surface border border-border p-4 rounded-xl flex items-center gap-4 shadow-sm">
                       <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                         <FileCode2 size={20} />
                       </div>
                       <div>
                         <p className="text-[10px] text-textMuted uppercase tracking-widest font-bold">Document Ref</p>
                         <p className="font-mono text-textMain font-bold text-sm mt-0.5 truncate max-w-[120px]">{result.invoice_id || 'UNKNOWN_DOC'}</p>
                       </div>
                    </div>
                    <div className="bg-surface border border-border p-4 rounded-xl flex items-center gap-4 shadow-sm">
                       <div className={`w-10 h-10 rounded-full flex items-center justify-center ${result.pass_fail === 'PASS' ? 'bg-success/10 text-success' : 'bg-accent/10 text-accent'}`}>
                         <Activity size={20} />
                       </div>
                       <div>
                         <p className="text-[10px] text-textMuted uppercase tracking-widest font-bold">Execution Status</p>
                         <p className={`font-bold text-sm mt-0.5 ${result.pass_fail === 'PASS' ? 'text-success' : 'text-accent'}`}>
                           {result.pass_fail === 'PASS' ? 'VERIFIED' : 'FAILED'}
                         </p>
                       </div>
                    </div>
                  </div>

                  {/* Hard Errors */}
                  {result.validation_errors && result.validation_errors.length > 0 && (
                    <div className="p-5 bg-accent/5 border-l-4 border-accent rounded-r-xl shadow-sm">
                      <h3 className="text-accent font-bold mb-3 flex items-center gap-2"><XCircle size={18}/> Critical Errors</h3>
                      <ul className="space-y-2">
                        {result.validation_errors.map((err, i) => (
                          <li key={i} className="text-sm text-textMain flex items-start gap-3">
                            <span className="font-mono bg-accent/20 text-accent px-1.5 py-0.5 rounded text-xs mt-0.5">{err.rule_id || 'SYS'}</span>
                            <span className="opacity-90">{err.message}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Execution Graph / Trace */}
                  <div>
                    <h3 className="font-bold text-textMain mb-6 flex items-center gap-2 border-b border-border pb-4">
                       <Network size={18} className="text-secondary" /> Execution Pipeline Trace
                    </h3>
                    
                    <div className="relative pl-4">
                       {/* Vertical Connecting Line */}
                       <div className="absolute left-[31px] top-4 bottom-8 w-0.5 bg-border z-0"></div>
                       
                       <div className="space-y-8 relative z-10">
                         {/* Parsing Step */}
                         <div className="flex items-start gap-6">
                           <div className="w-8 h-8 shrink-0 rounded-full bg-background border-[3px] border-primary flex items-center justify-center shadow-sm relative z-10">
                             <CheckCircle2 size={14} className="text-primary" />
                           </div>
                           <div className="flex-1 bg-surface border border-border p-4 rounded-xl shadow-sm hover:shadow transition-shadow">
                             <h4 className="font-bold text-textMain text-sm">XML Document Extraction</h4>
                             <p className="text-xs text-textMuted mt-1.5 leading-relaxed">Successfully parsed document payload and extracted required deterministic variables.</p>
                           </div>
                         </div>
                         
                         {/* Dynamic Trace Loop */}
                         {result.trace?.map((t, i) => (
                           <div key={i} className="flex items-start gap-6">
                             <div className={`w-8 h-8 shrink-0 rounded-full bg-background border-[3px] flex items-center justify-center shadow-sm relative z-10 ${t.passed ? 'border-success' : 'border-accent'}`}>
                               {t.passed ? <CheckCircle2 size={14} className="text-success" /> : <XCircle size={14} className="text-accent" />}
                             </div>
                             <div className={`flex-1 bg-surface border p-5 rounded-xl shadow-sm transition-all hover:shadow-md ${t.passed ? 'border-success/30 hover:border-success/50' : 'border-accent/40 bg-accent/5 hover:border-accent/60'}`}>
                               <div className="flex justify-between items-start mb-3 gap-4">
                                 <h4 className="font-bold text-textMain text-sm leading-snug">{t.rule_text}</h4>
                                 <span className={`text-[10px] shrink-0 font-bold uppercase tracking-widest px-2.5 py-1 rounded-full ${t.passed ? 'bg-success/10 text-success border border-success/20' : 'bg-accent/10 text-accent border border-accent/20'}`}>
                                   {t.passed ? 'PASSED' : 'VIOLATION'}
                                 </span>
                               </div>
                               
                               <div className="bg-background border border-border p-3 rounded-lg flex items-start gap-3">
                                 <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${t.passed ? 'bg-success/50' : 'bg-accent/50'}`}></div>
                                 <p className="text-[13px] font-mono text-textMuted leading-relaxed">{t.evaluation_details}</p>
                               </div>
                             </div>
                           </div>
                         ))}
                       </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
