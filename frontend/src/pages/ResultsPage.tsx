import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FileText,
  Download,
  BarChart2,
  Clock,
  Cpu,
  Layers,
  ArrowRight,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Eye,
  Sparkles,
  Archive,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { useAppStore } from '../store/useAppStore';
import { resultsService } from '../api/resultsService';

// ─── Helpers ────────────────────────────────────────────────────────────────

function fmtNum(n: number): string {
  return n.toLocaleString('en-US');
}

function fmtDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return iso;
  }
}

// ─── Custom recharts tooltip ─────────────────────────────────────────────────

interface TooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; name: string }>;
  label?: string;
}

const VoxelTooltip: React.FC<TooltipProps> = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="bg-panel border border-panelBorder rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-slate-300 font-semibold mb-1">{label}</p>
      <p className="text-white font-mono">{fmtNum(payload[0].value)} voxels</p>
    </div>
  );
};

// ─── Metric cell ─────────────────────────────────────────────────────────────

interface MetricCellProps {
  value: number | null | undefined;
}

const MetricCell: React.FC<MetricCellProps> = ({ value }) => {
  const display =
    value == null ? '—' : `${(value * 100).toFixed(2)}%`;
  const color =
    value == null
      ? 'text-slate-500'
      : value >= 0.8
      ? 'text-emerald-400'
      : value >= 0.6
      ? 'text-yellow-400'
      : 'text-red-400';

  return (
    <td className="px-4 py-3 text-right">
      <span className={`font-mono text-sm font-semibold ${color}`}>{display}</span>
    </td>
  );
};

// ─── Region pill ─────────────────────────────────────────────────────────────

const regionMeta = {
  WT: { label: 'Whole Tumour', color: 'text-cyan-400', border: 'border-cyan-700', bg: 'bg-cyan-900/20', bar: '#00D5FF' },
  TC: { label: 'Tumour Core',  color: 'text-yellow-400', border: 'border-yellow-700', bg: 'bg-yellow-900/20', bar: '#FFD43B' },
  ET: { label: 'Enhancing Tumour', color: 'text-red-400', border: 'border-red-700', bg: 'bg-red-900/20', bar: '#FF4B4B' },
};

// ─── Page ────────────────────────────────────────────────────────────────────

