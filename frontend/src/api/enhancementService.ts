import { apiClient } from './client';
import type { EnhanceRequest, EnhanceResponse } from '../types';

export const enhancementService = {
  async runEnhancement(
    jobId: string,
    params: EnhanceRequest = { modality: 0, clip_limit: 2.0 }
  ): Promise<EnhanceResponse> {
    const response = await apiClient.post<EnhanceResponse>(
      `/api/enhance/${jobId}`,
      params
    );
    return response.data;
  },
};
