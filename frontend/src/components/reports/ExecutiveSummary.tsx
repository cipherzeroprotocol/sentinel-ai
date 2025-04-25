import React from 'react';
import { Card } from '@/components/ui/card';
import RiskGauge from '@/components/visualizations/RiskGauge';

import { cn } from '@/lib/utils';

interface ExecutiveSummaryProps {
  findings: string[];
  riskScore: number;
  target?: string;
  targetType?: string;
  analysisTypes: string[];
}

const ExecutiveSummary: React.FC<ExecutiveSummaryProps> = ({
  findings,
  riskScore,
  target,
  targetType,
  analysisTypes
}) => {
  const getRiskLevel = (score: number) => {
    if (score >= 80) return 'very-high';
    if (score >= 60) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
  };
  
  const riskLevel = getRiskLevel(riskScore);
  
  const shieldVariant = 
    riskLevel === 'very-high' ? 'destructive' :
    riskLevel === 'high' ? 'destructive' :
    riskLevel === 'medium' ? 'warning' :
    'success';
  
  return (
    <Card className="p-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk score gauge */}
        <div className="flex flex-col items-center justify-center">
          <h2 className="text-xl font-bold mb-4">Security Risk Score</h2>
          <div className={cn("mb-2", shieldVariant)}>
            <RiskGauge 
              score={riskScore} 
              size={180}
              label={`${targetType === 'token' ? 'Token' : 'Wallet'} Risk`} 
            />
          </div>
          <div className="text-center mt-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Analysis types: {analysisTypes.map(t => t.replace(/_/g, ' ')).join(', ')}
            </span>
          </div>
        </div>
        
        {/* Key findings */}
        <div className="lg:col-span-2">
          <h2 className="text-xl font-bold mb-4">Executive Summary</h2>
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <h3>Key Findings:</h3>
            <ul className="space-y-1">
              {findings.map((finding, index) => (
                <li key={index} className="text-gray-700 dark:text-gray-300">{finding}</li>
              ))}
            </ul>
          </div>
          
          {target && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Target:</h3>
              <p className="font-mono text-sm truncate">{target}</p>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

export default ExecutiveSummary;
