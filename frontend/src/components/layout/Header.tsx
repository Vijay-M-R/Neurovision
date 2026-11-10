import React, { useEffect } from 'react';
import { Cpu, RotateCcw, Copy, Check, Server } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { healthService } from '../../api/healthService';
import { modelService } from '../../api/modelService';

export const Header: React.FC = () => {
  const { health, currentJobId, setHealth, setModelInfo, resetSession } = useAppStore();
  const [copied, setCopied] = React.useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [healthRes, modelRes] = await Promise.all([
          healthService.getHealth(),
          modelService.getModelInfo(),
        ]);
        setHealth(healthRes);
        setModelInfo(modelRes);
      } catch (err) {
        console.warn('Backend connection error:', err);
        setHealth(null);
        setModelInfo(null);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, [setHealth, setModelInfo]);

  const handleCopyJobId = () => {
    if (currentJobId) {
      navigator.clipboard.writeText(currentJobId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const isHealthy = health?.status === 'ok';

  return (
    <header className="h-16 bg-[#0d131f] border-b border-panelBorder px-6 flex items-center justify-between shrink-0">
      {/* Brand & Subtitle */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-teal-400 flex items-center justify-center font-mono font-bold text-slate-950 text-base shadow-sm">
          NV
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold tracking-wider text-sm text-slate-100 font-mono">NEUROVISION</span>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-800/50">
              v1.0-AI
            </span>
          </div>
          <p className="text-[11px] text-slate-400 hidden sm:block">
            Medical Image Processing & Tumor Segmentation
          </p>
        </div>
      </div>

      {/* Status Badges & Active Job Pill */}
      <div className="flex items-center gap-3">
        {/* Active Job ID Badge */}
        {currentJobId && (
          <div className="hidden md:flex items-center gap-2 bg-slate-900 border border-slate-700/60 rounded-md px-2.5 py-1 text-xs">
            <span className="text-slate-400 font-mono text-[11px]">JOB:</span>
            <span className="text-cyan-300 font-mono text-[11px]">{currentJobId.slice(0, 8)}...</span>
            <button
              onClick={handleCopyJobId}
              title="Copy Job ID"
              className="text-slate-400 hover:text-slate-200 transition-colors p-0.5"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-teal-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
            <div className="h-3 w-px bg-slate-700 mx-0.5" />
            <button
              onClick={resetSession}
              title="Reset session and upload new scan"
              className="text-slate-400 hover:text-rose-400 transition-colors flex items-center gap-1 text-[11px]"
            >
              <RotateCcw className="w-3 h-3" />
              <span>New</span>
            </button>
          </div>
        )}

        {/* GPU Status Pill */}
        <div className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 rounded-md px-2.5 py-1 text-xs">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-300 font-mono text-[11px] hidden lg:inline">
            {health?.device_name || (health?.cuda_available ? 'CUDA GPU' : 'CPU')}
          </span>
          <span className="text-slate-300 font-mono text-[11px] lg:hidden">
            {health?.cuda_available ? 'GPU' : 'CPU'}
          </span>
        </div>

        {/* Backend & Model Status Pill */}
        <div
          className={`flex items-center gap-1.5 border rounded-md px-2.5 py-1 text-xs font-mono text-[11px] ${
            isHealthy
              ? 'bg-teal-950/40 border-teal-800/60 text-teal-300'
              : 'bg-rose-950/40 border-rose-800/60 text-rose-300'
          }`}
        >
          <span className="relative flex h-2 w-2">
            {isHealthy && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
            )}
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                isHealthy ? 'bg-teal-400' : 'bg-rose-400'
              }`}
            ></span>
          </span>
          <Server className="w-3 h-3" />
          <span>{isHealthy ? 'BACKEND ONLINE' : 'DISCONNECTED'}</span>
        </div>
      </div>
    </header>
  );
};
