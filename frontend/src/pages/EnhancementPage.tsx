import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  SlidersHorizontal,
  Info,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { enhancementService } from '../api/enhancementService';
import { resultsService } from '../api/resultsService';

const MODALITY_OPTIONS = [
  { value: 0, label: 'FLAIR', description: 'Fluid Attenuated Inversion Recovery — edema highlight' },
  { value: 1, label: 'T1', description: 'T1-weighted — anatomical contrast' },
  { value: 2, label: 'T1ce', description: 'T1 contrast-enhanced — blood-brain barrier disruption' },
  { value: 3, label: 'T2', description: 'T2-weighted — peritumoral edema' },
];

export const EnhancementPage: React.FC = () => {
  const { currentJobId, enhanceResult, setEnhanceResult, isEnhancing, setIsEnhancing, error, setError } = useAppStore();
  const [modality, setModality] = useState(0);
  const [clipLimit, setClipLimit] = useState(2.0);
  const [imgLoadErrors, setImgLoadErrors] = useState<Record<string, boolean>>({});

  if (!currentJobId) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12 space-y-4">
        <div className="w-12 h-12 rounded-full bg-slate-800 text-slate-400 mx-auto flex items-center justify-center">
          <Sparkles className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-white">No MRI Scan Loaded</h2>
        <p className="text-xs text-slate-400">Upload a 4D NIfTI brain MRI scan to generate contrast-enhanced previews.</p>
        <Link to="/upload" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 text-xs font-semibold">
          <span>Go to MRI Upload</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    );
  }

  const handleRunEnhancement = async () => {
    setIsEnhancing(true);
    setError(null);
    try {
      const res = await enhancementService.runEnhancement(currentJobId, {
        modality,
        clip_limit: clipLimit,
      });
      setEnhanceResult(res);
    } catch (err: any) {
      setError(err.message || 'CLAHE enhancement failed on the backend.');
    } finally {
      setIsEnhancing(false);
    }
  };

  const views = ['axial', 'coronal', 'sagittal'] as const;

  const getPreviewUrl = (view: 'axial' | 'coronal' | 'sagittal') => {
    if (enhanceResult) {
      // Use the returned preview_urls resolved against base URL
      const relUrl = enhanceResult.preview_urls[view];
      if (relUrl) return resultsService.getPreviewUrl(currentJobId, view);
    }
    return resultsService.getPreviewUrl(currentJobId, view);
  };

  const selectedModality = MODALITY_OPTIONS.find((m) => m.value === modality)!;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-cyan-400" />
          <span>CLAHE Contrast Enhancement Studio</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Contrast-Limited Adaptive Histogram Equalization applied per-slice on the selected MRI modality. Enhancement is an independent visualization operation and does not affect segmentation inference.
        </p>
      </div>

      {/* CLAHE Info Banner */}
      <div className="bg-[#0d1626] border border-cyan-900/30 rounded-xl p-4 text-xs text-slate-300 flex items-start gap-3">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-cyan-200">About CLAHE Enhancement: </span>
          CLAHE improves local contrast visibility for radiology review. It operates exclusively on slice-level image rendering.
          The original MRI file and segmentation inputs are strictly unmodified.
        </div>
      </div>

      {error && (
        <div className="bg-rose-950/40 border border-rose-800/80 rounded-lg p-3 text-xs text-rose-300 flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Controls & Preview Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls Panel */}
        <div className="bg-panel border border-panelBorder rounded-xl p-5 space-y-5">
          <div className="flex items-center gap-2 border-b border-panelBorder pb-3">
            <SlidersHorizontal className="w-4 h-4 text-cyan-400" />
            <h2 className="text-xs font-bold text-white uppercase font-mono tracking-wider">Enhancement Controls</h2>
          </div>

          {/* Modality Selector */}
          <div className="space-y-2">
            <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">MRI Modality</label>
            <div className="grid grid-cols-2 gap-2">
              {MODALITY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setModality(opt.value)}
                  disabled={isEnhancing}
                  className={`px-3 py-2 rounded-lg text-xs font-mono font-semibold transition-all border ${
                    modality === opt.value
                      ? 'bg-cyan-900/60 border-cyan-700 text-cyan-200'
                      : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-600 hover:text-slate-300'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <p className="text-[11px] text-slate-500">{selectedModality.description}</p>
          </div>

          {/* Clip Limit Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">CLAHE Clip Limit</label>
              <span className="text-xs font-mono text-cyan-300">{clipLimit.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min={0.5}
              max={10.0}
              step={0.5}
              value={clipLimit}
              onChange={(e) => setClipLimit(parseFloat(e.target.value))}
              disabled={isEnhancing}
              className="w-full accent-cyan-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>0.5 (subtle)</span>
              <span>10.0 (aggressive)</span>
            </div>
          </div>

          {/* Run Button */}
          <button
            onClick={handleRunEnhancement}
            disabled={isEnhancing}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-60 text-slate-950 text-xs font-bold shadow-md transition-colors"
          >
            {isEnhancing ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Generating Previews...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Generate Enhanced Previews</span>
              </>
            )}
          </button>

          {enhanceResult && (
            <div className="bg-teal-950/40 border border-teal-800/60 rounded-lg p-3 text-[11px] text-teal-300 flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
              <span>Previews generated for <strong>{enhanceResult.modality}</strong> modality</span>
            </div>
          )}
        </div>

        {/* Preview Images Panel */}
        <div className="lg:col-span-2 space-y-4">
          {!enhanceResult && !isEnhancing && (
            <div className="bg-panel border border-panelBorder rounded-xl h-64 flex flex-col items-center justify-center gap-3 text-center p-6">
              <Sparkles className="w-8 h-8 text-slate-600" />
              <div>
                <div className="text-sm font-semibold text-slate-400">No Enhanced Previews Yet</div>
                <div className="text-xs text-slate-500 mt-1">
                  Select a modality, adjust the CLAHE clip limit, and click <strong>Generate Enhanced Previews</strong>.
                </div>
              </div>
            </div>
          )}

          {isEnhancing && (
            <div className="bg-panel border border-panelBorder rounded-xl h-64 flex flex-col items-center justify-center gap-3">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
              <div className="text-xs font-mono text-slate-300">Applying CLAHE slice-by-slice...</div>
            </div>
          )}

          {enhanceResult && !isEnhancing && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="text-xs font-mono text-slate-300 font-semibold uppercase tracking-wider">
                  {enhanceResult.modality} — Enhanced Slice Previews
                </div>
                <div className="text-[11px] text-slate-400 font-mono">
                  Slices: Axial {enhanceResult.slices.axial} · Coronal {enhanceResult.slices.coronal} · Sagittal {enhanceResult.slices.sagittal}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {views.map((view) => (
                  <div key={view} className="bg-[#080d16] border border-panelBorder rounded-xl overflow-hidden">
                    <div className="text-[11px] font-mono uppercase text-slate-400 px-3 py-2 border-b border-panelBorder/60 flex items-center justify-between">
                      <span>{view}</span>
                      <a
                        href={getPreviewUrl(view)}
                        target="_blank"
                        rel="noreferrer"
                        download
                        className="text-cyan-400 hover:text-cyan-300 text-[10px]"
                      >
                        Save
                      </a>
                    </div>
                    {imgLoadErrors[view] ? (
                      <div className="aspect-square flex items-center justify-center text-xs text-slate-500 p-4 text-center">
                        <AlertCircle className="w-5 h-5 text-rose-400 mx-auto mb-1" />
                        <p>Preview unavailable</p>
                      </div>
                    ) : (
                      <img
                        src={getPreviewUrl(view)}
                        alt={`${view} CLAHE enhanced MRI preview`}
                        className="w-full object-contain bg-black"
                        onError={() => setImgLoadErrors((prev) => ({ ...prev, [view]: true }))}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