export const ResultsPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    currentJobId,
    resultRecord,
    setResultRecord,
    isLoadingResults,
    setIsLoadingResults,
  } = useAppStore();

  const [loadError, setLoadError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  // Load result record on mount if not already in store
  useEffect(() => {
    if (!currentJobId) return;
    if (resultRecord) return;

    setIsLoadingResults(true);
    setLoadError(null);

    resultsService
      .getResults(currentJobId)
      .then((rec) => setResultRecord(rec))
      .catch((err) => {
        const msg =
          err?.response?.data?.detail ||
          err?.message ||
          'Failed to load results from backend.';
        setLoadError(msg);
      })
      .finally(() => setIsLoadingResults(false));
  }, [currentJobId, resultRecord, setResultRecord, setIsLoadingResults]);

  const handleRefresh = () => {
    if (!currentJobId) return;
    setResultRecord(null);
    setLoadError(null);
  };

  const handleDownloadZip = async () => {
    if (!currentJobId) return;
    setIsDownloading(true);
    try {
      await resultsService.downloadZip(currentJobId);
    } catch {
      // silent — browser will show nothing if download fails
    } finally {
      setIsDownloading(false);
    }
  };

  // ── Guard: no active job ──────────────────────────────────────────────────

  if (!currentJobId) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16 space-y-4">
        <div className="w-14 h-14 rounded-full bg-slate-800 text-slate-400 mx-auto flex items-center justify-center">
          <FileText className="w-7 h-7" />
        </div>
        <h2 className="text-lg font-bold text-white">No Active Session</h2>
        <p className="text-xs text-slate-400">
          Upload an MRI scan and run segmentation to view full results.
        </p>
        <Link
          to="/upload"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 text-xs font-semibold transition-colors"
        >
          <span>Upload MRI Scan</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    );
  }

  // ── Loading ───────────────────────────────────────────────────────────────

  if (isLoadingResults) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4 text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin text-cyan-500" />
        <p className="text-sm">Loading results…</p>
      </div>
    );
  }

  // ── Load error ────────────────────────────────────────────────────────────

  if (loadError) {
    return (
      <div className="max-w-2xl mx-auto py-10 space-y-4">
        <div className="rounded-xl border border-red-800 bg-red-950/30 p-5 flex gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-red-300">Failed to load results</p>
            <p className="text-xs text-red-400 mt-1 font-mono break-all">{loadError}</p>
          </div>
        </div>
        <button
          onClick={handleRefresh}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold transition-colors"
        >
          <RefreshCw className="w-4 h-4" /> Retry
        </button>
      </div>
    );
  }

  if (!resultRecord) return null;

  // ── Voxel chart data ──────────────────────────────────────────────────────

  const voxelChartData = [
    { region: 'WT', voxels: resultRecord.region_voxels.WT, ...regionMeta.WT },
    { region: 'TC', voxels: resultRecord.region_voxels.TC, ...regionMeta.TC },
    { region: 'ET', voxels: resultRecord.region_voxels.ET, ...regionMeta.ET },
  ];

  // ── Evaluation metrics ────────────────────────────────────────────────────

  const metrics = resultRecord.evaluation_metrics;
  const metricRows = metrics
    ? [
        { label: 'Dice Score', key: 'dice' },
        { label: 'IoU (Jaccard)', key: 'iou' },
        { label: 'Precision', key: 'precision' },
        { label: 'Recall (Sensitivity)', key: 'recall' },
      ]
    : [];

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6 max-w-5xl mx-auto">

      {/* ── Page header ────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-400" />
            Results Report
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Full inference record for job{' '}
            <span className="font-mono text-cyan-400">{currentJobId}</span>
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleRefresh}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs font-semibold transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
          <button
            onClick={handleDownloadZip}
            disabled={isDownloading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-700 hover:bg-cyan-600 disabled:opacity-50 text-white text-xs font-semibold transition-colors"
          >
            {isDownloading ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Archive className="w-3.5 h-3.5" />
            )}
            {isDownloading ? 'Preparing…' : 'Download ZIP Bundle'}
          </button>
        </div>
      </div>

      {/* ── Status badge ───────────────────────────────────────────────── */}
      <div
        className={`flex items-center gap-2 px-4 py-2 rounded-lg border w-fit text-xs font-semibold ${
          resultRecord.status === 'completed'
            ? 'border-emerald-700 bg-emerald-900/20 text-emerald-400'
            : 'border-yellow-700 bg-yellow-900/20 text-yellow-400'
        }`}
      >
        <CheckCircle2 className="w-4 h-4" />
        Status: {resultRecord.status.toUpperCase()}
      </div>

      {/* ── Summary cards ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="rounded-xl border border-panelBorder bg-panel p-4 space-y-1">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Model</p>
          <p className="text-sm font-mono text-white truncate">{resultRecord.model}</p>
        </div>
        <div className="rounded-xl border border-panelBorder bg-panel p-4 space-y-1">
          <p className="text-xs text-slate-500 uppercase tracking-wide flex items-center gap-1">
            <Cpu className="w-3 h-3" /> Device
          </p>
          <p className="text-sm font-mono text-cyan-400 uppercase">{resultRecord.device}</p>
        </div>
        <div className="rounded-xl border border-panelBorder bg-panel p-4 space-y-1">
          <p className="text-xs text-slate-500 uppercase tracking-wide flex items-center gap-1">
            <Clock className="w-3 h-3" /> Inference Time
          </p>
          <p className="text-sm font-mono text-white">
            {resultRecord.processing_time_seconds.toFixed(3)}s
          </p>
        </div>
        <div className="rounded-xl border border-panelBorder bg-panel p-4 space-y-1">
          <p className="text-xs text-slate-500 uppercase tracking-wide flex items-center gap-1">
            <Layers className="w-3 h-3" /> Volume Shape
          </p>
          <p className="text-sm font-mono text-white">
            {resultRecord.shape?.join(' × ') || '—'}
          </p>
        </div>
      </div>

      {/* ── Metadata row ───────────────────────────────────────────────── */}
      <div className="rounded-xl border border-panelBorder bg-panel p-4">
        <table className="w-full text-xs">
          <tbody className="divide-y divide-panelBorder">
            <tr>
              <td className="py-2 pr-6 text-slate-500 w-40">Job ID</td>
              <td className="py-2 font-mono text-slate-200 break-all">{resultRecord.job_id}</td>
            </tr>
            {resultRecord.patient_id && (
              <tr>
                <td className="py-2 pr-6 text-slate-500">Patient ID</td>
                <td className="py-2 font-mono text-slate-200">{resultRecord.patient_id}</td>
              </tr>
            )}
            <tr>
              <td className="py-2 pr-6 text-slate-500">Created At</td>
              <td className="py-2 font-mono text-slate-200">{fmtDate(resultRecord.created_at)}</td>
            </tr>
            <tr>
              <td className="py-2 pr-6 text-slate-500">Project</td>
              <td className="py-2 font-mono text-slate-200">{resultRecord.project}</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* ── Voxel counts + chart ────────────────────────────────────────── */}
      <section className="rounded-xl border border-panelBorder bg-panel p-5 space-y-4">
        <h2 className="text-sm font-bold text-white flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-cyan-400" />
          Region Voxel Counts
        </h2>

        {/* Overlap disclaimer */}
        <div className="flex gap-2 p-3 rounded-lg bg-yellow-900/20 border border-yellow-700 text-xs text-yellow-300">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>
            Regions are <strong>nested, not independent</strong>: ET ⊆ TC ⊆ WT.
            Do not sum these counts — WT includes both TC and ET voxels.
          </span>
        </div>

        {/* Count pills */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {(['WT', 'TC', 'ET'] as const).map((region) => {
            const meta = regionMeta[region];
            return (
              <div
                key={region}
                className={`rounded-lg border ${meta.border} ${meta.bg} p-4 space-y-1`}
              >
                <p className={`text-xs font-semibold uppercase tracking-wide ${meta.color}`}>
                  {meta.label}
                </p>
                <p className={`text-2xl font-mono font-bold ${meta.color}`}>
                  {fmtNum(resultRecord.region_voxels[region])}
                </p>
                <p className="text-xs text-slate-500">voxels</p>
              </div>
            );
          })}
        </div>

        {/* Bar chart */}
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={voxelChartData}
              margin={{ top: 8, right: 16, left: 24, bottom: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis
                dataKey="region"
                tick={{ fill: '#94a3b8', fontSize: 12 }}
                axisLine={{ stroke: '#1f2937' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#94a3b8', fontSize: 10 }}
                axisLine={{ stroke: '#1f2937' }}
                tickLine={false}
                tickFormatter={(v: number) =>
                  v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)
                }
              />
              <Tooltip content={<VoxelTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <Bar dataKey="voxels" radius={[4, 4, 0, 0]} maxBarSize={80}>
                {voxelChartData.map((entry) => (
                  <Cell key={entry.region} fill={entry.bar} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* ── Evaluation metrics ──────────────────────────────────────────── */}
      <section className="rounded-xl border border-panelBorder bg-panel p-5 space-y-4">
        <h2 className="text-sm font-bold text-white flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-cyan-400" />
          Evaluation Metrics
        </h2>

        {!metrics ? (
          <div className="flex gap-2 p-3 rounded-lg bg-amber-900/20 border border-amber-700 text-xs text-amber-300">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>
              <strong>Ground truth unavailable.</strong> Evaluation metrics cannot be calculated.
              Upload with matching ground-truth segmentation masks to enable Dice, IoU, Precision
              and Recall scoring.
            </span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-panelBorder">
                  <th className="px-4 py-2 text-left text-slate-500 font-medium">Metric</th>
                  {(['WT', 'TC', 'ET'] as const).map((r) => (
                    <th key={r} className={`px-4 py-2 text-right font-semibold ${regionMeta[r].color}`}>
                      {r}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-panelBorder">
                {metricRows.map(({ label, key }) => (
                  <tr key={key}>
                    <td className="px-4 py-3 text-slate-400">{label}</td>
                    {(['WT', 'TC', 'ET'] as const).map((r) => (
                      <MetricCell key={r} value={metrics?.[r]?.[key]} />
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ── Mask downloads ──────────────────────────────────────────────── */}
      <section className="rounded-xl border border-panelBorder bg-panel p-5 space-y-3">
        <h2 className="text-sm font-bold text-white flex items-center gap-2">
          <Download className="w-4 h-4 text-cyan-400" />
          Download Individual Masks
        </h2>
        <p className="text-xs text-slate-500">
          NIfTI masks (.nii.gz) for each segmentation region. Served as{' '}
          <span className="font-mono">application/gzip</span>.
        </p>
        <div className="flex flex-wrap gap-3">
          {(['WT', 'TC', 'ET'] as const).map((region) => {
            const meta = regionMeta[region];
            return (
              <a
                key={region}
                href={resultsService.getMaskDownloadUrl(currentJobId, region)}
                download
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border ${meta.border} ${meta.bg} ${meta.color} text-xs font-semibold hover:brightness-125 transition-all`}
              >
                <Download className="w-3.5 h-3.5" />
                {region} Mask (.nii.gz)
              </a>
            );
          })}
        </div>
      </section>

      {/* ── Navigation actions ──────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-3 pb-6">
        <Link
          to="/visualization"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold transition-colors"
        >
          <Eye className="w-4 h-4" />
          3-View Visualization
        </Link>
        <Link
          to="/enhancement"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold transition-colors"
        >
          <Sparkles className="w-4 h-4" />
          Enhancement Viewer
        </Link>
        <button
          onClick={() => navigate('/processing')}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Re-run Segmentation
        </button>
      </div>
    </div>
  );
};
