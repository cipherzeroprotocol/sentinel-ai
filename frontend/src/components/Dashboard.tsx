'use client';

import { useState, useEffect } from 'react';
import { AlertCircle, ArrowRight, Clock, Search, Shield, Loader2 } from 'lucide-react';
import { sentinelApi } from '@/lib/apiClient';
import type { AnalysisType, RiskScore, RiskLevel, SecurityReport } from '@/types';
import Link from 'next/link';
import ReportVisualizations from '@/components/ReportVisualizations';
import ApiStatusWidget from './dashboard/ApiStatusWidget';

// Risk level colors
const riskLevelColors: Record<RiskLevel, string> = {
  low: 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-800',
  high: 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800',
  very_high: 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800',
  unknown: 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-900/30 dark:text-gray-400 dark:border-gray-800',
};

// Analysis type options
const analysisOptions: { value: AnalysisType; label: string }[] = [
  { value: 'ico', label: 'ICO Analysis' },
  { value: 'rugpull', label: 'Rugpull Detection' },
  { value: 'money_laundering', label: 'Money Laundering' },
  { value: 'mixer', label: 'Mixer Detection' },
  { value: 'dusting', label: 'Address Poisoning' },
  { value: 'wallet', label: 'Wallet Profile' },
  { value: 'transaction', label: 'Transaction Analysis' },
];

// Get risk level from score
function getRiskLevel(score: number): RiskLevel {
  if (score >= 80) return 'very_high';
  if (score >= 60) return 'high';
  if (score >= 40) return 'medium';
  return 'low';
}

// Risk score component with color-coding
interface RiskScoreProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const RiskScore = ({ score, size = 'md', showLabel = true }: RiskScoreProps) => {
  const level = getRiskLevel(score);
  const sizeClasses = {
    sm: 'w-16 h-16 text-lg',
    md: 'w-20 h-20 text-xl',
    lg: 'w-24 h-24 text-2xl',
  };

  return (
    <div className="flex flex-col items-center">
      <div 
        className={`${sizeClasses[size]} rounded-full flex items-center justify-center border-4 ${
          level === 'low' ? 'border-green-500 text-green-500' : 
          level === 'medium' ? 'border-yellow-500 text-yellow-500' : 
          'border-red-500 text-red-500'
        }`}
      >
        {score}
      </div>
      {showLabel && (
        <div className={`mt-2 font-medium ${
          level === 'low' ? 'text-green-600 dark:text-green-400' : 
          level === 'medium' ? 'text-yellow-600 dark:text-yellow-400' : 
          'text-red-600 dark:text-red-400'
        }`}>
          {level === 'very_high' ? 'Very High' : level.charAt(0).toUpperCase() + level.slice(1)}
        </div>
      )}
    </div>
  );
};

// Entity card component
interface EntityCardProps {
  title: string;
  address: string;
  type: string;
  riskScore: number;
  date?: string;
}

