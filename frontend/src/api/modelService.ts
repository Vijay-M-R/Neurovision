import { apiClient } from './client';
import type { ModelInfoResponse } from '../types';

export const modelService = {
  async getModelInfo(): Promise<ModelInfoResponse> {
    const response = await apiClient.get<ModelInfoResponse>('/api/model-info');
    return response.data;
  },
};
