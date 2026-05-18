import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronRight, Check } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const TOUR_STEPS = [
  {
    target: "tour-studio",
    path: "/studio",
    title: "Rule Studio",
    desc: "Write rules naturally such as: 'Tax amount > 0'. Instantly generate Intermediate Representation (IR) and deterministic XSLT scripts.",
    align: "left"
  },
  {
    target: "tour-validator",
    path: "/validator",
    title: "XML Validator",
    desc: "Upload invoices and validate them against your generated rules. View detailed, explainable trace logs instantly.",
    align: "left"
  },
  {
    target: "tour-analytics",
    path: "/analytics",
    title: "Analytics & Monitoring",
    desc: "Monitor validation statistics, view failure heatmaps, and track the health of your compliance pipelines.",
    align: "left"
  }
];

export default function Onboarding({ onComplete }) {
  const [step, setStep] = useState(0);
  const navigate = useNavigate();

  const handleNext = () => {
    if (step < TOUR_STEPS.length - 1) {
      setStep(step + 1);
      navigate(TOUR_STEPS[step + 1].path);
    } else {
      finishTour();
    }
  };

  const finishTour = () => {
    localStorage.setItem('complyos_tour_completed', 'true');
    onComplete();
  };

  const currentStep = TOUR_STEPS[step];

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 pointer-events-none flex items-center justify-center">
        {/* Backdrop overlay */}
        <motion.div 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="absolute inset-0 bg-slate-900/20 backdrop-blur-sm pointer-events-auto"
        />

        {/* Modal Spotlight */}
        <motion.div 
          key={step}
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="relative bg-white rounded-2xl shadow-2xl border border-gray-100 p-6 max-w-sm pointer-events-auto"
        >
          <button onClick={finishTour} className="absolute top-4 right-4 text-gray-400 hover:text-gray-700 transition">
            <X size={18} />
          </button>
          
          <div className="flex items-center gap-2 mb-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold">
              {step + 1}
            </span>
            <span className="text-xs font-medium text-gray-400 uppercase tracking-widest">
              of {TOUR_STEPS.length}
            </span>
          </div>

          <h3 className="text-xl font-bold text-gray-900 mb-2">{currentStep.title}</h3>
          <p className="text-gray-600 text-sm leading-relaxed mb-6">
            {currentStep.desc}
          </p>

          <div className="flex items-center justify-between mt-4">
            <button onClick={finishTour} className="text-sm text-gray-500 font-medium hover:text-gray-800">
              Skip Tour
            </button>
            <button onClick={handleNext} className="btn-primary py-1.5 px-4 text-sm shadow-md">
              {step === TOUR_STEPS.length - 1 ? (
                <><Check size={16} /> Finish</>
              ) : (
                <>Next <ChevronRight size={16} /></>
              )}
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
