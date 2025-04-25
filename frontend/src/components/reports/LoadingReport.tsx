import React from 'react';

export default function LoadingReport() {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="animate-pulse">
        {/* Loading skeleton for tabs */}
        <div className="flex gap-2 mb-6">
          <div className="bg-gray-200 dark:bg-gray-700 h-8 w-32 rounded-md"></div>
          <div className="bg-gray-200 dark:bg-gray-700 h-8 w-32 rounded-md"></div>
        </div>
        
        {/* Loading skeleton for content */}
        <div className="space-y-4">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-4/6"></div>
          
          <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded w-full mt-6"></div>
          
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
        </div>
      </div>
    </div>
  );
}
