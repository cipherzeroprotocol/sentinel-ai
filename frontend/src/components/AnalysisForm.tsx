'use client'; // Mark as a Client Component

import React, { useState, useEffect } from 'react';
import { sentinelApi } from '@/lib/apiClient';
import ReportVisualizations from '@/components/ReportVisualizations';

// Define expected API response structure (adjust based on actual API)
interface AnalysisResult {
    // Define structure based on your API response for different analysis types
    [key: string]: any; // Example: ico, money_laundering, etc.
}

interface ApiResponse {
    success: boolean;
    target: string;
    target_type: 'address' | 'token';
    analysis_type: string; // The type requested ('all' or specific)
    results: AnalysisResult; // Contains keys for each analysis performed
    report_id?: string; // Optional - Deprecated if reports are just files
    report_path?: string; // Optional - Path to the generated report file
    error?: string;
}

// Define the structure for individual analysis results display
interface AnalysisDetailProps {
    title: string;
    data: any; // The specific result data for this analysis type
    reportBaseUrl: string; // Base URL for report images
}

// Helper function to format result keys into titles
function formatResultTitle(key: string): string {
    return key
        .replace(/_/g, ' ') // Replace underscores with spaces
        .replace(/\b\w/g, char => char.toUpperCase()); // Capitalize first letter of each word
}