const EntityCard = ({ title, address, type, riskScore, date }: EntityCardProps) => {
  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-medium text-gray-900 dark:text-gray-100">{title}</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 font-mono truncate">{address}</p>
          <div className="flex items-center mt-2">
            <span className={`text-xs px-2 py-1 rounded ${riskLevelColors[getRiskLevel(riskScore)]}`}>
              {type}
            </span>
            {date && (
              <span className="text-xs text-gray-500 dark:text-gray-400 ml-2 flex items-center">
                <Clock className="w-3 h-3 mr-1" />
                {new Date(date).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
        <RiskScore score={riskScore} size="sm" showLabel={false} />
      </div>
    </div>
  );
};

// Main Dashboard Component
export default function Dashboard() {
  // State for search and filters
  const [address, setAddress] = useState('');
  const [selectedAnalysisTypes, setSelectedAnalysisTypes] = useState<AnalysisType[]>(['wallet']);
  const [timeframe, setTimeframe] = useState(30); // Days
  
  // State for results and loading
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisResults, setAnalysisResults] = useState<Record<string, any> | null>(null);
  
  // State for recent analyses and high-risk entities
  const [recentReports, setRecentReports] = useState<any[]>([]);
  const [highRiskEntities, setHighRiskEntities] = useState<any[]>([]);

  // Load recent reports on component mount
  useEffect(() => {
    const loadRecentReports = async () => {
      try {
        // Assume getReport() without args fetches all reports.
        // If it strictly requires an ID, the API client needs adjustment or a different method call.
        // Fetch all reports using getReports()
        const data = await sentinelApi.getReports(); 

        // Explicitly check the structure and type before accessing .slice()
        if (data && typeof data === 'object' && 'reports' in data && Array.isArray(data.reports)) {
          setRecentReports(data.reports.slice(0, 5)); // Get top 5
        } else {
          console.warn("Received unexpected data structure for recent reports:", data);
          setRecentReports([]); // Default to empty array if structure is wrong
        }
      } catch (error) {
        console.error("Error loading recent reports:", error);
        // Optionally set an error state for the user
      }
    };
    
    // Mock high-risk entities (in a real app, this would come from API)
    setHighRiskEntities([
      { 
        title: "Suspicious Mixer", 
        address: "8JUjWjLS9KJcZPVE54x1m6MJGgVPTtKhB6azuX5xMRid", 
        type: "Mixer", 
        riskScore: 92,
        date: new Date().toISOString()
      },
      { 
        title: "Potential Scam Token", 
        address: "2tWC4JAdL4AxEFJySziYJfsAnW2MHKRo98vbAPiRDSk8", 
        type: "Rugpull", 
        riskScore: 87,
        date: new Date().toISOString() 
      },
      { 
        title: "Laundering Wallet", 
        address: "EsZoSC2u3TXXhwPxTNHpJnHDnx8c8pp8QQKJKhS7Yowr", 
        type: "Money Laundering", 
        riskScore: 78,
        date: new Date().toISOString() 
      },
    ]);
    
    loadRecentReports();
  }, []);

  // Handle analysis type selection toggle
  const toggleAnalysisType = (type: AnalysisType) => {
    setSelectedAnalysisTypes(prev => {
      if (prev.includes(type)) {
        // Don't allow removing the last selected analysis type
        if (prev.length === 1) return prev;
        return prev.filter(t => t !== type);
      } else {
        return [...prev, type];
      }
    });
  };

  // Run analysis
  const handleAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!address.trim()) {
      setError("Please enter a valid Solana address");
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setAnalysisResults(null);
    
    try {
      // Run analysis for each selected type
      const analysisType = selectedAnalysisTypes.length > 1 ? 'all' : selectedAnalysisTypes[0];
      
      const result = await sentinelApi.analyze({
        type: analysisType,
        address,
        days: timeframe
      });
      
      if (!result.success) {
        throw new Error(result.error || 'Analysis failed');
      }
      
      setAnalysisResults(result);
    } catch (err: any) {
      console.error("Error running analysis:", err);
      setError(err.message || 'An error occurred during analysis');
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to get an overall risk score from results
  const getOverallRiskScore = (): number => {
    if (!analysisResults?.results) return 0;
    
    const results = analysisResults.results;
    let totalScore = 0;
    let count = 0;
    
    // Check each analysis type for risk scores
    if (results.wallet?.risk_assessment?.risk_score) {
      totalScore += results.wallet.risk_assessment.risk_score;
      count++;
    }
    
    if (results.money_laundering?.risk_assessment?.risk_score) {
      totalScore += results.money_laundering.risk_assessment.risk_score;
      count++;
    }
    
    if (results.mixer?.confidence_score) {
      // Convert confidence (0-10) to risk score (0-100)
      totalScore += results.mixer.confidence_score * 10;
      count++;
    }
    
    if (results.rugpull?.risk_score) {
      totalScore += results.rugpull.risk_score;
      count++;
    }
    
    // Add other analysis types as needed
    
    return count > 0 ? Math.round(totalScore / count) : 0;
  };

  // Get factors from analysis results
  const getRiskFactors = (): string[] => {
    if (!analysisResults?.results) return [];
    
    const results = analysisResults.results;
    const factors: string[] = [];
    
    // Collect risk factors from different analysis types
    if (results.wallet?.risk_assessment?.high_risk_interactions) {
      factors.push(...results.wallet.risk_assessment.high_risk_interactions);
    }
    
    if (results.money_laundering?.risk_assessment?.factors) {
      factors.push(...results.money_laundering.risk_assessment.factors);
    }
    
    if (results.rugpull?.risk_factors) {
      factors.push(...results.rugpull.risk_factors);
    }
    
    // Add more factors from other analysis types
    
    // Add placeholder if no factors found
    if (factors.length === 0 && analysisResults?.target) {
      factors.push(`Analysis performed on ${analysisResults.target}`);
    }
    
    return factors;
  };

  return (
    <div className="space-y-6">
      {/* Search and Filter Section */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
          Security Analysis Dashboard
        </h2>
        
        <form onSubmit={handleAnalysis} className="space-y-4">
          {/* Search bar */}
          <div className="flex flex-col sm:flex-row sm:space-x-4 space-y-3 sm:space-y-0">
            <div className="flex-grow relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="Enter Solana address or token"
                className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
            </div>
            
            <div className="sm:w-24">
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              >
                <option value={7}>7d</option>
                <option value={30}>30d</option>
                <option value={90}>90d</option>
                <option value={180}>180d</option>
              </select>
            </div>
            
            <button
              type="submit"
              disabled={isLoading || !address.trim()}
              className="sm:w-32 px-4 py-2 bg-indigo-600 text-white font-medium rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin mr-2" />
              ) : (
                <Shield className="h-5 w-5 mr-2" />
              )}
              {isLoading ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>
          
          {/* Analysis type selection */}
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Analysis Types:</p>
            <div className="flex flex-wrap gap-2">
              {analysisOptions.map((option) => (
                <label 
                  key={option.value}
                  className={`flex items-center p-2 rounded-md cursor-pointer border ${
                    selectedAnalysisTypes.includes(option.value) 
                      ? 'bg-indigo-100 border-indigo-300 dark:bg-indigo-900/30 dark:border-indigo-700'
                      : 'bg-gray-100 border-gray-300 dark:bg-gray-800 dark:border-gray-700'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedAnalysisTypes.includes(option.value)}
                    onChange={() => toggleAnalysisType(option.value)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    {option.label}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </form>
      </div>
      
      {/* Error display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 flex items-start">
          <AlertCircle className="h-5 w-5 text-red-400 dark:text-red-500 mt-0.5 mr-2" />
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}
      
      {/* Results section */}
      {analysisResults && !isLoading && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                Analysis Results
                <span className="ml-2 text-sm px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 rounded-md">
                  {analysisResults.target_type}
                </span>
              </h3>
              <p className="text-sm font-mono text-gray-500 dark:text-gray-400 mt-1">
                {analysisResults.target}
              </p>
            </div>
            
            <div className="mt-4 md:mt-0">
              {analysisResults.report_path && (
                <Link 
                  href={`/reports/${encodeURIComponent(analysisResults.report_path)}`}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
                >
                  Full Report
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              )}
            </div>
          </div>
          
          {/* Add Visualizations */}
          <ReportVisualizations 
            analysisResults={analysisResults} 
            className="mt-6"
          />
          
          {/* Existing content can be removed or kept as detailed data section */}
          <div className="grid grid-cols-1 lg:grid-cols-6 gap-6">
            {/* Overall risk score */}
            <div className="lg:col-span-2 p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800/50">
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">Overall Risk Assessment</h4>
              <div className="flex justify-center">
                <RiskScore score={getOverallRiskScore()} size="lg" />
              </div>
            </div>
            
            {/* Risk factors */}
            <div className="lg:col-span-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800/50">
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">Risk Factors</h4>
              <ul className="space-y-2">
                {getRiskFactors().map((factor, index) => (
                  <li key={index} className="flex items-start">
                    <div className="flex-shrink-0 w-1.5 h-1.5 mt-1.5 rounded-full bg-red-500 mr-2"></div>
                    <span className="text-sm text-gray-700 dark:text-gray-300">{factor}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          
          {/* Analysis details breakdown */}
          <div className="mt-6 space-y-4">
            {analysisResults.results && Object.entries(analysisResults.results).map(([key, value]: [string, any]) => {
              // Skip empty results
              if (!value || Object.keys(value).length === 0) return null;
              
              return (
                <div key={key} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} Analysis
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* Display relevant data for this analysis type - customize based on your data structure */}
                    {key === 'wallet' && value.classification && (
                      <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded border border-gray-200 dark:border-gray-700">
                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Wallet Type</p>
                        <p className="mt-1 text-gray-900 dark:text-white">{value.classification.primary_type}</p>
                        <div className="mt-1 text-xs text-gray-500">Confidence: {value.classification.primary_confidence.toFixed(1)}/10</div>
                      </div>
                    )}
                    
                    {value.risk_assessment && (
                      <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded border border-gray-200 dark:border-gray-700">
                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Risk Score</p>
                        <div className="flex items-center mt-1">
                          <RiskScore 
                            score={value.risk_assessment.risk_score || 0} 
                            size="sm" 
                            showLabel={false} 
                          />
                          <span className="ml-2 text-gray-900 dark:text-white">
                            {value.risk_assessment.risk_level?.replace(/_/g, ' ')}
                          </span>
                        </div>
                      </div>
                    )}
                    
                    {/* Transaction count for transaction or wallet analysis */}
                    {(key === 'transaction' || key === 'wallet') && value.features && (
                      <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded border border-gray-200 dark:border-gray-700">
                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Transaction Count</p>
                        <p className="mt-1 text-gray-900 dark:text-white">
                          {key === 'transaction' ? value.transaction_count : value.features.total_tx_count}
                        </p>
                      </div>
                    )}
                    
                    {/* Add more metric cards based on analysis type */}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      
      {/* Loading state */}
      {isLoading && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 flex flex-col items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="h-12 w-12 text-indigo-500 animate-spin" />
            <p className="text-gray-600 dark:text-gray-400">Analyzing address security...</p>
            <div className="w-64 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full bg-indigo-500 rounded-full animate-pulse" style={{ width: '70%' }}></div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Analyses and High Risk Entities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Analyses */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Recent Analyses</h2>
          
          <div className="space-y-3">
            {recentReports.length > 0 ? (
              recentReports.map((report, index) => {
                // Extract info from filename: report_analysisType_target_timestamp.md
                const parts = report.filename.replace(/\.md$/, '').split('_');
                const analysisType = parts.length > 1 ? parts[1].replace(/-/g, ' ') : 'Unknown';
                const target = parts.length > 2 ? parts[2] : 'Unknown';
                
                return (
                  <Link 
                    key={report.id} 
                    href={`/reports/${encodeURIComponent(report.filename)}`}
                    className="block p-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {analysisType.charAt(0).toUpperCase() + analysisType.slice(1)} Analysis
                        </p>
                        <p className="text-sm font-mono text-gray-500 dark:text-gray-400 truncate">
                          {target}
                        </p>
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        {report.created_at ? new Date(report.created_at).toLocaleDateString() : 'Unknown date'}
                      </div>
                    </div>
                  </Link>
                );
              })
            ) : (
              <p className="text-gray-500 dark:text-gray-400 text-center py-6">
                No recent analyses found
              </p>
            )}
          </div>
          
          <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
            <Link 
              href="/reports" 
              className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 flex items-center justify-center"
            >
              View All Reports
              <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </div>
        </div>
        
        {/* Right column with High Risk Entities and API Status */}
        <div className="space-y-6">
          {/* High Risk Entities */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">High Risk Entities</h2>
            
            <div className="space-y-3">
              {highRiskEntities.length > 0 ? (
                highRiskEntities.map((entity, index) => (
                  <EntityCard 
                    key={index}
                    title={entity.title}
                    address={entity.address}
                    type={entity.type}
                    riskScore={entity.riskScore}
                    date={entity.date}
                  />
                ))
              ) : (
                <p className="text-gray-500 dark:text-gray-400 text-center py-6">
                  No high risk entities found
                </p>
              )}
            </div>
          </div>
          
          {/* API Status Widget */}
          <ApiStatusWidget />
        </div>
      </div>
    </div>
  );
}
