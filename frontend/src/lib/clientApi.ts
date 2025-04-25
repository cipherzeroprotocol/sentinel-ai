/**
 * Client API functions for making requests to the backend
 */

import { AnalysisType } from '@/hooks/api';

// Generic error handling for fetch requests
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `API Error: ${response.status} ${response.statusText}`);
  }
  
  return await response.json() as T;
}

// API functions
export const clientApi = {
  // Analysis functions
  analyze: async (params: {
    address?: string;
    token?: string;
    type: AnalysisType;
    days?: number;
  }) => {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    
    return handleResponse(response);
  },
  
  // Report functions
  getReport: async (reportId: string) => {
    const response = await fetch(`/api/reports/${reportId}`);
    return handleResponse(response);
  },
  
  getReports: async () => {
    const response = await fetch('/api/reports');
    return handleResponse(response);
  },
  
  // Search functions
  search: async (query: string) => {
    const response = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    
    return handleResponse(response);
  },
  
  // High risk entities
  getHighRiskAddresses: async (limit: number = 10) => {
    const response = await fetch(`/api/high-risk/addresses?limit=${limit}`);
    return handleResponse(response);
  },
  
  getHighRiskTokens: async (limit: number = 10) => {
    const response = await fetch(`/api/high-risk/tokens?limit=${limit}`);
    return handleResponse(response);
  },
};
