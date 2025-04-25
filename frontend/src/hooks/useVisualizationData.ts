"use client";

import { useState, useEffect } from 'react';

// Interfaces for structured data
interface RiskFactor {
  id: string;
  category: string;
  title: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
  evidence?: string;
  recommendation?: string;
}

// Align Transaction interface with TransactionFlow component's expectation
interface Transaction {
  id: string;
  source: string;
  target: string;
  amount: number; // Ensure amount is always number
  timestamp: string; // Ensure timestamp is always string
  type?: string;
  isSuspicious?: boolean; // Add isSuspicious if used by TransactionFlow
}

interface Address {
  id: string;
  label?: string;
  type?: string;
  risk?: number;
}

interface DistributionData {
  label: string;
  value: number;
  color?: string;
}

interface TimelineEvent {
  id: string;
  title: string;
  date: string;
  description?: string;
  type: string;
  risk?: 'low' | 'medium' | 'high';
}

// Interface for the data structure expected by TransactionFlow component
interface TransactionFlowAddressMap {
  [key: string]: {
    address: string; // Use 'address' field as expected by TransactionFlow
    label?: string;
    type?: string;
    isSuspicious?: boolean;
    risk?: number;
  };
}

// Interface for the data structure expected by DistributionChart component
interface DistributionChartItem {
  name: string; // Changed from 'label'
  value: number;
  color?: string;
}

// Interface for the data structure expected by ActivityTimeline component
interface ActivityTimelineEvent {
  id: string;
  timestamp: string | Date; // Changed from 'date'
  type: string;
  title: string;
  description?: string;
  isSuspicious?: boolean;
  severity?: 'low' | 'medium' | 'high';
  amount?: number;
  relatedAddress?: string;
}

// Define the hook's return type using the component-specific types
interface VisualizationData {
  riskScore: number;
  riskFactors: RiskFactor[]; // Assuming RiskTable uses the hook's RiskFactor type
  transactionFlowData: {
    transactions: Transaction[]; // Use the updated Transaction type
    addresses: TransactionFlowAddressMap; // Use the map type
  };
  distributionData: DistributionChartItem[]; // Use the chart's item type
  timelineEvents: ActivityTimelineEvent[]; // Use the timeline's event type
  loading: boolean;
  error: string | null;
}

export function useVisualizationData(analysisResults: any): VisualizationData {
  const [data, setData] = useState<VisualizationData>({
    riskScore: 0,
    riskFactors: [],
    transactionFlowData: {
      transactions: [],
      addresses: {}, // Initialize as an empty object
    },
    distributionData: [],
    timelineEvents: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    if (!analysisResults) {
      setData(prev => ({ ...prev, loading: false }));
      return;
    }

    try {
      // Extract data from the analysis results
      const extractedData = extractVisualizationData(analysisResults);

      // --- Transformations to match component props ---

      // 1. Transform addresses for TransactionFlow
      const addressMap: TransactionFlowAddressMap = {};
      extractedData.transactionFlowData.addresses.forEach(addr => {
        addressMap[addr.id] = { // Use addr.id as the key
          address: addr.id, // Keep the address string itself
          label: addr.label,
          type: addr.type,
          isSuspicious: addr.risk ? addr.risk > 50 : false, // Example logic for isSuspicious
          risk: addr.risk
        };
      });

      // 2. Transactions are already extracted with amount as number (due to updated extractVisualizationData)
      const validatedTransactions = extractedData.transactionFlowData.transactions;

      // 3. Transform distribution data for DistributionChart
      const chartDistributionData: DistributionChartItem[] = extractedData.distributionData.map(item => ({
        name: item.label, // Map label to name
        value: item.value,
        color: item.color,
      }));

      // 4. Transform timeline events for ActivityTimeline
      const timelineComponentEvents: ActivityTimelineEvent[] = extractedData.timelineEvents.map(event => ({
        id: event.id,
        timestamp: event.date, // Map date to timestamp
        type: event.type,
        title: event.title,
        description: event.description,
        isSuspicious: event.risk === 'high' || event.risk === 'medium', // Example logic
        severity: event.risk,
        amount: undefined, // Add amount if available in hook's TimelineEvent
        relatedAddress: undefined, // Add relatedAddress if available
      }));

      setData({
        riskScore: extractedData.riskScore,
        riskFactors: extractedData.riskFactors,
        transactionFlowData: {
          transactions: validatedTransactions, // Pass directly now
          addresses: addressMap, // Use the transformed map
        },
        distributionData: chartDistributionData, // Use transformed data
        timelineEvents: timelineComponentEvents, // Use transformed data
        loading: false,
        error: null,
      });
    } catch (error) {
      console.error('Error processing visualization data:', error);
      setData(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to process visualization data'
      }));
    }
  }, [analysisResults]);

  return data;
}

