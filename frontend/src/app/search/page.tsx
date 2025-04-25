'use client'; // Needs to be client component for form interaction

import React, { useState } from 'react';
// Import SearchResultItem from apiClient
import { sentinelApi, SearchResultItem } from '@/lib/apiClient'; 

export default function SearchPage() {
  const [query, setQuery] = useState('');
  // Update state type to use SearchResultItem
  const [results, setResults] = useState<SearchResultItem[]>([]); 
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setResults([]);

    try {
      // Use the new API client
      const data = await sentinelApi.search(query);
      
      if (!data.success) {
        throw new Error(data.error || 'Search failed');
      }

      setResults(data.results);
    } catch (err: any) {
      setError(err.message || 'Failed to perform search.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6 text-gray-800 dark:text-white">Search Entities</h1>
      <form onSubmit={handleSearch} className="mb-6 flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter address, tag, or keyword..."
          className="flex-grow px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          required
        />
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <p className="text-red-500 dark:text-red-400">Error: {error}</p>}

      {isLoading && <p>Loading results...</p>}

      {!isLoading && results.length > 0 && (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-3">Search Results for "{query}"</h2>
          <ul className="space-y-2">
            {results.map((result, index) => (
              <li key={result.id || index} className="border-b border-gray-200 dark:border-gray-700 pb-2 last:border-b-0">
                {/* Use result.value instead of result.address */}
                <p className="font-mono text-sm text-gray-700 dark:text-gray-300">{result.value}</p> 
                {/* Display type and label if available */}
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Type: {result.type} {result.label ? `(${result.label})` : ''}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

       {!isLoading && !error && results.length === 0 && query && (
         <p className="text-gray-600 dark:text-gray-400">No results found for "{query}".</p>
       )}
    </div>
  );
}
