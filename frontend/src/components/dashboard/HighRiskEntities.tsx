'use client';

import { useState, useEffect } from 'react';
import { AlertTriangle, Search } from 'lucide-react';
import Link from 'next/link';
import { sentinelApi, HighRiskEntity as ApiHighRiskEntity } from '@/lib/apiClient';
import { formatDistanceToNow } from 'date-fns';

interface HighRiskEntity {
  id: string;
  address: string;
  type: 'address' | 'token';
  risk_score: number;
  category: string;
  name?: string;
  first_detected: string;
}

export default function HighRiskEntities() {
  const [entities, setEntities] = useState<HighRiskEntity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHighRiskEntities() {
      try {
        const data: ApiHighRiskEntity[] = await sentinelApi.getHighRiskEntities();
        setEntities(data);
        setError(null);
      } catch (err: any) {
        console.error('Failed to fetch high risk entities:', err);
        setError('Failed to load high risk entities');
      } finally {
        setIsLoading(false);
      }
    }

    fetchHighRiskEntities();
  }, []);

  function formatAddress(address: string): string {
    if (!address) return '';
    return `${address.substring(0, 4)}...${address.substring(address.length - 4)}`;
  }

  function getRiskBadgeColor(score: number) {
    if (score >= 80) return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">High Risk Entities</h2>
        <div className="flex items-center">
          <AlertTriangle className="h-4 w-4 text-red-500 mr-1" />
          <span className="text-xs text-gray-500 dark:text-gray-400">Requires attention</span>
        </div>
      </div>
      
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
      
      {!isLoading && !error && entities.length === 0 && (
        <div className="text-center p-4 text-gray-500 dark:text-gray-400">
          <Search className="inline-block h-12 w-12 mb-2 opacity-50" />
          <p>No high risk entities detected at this time.</p>
        </div>
      )}
      
      {entities.length > 0 && (
        <div className="space-y-3">
          {entities.map((entity) => (
            <div 
              key={entity.id}
              className="p-3 border border-gray-200 dark:border-gray-700 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700/50"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <span className="font-mono text-sm mr-2" title={entity.address}>
                    {formatAddress(entity.address)}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                    {entity.type}
                  </span>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${getRiskBadgeColor(entity.risk_score)}`}>
                  {entity.risk_score}% Risk
                </span>
              </div>
              
              {entity.category && (
                <div className="mb-2">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Category:</p>
                  <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
                    {entity.category}
                  </span>
                </div>
              )}
              
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  First detected: {formatDistanceToNow(new Date(entity.first_detected), { addSuffix: true })}
                </span>
                <Link 
                  href={`/analyze?address=${encodeURIComponent(entity.address)}`}
                  className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Analyze
                </Link>
              </div>
            </div>
          ))}
          
          {entities.length > 5 && (
            <div className="text-center pt-2">
              <Link 
                href="/reports?filter=high-risk" 
                className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
              >
                View all high risk entities
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
