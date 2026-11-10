import { apiClient } from './client';
import type { HealthResponse } from '../types';

export const healthService = {
  async getHealth(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>('/api/health');
    return response.data;
  },
};
