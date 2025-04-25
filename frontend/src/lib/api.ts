/**
 * API utilities for interacting with the Sentinel AI backend
 */

// Global API configuration from environment variables
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
const API_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '120000', 10);
const API_MAX_RETRIES = parseInt(process.env.NEXT_PUBLIC_API_MAX_RETRIES || '3', 10);

// Common error messages
const ERROR_MESSAGES = {
  CONNECTION: 'Unable to connect to the Sentinel AI backend. Please check your network connection.',
  TIMEOUT: 'The request took too long to complete. AI analysis operations can be resource-intensive, please try again.',
  SERVER: 'The Sentinel AI server encountered an error. Our team has been notified.',
  AUTHENTICATION: 'Authentication failed. Please check your credentials.',
  GENERIC: 'An unexpected error occurred while communicating with the Sentinel AI backend.',
};

/**
 * Adds timeout to a fetch request
 */
async function fetchWithTimeout(url: string, options: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const { signal } = controller;
  
  // Create timeout promise
  const timeout = setTimeout(() => {
    controller.abort();
  }, timeoutMs);
  
  try {
    const response = await fetch(url, { ...options, signal });
    clearTimeout(timeout);
    return response;
  } catch (error) {
    clearTimeout(timeout);
    if ((error as any).name === 'AbortError') {
      throw new Error(ERROR_MESSAGES.TIMEOUT);
    }
    throw error;
  }
}

/**
 * Makes an API request with retry capability
 */
export async function makeApiRequest<T>(
  endpoint: string,
  method: 'GET' | 'POST' = 'GET',
  body?: any,
  customConfig: RequestInit = {},
  maxRetries: number = API_MAX_RETRIES
): Promise<T> {
  // Construct full URL
  const url = `${API_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  
  // Prepare headers
  const headers = {
    'Content-Type': 'application/json',
    ...customConfig.headers,
  };
  
  // Prepare request options
  const config: RequestInit = {
    method,
    headers,
    ...customConfig,
    body: body ? JSON.stringify(body) : undefined,
  };
  
  let lastError: Error | null = null;
  let retries = 0;
  
  while (retries <= maxRetries) {
    try {
      // Only log in non-production environments to avoid console clutter
      if (process.env.NODE_ENV !== 'production') {
        console.log(`API Request: ${method} ${url}${retries > 0 ? ` (retry ${retries}/${maxRetries})` : ''}`);
      }
      
      // Make request with timeout
      const response = await fetchWithTimeout(url, config, API_TIMEOUT);
      
      // Handle non-2xx responses
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.error || `HTTP Error ${response.status}: ${response.statusText}`;
        
        // Don't retry for client errors (4xx)
        if (response.status >= 400 && response.status < 500) {
          throw new Error(errorMessage);
        }
        
        // For server errors, attempt retry
        lastError = new Error(errorMessage);
        throw lastError;
      }
      
      // Parse and return response data
      return await response.json() as T;
      
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(ERROR_MESSAGES.GENERIC);
      
      if (retries >= maxRetries) {
        console.error('API request failed after all retries:', lastError);
        break;
      }
      
      retries++;
      
      // Exponential backoff: 1s, 2s, 4s, etc.
      const delay = 1000 * Math.pow(2, retries - 1);
      console.log(`Retrying in ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  // If we got here, all retries failed
  throw lastError || new Error(ERROR_MESSAGES.CONNECTION);
}

/**
 * Analysis API operations
 */
export const sentinelApi = {
  /**
   * Submit an analysis request
   */
  analyze: async (params: {
    type: string;
    address?: string;
    token?: string;
    days: number;
  }) => {
    return makeApiRequest('/api/analyze', 'POST', params);
  },
  
  /**
   * Get all available reports
   */
  getReports: async () => {
    return makeApiRequest('/api/reports');
  },
  
  /**
   * Get a specific report by ID
   */
  getReportMetadata: async (reportId: string) => {
    return makeApiRequest(`/api/reports/${reportId}`);
  },
  
  /**
   * Search for entities
   */
  search: async (query: string) => {
    return makeApiRequest('/api/search', 'POST', { query });
  },
  
  /**
   * Get the full URL for a report file
   */
  getReportFileUrl: (filename: string): string => {
    return `${API_URL}/generated_reports/${encodeURIComponent(filename)}`;
  }
};
