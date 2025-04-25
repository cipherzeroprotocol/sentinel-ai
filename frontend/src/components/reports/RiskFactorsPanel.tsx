import React from 'react';
import { Badge } from "@/components/ui/badge"; // Import Badge

// Define a more specific type for factors based on usage in DetailedReportView
interface RiskFactor {
  id: string;
  name: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'unknown'; // Match severity levels
  category?: string;
  evidence?: any; // Include evidence if needed
}

interface RiskFactorsPanelProps {
  factors: RiskFactor[]; // Use the specific RiskFactor type
}

const RiskFactorsPanel: React.FC<RiskFactorsPanelProps> = ({ factors }) => {
  // Modify to return only valid Badge variants: "default", "destructive", "outline", "secondary"
  const getSeverityVariant = (severity: RiskFactor['severity']): "default" | "destructive" | "outline" | "secondary" => {
    switch (severity) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive'; // Changed from 'warning' to 'destructive'
      case 'medium': return 'secondary';
      case 'low': return 'outline'; // Changed from 'success' to 'outline'
      default: return 'default';
    }
  };

  const getSeverityColor = (severity: RiskFactor['severity']): string => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      case 'high': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
      case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'low': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  // Sort factors by severity
  const sortedFactors = [...factors].sort((a, b) => {
    const severityOrder: Record<string, number> = { critical: 4, high: 3, medium: 2, low: 1, unknown: 0 };
    return (severityOrder[b.severity] ?? 0) - (severityOrder[a.severity] ?? 0);
  });

  return (
    <div className="risk-factors-panel space-y-4">
      {sortedFactors.length > 0 ? (
        sortedFactors.map((factor) => (
          <div key={factor.id} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 shadow-sm">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <h4 className="font-semibold text-base text-gray-900 dark:text-white flex-grow">{factor.name}</h4>
              <Badge
                variant={getSeverityVariant(factor.severity)}
                className={getSeverityColor(factor.severity)}
              >
                {factor.severity.charAt(0).toUpperCase() + factor.severity.slice(1)}
              </Badge>
              {factor.category && (
                <Badge variant="outline">{factor.category}</Badge>
              )}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{factor.description}</p>
            {factor.evidence && (
              <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded border border-gray-200 dark:border-gray-600">
                <h5 className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 uppercase">Evidence</h5>
                <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(factor.evidence, null, 2)}
                </pre>
              </div>
            )}
          </div>
        ))
      ) : (
        <p className="text-gray-500 dark:text-gray-400">No significant risk factors identified.</p>
      )}
    </div>
  );
};

export default RiskFactorsPanel;

// Note: If you want to use 'warning' and 'success' variants, you would need to extend
// the Badge component in your UI library to support these additional variants.
// The comment below can be removed since we're not adding these variants for now:
// /*
//   variants: {
//     variant: {
//       // ... existing variants
//       warning: "border-transparent bg-orange-500 text-white hover:bg-orange-500/80", // Example
//       success: "border-transparent bg-green-500 text-white hover:bg-green-500/80", // Example
//     },
//   },
// */
