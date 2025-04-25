import { useState, useMemo } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge"; // Import Badge from UI library
import ExecutiveSummary from '@/components/reports/ExecutiveSummary';
import ReportVisualizations from '@/components/ReportVisualizations';
import RiskFactorsPanel from './RiskFactorsPanel'; // Update import path to be relative
import TransactionTable from './TransactionTable'; // Update import path to be relative


import { AlertTriangle, AlertCircle, Info, CheckCircle } from 'lucide-react'; // Remove Badge from here

interface DetailedReportViewProps {
  reportData: any;
}

const DetailedReportView = ({ reportData }: DetailedReportViewProps) => {
  const [activeTab, setActiveTab] = useState('summary');

  // Extract analysis types available in the report data
  const analysisTypes = useMemo(() => {
    if (!reportData?.results) return [];
    return Object.keys(reportData.results).filter(key => 
      reportData.results[key] && typeof reportData.results[key] === 'object'
    );
  }, [reportData]);

  // Extract overall risk score
  const overallRiskScore = useMemo(() => {
    if (!reportData?.results) return 0;
    
    const results = reportData.results;
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
    
    if (results.dusting?.risk_assessment?.risk_score) {
      totalScore += results.dusting.risk_assessment.risk_score;
      count++;
    }
    
    if (count > 0) {
      return Math.round(totalScore / count);
    }
    
    return 0;
  }, [reportData]);

  // Extract all risk factors
  const allRiskFactors = useMemo(() => {
    if (!reportData?.results) return [];
    
    const results = reportData.results;
    let factors: any[] = [];
    
    // Collect risk factors from different analysis types
    if (results.wallet?.risk_assessment?.high_risk_interactions) {
      results.wallet.risk_assessment.high_risk_interactions.forEach((item: string, index: number) => {
        factors.push({
          id: `wallet-risk-${index}`,
          name: `Suspicious Interaction ${index + 1}`,
          description: item,
          severity: 'medium',
          category: 'Wallet Interaction'
        });
      });
    }
    
    if (results.money_laundering?.risk_assessment?.factors) {
      results.money_laundering.risk_assessment.factors.forEach((item: any, index: number) => {
        factors.push({
          id: `ml-factor-${index}`,
          name: typeof item === 'string' ? item : `Money Laundering Pattern ${index + 1}`,
          description: typeof item === 'object' ? JSON.stringify(item) : item,
          severity: 'high',
          category: 'Money Laundering'
        });
      });
    }
    
    if (results.rugpull?.risk_factors) {
      results.rugpull.risk_factors.forEach((item: any, index: number) => {
        factors.push({
          id: `rugpull-factor-${index}`,
          name: typeof item === 'string' ? item : `Rugpull Warning ${index + 1}`,
          description: typeof item === 'object' ? JSON.stringify(item) : item,
          severity: 'critical',
          category: 'Rugpull'
        });
      });
    }
    
    if (results.dusting?.poisoning_attempts) {
      results.dusting.poisoning_attempts.forEach((item: any, index: number) => {
        factors.push({
          id: `dusting-attempt-${index}`,
          name: `Address Poisoning Attempt ${index + 1}`,
          description: item.description || 'Suspicious dusting transaction with possible address poisoning intent',
          severity: 'medium',
          category: 'Address Poisoning',
          evidence: {
            timestamp: item.timestamp,
            source: item.source_address,
            amount: item.amount
          }
        });
      });
    }
    
    return factors;
  }, [reportData]);

  // Extract key findings
  const keyFindings = useMemo(() => {
    const findings: string[] = [];
    
    // Target type and address information
    if (reportData?.target) {
      const targetType = reportData.target_type === 'address' ? 'Wallet' : 'Token';
      findings.push(`${targetType} address: ${reportData.target}`);
    }
    
    // Risk level based on overall score
    const riskLevel = overallRiskScore >= 80 ? 'Very High Risk' :
                     overallRiskScore >= 60 ? 'High Risk' :
                     overallRiskScore >= 40 ? 'Medium Risk' :
                     'Low Risk';
    
    findings.push(`Overall risk assessment: ${riskLevel} (${overallRiskScore}/100)`);
    
    // Risk factors count by severity
    const criticalFactors = allRiskFactors.filter(f => f.severity === 'critical').length;
    const highFactors = allRiskFactors.filter(f => f.severity === 'high').length;
    const mediumFactors = allRiskFactors.filter(f => f.severity === 'medium').length;
    
    if (criticalFactors > 0) {
      findings.push(`Detected ${criticalFactors} critical risk factors`);
    }
    if (highFactors > 0) {
      findings.push(`Detected ${highFactors} high risk factors`);
    }
    if (mediumFactors > 0) {
      findings.push(`Detected ${mediumFactors} medium risk factors`);
    }
    
    // Analysis-specific key findings
    const results = reportData.results || {};
    
    if (results.wallet?.classification?.primary_type) {
      findings.push(`Wallet type: ${results.wallet.classification.primary_type}`);
    }
    
    if (results.mixer?.is_known_mixer) {
      findings.push("Address matches known mixing service pattern");
    }
    
    if (results.money_laundering?.is_money_laundering) {
      findings.push("Strong indicators of money laundering activity detected");
    }
    
    if (results.rugpull?.is_rugpull) {
      findings.push("Token shows strong rugpull characteristics");
    } else if (results.rugpull) {
      findings.push(`Rugpull risk indicators: ${results.rugpull.risk_factors?.length || 0}`);
    }
    
    return findings;
  }, [reportData, overallRiskScore, allRiskFactors]);

  // Extract transactions from report data
  const transactions = useMemo(() => {
    const results = reportData?.results || {};
    let txs: any[] = [];
    
    // Try to find transactions in different analysis results
    if (results.transaction?.transaction_overview?.recent_transactions) {
      txs = results.transaction.transaction_overview.recent_transactions;
    } else if (results.wallet?.recent_transactions) {
      txs = results.wallet.recent_transactions;
    } else if (results.mixer?.transactions) {
      txs = results.mixer.transactions;
    }
    
    return txs;
  }, [reportData]);

  // Determine if we need to show the simple or advanced view
  const hasData = reportData?.results && Object.keys(reportData.results).length > 0;

  return (
    <div className="space-y-8">
      {/* Executive Summary */}
      <ExecutiveSummary 
        findings={keyFindings}
        riskScore={overallRiskScore}
        target={reportData?.target}
        targetType={reportData?.target_type}
        analysisTypes={analysisTypes}
      />

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="mb-6 flex flex-wrap overflow-x-auto">
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="visualizations">Visualizations</TabsTrigger>
          <TabsTrigger value="riskFactors">Risk Factors</TabsTrigger>
          {transactions.length > 0 && (
            <TabsTrigger value="transactions">Transactions</TabsTrigger>
          )}
          {analysisTypes.map(type => (
            <TabsTrigger key={type} value={type}>
              {type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, ' ')}
            </TabsTrigger>
          ))}
          <TabsTrigger value="rawData">Raw Data</TabsTrigger>
        </TabsList>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Analysis Overview</CardTitle>
              <CardDescription>
                Summary of security analysis findings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Analysis Details */}
                <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-medium mb-2">Analysis Details</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-gray-400">Analysis Types:</span>
                      <span className="font-medium">{analysisTypes.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-gray-400">Target:</span>
                      <span className="font-medium font-mono truncate max-w-[200px]">{reportData?.target}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-gray-400">Target Type:</span>
                      <span className="font-medium">{reportData?.target_type || 'Unknown'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-gray-400">Risk Factors:</span>
                      <span className="font-medium">{allRiskFactors.length}</span>
                    </div>
                  </div>
                </div>

                {/* Risk Breakdown */}
                <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-medium mb-2">Risk Breakdown</h3>
                  <div className="space-y-3">
                    <div className="flex items-center">
                      <AlertCircle className="h-4 w-4 text-red-500 mr-2" />
                      <span className="text-gray-700 dark:text-gray-300">Critical:</span>
                      <span className="ml-auto font-medium">{allRiskFactors.filter(f => f.severity === 'critical').length}</span>
                    </div>
                    <div className="flex items-center">
                      <AlertTriangle className="h-4 w-4 text-orange-500 mr-2" />
                      <span className="text-gray-700 dark:text-gray-300">High:</span>
                      <span className="ml-auto font-medium">{allRiskFactors.filter(f => f.severity === 'high').length}</span>
                    </div>
                    <div className="flex items-center">
                      <Info className="h-4 w-4 text-yellow-500 mr-2" />
                      <span className="text-gray-700 dark:text-gray-300">Medium:</span>
                      <span className="ml-auto font-medium">{allRiskFactors.filter(f => f.severity === 'medium').length}</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                      <span className="text-gray-700 dark:text-gray-300">Low:</span>
                      <span className="ml-auto font-medium">{allRiskFactors.filter(f => f.severity === 'low').length}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Key Findings */}
              <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium mb-2">Key Findings</h3>
                <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                  {keyFindings.map((finding, index) => (
                    <li key={index}>{finding}</li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Top Risk Factors */}
          {allRiskFactors.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Top Risk Factors</CardTitle>
                <CardDescription>
                  Most significant security concerns identified during analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {allRiskFactors
                    .sort((a, b) => {
                      const severityOrder: Record<string, number> = {
                        critical: 4,
                        high: 3,
                        medium: 2,
                        low: 1,
                        unknown: 0
                      };
                      return severityOrder[b.severity] - severityOrder[a.severity];
                    })
                    .slice(0, 5)
                    .map((factor, index) => {
                      const severityColor = 
                        factor.severity === 'critical' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                        factor.severity === 'high' ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400' :
                        factor.severity === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                        'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
                      
                      // Use the imported Badge component which accepts className
                      const severityBadgeVariant =
                        factor.severity === 'critical' ? 'destructive' :
                        factor.severity === 'high' ? 'warning' : // Assuming you have a 'warning' variant or adjust as needed
                        factor.severity === 'medium' ? 'secondary' :
                        'success'; // Assuming you have a 'success' variant or adjust as needed

                      return (
                        <div key={factor.id} className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <h4 className="font-medium text-gray-900 dark:text-white">{factor.name}</h4>
                            {/* Use the Badge component from the UI library */}
                            <Badge variant={severityBadgeVariant as any} className={severityColor}>
                              {factor.severity.charAt(0).toUpperCase() + factor.severity.slice(1)}
                            </Badge>
                            {factor.category && (
                              <Badge variant="outline">{factor.category}</Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{factor.description}</p>
                        </div>
                      );
                    })}
                </div>
                {allRiskFactors.length > 5 && (
                  <div className="mt-3 text-center">
                    <button 
                      onClick={() => setActiveTab('riskFactors')}
                      className="text-indigo-600 dark:text-indigo-400 hover:underline text-sm"
                    >
                      View all {allRiskFactors.length} risk factors
                    </button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Visualizations Tab */}
        <TabsContent value="visualizations">
          <Card>
            <CardHeader>
              <CardTitle>Interactive Visualizations</CardTitle>
              <CardDescription>
                Visual representation of analysis results
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ReportVisualizations 
                analysisResults={reportData}
                className="pt-4"
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Risk Factors Tab */}
        <TabsContent value="riskFactors">
          <Card>
            <CardHeader>
              <CardTitle>Risk Factors</CardTitle>
              <CardDescription>
                Detailed breakdown of identified security risks
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Use the imported RiskFactorsPanel component */}
              <RiskFactorsPanel factors={allRiskFactors} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Transactions Tab */}
        {transactions.length > 0 && (
          <TabsContent value="transactions">
            <Card>
              <CardHeader>
                <CardTitle>Transactions</CardTitle>
                <CardDescription>
                  Detailed transaction history and analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Use the imported TransactionTable component */}
                <TransactionTable transactions={transactions} />
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Analysis Type Specific Tabs */}
        {analysisTypes.map(type => (
          <TabsContent key={type} value={type}>
            <Card>
              <CardHeader>
                <CardTitle>{type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, ' ')} Analysis</CardTitle>
                <CardDescription>
                  Detailed {type.replace(/_/g, ' ')} analysis results
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {renderAnalysisTypeContent(type, reportData.results[type])}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        ))}

        {/* Raw Data Tab */}
        <TabsContent value="rawData">
          <Card>
            <CardHeader>
              <CardTitle>Raw Analysis Data</CardTitle>
              <CardDescription>
                Complete unformatted analysis results
              </CardDescription>
            </CardHeader>
            <CardContent>
              <pre className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700 overflow-x-auto text-sm">
                {JSON.stringify(reportData, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Helper function to render analysis type specific content
const renderAnalysisTypeContent = (type: string, data: any) => {
  if (!data) return <p>No data available for this analysis type.</p>;

  // Customize rendering based on analysis type
  switch (type) {
    case 'ico':
      return (
        <>
          {data.token_data && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium mb-2">Token Information</h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-gray-500 dark:text-gray-400">Name:</div>
                <div className="font-medium">{data.token_data.name}</div>
                <div className="text-gray-500 dark:text-gray-400">Symbol:</div>
                <div className="font-medium">{data.token_data.symbol}</div>
                <div className="text-gray-500 dark:text-gray-400">Supply:</div>
                <div className="font-medium">{data.token_data.supply?.toLocaleString()}</div>
                <div className="text-gray-500 dark:text-gray-400">Decimals:</div>
                <div className="font-medium">{data.token_data.decimals}</div>
                <div className="text-gray-500 dark:text-gray-400">Creator:</div>
                <div className="font-medium font-mono truncate">{data.token_data.creator}</div>
              </div>
            </div>
          )}

          {data.funding_flow && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium mb-2">Funding Information</h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-gray-500 dark:text-gray-400">Total Raised:</div>
                <div className="font-medium">${data.funding_flow.total_raised?.toLocaleString()}</div>
                <div className="text-gray-500 dark:text-gray-400">Investor Count:</div>
                <div className="font-medium">{data.funding_flow.investor_count}</div>
                <div className="text-gray-500 dark:text-gray-400">Distribution Fairness:</div>
                <div className="font-medium">{data.funding_flow.distribution_fairness_score}/10</div>
              </div>
            </div>
          )}

          {data.risk_assessment && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium mb-2">Risk Assessment</h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-gray-500 dark:text-gray-400">Risk Score:</div>
                <div className="font-medium">{data.risk_assessment.risk_score}/100</div>
                <div className="text-gray-500 dark:text-gray-400">Risk Level:</div>
                <div className="font-medium">{data.risk_assessment.risk_level}</div>
                <div className="text-gray-500 dark:text-gray-400">Confidence:</div>
                <div className="font-medium">{data.risk_assessment.confidence}/10</div>
              </div>
              {data.risk_assessment.risk_factors && (
                <div className="mt-2">
                  <div className="text-gray-500 dark:text-gray-400 mb-1">Risk Factors:</div>
                  <ul className="list-disc list-inside">
                    {data.risk_assessment.risk_factors.map((factor: string, index: number) => (
                      <li key={index} className="text-sm">{factor}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </>
      );

    case 'rugpull':
      return (
        <>
          {data.token_data && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium mb-2">Token Information</h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-gray-500 dark:text-gray-400">Name:</div>
                <div className="font-medium">{data.token_data.name}</div>
                <div className="text-gray-500 dark:text-gray-400">Symbol:</div>
                <div className="font-medium">{data.token_data.symbol}</div>
                <div className="text-gray-500 dark:text-gray-400">Mint:</div>
                <div className="font-medium font-mono truncate">{data.token_mint}</div>
              </div>
            </div>
          )}

          {data.holder_analysis && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium mb-2">Holder Analysis</h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-gray-500 dark:text-gray-400">Holder Count:</div>
                <div className="font-medium">{data.holder_analysis.holder_count}</div>
                <div className="text-gray-500 dark:text-gray-400">Top 10 Concentration:</div>
                <div className="font-medium">{data.holder_analysis.top_10_concentration}%</div>
              </div>
              {data.holder_analysis.top_holders && data.holder_analysis.top_holders.length > 0 && (
                <div className="mt-2">
                  <div className="text-gray-500 dark:text-gray-400 mb-1">Top Holders:</div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead>
                        <tr>
                          <th className="text-left px-2 py-1">Address</th>
                          <th className="text-right px-2 py-1">Percentage</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.holder_analysis.top_holders.slice(0, 5).map((holder: any, index: number) => (
                          <tr key={index}>
                            <td className="font-mono px-2 py-1 truncate max-w-[200px]">{holder.address}</td>
                            <td className="text-right px-2 py-1">{holder.percentage}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {data.liquidity_data && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium mb-2">Liquidity Analysis</h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-gray-500 dark:text-gray-400">Total Liquidity:</div>
                <div className="font-medium">${data.liquidity_data.total_liquidity_usd?.toLocaleString()}</div>
                <div className="text-gray-500 dark:text-gray-400">Liquidity/MCap Ratio:</div>
                <div className="font-medium">{data.liquidity_data.liquidity_to_mcap_ratio}</div>
                <div className="text-gray-500 dark:text-gray-400">Locked Percentage:</div>
                <div className="font-medium">{data.liquidity_data.locked_percentage}%</div>
                {data.liquidity_data.lock_expiration && (
                  <>
                    <div className="text-gray-500 dark:text-gray-400">Lock Expiration:</div>
                    <div className="font-medium">{new Date(data.liquidity_data.lock_expiration).toLocaleDateString()}</div>
                  </>
                )}
              </div>
            </div>
          )}

          <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium mb-2">Rugpull Risk</h3>
            <div className="grid grid-cols-2 gap-2">
              <div className="text-gray-500 dark:text-gray-400">Risk Score:</div>
              <div className="font-medium">{data.risk_score}/100</div>
              <div className="text-gray-500 dark:text-gray-400">Is Rugpull:</div>
              <div className="font-medium">{data.is_rugpull ? 'Yes' : 'No'}</div>
            </div>
            {data.risk_factors && data.risk_factors.length > 0 && (
              <div className="mt-2">
                <div className="text-gray-500 dark:text-gray-400 mb-1">Risk Factors:</div>
                <ul className="list-disc list-inside">
                  {data.risk_factors.map((factor: string, index: number) => (
                    <li key={index} className="text-sm">{factor}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </>
      );

    case 'money_laundering':
      return (
        <>
          {data.transaction_patterns && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium mb-2">Transaction Patterns</h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-gray-500 dark:text-gray-400">Layering Detected:</div>
                <div className="font-medium">{data.transaction_patterns.layering_detected ? 'Yes' : 'No'}</div>
                <div className="text-gray-500 dark:text-gray-400">Smurfing Detected:</div>
                <div className="font-medium">{data.transaction_patterns.smurfing_detected ? 'Yes' : 'No'}</div>
                <div className="text-gray-500 dark:text-gray-400">Round Trip Detected:</div>
                <div className="font-medium">{data.transaction_patterns.round_trip_detected ? 'Yes' : 'No'}</div>
              </div>
              {data.transaction_patterns.obfuscation_techniques && data.transaction_patterns.obfuscation_techniques.length > 0 && (
                <div className="mt-2">
                  <div className="text-gray-500 dark:text-gray-400 mb-1">Obfuscation Techniques:</div>
                  <ul className="list-disc list-inside">
                    {data.transaction_patterns.obfuscation_techniques.map((tech: string, index: number) => (
                      <li key={index} className="text-sm">{tech}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {data.mixer_interaction && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium mb-2">Mixer Interaction</h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-gray-500 dark:text-gray-400">Mixer Detected:</div>
                <div className="font-medium">{data.mixer_interaction.detected ? 'Yes' : 'No'}</div>
                {data.mixer_interaction.mixed_amount_usd && (
                  <>
                    <div className="text-gray-500 dark:text-gray-400">Mixed Amount:</div>
                    <div className="font-medium">${data.mixer_interaction.mixed_amount_usd.toLocaleString()}</div>
                  </>
                )}
              </div>
              {data.mixer_interaction.mixer_addresses && data.mixer_interaction.mixer_addresses.length > 0 && (
                <div className="mt-2">
                  <div className="text-gray-500 dark:text-gray-400 mb-1">Mixer Addresses:</div>
                  <ul className="list-disc list-inside">
                    {data.mixer_interaction.mixer_addresses.map((addr: string, index: number) => (
                      <li key={index} className="text-sm font-mono truncate">{addr}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {data.risk_assessment && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium mb-2">Risk Assessment</h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-gray-500 dark:text-gray-400">Risk Score:</div>
                <div className="font-medium">{data.risk_assessment.risk_score}/100</div>
                <div className="text-gray-500 dark:text-gray-400">Risk Level:</div>
                <div className="font-medium">{data.risk_assessment.risk_level}</div>
                <div className="text-gray-500 dark:text-gray-400">Confidence:</div>
                <div className="font-medium">{data.risk_assessment.confidence}/10</div>
                {data.risk_assessment.laundering_stage && (
                  <>
                    <div className="text-gray-500 dark:text-gray-400">Laundering Stage:</div>
                    <div className="font-medium">{data.risk_assessment.laundering_stage}</div>
                  </>
                )}
              </div>
            </div>
          )}
        </>
      );

    // Add more case blocks for other analysis types
    case 'mixer':
    case 'dusting':
    case 'wallet':
    case 'transaction':
      // Generic handler for other types
      return (
        <div className="space-y-4">
          {Object.entries(data).map(([key, value]: [string, any]) => {
            if (typeof value === 'object' && value !== null) {
              return (
                <div key={key} className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-medium mb-2">{key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</h3>
                  <pre className="text-sm overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(value, null, 2)}
                  </pre>
                </div>
              );
            }
            return null;
          })}
        </div>
      );
      
    default:
      return (
        <pre className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700 overflow-x-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      );
  }
};

export default DetailedReportView;
