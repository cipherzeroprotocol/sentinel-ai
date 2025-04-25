import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import RiskGauge from './visualizations/RiskGauge';
import TransactionFlow from './visualizations/TransactionFlow';
import DistributionChart from './visualizations/DistributionChart';
import RiskTable from './visualizations/RiskTable';
import ActivityTimeline from './visualizations/ActivityTimeline';
import { useVisualizationData } from '@/hooks/useVisualizationData';

interface ReportVisualizationsProps {
  analysisResults: any;
  showRiskGauge?: boolean;
  showTransactionFlow?: boolean;
  showDistribution?: boolean;
  showRiskTable?: boolean;
  showTimeline?: boolean;
  className?: string;
}

const ReportVisualizations: React.FC<ReportVisualizationsProps> = ({
  analysisResults,
  showRiskGauge = true,
  showTransactionFlow = true,
  showDistribution = true,
  showRiskTable = true,
  showTimeline = true,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  
  const {
    riskScore,
    riskFactors,
    transactionFlowData,
    distributionData,
    timelineEvents,
    loading,
    error
  } = useVisualizationData(analysisResults);

  // Show loading state
  if (loading) {
    return (
      <div className={`p-4 text-center ${className}`}>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto"></div>
        <p className="mt-2 text-gray-600 dark:text-gray-400">Loading visualizations...</p>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className={`p-4 border border-red-300 bg-red-50 dark:bg-red-900/20 dark:border-red-800 rounded-md ${className}`}>
        <p className="text-red-600 dark:text-red-400">Error: {error}</p>
      </div>
    );
  }

  // No data available
  if (!analysisResults?.results) {
    return null;
  }
  
  // Determine which visualizations to show
  const hasTransactions = transactionFlowData.transactions.length > 0;
  const hasDistribution = distributionData.length > 0;
  const hasRiskFactors = riskFactors.length > 0;
  const hasTimelineEvents = timelineEvents.length > 0;
  
  // Determine target type from analysis results
  const targetType = analysisResults.target_type || 'address';

  return (
    <div className={className}>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="border-b border-gray-200 dark:border-gray-700">
          <TabsList className="flex bg-transparent">
            <TabsTrigger value="overview" className="px-4 py-2 text-sm">Overview</TabsTrigger>
            {hasTransactions && showTransactionFlow && (
              <TabsTrigger value="transactions" className="px-4 py-2 text-sm">Transactions</TabsTrigger>
            )}
            {hasDistribution && showDistribution && (
              <TabsTrigger value="distribution" className="px-4 py-2 text-sm">Distribution</TabsTrigger>
            )}
            {hasRiskFactors && showRiskTable && (
              <TabsTrigger value="riskFactors" className="px-4 py-2 text-sm">Risk Factors</TabsTrigger>
            )}
            {hasTimelineEvents && showTimeline && (
              <TabsTrigger value="timeline" className="px-4 py-2 text-sm">Activity Timeline</TabsTrigger>
            )}
          </TabsList>
        </div>

        <div className="py-4">
          {/* Overview Tab */}
          <TabsContent value="overview" className="mt-0">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Risk Gauge */}
              {showRiskGauge && (
                <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 flex flex-col items-center">
                  <h3 className="text-lg font-medium mb-4">Overall Security Risk</h3>
                  <RiskGauge 
                    score={riskScore} 
                    size={180} 
                    label={`${targetType === 'address' ? 'Wallet' : 'Token'} Risk Score`}
                  />
                </div>
              )}

              {/* Summary Stats */}
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium mb-4">Analysis Summary</h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Target</p>
                    <p className="font-mono text-sm truncate">{analysisResults.target}</p>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Analysis Types</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {Object.keys(analysisResults.results).map(type => (
                        <span key={type} className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 rounded">
                          {type.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Risk Factors Identified</p>
                    <p className="font-medium">{riskFactors.length}</p>
                  </div>
                  
                  {hasTransactions && (
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Transactions Analyzed</p>
                      <p className="font-medium">{transactionFlowData.transactions.length}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Basic Transaction Flow Preview (if available) */}
              {hasTransactions && showTransactionFlow && (
                <div className="col-span-1 md:col-span-2 bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-medium mb-4">Transaction Flow Preview</h3>
                  <TransactionFlow 
                    transactions={transactionFlowData.transactions.slice(0, 20)} 
                    addresses={transactionFlowData.addresses}
                    height={250}
                    fitView={true}
                  />
                </div>
              )}
            </div>
          </TabsContent>

          {/* Transaction Flow Tab */}
          {hasTransactions && showTransactionFlow && (
            <TabsContent value="transactions" className="mt-0">
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium mb-4">Transaction Network Analysis</h3>
                <TransactionFlow 
                  transactions={transactionFlowData.transactions} 
                  addresses={transactionFlowData.addresses}
                  height={500}
                  fitView={true}
                  interactive={true}
                  title="Transaction Flow"
                />
              </div>
            </TabsContent>
          )}

          {/* Distribution Tab */}
          {hasDistribution && showDistribution && (
            <TabsContent value="distribution" className="mt-0">
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium mb-4">
                  {targetType === 'token' ? 'Token Distribution' : 'Transaction Distribution'}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <DistributionChart 
                    data={distributionData} 
                    height={400}
                    title="Holder Distribution"
                    showLegend={true}
                    interactive={true}
                  />
                  
                  {/* Additional chart could go here */}
                </div>
              </div>
            </TabsContent>
          )}

          {/* Risk Factors Tab */}
          {hasRiskFactors && showRiskTable && (
            <TabsContent value="riskFactors" className="mt-0">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                <RiskTable 
                  factors={riskFactors} 
                  title="Identified Risk Factors"
                  showSearch={true}
                  showPagination={true}
                  sortable={true}
                  expandable={true}
                />
              </div>
            </TabsContent>
          )}

          {/* Activity Timeline Tab */}
          {hasTimelineEvents && showTimeline && (
            <TabsContent value="timeline" className="mt-0">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                <ActivityTimeline 
                  events={timelineEvents}
                  title="Activity Timeline"
                  showFilters={true}
                  highlightSuspicious={true}
                  height={400}
                />
              </div>
            </TabsContent>
          )}
        </div>
      </Tabs>
    </div>
  );
};

export default ReportVisualizations;
