/**
 * API client for the Sentinel AI backend
 * This client handles all API requests to the backend using Axios.
 */
import axios, { AxiosError } from 'axios';

// Base configuration from environment variables
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// Type definitions for API responses (Ensure these are defined or imported correctly)
// Assuming they might be defined in a separate types file, e.g., '@/types'
// If not, define them here or import from their actual location.
// Example definitions (adjust as needed):
export interface ApiResponse {
  success: boolean;
  error?: string;
}

export interface AnalysisApiResponse extends ApiResponse {
  reports(reports: any): unknown;
  target: string;
  target_type: 'address' | 'token';
  analysis_type: string;
  results: Record<string, any>;
  report_id?: string;
  report_path?: string;
}

// Define the Search API response structure
export interface SearchResultItem {
  id: string;
  type: 'address' | 'token' | 'transaction' | 'report'; // Add other possible types
  value: string; // The actual address, token symbol, tx hash, or report title
  label?: string; // A user-friendly label (e.g., token name)
  risk_score?: number;
  timestamp?: string; // Relevant timestamp (e.g., report creation, tx time)
}

export interface SearchApiResponse extends ApiResponse {
  query: string;
  results: SearchResultItem[];
}

export interface RecentAnalysis {
  id: string;
  target: string;
  target_type: 'address' | 'token'; // Corrected from targetType
  analysis_type: string; // Corrected from analysisType
  risk_score: number; // Corrected from riskScore
  timestamp: string; // Corrected from date
  status: 'completed' | 'failed' | 'processing';
  report_path?: string;
  // findings?: string[]; // Removed if not provided by backend
}

export interface HighRiskEntity {
  id: string;
  address: string;
  type: 'address' | 'token'; // Corrected from entity_type
  risk_score: number; // Corrected from risk_score
  category: string; // Added based on dashboard component usage
  name?: string;
  first_detected: string; // Corrected from last_activity
  // flags?: string[]; // Removed if not provided by backend
  // risk_factors?: string[]; // Removed if not provided by backend
}

export interface ApiStatusResponse {
  status: 'operational' | 'degraded' | 'down' | 'maintenance';
  message?: string;
  services: {
    blockchain_api: 'operational' | 'degraded' | 'down' | 'unknown'; // Added unknown
    analysis_engine: 'operational' | 'degraded' | 'down' | 'unknown'; // Added unknown
    database: 'operational' | 'degraded' | 'down' | 'unknown'; // Added unknown
  };
  last_updated: string;
  // Add other fields if provided by backend (version, uptime, etc.)
  version?: string;
  uptime?: number;
}

// Define types for Activity Timeline
export interface TimelineEvent {
  id: string;
  timestamp: string | Date; // API might return string, client might convert to Date
  type: string;
  title: string;
  description?: string;
  isSuspicious?: boolean;
  severity?: 'low' | 'medium' | 'high';
  amount?: number;
  relatedAddress?: string;
  // Add any other fields returned by the API
}

export interface ActivityTimelineApiResponse extends ApiResponse {
  address: string;
  events: TimelineEvent[];
}

// Create an axios instance with default configuration
const axiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 60000, // 60 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include auth token if available
axiosInstance.interceptors.request.use(
  (config) => {
    // Add auth token from localStorage if available
    // Consider using next-auth session token if applicable
    const token = typeof window !== 'undefined' ? localStorage.getItem('sentinelAuthToken') : null;
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor for simplified error handling
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Log the error for debugging
    console.error('API Error:', error.response?.status, error.message, error.config?.url);
    // Rethrow a formatted error
    return Promise.reject(formatError(error));
  }
);


