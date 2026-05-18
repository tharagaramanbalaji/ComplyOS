import React, { useState, useEffect, useContext, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wand2, Code2, Network, Save, ChevronRight, Send, Bot, User, Sparkles, CheckCircle2 } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { RuleContext } from '../App';

const API_URL = 'http://localhost:8000/api';

export default function RuleStudio() {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Studio State
  const [parsedIR, setParsedIR] = useState(null);
  const [xslt, setXslt] = useState('');
  const [loading, setLoading] = useState(false);
  const { setActiveRuleId } = useContext(RuleContext);

  // Assistant State
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [options, setOptions] = useState([]);
  const [clarificationType, setClarificationType] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const initSession = async () => {
      const newSessionId = 'session_' + Math.random().toString(36).substring(7);
      setSessionId(newSessionId);
      
      const formData = new FormData();
      formData.append('session_id', newSessionId);
      
      await axios.post(`${API_URL}/chat/start`, formData);
      
      setMessages([
        {
          id: 1,
          type: 'system',
          text: "Hi! I'm the ComplyOS Engine. Describe a rule you want to build.",
          timestamp: new Date()
        }
      ]);
      
      if (location.state && location.state.templateText) {
        handleSend(location.state.templateText);
      }
    };
    initSession();
  }, [location]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping, options]);

  const handleSend = async (text, isClarification = false) => {
    if (!text.trim()) return;

    const userMessage = { id: Date.now(), type: 'user', text: text, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setOptions([]);
    setIsTyping(true);

    try {
      const res = await axios.post(`${API_URL}/chat/message`, {
        conversation_id: sessionId,
        text: text,
        is_clarification_response: isClarification,
        clarification_type: clarificationType
      });

      const data = res.data;
      
      setTimeout(() => {
        setIsTyping(false);
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          type: 'system',
          text: data.message,
          status: data.status,
          finalized_rule: data.finalized_rule,
          timestamp: new Date()
        }]);
        
        if (data.options && data.options.length > 0) {
          setOptions(data.options);
          setClarificationType(data.clarification_type);
        } else {
          setClarificationType(null);
        }
        
        if (data.status === 'resolved' && data.finalized_rule) {
          handleParse(data.finalized_rule);
        }
      }, 500); 
    } catch (err) {
      console.error(err);
      setIsTyping(false);
    }
  };

  const handleParse = async (textToParse) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('rule_text', textToParse);
      formData.append('severity', 'ERROR');
      
      const res = await axios.post(`${API_URL}/rules/parse`, formData);
      // Backend now returns a list of parsed rules
      const rules = res.data;
      setParsedIR(rules);
      if (rules.length > 0) {
          setActiveRuleId(rules[0].rule_id);
          const ids = rules.map(r => r.rule_id).join(",");
          const xsltRes = await axios.post(`${API_URL}/xslt?rule_id=${ids}`);
          setXslt(xsltRes.data.xslt);
      }
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  const handleSaveMap = () => {
    if (!xslt) return;
    const blob = new Blob([xslt], { type: 'text/xml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = (parsedIR && parsedIR.length > 0) ? `${parsedIR[0].rule_id}.xslt` : 'rule_map.xslt';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-8 h-full flex flex-col bg-[#FAF9F6]">
      <header className="mb-6 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-800 flex items-center gap-3">
            Rule Studio <Sparkles size={24} className="text-purple-500"/>
          </h1>
          <p className="text-gray-500 mt-2 font-medium">Build rules conversationally and map them to deterministic XSLT.</p>
        </div>
        <button onClick={() => navigate('/templates')} className="px-4 py-2 bg-white text-purple-600 rounded-lg shadow-sm border border-purple-100 hover:shadow-md transition-all font-semibold flex items-center gap-2">
          Browse Templates <ChevronRight size={16} />
        </button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        
        {/* LEFT PANEL: Assistant Chat */}
        <div className="bg-white/80 backdrop-blur-xl rounded-2xl flex flex-col overflow-hidden border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
          <div className="flex justify-between items-center p-4 border-b border-gray-100 bg-white/50">
            <h2 className="font-bold text-gray-700 flex items-center gap-2"><Wand2 size={18} className="text-purple-500"/> Natural Language Engine</h2>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <motion.div 
                  key={msg.id}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex gap-3 max-w-[85%] ${msg.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`w-8 h-8 shrink-0 rounded-full flex items-center justify-center shadow-sm ${
                      msg.type === 'user' 
                        ? 'bg-purple-600 text-white' 
                        : 'bg-purple-50 text-purple-600 border border-purple-100'
                    }`}>
                      {msg.type === 'user' ? <User size={16} /> : <Bot size={16} />}
                    </div>
                    
                    <div className={`flex flex-col ${msg.type === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className={`p-3 rounded-2xl text-[14px] leading-relaxed shadow-sm ${
                        msg.type === 'user'
                          ? 'bg-purple-600 text-white rounded-tr-sm'
                          : 'bg-white border border-gray-100 text-gray-700 rounded-tl-sm'
                      }`}>
                        {msg.text}
                      </div>
                      
                      {msg.status === 'resolved' && msg.finalized_rule && (
                        <div className="mt-2 p-3 bg-green-50 border border-green-100 rounded-xl shadow-sm w-full">
                          <p className="text-[10px] font-bold text-green-600 uppercase tracking-widest flex items-center gap-1 mb-1">
                            <CheckCircle2 size={12} /> Parsing Initiated
                          </p>
                          <p className="font-mono text-xs text-gray-700 bg-white p-2 rounded-lg border border-gray-100">
                            {msg.finalized_rule}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
              
              {isTyping && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-purple-50 text-purple-600 flex items-center justify-center shadow-sm">
                      <Bot size={16} />
                    </div>
                    <div className="p-4 rounded-2xl bg-white border border-gray-100 rounded-tl-sm flex items-center gap-1.5 shadow-sm">
                      <div className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>

          <AnimatePresence>
            {options.length > 0 && !isTyping && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }} 
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 5 }}
                className="px-4 pb-3 flex flex-wrap gap-2"
              >
                {options.map((opt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(opt, true)}
                    className="px-3 py-1.5 bg-purple-50 hover:bg-purple-100 border border-purple-200 text-purple-700 rounded-full text-xs font-bold transition-colors shadow-sm flex items-center gap-1"
                  >
                    {opt} <ChevronRight size={12} />
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          <div className="p-4 bg-white/50 border-t border-gray-100">
            <form 
              onSubmit={(e) => { e.preventDefault(); handleSend(input); }}
              className="flex items-center gap-3 relative"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your condition here..."
                className="flex-1 bg-white border border-gray-200 px-4 py-3 rounded-xl text-gray-700 outline-none focus:ring-2 focus:ring-purple-200 text-sm shadow-sm"
                disabled={isTyping}
              />
              <button 
                type="submit"
                disabled={!input.trim() || isTyping}
                className="w-12 h-12 bg-purple-600 text-white rounded-xl flex items-center justify-center disabled:opacity-50 shadow-md hover:brightness-110 transition-all"
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </div>

        {/* CENTER PANEL: IR Preview */}
        <div className="bg-white/80 backdrop-blur-xl rounded-2xl flex flex-col p-5 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100">
          <h2 className="font-bold text-gray-700 mb-3 flex items-center gap-2 text-sm"><Network size={16} className="text-orange-500"/> Intermediate Representation (IR)</h2>
          <div className="bg-[#FFFDF9] rounded-xl p-4 flex-1 overflow-auto border border-orange-100 shadow-inner relative">
             {loading && (
               <div className="absolute inset-0 bg-white/50 flex items-center justify-center">
                 <div className="w-6 h-6 border-2 border-orange-400 border-t-transparent rounded-full animate-spin"></div>
               </div>
             )}
            <pre className="text-xs font-mono text-gray-800 whitespace-pre-wrap">
              {parsedIR ? JSON.stringify(parsedIR.map(r => r.structured_IR), null, 2) : '// System waiting for resolved rule'}
            </pre>
          </div>
          {parsedIR && parsedIR.map((r, i) => (
            <div key={i} className="mt-3 flex gap-2 flex-wrap">
              <span className="px-2 py-1 bg-orange-50 text-orange-700 text-[10px] font-bold rounded border border-orange-200 tracking-wider">ID: {r.rule_id}</span>
              <span className="px-2 py-1 bg-purple-50 text-purple-700 text-[10px] font-bold rounded border border-purple-200 tracking-wider">TYPE: {r.rule_type.toUpperCase()}</span>
            </div>
          ))}
        </div>

        {/* RIGHT PANEL: XSLT Output */}
        <div className="bg-white/80 backdrop-blur-xl rounded-2xl flex flex-col p-5 border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border-t-4 border-t-purple-500">
          <div className="flex justify-between items-center mb-3">
            <h2 className="font-bold text-gray-700 flex items-center gap-2 text-sm"><Code2 size={16} className="text-purple-600"/> Deterministic XSLT Map</h2>
            <button onClick={handleSaveMap} disabled={!xslt} className="px-3 py-1.5 bg-white text-purple-600 border border-purple-200 rounded text-xs font-semibold hover:bg-purple-50 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm flex items-center gap-1"><Save size={14}/> Save Map</button>
          </div>
          <div className="bg-gray-900 rounded-xl p-4 flex-1 overflow-auto border border-gray-800 shadow-inner relative">
             {loading && (
               <div className="absolute inset-0 bg-gray-900/50 flex items-center justify-center">
                 <div className="w-6 h-6 border-2 border-purple-400 border-t-transparent rounded-full animate-spin"></div>
               </div>
             )}
            <pre className="text-xs font-mono text-purple-200 whitespace-pre-wrap">
              {xslt || '<!-- Generated XSLT logic will appear here -->'}
            </pre>
          </div>
        </div>

      </div>
    </div>
  );
}
