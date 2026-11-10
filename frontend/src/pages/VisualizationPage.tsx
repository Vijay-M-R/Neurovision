import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Eye,
  Download,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  RefreshCw,
  AlertCircle,
  FileDown,
  ShieldAlert,
  ArrowRight,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { resultsService } from '../api/resultsService';
import type { ResultRecord } from '../types';

export const VisualizationPage: React.FC = () => {
  const { currentJobId, segmentResult, resultRecord, setResultRecord } = useAppStore();
  const [zoomLevel, setZoomLevel] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);
  const [imageError, setImageError] = useState(false);
  const [_recordLoading, setRecordLoading] = useState(false);

  useEffect(() => {
    if (currentJobId && !resultRecord) {
      setRecordLoading(true);
      resultsService
        .getResults(currentJobId)
        .then((res: ResultRecord) => setResultRecord(res))
        .catch((err) => console.warn('Could not preload result record:', err))
        .finally(() => setRecordLoading(false));
    }
  }, [currentJobId, resultRecord, setResultRecord]);

  if (!currentJobId) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12 space-y-4">
        <div className="w-12 h-12 rounded-full bg-slate-800 text-slate-400 mx-auto flex items-center justify-center">
          <Eye className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-white">No Active Brain MRI Job</h2>
        <p className="text-xs text-slate-400">
          Upload an MRI scan and execute segmentation to view the multi-region visualization.
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

  const visUrl = resultsService.getVisualizationUrl(currentJobId);
  const regions = segmentResult?.regions || resultRecord?.region_voxels || { WT: 0, TC: 0, ET: 0 };
  void (segmentResult?.processing_time_seconds || resultRecord?.processing_time_seconds);

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 0.25, 2.5));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 0.25, 0.75));
  const handleResetZoom = () => setZoomLevel(1);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Title & Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Eye className="w-5 h-5 text-cyan-400" />
            <span>Orthogonal 3-View Tumor Segmentation Workspace</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Axial, Coronal, and Sagittal cross-sections demonstrating multi-label tumor boundaries.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Zoom & View Controls */}
          <div className="flex items-center bg-panel border border-panelBorder rounded-lg p-1 text-slate-300">
            <button
              onClick={handleZoomOut}
              disabled={zoomLevel <= 0.75}
              title="Zoom Out"
              className="p-1.5 hover:bg-slate-800 rounded disabled:opacity-40"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              onClick={handleResetZoom}
              title="Reset Zoom"
              className="px-2 py-1 text-xs font-mono text-cyan-300 hover:bg-slate-800 rounded"
            >
              {Math.round(zoomLevel * 100)}%
            </button>
            <button
              onClick={handleZoomIn}
              disabled={zoomLevel >= 2.5}
              title="Zoom In"
              className="p-1.5 hover:bg-slate-800 rounded disabled:opacity-40"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <div className="h-4 w-px bg-slate-800 mx-1" />
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
              className="p-1.5 hover:bg-slate-800 rounded text-slate-300"
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          </div>

          <a
            href={visUrl}
            target="_blank"
            rel="noreferrer"
            download={`neurovision_${currentJobId}_visualization.png`}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Save PNG</span>
          </a>
        </div>
      </div>

      {/* Main Image Viewport */}
      <div
        className={`bg-[#0a0f18] border border-panelBorder rounded-xl overflow-hidden relative shadow-2xl transition-all ${
          isFullscreen ? 'fixed inset-4 z-50 flex flex-col' : 'min-h-[500px]'
        }`}
      >
        {isFullscreen && (
          <div className="p-3 bg-panel/90 border-b border-panelBorder flex justify-between items-center text-xs">
            <span className="font-mono text-cyan-300">NEUROVISION ORTHOGONAL VIEWER — FULLSCREEN</span>
            <button
              onClick={() => setIsFullscreen(false)}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs"
            >
              Close
            </button>
          </div>
        )}

        <div className="flex-1 overflow-auto flex items-center justify-center p-4">
          {imageLoading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-[#0a0f18]/80 z-10">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
              <div className="text-xs font-mono text-slate-300">
                Loading high-resolution 3x3 orthogonal visualization...
              </div>
            </div>
          )}

          {imageError ? (
            <div className="text-center p-8 space-y-3">
              <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
              <div className="text-sm font-semibold text-rose-300">
                Visualization Image Unavailable
              </div>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                The visualization artifact could not be retrieved from <code>/api/results/{currentJobId}/visualization</code>. Please verify that segmentation was executed with visualization enabled.
              </p>
              <Link
                to="/processing"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs text-cyan-300 font-mono mt-2"
              >
                Return to Processing
              </Link>
            </div>
          ) : (
            <img
              src={visUrl}
              alt="NeuroVision Orthogonal Multi-Region Tumor Segmentation"
              onLoad={() => setImageLoading(false)}
              onError={() => {
                setImageLoading(false);
                setImageError(true);
              }}
              style={{
                transform: `scale(${zoomLevel})`,
                transformOrigin: 'center center',
                transition: 'transform 0.15s ease-out',
              }}
              className="max-w-full h-auto object-contain select-none rounded shadow-md"
            />
          )}
        </div>
      </div>

      {/* Tumor Region Badges & Raw NIfTI Mask Downloads */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* WT Card */}
        <div className="bg-panel border border-cyan-950/80 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-panelBorder pb-2">
            <span className="text-xs font-bold text-tumor-wt flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-tumor-wt" />
              WT — Whole Tumor
            </span>
            <span className="text-[10px] font-mono text-slate-400">Class Label 2 / In Channel 1</span>
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-white">
              {regions.WT.toLocaleString()}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              Encompasses total edema, core, and enhancing regions
            </div>
          </div>
          <div className="pt-2">
            <a
              href={resultsService.getMaskDownloadUrl(currentJobId, 'WT')}
              download
              className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-mono font-medium transition-colors border border-slate-700/60"
            >
              <FileDown className="w-3.5 h-3.5" />
              <span>Download WT.nii.gz</span>
            </a>
          </div>
        </div>

        {/* TC Card */}
        <div className="bg-panel border border-amber-950/80 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-panelBorder pb-2">
            <span className="text-xs font-bold text-tumor-tc flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-tumor-tc" />
              TC — Tumor Core
            </span>
            <span className="text-[10px] font-mono text-slate-400">Class Label 1 / In Channel 0</span>
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-white">
              {regions.TC.toLocaleString()}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              Includes non-enhancing & enhancing solid active tumor
            </div>
          </div>
          <div className="pt-2">
            <a
              href={resultsService.getMaskDownloadUrl(currentJobId, 'TC')}
              download
              className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 text-xs font-mono font-medium transition-colors border border-slate-700/60"
            >
              <FileDown className="w-3.5 h-3.5" />
              <span>Download TC.nii.gz</span>
            </a>
          </div>
        </div>

        {/* ET Card */}
        <div className="bg-panel border border-rose-950/80 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-panelBorder pb-2">
            <span className="text-xs font-bold text-tumor-et flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-tumor-et" />
              ET — Enhancing Tumor
            </span>
            <span className="text-[10px] font-mono text-slate-400">Class Label 4 / In Channel 2</span>
          </div>
          <div>
            <div className="text-2xl font-bold font-mono text-white">
              {regions.ET.toLocaleString()}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              Hyper-intense T1ce active neo-vascularized rim
            </div>
          </div>
          <div className="pt-2">
            <a
              href={resultsService.getMaskDownloadUrl(currentJobId, 'ET')}
              download
              className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-rose-300 text-xs font-mono font-medium transition-colors border border-slate-700/60"
            >
              <FileDown className="w-3.5 h-3.5" />
              <span>Download ET.nii.gz</span>
            </a>
          </div>
        </div>
      </div>

      {/* Overlap Disclaimer Note */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-3 text-xs text-slate-400 flex items-start gap-2.5">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300">Spatial Region Overlap: </span>
          The WT (Whole Tumor), TC (Tumor Core), and ET (Enhancing Tumor) masks are hierarchically nested in 3D anatomical space (ET ⊆ TC ⊆ WT). Voxel counts must not be summed together.
        </div>
      </div>
    </div>
  );
};
