export interface HealthResponse {
  status: string;
  ai_engine_available: boolean;
  model_loaded: boolean;
  device: string;
  cuda_available: boolean;
  device_name?: string | null;
}

export interface ModelInfoResponse {
  model_name: string;
  architecture: string;
  bundle: string;
  version: string;
  parameters: number;
  input_channels: number;
  output_channels: number;
  device: string;
  status: string;
  training_disabled: boolean;
  fine_tuning_disabled: boolean;
  cached: boolean;
}

export interface UploadResponse {
  job_id: string;
  status: string;
  filename: string;
  file_size_bytes: number;
  dimensions: number[];
  modalities: number;
  message?: string;
}

export interface RegionVoxelCounts {
  WT: number;
  TC: number;
  ET: number;
}

export interface SegmentRequest {
  generate_visualization?: boolean;
}

export interface SegmentResponse {
  job_id: string;
  status: string;
  model: string;
  device: string;
  processing_time_seconds: number;
  regions: RegionVoxelCounts;
  tumor_voxels: number;
  dimensions: number[];
  visualization_url: string;
  results_url: string;
  download_url: string;
  evaluation_available: boolean;
  evaluation_message?: string | null;
}

export interface EnhanceRequest {
  modality?: number;
  clip_limit?: number;
  slice_indices?: {
    axial: number;
    coronal: number;
    sagittal: number;
  } | null;
}

export interface EnhanceResponse {
  job_id: string;
  status: string;
  modality: string;
  slices: {
    axial: number;
    coronal: number;
    sagittal: number;
  };
  preview_urls: {
    axial: string;
    coronal: string;
    sagittal: string;
  };
}

export interface ResultRecord {
  project: string;
  job_id: string;
  patient_id?: string;
  created_at: string;
  status: string;
  model: string;
  device: string;
  processing_time_seconds: number;
  tumor_voxels: number;
  region_voxels: RegionVoxelCounts;
  shape: number[];
  evaluation_metrics?: any | null;
  visualization?: {
    visualization_path: string;
    slices: {
      axial: number;
      coronal: number;
      sagittal: number;
    };
    ground_truth_available: boolean;
    layout: string;
  } | null;
  urls?: {
    results: string;
    visualization: string;
    masks: {
      WT: string;
      TC: string;
      ET: string;
    };
    download: string;
  };
}
