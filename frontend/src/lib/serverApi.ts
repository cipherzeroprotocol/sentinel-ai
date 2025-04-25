/**
 * Server-side API client for the Sentinel AI backend
 * Used for server components and getServerSideProps
 */
import { cookies, headers } from 'next/headers';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { NextResponse } from 'next/server';
import { notFound, redirect } from 'next/navigation';
import { revalidatePath } from 'next/cache';

// Global API configuration from environment variables
const API_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
const API_TIMEOUT = parseInt(process.env.API_TIMEOUT || process.env.NEXT_PUBLIC_API_TIMEOUT || '60000', 10);
const API_MAX_RETRIES = parseInt(process.env.API_MAX_RETRIES || process.env.NEXT_PUBLIC_API_MAX_RETRIES || '2', 10);

// Common error messages
const ERROR_MESSAGES = {
  CONNECTION: 'Unable to connect to the Sentinel AI backend. Please check your network connection.',
  TIMEOUT: 'The request took too long to complete. Analysis operations can be resource-intensive, please try again.',
  SERVER: 'The Sentinel AI server encountered an error. Our team has been notified.',
  AUTHENTICATION: 'Authentication failed. Please check your credentials.',
  UNAUTHORIZED: 'You don\'t have permission to access this resource.',
  GENERIC: 'An unexpected error occurred while communicating with the Sentinel AI backend.',
};

/**
 * Makes an API request with retry capability - server side version
 */
export async function makeServerApiRequest<T>(
  endpoint: string,
  method: 'GET' | 'POST' = 'GET',
  body?: any,
  customConfig: RequestInit = {},
  maxRetries: number = API_MAX_RETRIES,
  requireAuth: boolean = true
): Promise<T> {
  // Construct full URL
  const url = `${API_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  
  // Get auth session if authentication is required
  let session = null;
  if (requireAuth) {
    session = await getServerSession(authOptions);
    if (!session) {
      // Save the current path for redirect after login
      const currentPath = headers().get('x-pathname') || endpoint;
      redirect(`/login?callbackUrl=${encodeURIComponent(currentPath)}`);
    }
  }

  // Prepare headers
  const requestHeaders: HeadersInit = {
    'Content-Type': 'application/json',
    ...customConfig.headers,
  };
  
  // Add authentication token if available
  if (session?.user) {
    (requestHeaders as Record<string, string>)['Authorization'] = `Bearer ${session.accessToken}`;
  }
  
  // Prepare request options
  const config: RequestInit = {
    method,
    headers: requestHeaders,
    ...customConfig,
    body: body ? JSON.stringify(body) : undefined,
    // Set cache option to no-store for real-time data
    cache: customConfig.cache || 'no-store',
    next: {
      tags: ['sentinel-api'],
      ...customConfig.next,
    },
  };
  
  let lastError: Error | null = null;
  let retries = 0;
  
  while (retries <= maxRetries) {
    try {
      // Only log in development
      if (process.env.NODE_ENV !== 'production') {
        console.log(`[Server] API Request: ${method} ${url}${retries > 0 ? ` (retry ${retries}/${maxRetries})` : ''}`);
      }
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
      
      const response = await fetch(url, {
        ...config,
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      // Handle non-2xx responses
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.error || `HTTP Error ${response.status}: ${response.statusText}`;
        
        // Handle authentication errors
        if (response.status === 401 || response.status === 403) {
          if (requireAuth) {
            redirect('/login');
          }
          throw new Error(ERROR_MESSAGES.UNAUTHORIZED);
        }
        
        // Handle not found
        if (response.status === 404) {
          notFound();
        }
        
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
      
      // Check for timeout
      if (lastError.name === 'AbortError') {
        lastError = new Error(ERROR_MESSAGES.TIMEOUT);
      }
      
      if (retries >= maxRetries) {
        console.error('API request failed after all retries:', lastError);
        break;
      }
      
      retries++;
      
      // Exponential backoff: 1s, 2s, 4s, etc.
      const delay = 1000 * Math.pow(2, retries - 1);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  // If we got here, all retries failed
  throw lastError || new Error(ERROR_MESSAGES.CONNECTION);
}

/**
 * Server-side API operations
 */
export const serverApi = {
  /**
   * Get all available reports
   */
  getReports: async (options: { cache?: RequestCache } = {}) => {
    return makeServerApiRequest('/api/reports', 'GET', undefined, {
      cache: options.cache || 'no-store',
      next: { revalidate: 300 }, // Revalidate every 5 minutes
    });
  },
  
  /**
   * Get a specific report by ID
   */
  getReportMetadata: async (reportId: string, options: { cache?: RequestCache } = {}) => {
    return makeServerApiRequest(`/api/reports/${reportId}`, 'GET', undefined, {
      cache: options.cache || 'no-store',
      next: { revalidate: 3600 }, // Revalidate every hour
    });
  },
  
  /**
   * Get raw report content (markdown)
   */
  getReportContent: async (filename: string, options: { cache?: RequestCache } = {}) => {
    try {
      const reportUrl = `/generated_reports/${encodeURIComponent(filename)}`;
      const response = await fetch(`${API_URL}${reportUrl}`, {
        headers: {
          'Accept': 'text/markdown, text/plain, */*'
        },
        cache: options.cache || 'no-store',
        next: { revalidate: 3600 }, // Revalidate every hour
      });
      
      if (!response.ok) {
        if (response.status === 404) {
          notFound();
        }
        throw new Error(`Failed to fetch report content: ${response.statusText}`);
      }
      
      return await response.text();
    } catch (error) {
      console.error('Error fetching report content:', error);
      throw error;
    }
  },
  
  /**
   * Utility function to invalidate cache for reports
   */
  revalidateReports: () => {
    revalidatePath('/reports');
  },
  
  /**
   * Utility function to invalidate cache for a specific report
   */
  revalidateReport: (filename: string) => {
    revalidatePath(`/reports/${filename}`);
  },
  
  /**
   * Get the full URL for a report file
   */
  getReportFileUrl: (filename: string): string => {
    return `${API_URL}/generated_reports/${encodeURIComponent(filename)}`;
  }
};

export default serverApi;
