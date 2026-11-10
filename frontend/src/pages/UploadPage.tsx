import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  FileCheck,
  AlertCircle,
  ArrowRight,
  HardDrive,
  Info,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { uploadService } from '../api/uploadService';

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    currentJobId,
    uploadData,
    setJob,
    isUploading,
    uploadProgress,
    setIsUploading,
    setUploadProgress,
    setError,
    error,
  } = useAppStore();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [localValidationMsg, setLocalValidationMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateAndSelectFile = (file: File) => {
    setLocalValidationMsg(null);
    setError(null);

    const name = file.name.toLowerCase();
    if (!name.endsWith('.nii') && !name.endsWith('.nii.gz')) {
      setLocalValidationMsg('Invalid file format. Only 4D NIfTI files (.nii or .nii.gz) are supported.');
      setSelectedFile(null);
      return;
    }

    if (file.size === 0) {
      setLocalValidationMsg('File is empty (0 bytes).');
      setSelectedFile(null);
      return;
    }

    // Check size against 150 MB limit
    const sizeMb = file.size / (1024 * 1024);
    if (sizeMb > 150) {
      setLocalValidationMsg(`File size (${sizeMb.toFixed(1)} MB) exceeds the maximum limit of 150 MB.`);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSelectFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSelectFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);
    setLocalValidationMsg(null);

    try {
      const res = await uploadService.uploadMRI(selectedFile, (percent) => {
        setUploadProgress(percent);
      });
      setJob(res.job_id, res);
      setSelectedFile(null);
    } catch (err: any) {
      setError(err.message || 'MRI upload or backend validation failed.');
    } finally {
      setIsUploading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <Upload className="w-5 h-5 text-cyan-400" />
          <span>Upload 4D Brain MRI Volume</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Upload a multi-modality NIfTI scan (FLAIR, T1, T1ce, T2). The backend performs structural verification and creates an isolated job session.
        </p>
      </div>

      {/* Format Requirements Panel */}
      <div className="bg-[#0e1626] border border-cyan-900/30 rounded-xl p-4 text-xs text-slate-300 grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="flex items-start gap-2.5">
          <FileCheck className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-slate-200">Supported Formats</div>
            <div className="text-[11px] text-slate-400 mt-0.5"><code>.nii</code> or <code>.nii.gz</code> 4-modality files</div>
          </div>
        </div>

        <div className="flex items-start gap-2.5">
          <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-slate-200">Channel Order</div>
            <div className="text-[11px] text-slate-400 mt-0.5">0: FLAIR, 1: T1, 2: T1ce, 3: T2</div>
          </div>
        </div>

        <div className="flex items-start gap-2.5">
          <HardDrive className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-slate-200">Dimensions & Cap</div>
            <div className="text-[11px] text-slate-400 mt-0.5">4D (X, Y, Z, 4) up to 150 MB</div>
          </div>
        </div>
      </div>

      {/* Upload Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all ${
          dragActive
            ? 'border-cyan-400 bg-cyan-950/30'
            : selectedFile
            ? 'border-teal-500/80 bg-teal-950/20'
            : 'border-slate-700/80 hover:border-slate-600 bg-panel hover:bg-panelHover'
        } ${isUploading ? 'pointer-events-none opacity-60' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".nii,.nii.gz,application/gzip"
          onChange={handleFileInputChange}
          className="hidden"
        />

        <div className="w-12 h-12 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center text-cyan-400 mb-3">
          <Upload className="w-6 h-6" />
        </div>

        {selectedFile ? (
          <div className="space-y-1">
            <div className="text-sm font-semibold text-teal-300 font-mono">
              {selectedFile.name}
            </div>
            <div className="text-xs text-slate-400 font-mono">
              {formatBytes(selectedFile.size)} — Ready to upload
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            <div className="text-sm font-semibold text-slate-200">
              Drag and drop your 4D Brain MRI scan here
            </div>
            <div className="text-xs text-slate-400">
              or <span className="text-cyan-400 font-medium">browse files</span> from your computer
            </div>
          </div>
        )}
      </div>

      {/* Validation Message / Error */}
      {localValidationMsg && (
        <div className="bg-amber-950/40 border border-amber-800/80 rounded-lg p-3 text-xs text-amber-300 flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>{localValidationMsg}</span>
        </div>
      )}

      {error && (
        <div className="bg-rose-950/40 border border-rose-800/80 rounded-lg p-3 text-xs text-rose-300 flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Action Buttons & Upload Progress */}
      {selectedFile && !isUploading && (
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setSelectedFile(null);
            }}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            className="flex items-center gap-2 px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 text-xs font-semibold shadow-md transition-colors"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload and Verify MRI</span>
          </button>
        </div>
      )}

      {/* Uploading Progress State */}
      {isUploading && (
        <div className="bg-panel border border-panelBorder rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-cyan-300 flex items-center gap-2">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              Streaming MRI volume to backend...
            </span>
            <span className="text-slate-400">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className="bg-cyan-500 h-2 transition-all duration-300 rounded-full"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-400">
            Backend is performing NiBabel format parsing and multi-channel validation...
          </p>
        </div>
      )}

      {/* Successfully Uploaded Active Job Card */}
      {uploadData && currentJobId && (
        <div className="bg-panel border border-teal-800/60 rounded-xl p-5 space-y-4 shadow-lg">
          <div className="flex items-center justify-between border-b border-panelBorder pb-3">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-teal-400" />
              <div>
                <h3 className="text-sm font-bold text-white font-mono">
                  MRI Scan Successfully Verified & Stored
                </h3>
                <div className="text-[11px] text-slate-400">
                  Job ID: <code className="text-cyan-300">{currentJobId}</code>
                </div>
              </div>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800">
              READY FOR INFERENCE
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <div className="text-[11px] text-slate-400">Saved Filename</div>
              <div className="text-slate-200 font-mono font-medium truncate mt-1">
                {uploadData.filename}
              </div>
            </div>

            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <div className="text-[11px] text-slate-400">Dimensions</div>
              <div className="text-cyan-300 font-mono font-medium mt-1">
                {uploadData.dimensions.join(' × ')}
              </div>
            </div>

            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <div className="text-[11px] text-slate-400">Modalities</div>
              <div className="text-slate-200 font-mono font-medium mt-1">
                {uploadData.modalities} Channels
              </div>
            </div>

            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <div className="text-[11px] text-slate-400">File Size</div>
              <div className="text-slate-200 font-mono font-medium mt-1">
                {formatBytes(uploadData.file_size_bytes)}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              onClick={() => navigate('/processing')}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 text-xs font-bold shadow-md transition-colors"
            >
              <span>Continue to AI Segmentation</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
