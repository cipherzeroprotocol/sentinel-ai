"use client";

import React, { useState, useMemo } from 'react';
import { Search, ChevronDown, ChevronUp, AlertTriangle, AlertCircle, AlertOctagon } from 'lucide-react';

interface RiskFactor {
  id: string;
  category: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
  details?: string;
  source?: string;
  timestamp?: string;
  impact?: string;
}

interface RiskTableProps {
  factors: RiskFactor[];
  title?: string;
  showSearch?: boolean;
  showPagination?: boolean;
  sortable?: boolean;
  expandable?: boolean;
  pageSize?: number;
}

const RiskTable: React.FC<RiskTableProps> = ({
  factors,
  title = 'Risk Factors',
  showSearch = false,
  showPagination = false,
  sortable = false,
  expandable = false,
  pageSize = 10
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState<keyof RiskFactor>('severity');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  // Filter by search term
  const filteredFactors = useMemo(() => {
    if (!searchTerm.trim()) return factors;
    
    const lowerSearchTerm = searchTerm.toLowerCase();
    return factors.filter(factor => 
      factor.description.toLowerCase().includes(lowerSearchTerm) ||
      factor.category.toLowerCase().includes(lowerSearchTerm) ||
      factor.severity.toLowerCase().includes(lowerSearchTerm) ||
      (factor.details && factor.details.toLowerCase().includes(lowerSearchTerm)) ||
      (factor.source && factor.source.toLowerCase().includes(lowerSearchTerm))
    );
  }, [factors, searchTerm]);

  // Sort factors if sortable
  const sortedFactors = useMemo(() => {
    if (!sortable) return filteredFactors;
    
    return [...filteredFactors].sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      
      // Handle undefined values
      if (aValue === undefined) return sortDirection === 'asc' ? -1 : 1;
      if (bValue === undefined) return sortDirection === 'asc' ? 1 : -1;
      
      // Special case for severity
      if (sortField === 'severity') {
        const severityMap = { low: 1, medium: 2, high: 3 };
        const aNum = severityMap[a.severity as keyof typeof severityMap];
        const bNum = severityMap[b.severity as keyof typeof severityMap];
        return sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
      }
      
      // String comparison for other fields
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      return 0;
    });
  }, [filteredFactors, sortField, sortDirection, sortable]);
  
  // Paginate results
  const paginatedFactors = useMemo(() => {
    if (!showPagination) return sortedFactors;
    
    const startIndex = (currentPage - 1) * pageSize;
    return sortedFactors.slice(startIndex, startIndex + pageSize);
  }, [sortedFactors, currentPage, pageSize, showPagination]);
  
  // Calculate total pages
  const totalPages = useMemo(() => {
    if (!showPagination) return 1;
    return Math.max(1, Math.ceil(sortedFactors.length / pageSize));
  }, [sortedFactors.length, pageSize, showPagination]);
  
  // Handle sorting
  const handleSort = (field: keyof RiskFactor) => {
    if (!sortable) return;
    
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };
  
  // Handle row expansion
  const toggleRow = (id: string) => {
    if (!expandable) return;
    
    const newExpandedRows = new Set(expandedRows);
    if (newExpandedRows.has(id)) {
      newExpandedRows.delete(id);
    } else {
      newExpandedRows.add(id);
    }
    setExpandedRows(newExpandedRows);
  };
  
  // Render severity icon
  const renderSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <AlertOctagon className="h-5 w-5 text-red-500" />;
      case 'medium':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-blue-500" />;
    }
  };
  
  // Get severity text class
  const getSeverityClass = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'text-red-600 dark:text-red-400';
      case 'medium':
        return 'text-yellow-600 dark:text-yellow-400';
      default:
        return 'text-blue-600 dark:text-blue-400';
    }
  };
  
  if (!factors.length) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md p-4">
        <h3 className="text-lg font-medium mb-2">{title}</h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          No risk factors identified
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium">{title}</h3>
          {showSearch && (
            <div className="relative w-64">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Search risks..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1); // Reset to first page on search
                }}
                className="w-full pl-10 pr-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
            </div>
          )}
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800/50">
            <tr>
              {expandable && <th className="px-4 py-3 w-10"></th>}
              <th 
                className={`px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider ${sortable ? 'cursor-pointer' : ''}`}
                onClick={() => sortable && handleSort('severity')}
              >
                <div className="flex items-center">
                  Severity
                  {sortable && sortField === 'severity' && (
                    <span className="ml-1">
                      {sortDirection === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </span>
                  )}
                </div>
              </th>
              <th 
                className={`px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider ${sortable ? 'cursor-pointer' : ''}`}
                onClick={() => sortable && handleSort('category')}
              >
                <div className="flex items-center">
                  Category
                  {sortable && sortField === 'category' && (
                    <span className="ml-1">
                      {sortDirection === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </span>
                  )}
                </div>
              </th>
              <th 
                className={`px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider ${sortable ? 'cursor-pointer' : ''}`}
                onClick={() => sortable && handleSort('description')}
              >
                <div className="flex items-center">
                  Description
                  {sortable && sortField === 'description' && (
                    <span className="ml-1">
                      {sortDirection === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </span>
                  )}
                </div>
              </th>
              {!expandable && (
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Details
                </th>
              )}
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {paginatedFactors.map((factor) => (
              <React.Fragment key={factor.id}>
                <tr 
                  className={`${expandable ? 'cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50' : ''}`}
                  onClick={expandable ? () => toggleRow(factor.id) : undefined}
                >
                  {expandable && (
                    <td className="px-3 text-center">
                      {expandedRows.has(factor.id) ? (
                        <ChevronUp className="h-4 w-4 text-gray-500" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-gray-500" />
                      )}
                    </td>
                  )}
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="mr-2">{renderSeverityIcon(factor.severity)}</span>
                      <span className={`text-sm font-medium capitalize ${getSeverityClass(factor.severity)}`}>
                        {factor.severity}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                    {factor.category}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                    {factor.description}
                  </td>
                  {!expandable && (
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                      {factor.details || 'No additional details'}
                    </td>
                  )}
                </tr>
                {expandable && expandedRows.has(factor.id) && (
                  <tr className="bg-gray-50 dark:bg-gray-700/20">
                    <td colSpan={4} className="px-4 py-3">
                      <div className="text-sm text-gray-600 dark:text-gray-300 space-y-2">
                        {factor.details && (
                          <div>
                            <span className="font-medium">Details:</span> {factor.details}
                          </div>
                        )}
                        {factor.source && (
                          <div>
                            <span className="font-medium">Source:</span> {factor.source}
                          </div>
                        )}
                        {factor.impact && (
                          <div>
                            <span className="font-medium">Impact:</span> {factor.impact}
                          </div>
                        )}
                        {factor.timestamp && (
                          <div>
                            <span className="font-medium">Detected:</span>{' '}
                            {new Date(factor.timestamp).toLocaleString()}
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
      
      {showPagination && totalPages > 1 && (
        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, sortedFactors.length)} of {sortedFactors.length} factors
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskTable;
