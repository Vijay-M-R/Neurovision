import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Brain,
  Cpu,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Eye,
  RefreshCw,
  Clock,
  ShieldAlert,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { segmentationService } from '../api/segmentationService';

export const ProcessingPage: React.FC = () => {
  const {
    currentJobId,
    uploadData,
    segmentResult,
    setSegmentResult,
    isSegmenting,
    setIsSegmenting,
    health,
    modelInfo,
    setError,
    error,
  } = useAppStore();

  const [generateVis, setGenerateVis] = useState(true);

  if (!currentJobId) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12 space-y-4">
        <div className="w-12 h-12 rounded-full bg-slate-800 text-slate-400 mx-auto flex items-center justify-center">
          <Brain className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-white">No Brain MRI Loaded</h2>
        <p className="text-xs text-slate-400">
          You must upload a 4D NIfTI brain MRI scan before initiating AI segmentation inference.
        </p>
        <Link
          to="/upload"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 text-xs font-semibold"
        >
          <span>Go to MRI Upload</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    );
  }

  const handleStartSegmentation = async () => {
    setIsSegmenting(true);
    setError(null);

    try {
      const result = await segmentationService.runSegmentation(currentJobId, {
        generate_visualization: generateVis,
      });
      setSegmentResult(result);
    } catch (err: any) {
      setError(err.message || 'Segmentation inference failed on the backend.');
    } finally {
      setIsSegmenting(false);
    }
  };

  const hasCompleted = Boolean(segmentResult);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <Brain className="w-5 h-5 text-cyan-400" />
          <span>AI Multi-Region Tumor Segmentation Workspace</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Execute sliding-window inference with MONAI SegResNet on the active MRI scan. Extract Whole Tumor (WT), Tumor Core (TC), and Enhancing Tumor (ET) volumes.
        </p>
      </div>

      {error && (
        <div className="bg-rose-950/40 border border-rose-800/80 rounded-lg p-3 text-xs text-rose-300 flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Target Scan & Hardware Context Card */}
      <div className="bg-panel border border-panelBorder rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-panelBorder pb-3">
          <div className="text-xs font-bold text-slate-200 uppercase font-mono tracking-wider">
            Target Scan & Engine Specifications
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            GPU SERIALIZED QUEUE
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <div className="text-[11px] text-slate-400">Active Job ID</div>
            <div className="text-cyan-300 font-mono font-medium truncate mt-1" title={currentJobId}>
              {currentJobId.slice(0, 16)}...
            </div>
          </div>

          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <div className="text-[11px] text-slate-400">Model Architecture</div>
            <div className="text-slate-200 font-mono font-medium mt-1">
              {modelInfo?.architecture || 'SegResNet (MONAI)'}
            </div>
          </div>

          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <div className="text-[11px] text-slate-400">Compute Device</div>
            <div className="text-slate-200 font-mono font-medium mt-1 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span>{health?.device_name || 'CUDA 12.1 GPU'}</span>
            </div>
          </div>

          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <div className="text-[11px] text-slate-400">Scan Dimensions</div>
            <div className="text-slate-200 font-mono font-medium mt-1">
              {uploadData?.dimensions ? uploadData.dimensions.join(' × ') : '4D NIfTI'}
            </div>
          </div>
        </div>
      </div>

      {/* Execution Control Card */}
      {!hasCompleted && (
        <div className="bg-panel border border-panelBorder rounded-xl p-6 space-y-5">
          <div>
            <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
              Execute Neural Inference
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              The SegResNet inferer runs a 3D sliding-window pass across the 4 modalities with fp16 mixed precision.
            </p>
          </div>

          <div className="flex items-center gap-3 bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-xs">
            <input
              type="checkbox"
              id="genVis"
              checked={generateVis}
              onChange={(e) => setGenerateVis(e.target.checked)}
              disabled={isSegmenting}
              className="rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-0 cursor-pointer"
            />
            <label htmlFor="genVis" className="text-slate-300 cursor-pointer select-none">
              Generate high-resolution 3x3 orthogonal comparison PNG visualization
            </label>
          </div>

          {isSegmenting ? (
            <div className="bg-[#0b1322] border border-cyan-800/60 rounded-xl p-6 space-y-4 text-center">
              <div className="w-12 h-12 rounded-full bg-cyan-950/80 border border-cyan-700 text-cyan-400 mx-auto flex items-center justify-center animate-pulse">
                <Brain className="w-6 h-6 animate-spin" />
              </div>
              <div className="space-y-1">
                <div className="text-sm font-semibold text-white font-mono">
                  Inference Running on GPU...
                </div>
                <div className="text-xs text-slate-400">
                  Executing MONAI SegResNet sliding-window tensor operations. Please wait...
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={handleStartSegmentation}
                disabled={isSegmenting}
                className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 text-xs font-bold shadow-md transition-colors"
              >
                <Brain className="w-4 h-4" />
                <span>Start Segmentation Inference</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Completed Results Overview Card */}
      {hasCompleted && segmentResult && (
        <div className="bg-panel border border-teal-800/70 rounded-xl p-6 space-y-5 shadow-lg">
          <div className="flex items-center justify-between border-b border-panelBorder pb-3">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-teal-400" />
              <div>
                <h3 className="text-sm font-bold text-white font-mono">
                  Multi-Region Segmentation Completed
                </h3>
                <div className="text-[11px] text-slate-400 flex items-center gap-3 mt-0.5">
                  <span className="flex items-center gap-1 font-mono">
                    <Clock className="w-3 h-3 text-slate-500" />
                    {segmentResult.processing_time_seconds}s
                  </span>
                  <span>•</span>
                  <span className="text-slate-300 font-mono">Device: {segmentResult.device}</span>
                </div>
              </div>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800">
              SEGMENTATION COMPLETE
            </span>
          </div>

          {/* Voxel Count Badges */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-slate-900/80 p-4 rounded-xl border border-cyan-900/40 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-tumor-wt flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-tumor-wt inline-block" />
                  WT — Whole Tumor
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Channel 1</span>
              </div>
              <div className="text-xl font-bold font-mono text-white mt-1">
                {segmentResult.regions.WT.toLocaleString()}
                <span className="text-xs text-slate-400 font-normal ml-1">voxels</span>
              </div>
            </div>

            <div className="bg-slate-900/80 p-4 rounded-xl border border-amber-900/40 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-tumor-tc flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-tumor-tc inline-block" />
                  TC — Tumor Core
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Channel 0</span>
              </div>
              <div className="text-xl font-bold font-mono text-white mt-1">
                {segmentResult.regions.TC.toLocaleString()}
                <span className="text-xs text-slate-400 font-normal ml-1">voxels</span>
              </div>
            </div>

            <div className="bg-slate-900/80 p-4 rounded-xl border border-rose-900/40 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-tumor-et flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-tumor-et inline-block" />
                  ET — Enhancing Tumor
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Channel 2</span>
              </div>
              <div className="text-xl font-bold font-mono text-white mt-1">
                {segmentResult.regions.ET.toLocaleString()}
                <span className="text-xs text-slate-400 font-normal ml-1">voxels</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-3 text-[11px] text-slate-400 flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <span>
              <strong>Note on Region Volumes:</strong> WT, TC, and ET masks overlap in 3D space. Do not add their voxel counts together to estimate total tumor volume.
            </span>
          </div>

          {/* Action Navigation */}
          <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
            <button
              onClick={handleStartSegmentation}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Rerun Inference</span>
            </button>
            <Link
              to="/visualization"
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 text-xs font-bold shadow-md transition-colors"
            >
              <Eye className="w-4 h-4" />
              <span>Open 3-View Visualization Workspace</span>
              <ArrowRight className="w-4 h-4 ml-0.5" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