// API client object
export const sentinelApi = {
  /**
   * Submit an analysis request
   */
  analyze: async (params: {
    type: string; // Consider using a specific AnalysisType enum/union
    address?: string;
    token?: string;
    days: number;
  }): Promise<AnalysisApiResponse> => {
    console.log("Sending analysis request with params:", params);
    try {
      const response = await axiosInstance.post<AnalysisApiResponse>('/api/analyze', params);
      console.log("Analysis API response:", response.data);
      return response.data;
    } catch (err) {
      console.error("Analysis API error:", err);
      throw err;
    }
  },

  /**
   * Get a list of recent analyses
   * Updated endpoint based on dashboard usage
   */
  getRecentAnalyses: async (limit: number = 10): Promise<RecentAnalysis[]> => {
    // Assuming the backend endpoint is /api/analyses/recent
    const response = await axiosInstance.get<{ analyses: RecentAnalysis[] }>(`/api/analyses/recent?limit=${limit}`);
    return response.data.analyses || [];
  },

  /**
   * Get a list of high risk entities
   * Updated endpoint based on dashboard usage
   */
  getHighRiskEntities: async (limit: number = 5): Promise<HighRiskEntity[]> => {
    // Assuming the backend endpoint is /api/entities/high-risk
    const response = await axiosInstance.get<{ entities: HighRiskEntity[] }>(`/api/entities/high-risk?limit=${limit}`);
    return response.data.entities || [];
  },

  /**
   * Get API status information
   * Updated endpoint based on dashboard usage
   */
  getApiStatus: async (): Promise<ApiStatusResponse> => {
    // Assuming the backend endpoint is /api/status
    try {
      const response = await axiosInstance.get<ApiStatusResponse>('/api/status');
      return response.data;
    } catch (error) {
       // Provide a fallback status on error
       console.error("Failed to fetch API status, providing fallback:", error);
       return {
         status: 'degraded',
         message: 'Unable to connect to status service.',
         services: {
           blockchain_api: 'unknown',
           analysis_engine: 'unknown',
           database: 'unknown'
         },
         last_updated: new Date().toISOString()
       };
    }
  },

  /**
   * Get a specific report by ID
   * Assuming endpoint is /api/reports/{id}
   */
  getReport: async (id: string): Promise<AnalysisApiResponse> => {
    const response = await axiosInstance.get<AnalysisApiResponse>(`/api/reports/${id}`);
    return response.data;
  },

  /**
   * Get a list of all reports
   * Assuming endpoint is /api/reports
   */
  getReports: async (): Promise<{ reports: RecentAnalysis[] }> => { // Adjust return type if needed
    const response = await axiosInstance.get<{ reports: RecentAnalysis[] }>('/api/reports');
    return response.data;
  },

  /**
   * Search for entities (addresses or tokens)
   * Assuming endpoint is /api/search?q={query}
   */
  search: async (query: string): Promise<SearchApiResponse> => { // Update return type
    const response = await axiosInstance.get<SearchApiResponse>(`/api/search?q=${encodeURIComponent(query)}`); // Update expected response type
    return response.data; // Return the full response object
  },

  /**
   * Get URL for a report file (e.g., markdown or images within reports)
   * This URL depends on how the backend serves these files.
   * If served directly by the backend API:
   */
  getReportFileUrl: (assetPath: string): string => { // Renamed from getReportAssetUrl
    // Example: assetPath could be 'images/chart.png' from the report content
    // Adjust the base path as needed
    return `${API_URL}/reports/assets/${encodeURIComponent(assetPath)}`;
  },

   /**
   * Get URL for the full report file (e.g., PDF or Markdown download)
   * This depends on how reports are stored and served.
   * Example: If reports are stored with IDs and served via a specific endpoint
   */
  getReportDownloadUrl: (reportIdOrPath: string): string => {
    // Adjust endpoint as needed, e.g., /api/reports/{reportId}/download
    return `${API_URL}/api/reports/download/${encodeURIComponent(reportIdOrPath)}`;
  },

  /**
   * Get activity timeline for a specific address
   * Assuming endpoint is /api/timeline/{address}
   */
  getActivityTimeline: async (address: string | undefined): Promise<ActivityTimelineApiResponse> => {
    if (!address) {
      // Handle the case where address is undefined, maybe return empty or throw error
      return { success: true, address: '', events: [] }; 
    }
    const response = await axiosInstance.get<ActivityTimelineApiResponse>(`/api/timeline/${address}`);
    return response.data;
  }

  // Add other API methods as needed (e.g., getEntityById)
};

// Helper function to format error responses
function formatError(error: any): Error {
  if (axios.isAxiosError(error)) {
    const apiErrorMessage = error.response?.data?.error || error.response?.data?.message;
    const fallbackMessage = `API Error (${error.response?.status || 'Network Error'}): ${error.config?.url}`;
    return new Error(apiErrorMessage || error.message || fallbackMessage);
  }
  return error instanceof Error ? error : new Error('An unknown error occurred');
}

// Export the client instance
export default sentinelApi;
