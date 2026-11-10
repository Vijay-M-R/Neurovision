import React from 'react';
import { AlertCircle } from 'lucide-react';

export const MedicalDisclaimer: React.FC = () => {
  return (
    <div className="bg-[#0f172a] border border-cyan-900/40 rounded-lg p-3 text-xs text-slate-400 flex items-start gap-2.5">
      <AlertCircle className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
      <div>
        <span className="font-semibold text-cyan-300">RESEARCH & EDUCATIONAL DISCLAIMER: </span>
        NeuroVision is an advanced AI medical image processing prototype. It is not an FDA-cleared diagnostic device and must not be used as a substitute for professional clinical diagnosis, radiological review, or medical treatment planning.
      </div>
    </div>
  );
};
