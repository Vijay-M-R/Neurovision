import { create } from 'zustand';
import type {
  HealthResponse,
  ModelInfoResponse,
  UploadResponse,
  SegmentResponse,
  EnhanceResponse,
  ResultRecord,
} from '../types';

interface AppState {
  // Session Job State
  currentJobId: string | null;
  uploadData: UploadResponse | null;
  segmentResult: SegmentResponse | null;
  enhanceResult: EnhanceResponse | null;
  resultRecord: ResultRecord | null;

  // System & Model Information
  health: HealthResponse | null;
  modelInfo: ModelInfoResponse | null;

  // Loading & Progress States
  isUploading: boolean;
  uploadProgress: number;
  isSegmenting: boolean;
  isEnhancing: boolean;
  isLoadingResults: boolean;

  // Global Alerts / Errors
  error: string | null;

  // Actions
  setJob: (jobId: string, uploadData?: UploadResponse) => void;
  setUploadProgress: (progress: number) => void;
  setIsUploading: (val: boolean) => void;
  setSegmentResult: (result: SegmentResponse) => void;
  setIsSegmenting: (val: boolean) => void;
  setEnhanceResult: (result: EnhanceResponse) => void;
  setIsEnhancing: (val: boolean) => void;
  setResultRecord: (record: ResultRecord | null) => void;
  setIsLoadingResults: (val: boolean) => void;
  setHealth: (health: HealthResponse | null) => void;
  setModelInfo: (info: ModelInfoResponse | null) => void;
  setError: (error: string | null) => void;
  resetSession: () => void;
}

const STORAGE_JOB_ID_KEY = 'neurovision_active_job_id';
const STORAGE_UPLOAD_DATA_KEY = 'neurovision_upload_data';

export const useAppStore = create<AppState>((set) => ({
  currentJobId: sessionStorage.getItem(STORAGE_JOB_ID_KEY),
  uploadData: (() => {
    try {
      const saved = sessionStorage.getItem(STORAGE_UPLOAD_DATA_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  })(),
  segmentResult: null,
  enhanceResult: null,
  resultRecord: null,

  health: null,
  modelInfo: null,

  isUploading: false,
  uploadProgress: 0,
  isSegmenting: false,
  isEnhancing: false,
  isLoadingResults: false,

  error: null,

  setJob: (jobId: string, uploadData?: UploadResponse) => {
    sessionStorage.setItem(STORAGE_JOB_ID_KEY, jobId);
    if (uploadData) {
      sessionStorage.setItem(STORAGE_UPLOAD_DATA_KEY, JSON.stringify(uploadData));
    }
    set({
      currentJobId: jobId,
      uploadData: uploadData || null,
      error: null,
    });
  },

  setUploadProgress: (progress: number) => set({ uploadProgress: progress }),
  setIsUploading: (val: boolean) => set({ isUploading: val }),
  setSegmentResult: (result: SegmentResponse) => set({ segmentResult: result }),
  setIsSegmenting: (val: boolean) => set({ isSegmenting: val }),
  setEnhanceResult: (result: EnhanceResponse) => set({ enhanceResult: result }),
  setIsEnhancing: (val: boolean) => set({ isEnhancing: val }),
  setResultRecord: (record: ResultRecord | null) => set({ resultRecord: record }),
  setIsLoadingResults: (val: boolean) => set({ isLoadingResults: val }),
  setHealth: (health: HealthResponse | null) => set({ health }),
  setModelInfo: (info: ModelInfoResponse | null) => set({ modelInfo: info }),
  setError: (error: string | null) => set({ error }),

  resetSession: () => {
    sessionStorage.removeItem(STORAGE_JOB_ID_KEY);
    sessionStorage.removeItem(STORAGE_UPLOAD_DATA_KEY);
    set({
      currentJobId: null,
      uploadData: null,
      segmentResult: null,
      enhanceResult: null,
      resultRecord: null,
      uploadProgress: 0,
      isUploading: false,
      isSegmenting: false,
      isEnhancing: false,
      error: null,
    });
  },
}));