// Enhanced component to display individual analysis results
const AnalysisDetail: React.FC<AnalysisDetailProps> = ({ title, data, reportBaseUrl }) => {
    if (data === null || data === undefined || (typeof data === 'object' && Object.keys(data).length === 0 && !(data instanceof Date))) {
        // Optionally render something indicating no data for this section
        // return <div className="text-sm text-gray-500 dark:text-gray-400">No data available for {title}.</div>;
        return null; // Or just don't render the section
    }

    // Function to recursively render data, handling nested objects and arrays
    const renderData = (value: any, level = 0): React.ReactNode => {
        const indentClass = `ml-${level * 4}`; // Indentation for nested levels

        if (typeof value === 'boolean') {
            return value ? <span className="text-green-600 dark:text-green-400 font-semibold">Yes</span> : <span className="text-red-600 dark:text-red-400 font-semibold">No</span>;
        }
        if (typeof value === 'string') {
             // Check if it's a path to a report image
             if (value.startsWith('![') && value.includes('](./')) {
                 const match = value.match(/!\[.*?\]\(\.\/(.*?)\)/);
                 if (match && match[1]) {
                     const imageName = match[1];
                     const imageUrl = `${reportBaseUrl}/${imageName}`;
                     console.log("Rendering image:", imageUrl); // Debug log
                     return <img src={imageUrl} alt={imageName} className="max-w-full h-auto my-2 rounded border border-gray-300 dark:border-gray-600" />;
                 }
             }
             // Check for risk levels
             if (value.toLowerCase().includes('high') || value.toLowerCase().includes('severe')) return <span className="text-red-600 dark:text-red-400 font-semibold">{value}</span>;
             if (value.toLowerCase().includes('medium') || value.toLowerCase().includes('moderate')) return <span className="text-yellow-600 dark:text-yellow-400 font-semibold">{value}</span>;
             if (value.toLowerCase().includes('low')) return <span className="text-green-600 dark:text-green-400 font-semibold">{value}</span>;
             // Render multi-line strings (like markdown lists)
             if (value.includes('\n')) {
                 return value.split('\n').map((line, index) => (
                     <span key={index} className="block text-sm text-gray-700 dark:text-gray-300">{line}</span>
                 ));
             }
            return <span className="text-sm text-gray-700 dark:text-gray-300">{value}</span>;
        }
         if (typeof value === 'number') {
             // Check for scores (assuming keys contain 'score' or 'risk') - more specific checks might be needed
             const isScore = title.toLowerCase().includes('score') || title.toLowerCase().includes('risk'); // Check title of the section
             if (isScore) {
                 if (value > 75 || (value > 7.5 && value <= 10)) return <span className="text-red-600 dark:text-red-400 font-semibold">{value.toFixed(2)}</span>;
                 if (value > 40 || (value > 4 && value <= 10)) return <span className="text-yellow-600 dark:text-yellow-400 font-semibold">{value.toFixed(2)}</span>;
                 return <span className="text-green-600 dark:text-green-400 font-semibold">{value.toFixed(2)}</span>;
             }
             // Format large numbers or currency if applicable (e.g., based on key name)
             if (title.toLowerCase().includes('usd') || title.toLowerCase().includes('volume') || title.toLowerCase().includes('liquidity') || title.toLowerCase().includes('market cap')) {
                 return <span className="text-sm text-gray-700 dark:text-gray-300">${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>;
             }
             return <span className="text-sm text-gray-700 dark:text-gray-300">{value.toLocaleString()}</span>;
         }
        if (Array.isArray(value)) {
            if (value.length === 0) return <span className={`text-sm text-gray-500 dark:text-gray-400 ${indentClass}`}>None</span>;
            return (
                <ul className={`list-disc list-inside pl-4 space-y-1 ${indentClass}`}>
                    {value.map((item, index) => (
                        <li key={index} className="text-sm text-gray-700 dark:text-gray-300">{renderData(item, level + 1)}</li>
                    ))}
                </ul>
            );
        }
        if (typeof value === 'object' && value !== null && !(value instanceof Date)) {
            // Render nested objects - skip empty objects
            const entries = Object.entries(value).filter(([_, v]) => v !== null && v !== undefined && !(typeof v === 'object' && Object.keys(v).length === 0 && !(v instanceof Date)));
            if (entries.length === 0) return null; // Don't render empty objects

            return (
                <div className={`space-y-2 ${indentClass}`}>
                    {entries.map(([key, val]) => (
                        <div key={key}>
                            <strong className="text-sm font-medium text-gray-600 dark:text-gray-400">{formatResultTitle(key)}:</strong>
                            <div className="pl-2">{renderData(val, level + 1)}</div>
                        </div>
                    ))}
                </div>
            );
        }
         if (value instanceof Date) {
             return <span className="text-sm text-gray-700 dark:text-gray-300">{value.toLocaleString()}</span>;
         }
        return null; // Fallback for unhandled types
    };

    return (
        <div className="mb-4 p-4 border border-gray-200 dark:border-gray-700 rounded bg-gray-50 dark:bg-gray-700/50 shadow-sm">
            <h4 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-100">{title}</h4>
            {renderData(data)}
        </div>
    );
};


export default function AnalysisForm() {
    // ... existing state variables ...
    const [analysisType, setAnalysisType] = useState('ico');
    const [address, setAddress] = useState('');
    const [token, setToken] = useState('');
    const [days, setDays] = useState(30);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<ApiResponse | null>(null);

    // ... existing useEffect for input visibility ...
    const [showAddressInput, setShowAddressInput] = useState(false);
    const [showTokenInput, setShowTokenInput] = useState(true); // Default ICO

    useEffect(() => {
        // Update input visibility based on selected analysis type
        const needsAddress = ['money_laundering', 'mixer', 'dusting', 'wallet', 'transaction'];
        const needsToken = ['ico', 'rugpull'];

        if (analysisType === 'all') {
            setShowAddressInput(true);
            setShowTokenInput(true);
        } else {
            setShowAddressInput(needsAddress.includes(analysisType));
            setShowTokenInput(needsToken.includes(analysisType));
        }
        // Clear inputs when visibility changes to avoid sending wrong data
        // Only clear if the input is *not* needed for the new type or 'all'
        if (!needsAddress.includes(analysisType) && analysisType !== 'all') setAddress('');
        if (!needsToken.includes(analysisType) && analysisType !== 'all') setToken('');


    }, [analysisType]);

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setIsLoading(true);
        setError(null);
        setResults(null);

        const payload: { type: string; address?: string; token?: string; days: number } = {
            type: analysisType,
            days: days,
        };
        // Only include address/token if the input is visible AND has a value
        if (showAddressInput && address.trim()) payload.address = address.trim();
        if (showTokenInput && token.trim()) payload.token = token.trim();


        // Basic validation
        if (!payload.address && !payload.token) {
             setError('Please provide an Address or Token.');
             setIsLoading(false);
             return;
         }
        // Specific validation if not 'all'
        if (analysisType !== 'all') {
            const needsAddress = ['money_laundering', 'mixer', 'dusting', 'wallet', 'transaction'];
            const needsToken = ['ico', 'rugpull'];
            if (needsAddress.includes(analysisType) && !payload.address) {
                setError(`Wallet Address is required for ${formatResultTitle(analysisType)} analysis.`);
                setIsLoading(false);
                return;
            }
            if (needsToken.includes(analysisType) && !payload.token) {
                setError(`Token Address is required for ${formatResultTitle(analysisType)} analysis.`);
                setIsLoading(false);
                return;
            }
        }

        try {
            // Use the new API client
            const data = await sentinelApi.analyze(payload);
            console.log("Received response:", data);

            // Check for success flag from backend
            if (!data.success) {
                throw new Error(data.error || 'Analysis failed on the backend.');
            }

            setResults(data);

        } catch (err: any) {
            console.error("Analysis API call failed:", err);
            setError(err.message || 'Failed to fetch analysis results. Is the backend running?');
        } finally {
            setIsLoading(false);
        }
    };

    // Use API utility for report URL
    const getReportUrl = (filename: string) => {
        return sentinelApi.getReportFileUrl(filename);
    };

    // Base URL for report images served by the backend
    const reportBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

    return (
        <div className="space-y-6">
            {/* --- Form Section --- */}
            <form onSubmit={handleSubmit} className="space-y-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 shadow">
                {/* Analysis Type Dropdown */}
                <div>
                    <label htmlFor="analysis_type" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Analysis Type:</label>
                    <select
                        id="analysis_type"
                        value={analysisType}
                        onChange={(e) => setAnalysisType(e.target.value)}
                        required
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    >
                        <option value="ico">ICO Analysis</option>
                        <option value="rugpull">Rugpull Detection</option>
                        <option value="money_laundering">Money Laundering Detection</option>
                        <option value="mixer">Mixer Detection</option>
                        <option value="dusting">Address Poisoning Analysis</option>
                        <option value="wallet">Wallet Profiling</option>
                        <option value="transaction">Transaction Analysis</option>
                        <option value="all">All Analyses</option>
                    </select>
                </div>

                {/* Token Input (Conditional) */}
                {showTokenInput && (
                    <div>
                        <label htmlFor="token" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Token Address:</label>
                        <input
                            type="text"
                            id="token"
                            value={token}
                            onChange={(e) => setToken(e.target.value)}
                            placeholder="Solana token mint address (e.g., for ICO/Rugpull)"
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        />
                    </div>
                )}

                {/* Address Input (Conditional) */}
                {showAddressInput && (
                    <div>
                        <label htmlFor="address" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Wallet Address:</label>
                        <input
                            type="text"
                            id="address"
                            value={address}
                            onChange={(e) => setAddress(e.target.value)}
                            placeholder="Solana wallet address (e.g., for ML/Mixer/Dusting)"
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        />
                    </div>
                )}

                {/* Days Input */}
                <div>
                    <label htmlFor="days" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Analysis Timeframe (days):</label>
                    <input
                        type="number"
                        id="days"
                        value={days}
                        onChange={(e) => setDays(parseInt(e.target.value, 10))}
                        min="1"
                        max="365" // Example max
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    />
                </div>

                {/* Submit Button */}
                <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full px-4 py-2 bg-indigo-600 text-white font-medium rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isLoading ? 'Analyzing...' : 'Start Analysis'}
                </button>
            </form>

            {/* --- Loading Indicator --- */}
            {isLoading && (
                <div className="mt-6 text-center">
                    <p className="text-gray-600 dark:text-gray-400">Analyzing... Please wait.</p>
                    {/* Optional: Add a spinner */}
                </div>
            )}

            {/* --- Error Display --- */}
            {error && (
                <div className="mt-6 p-4 bg-red-100 dark:bg-red-900/50 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 rounded">
                    <p><span className="font-bold">Error:</span> {error}</p>
                </div>
            )}

            {/* --- Results Display Section --- */}
            {results && !isLoading && ( // Only show results when not loading
                <div className="mt-6 p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 shadow">
                    <h3 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-white">
                        Analysis Results for <code className="text-sm bg-gray-200 dark:bg-gray-600 p-1 rounded">{results.target}</code> ({results.target_type})
                    </h3>
                    {results.success ? (
                        <div className="space-y-4">
                            {/* Add Visualizations */}
                            <ReportVisualizations 
                                analysisResults={results}
                                className="mb-6"
                            />

                            {/* Original results display */}
                            {Object.entries(results.results).length > 0 ? (
                                Object.entries(results.results).map(([key, value]) => (
                                    <AnalysisDetail key={key} title={formatResultTitle(key)} data={value} reportBaseUrl={reportBaseUrl} />
                                ))
                            ) : (
                                <p className="text-gray-600 dark:text-gray-400">No specific results returned for this analysis type ({results.analysis_type}).</p>
                            )}
                            {/* Link to generated report file if path is available */}
                            {results.report_path && (
                                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                                    <a
                                        href={`/reports/${encodeURIComponent(results.report_path)}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-block px-4 py-2 bg-green-600 text-white font-medium rounded-md shadow-sm hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                                    >
                                        View Full Report
                                    </a>
                                </div>
                            )}
                        </div>
                    ) : (
                        // Display error from backend if success is false
                        <p className="text-orange-600 dark:text-orange-400">Analysis completed with issues: {results.error || 'Unknown issue occurred on the backend.'}</p>
                    )}
                </div>
            )}
        </div>
    );
}
