import { useState, useEffect, useCallback } from 'react';
import { clientApi } from '@/lib/clientApi';

// Define base types for API responses
interface ApiResponse {
  success: boolean;
  error?: string;
}

// Analysis types
export type AnalysisType = 
  | 'all' 
  | 'ico' 
  | 'rugpull' 
  | 'money_laundering' 
  | 'dusting' 
  | 'mixer' 
  | 'wallet' 
  | 'transaction';

interface AnalysisRequest {
  address?: string;
  token?: string;
  type: AnalysisType;
  days?: number;
}

interface AnalysisResult {
  // Generic result structure - specific analysis types will have their own structure
  risk_score?: number;
  risk_level?: string;
  risk_factors?: string[];
  [key: string]: any; // Allow for various properties based on analysis type
}

interface AnalysisResponse extends ApiResponse {
  target?: string;
  target_type?: 'address' | 'token';
  analysis_type?: AnalysisType;
  results?: {
    [key in AnalysisType]?: AnalysisResult;
  };
  report_path?: string;
}

// Report types
export interface ReportInfo {
  id: string;
  filename: string;
  created_at: string | null;
  target?: string;
  analysis_type?: string;
}

interface ReportsResponse extends ApiResponse {
  reports: ReportInfo[];
}

// Search types
export interface SearchResult {
  type: string;
  address: string;
  name?: string;
  risk_score?: number;
  last_seen?: string;
  [key: string]: any; // Allow for various properties
}

interface SearchResponse extends ApiResponse {
  query: string;
  results: SearchResult[];
}

// High risk entity types
export interface RiskEntity {
  id: number;
  address: string;
  entity_type?: string;
  entity_name?: string;
  risk_score: number;
  risk_level: string;
  type?: string; // For differentiation (address/token)
}

interface RiskEntitiesResponse extends ApiResponse {
  entities: RiskEntity[];
}

/**
 * Custom hook for triggering and fetching analysis results
 */
export function useAnalysis() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnalysisResponse | null>(null);

  const analyze = useCallback(async (params: AnalysisRequest) => {
    setIsLoading(true);
    setError(null);
    setData(null); // Reset data on new analysis

    try {
      // Assert the type of the result from clientApi.analyze
      const result = await clientApi.analyze(params) as AnalysisResponse;
      if (result.success) {
        setData(result);
      } else {
        setError(result.error || 'Analysis failed');
      }
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  return {
    analyze,
    data,
    isLoading,
    error,
  };
}

/**
 * Custom hook for fetching a specific report by ID
 */
export function useReport(reportId: string | null) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any | null>(null);

  useEffect(() => {
    if (!reportId) return;
    
    const fetchReport = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const data = await clientApi.getReport(reportId);
        setData(data);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch report';
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchReport();
  }, [reportId]);
  
  return { data, isLoading, error };
}

/**
 * Custom hook for fetching recent reports
 */
export function useRecentReports() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ReportInfo[]>([]);
  
  const fetchReports = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Assert the type of the result from clientApi.getReports
      const result = await clientApi.getReports() as ReportsResponse;
      if (result.success && result.reports) {
        setData(result.reports);
        return result.reports;
      } else {
        setError(result.error || 'Failed to fetch reports');
        setData([]); // Ensure data is an empty array on failure
        return [];
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch reports';
      setError(errorMessage);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  useEffect(() => {
    fetchReports();
  }, [fetchReports]);
  
  return { 
    data, 
    isLoading, 
    error, 
    refresh: fetchReports
  };
}

/**
 * Custom hook for fetching high risk entities
 */
export function useHighRiskEntities(limit: number = 10) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RiskEntity[]>([]);
  
  const fetchEntities = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Assert the types of the results from clientApi calls
      const [addressesData, tokensData] = await Promise.all([
        clientApi.getHighRiskAddresses(limit) as Promise<RiskEntitiesResponse>,
        clientApi.getHighRiskTokens(limit) as Promise<RiskEntitiesResponse>
      ]);
      
      // Check success flags before accessing entities
      const safeAddresses = (addressesData.success && addressesData.entities) ? addressesData.entities : [];
      const safeTokens = (tokensData.success && tokensData.entities) ? tokensData.entities : [];

      // Combine and sort by risk score
      const combinedEntities = [
        ...safeAddresses.map((e: RiskEntity) => ({ ...e, type: 'address' })),
        ...safeTokens.map((e: RiskEntity) => ({ ...e, type: 'token' }))
      ].sort((a, b) => b.risk_score - a.risk_score).slice(0, limit);
      
      setData(combinedEntities);
      return combinedEntities;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch high risk entities';
      setError(errorMessage);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [limit]);
  
  useEffect(() => {
    fetchEntities();
  }, [fetchEntities]);
  
  return { 
    data, 
    isLoading, 
    error, 
    refresh: fetchEntities
  };
}

/**
 * Custom hook for searching addresses and tokens
 */
export function useAddressSearch() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SearchResult[]>([]);
  const [query, setQuery] = useState<string>('');
  
  const search = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setData([]);
      setQuery('');
      return [];
    }
    
    setIsLoading(true);
    setError(null);
    setQuery(searchQuery);
    
    try {
      // Assert the type of the result from clientApi.search
      const result = await clientApi.search(searchQuery) as SearchResponse;
      if (result.success && result.results) {
        setData(result.results);
        return result.results;
      } else {
        setError(result.error || 'Search failed');
        setData([]); // Ensure data is an empty array on failure
        return [];
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Search failed';
      setError(errorMessage);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  return {
    search,
    data,
    query,
    isLoading,
    error,
    reset: () => {
      setData([]);
      setQuery('');
      setError(null);
    }
  };
}
