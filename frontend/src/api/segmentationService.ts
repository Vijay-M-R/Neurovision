import { apiClient } from './client';
import type { SegmentRequest, SegmentResponse } from '../types';

export const segmentationService = {
  async runSegmentation(
    jobId: string,
    options: SegmentRequest = { generate_visualization: true }
  ): Promise<SegmentResponse> {
    const response = await apiClient.post<SegmentResponse>(
      `/api/segment/${jobId}`,
      options
    );
    return response.data;
  },
};