// Helper function to extract visualization data from analysis results
function extractVisualizationData(analysisResults: any): {
  riskScore: number;
  riskFactors: RiskFactor[];
  transactionFlowData: {
    transactions: Transaction[]; // Returns the updated Transaction type
    addresses: Address[]; // Return array initially
  };
  distributionData: DistributionData[];
  timelineEvents: TimelineEvent[];
} {
  const results = analysisResults.results || {};

  // Extract risk score
  let riskScore = 0;
  const targetType = analysisResults.target_type || 'address';

  if (targetType === 'address') {
    // For addresses, check wallet analysis or money laundering scores
    if (results.wallet?.risk_score) {
      riskScore = Number(results.wallet.risk_score);
    } else if (results.money_laundering?.risk_score) {
      riskScore = Number(results.money_laundering.risk_score);
    }
  } else {
    // For tokens, check ico or rugpull scores
    if (results.rugpull?.risk_score) {
      riskScore = Number(results.rugpull.risk_score);
    } else if (results.ico?.risk_score) {
      riskScore = Number(results.ico.risk_score);
    }
  }

  // Extract risk factors from all analysis types
  const riskFactors: RiskFactor[] = [];
  Object.entries(results).forEach(([analysisType, analysisData]: [string, any]) => {
    // Skip if no data or not an object
    if (!analysisData || typeof analysisData !== 'object') return;

    // Extract risk factors specific to each analysis type
    if (analysisType === 'rugpull' && analysisData.risk_factors) {
      Object.entries(analysisData.risk_factors).forEach(([key, value]: [string, any]) => {
        if (value && typeof value === 'object') {
          riskFactors.push({
            id: `rugpull-${key}`,
            category: 'Rugpull',
            title: key.replace(/_/g, ' '),
            severity: getSeverityFromValue(value.score || 0),
            description: value.description || 'No description available',
            evidence: value.evidence || undefined,
            recommendation: value.recommendation || 'Monitor this risk factor closely'
          });
        }
      });
    } else if (analysisType === 'money_laundering' && analysisData.suspicious_patterns) {
      analysisData.suspicious_patterns.forEach((pattern: any, index: number) => {
        riskFactors.push({
          id: `ml-pattern-${index}`,
          category: 'Money Laundering',
          title: pattern.type || 'Suspicious Pattern',
          severity: getSeverityFromValue(pattern.confidence || 0),
          description: pattern.description || 'Suspicious transaction pattern detected',
          evidence: pattern.details || undefined
        });
      });
    } else if (analysisType === 'mixer' && analysisData.mixer_connections) {
      analysisData.mixer_connections.forEach((mixer: any, index: number) => {
        riskFactors.push({
          id: `mixer-${index}`,
          category: 'Mixer Usage',
          title: `Connection to ${mixer.mixer_name || 'Unknown Mixer'}`,
          severity: 'high',
          description: `Transactions connected to known mixer service`,
          evidence: `Transaction hashes: ${mixer.transactions?.join(', ')}`
        });
      });
    }
    // Add more analysis type specific extractors as needed
  });

  // Extract transaction flow data
  const transactionAddresses = new Set<string>();
  const transactions: Transaction[] = []; // Use the updated Transaction type

  // Process transactions from money laundering analysis
  if (results.money_laundering?.transactions) {
    results.money_laundering.transactions.forEach((tx: any) => {
      transactionAddresses.add(tx.from || '');
      transactionAddresses.add(tx.to || '');

      transactions.push({
        id: tx.hash || `tx-${transactions.length}`,
        source: tx.from || '',
        target: tx.to || '',
        amount: tx.amount ?? 0, // Ensure amount is number, default to 0
        timestamp: tx.timestamp || new Date(0).toISOString(), // Default to epoch if missing
        type: tx.type || 'transfer',
        isSuspicious: tx.is_suspicious ?? false // Add isSuspicious if available
      });
    });
  }

  // Process wallet profile transactions
  if (results.wallet?.transactions) {
    results.wallet.transactions.forEach((tx: any) => {
      transactionAddresses.add(tx.counterparty || '');

      transactions.push({
        id: tx.signature || `tx-${transactions.length}`,
        source: analysisResults.target,
        target: tx.counterparty || '',
        amount: tx.amount ?? 0, // Ensure amount is number, default to 0
        timestamp: tx.timestamp || new Date(0).toISOString(), // Default to epoch if missing
        type: tx.type || 'transfer',
        isSuspicious: tx.is_suspicious ?? false // Add isSuspicious if available
      });
    });
  }

  // Convert addresses set to array (initial extraction)
  const addressesArray: Address[] = Array.from(transactionAddresses).map(addr => ({
    id: addr,
    label: addr === analysisResults.target ? 'Target' : undefined,
    type: addr === analysisResults.target ? 'target' : 'external',
    risk: 0 // Default risk
  }));

  // Extract distribution data
  const distributionData: DistributionData[] = [];

  if (results.ico?.holder_distribution || results.rugpull?.holder_distribution) {
    const distribution = results.ico?.holder_distribution || results.rugpull?.holder_distribution;
    if (distribution && typeof distribution === 'object') {
      Object.entries(distribution).forEach(([key, value]: [string, any]) => {
        distributionData.push({
          label: key,
          value: Number(value) || 0,
          color: getColorForDistributionCategory(key)
        });
      });
    }
  }

  // Extract timeline events
  const timelineEvents: TimelineEvent[] = [];

  // Process ICO events
  if (results.ico?.key_events) {
    results.ico.key_events.forEach((event: any, index: number) => {
      timelineEvents.push({
        id: `ico-event-${index}`,
        title: event.title || 'ICO Event',
        date: event.date || '',
        description: event.description,
        type: 'ico',
        risk: event.risk ? getSeverityFromValue(event.risk) : undefined
      });
    });
  }

  // Process transaction timeline
  if (results.wallet?.timeline || results.money_laundering?.timeline) {
    const timeline = results.wallet?.timeline || results.money_laundering?.timeline;
    if (timeline && Array.isArray(timeline)) {
      timeline.forEach((event: any, index: number) => {
        timelineEvents.push({
          id: `timeline-${index}`,
          title: event.title || event.type || 'Transaction',
          date: event.date || event.timestamp || '',
          description: event.description,
          type: event.type || 'transaction',
          risk: event.risk ? getSeverityFromValue(event.risk) : undefined
        });
      });
    }
  }

  return {
    riskScore,
    riskFactors,
    transactionFlowData: { transactions, addresses: addressesArray }, // Return array here
    distributionData,
    timelineEvents
  };
}

// Helper functions
function getSeverityFromValue(value: number): 'low' | 'medium' | 'high' {
  if (value >= 0.7 || value >= 70) return 'high';
  if (value >= 0.4 || value >= 40) return 'medium';
  return 'low';
}

function getColorForDistributionCategory(category: string): string {
  const colorMap: Record<string, string> = {
    'top_holders': '#ff6384',
    'team_allocation': '#36a2eb',
    'liquidity': '#4bc0c0',
    'community': '#ffcd56',
    'marketing': '#9966ff',
    'reserves': '#c9cbcf',
  };

  // Try to match category with known keys
  for (const key of Object.keys(colorMap)) {
    if (category.toLowerCase().includes(key.toLowerCase())) {
      return colorMap[key];
    }
  }

  // Return a default color if no match
  return '#c9cbcf';
}

