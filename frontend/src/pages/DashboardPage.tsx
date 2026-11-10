import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Cpu,
  Brain,
  ShieldCheck,
  Upload,
  ArrowRight,
  Database,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { healthService } from '../api/healthService';
import { modelService } from '../api/modelService';

export const DashboardPage: React.FC = () => {
  const { health, modelInfo, currentJobId, uploadData, setHealth, setModelInfo } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const [h, m] = await Promise.all([
        healthService.getHealth(),
        modelService.getModelInfo(),
      ]);
      setHealth(h);
      setModelInfo(m);
    } catch (err: any) {
      setFetchError(err.message || 'Failed to connect to NeuroVision backend API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const isBackendOnline = health?.status === 'ok';

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-[#0d1627] via-[#111e38] to-[#0e182d] border border-cyan-900/40 rounded-xl p-6 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-mono tracking-wider px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-700/40">
              Diagnostic Research Console
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white mt-1">
            NeuroVision Radiology Workspace
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Pretrained MONAI SegResNet multi-region tumor segmentation & CLAHE contrast enhancement for 4D Brain MRI analysis.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <Link
            to="/upload"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 text-xs font-semibold shadow-md transition-colors"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Brain MRI</span>
            <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
          </Link>
        </div>
      </div>

      {fetchError && (
        <div className="bg-rose-950/40 border border-rose-800/80 rounded-lg p-4 text-xs text-rose-300 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <div>
            <span className="font-semibold">Backend Unreachable: </span>
            {fetchError}. Ensure the FastAPI server is running at <code>http://127.0.0.1:8000</code>.
          </div>
        </div>
      )}

      {/* Grid of Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Backend Connection */}
        <div className="bg-panel border border-panelBorder rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase">Backend Server</span>
            <div className={`w-2.5 h-2.5 rounded-full ${isBackendOnline ? 'bg-teal-400 shadow-teal-500/50 shadow-sm' : 'bg-rose-500'}`} />
          </div>
          <div>
            <div className="text-lg font-bold text-white font-mono">
              {isBackendOnline ? 'FastAPI 0.162' : 'Offline'}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              REST API & LRU Cached Runtime
            </div>
          </div>
          <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>AI Engine Link:</span>
            <span className="text-teal-400 font-medium">
              {health?.ai_engine_available ? 'Connected' : 'Unavailable'}
            </span>
          </div>
        </div>

        {/* Card 2: GPU Device */}
        <div className="bg-panel border border-panelBorder rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase">Inference Hardware</span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <div className="text-lg font-bold text-white font-mono">
              {health?.cuda_available ? 'CUDA 12.1' : 'CPU Mode'}
            </div>
            <div className="text-xs text-slate-400 mt-0.5 truncate" title={health?.device_name || 'NVIDIA GPU'}>
              {health?.device_name || (health?.cuda_available ? 'Dedicated GPU' : 'Host CPU')}
            </div>
          </div>
          <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>VRAM Lock:</span>
            <span className="text-cyan-400 font-mono">Serialized Guard</span>
          </div>
        </div>

        {/* Card 3: Neural Architecture */}
        <div className="bg-panel border border-panelBorder rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase">Architecture</span>
            <Brain className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <div className="text-lg font-bold text-white font-mono">
              {modelInfo?.architecture || 'SegResNet'}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              MONAI Bundle v{modelInfo?.version || '0.5.2'}
            </div>
          </div>
          <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Parameters:</span>
            <span className="text-slate-200 font-mono">
              {modelInfo ? modelInfo.parameters.toLocaleString() : '4,702,227'}
            </span>
          </div>
        </div>

        {/* Card 4: Active Session */}
        <div className="bg-panel border border-panelBorder rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase">Active Session</span>
            <Database className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <div className="text-lg font-bold text-white font-mono">
              {currentJobId ? 'Scan Loaded' : 'No Scan'}
            </div>
            <div className="text-xs text-slate-400 mt-0.5 truncate">
              {uploadData?.filename || (currentJobId ? currentJobId.slice(0, 16) + '...' : 'Awaiting NIfTI upload')}
            </div>
          </div>
          <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Modality Shape:</span>
            <span className="text-cyan-400 font-mono">
              {uploadData?.dimensions ? uploadData.dimensions.join('×') : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* Model Information & Safety Verification Table */}
      <div className="bg-panel border border-panelBorder rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-panelBorder pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-teal-400" />
            <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
              Verified Pretrained Model Specifications
            </h2>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-teal-950 border border-teal-800 text-teal-300">
            Source of Truth: /api/model-info
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
          <div className="bg-slate-900/60 p-3.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[11px]">Model Name</div>
            <div className="text-slate-200 font-semibold font-mono mt-1">
              {modelInfo?.model_name || 'MONAI SegResNet'}
            </div>
          </div>

          <div className="bg-slate-900/60 p-3.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[11px]">Bundle Name</div>
            <div className="text-slate-200 font-semibold font-mono mt-1">
              {modelInfo?.bundle || 'brats_mri_segmentation'}
            </div>
          </div>

          <div className="bg-slate-900/60 p-3.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[11px]">Input / Output Channels</div>
            <div className="text-slate-200 font-semibold font-mono mt-1">
              {modelInfo ? `${modelInfo.input_channels} In (FLAIR, T1, T1ce, T2) / ${modelInfo.output_channels} Out (TC, WT, ET)` : '4 In / 3 Out'}
            </div>
          </div>

          <div className="bg-slate-900/60 p-3.5 rounded-lg border border-slate-800 flex items-center justify-between">
            <div>
              <div className="text-slate-400 text-[11px]">Training Mode</div>
              <div className="text-slate-200 font-semibold mt-1">Strictly Disabled</div>
            </div>
            <CheckCircle2 className="w-4 h-4 text-teal-400" />
          </div>

          <div className="bg-slate-900/60 p-3.5 rounded-lg border border-slate-800 flex items-center justify-between">
            <div>
              <div className="text-slate-400 text-[11px]">Fine-Tuning Mode</div>
              <div className="text-slate-200 font-semibold mt-1">Strictly Disabled</div>
            </div>
            <CheckCircle2 className="w-4 h-4 text-teal-400" />
          </div>

          <div className="bg-slate-900/60 p-3.5 rounded-lg border border-slate-800 flex items-center justify-between">
            <div>
              <div className="text-slate-400 text-[11px]">Memory Residency</div>
              <div className="text-slate-200 font-semibold mt-1">
                {modelInfo?.cached ? 'Single LRU Cached Instance' : 'Ready'}
              </div>
            </div>
            <CheckCircle2 className="w-4 h-4 text-teal-400" />
          </div>
        </div>
      </div>
    </div>
  );
};
