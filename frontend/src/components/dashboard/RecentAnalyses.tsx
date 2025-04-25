'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Clock, AlertTriangle, Check, Search } from 'lucide-react';
import { sentinelApi } from '@/lib/apiClient';
import { formatDistanceToNow } from 'date-fns';

interface Analysis {
  id: string;
  target: string;
  target_type: string;
  analysis_type: string;
  risk_score: number;
  status: string;
  timestamp: string;
  report_path?: string;
}

export default function RecentAnalyses() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchRecentAnalyses() {
      try {
        // Call the API to get recent analyses
        const data = await sentinelApi.getRecentAnalyses();
        setAnalyses(data);
        setError(null);
      } catch (err: any) {
        console.error('Failed to fetch recent analyses:', err);
        setError('Failed to load recent analyses. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    }

    fetchRecentAnalyses();
  }, []);

  function getRiskBadgeColor(score: number) {
    if (score >= 70) return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
    if (score >= 40) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
  }

  function getStatusIcon(status: string) {
    switch (status.toLowerCase()) {
      case 'completed':
        return <Check className="h-4 w-4 text-green-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500 animate-pulse" />;
      case 'failed':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  }

  function formatAnalysisType(type: string): string {
    return type
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
      <h2 className="text-lg font-semibold mb-4">Recent Analyses</h2>
      
      {isLoading && (
        <div className="flex justify-center p-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
        </div>
      )}
      
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-md">
          {error}
        </div>
      )}
      
      {!isLoading && !error && analyses.length === 0 && (
        <div className="text-center p-4 text-gray-500 dark:text-gray-400">
          <Search className="inline-block h-12 w-12 mb-2 opacity-50" />
          <p>No analyses found. Start by analyzing an address or token.</p>
          <Link href="/analyze" className="text-blue-500 hover:text-blue-600 mt-2 inline-block">
            Perform analysis
          </Link>
        </div>
      )}
      
      {analyses.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Target
                </th>
                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Type
                </th>
                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Risk
                </th>
                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Time
                </th>
                <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {analyses.map((analysis) => (
                <tr key={analysis.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-3 py-2 whitespace-nowrap text-sm">
                    <div className="font-mono text-xs truncate max-w-[120px]" title={analysis.target}>
                      {analysis.target}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {analysis.target_type.charAt(0).toUpperCase() + analysis.target_type.slice(1)}
                    </div>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm">
                    {formatAnalysisType(analysis.analysis_type)}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <span className={`inline-flex text-xs px-2 py-1 rounded-full ${getRiskBadgeColor(analysis.risk_score)}`}>
                      {analysis.risk_score}%
                    </span>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm">
                    <div className="flex items-center">
                      {getStatusIcon(analysis.status)}
                      <span className="ml-1 text-xs">
                        {analysis.status.charAt(0).toUpperCase() + analysis.status.slice(1)}
                      </span>
                    </div>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400">
                    {formatDistanceToNow(new Date(analysis.timestamp), { addSuffix: true })}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-right text-sm">
                    {analysis.report_path ? (
                      <Link 
                        href={`/reports/${encodeURIComponent(analysis.report_path)}`} 
                        className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-xs"
                      >
                        View Report
                      </Link>
                    ) : (
                      <span className="text-gray-400 dark:text-gray-600 text-xs">No Report</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
