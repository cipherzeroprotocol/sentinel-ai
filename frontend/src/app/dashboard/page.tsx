"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { sentinelApi, RecentAnalysis, HighRiskEntity, ApiStatusResponse } from "@/lib/apiClient";

export default function DashboardPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [recentAnalyses, setRecentAnalyses] = useState<RecentAnalysis[]>([]);
  const [highRiskEntities, setHighRiskEntities] = useState<HighRiskEntity[]>([]);
  const [apiStatus, setApiStatus] = useState<ApiStatusResponse | null>(null);

  useEffect(() => {
    async function loadDashboardData() {
      setIsLoading(true);
      try {
        // Load data in parallel
        const [recentAnalysesData, highRiskEntitiesData, apiStatusData] = await Promise.all([
          sentinelApi.getRecentAnalyses(5).catch(() => [] as RecentAnalysis[]),
          sentinelApi.getHighRiskEntities(5).catch(() => [] as HighRiskEntity[]),
          sentinelApi.getApiStatus().catch(() => ({
            status: 'degraded',
            message: 'Unable to connect to status service.',
            services: {
              blockchain_api: 'unknown',
              analysis_engine: 'unknown',
              database: 'unknown'
            },
            last_updated: new Date().toISOString()
          } as ApiStatusResponse))
        ]);
        
        setRecentAnalyses(recentAnalysesData);
        setHighRiskEntities(highRiskEntitiesData);
        setApiStatus(apiStatusData);
      } catch (error) {
        console.error("Error loading dashboard data:", error);
      } finally {
        setIsLoading(false);
      }
    }
    
    loadDashboardData();
  }, []);

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">System Status</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-12 w-full" />
            ) : (
              <div className="flex items-center">
                <div
                  className={`w-4 h-4 rounded-full mr-2 ${
                    apiStatus?.status === 'operational' ? 'bg-green-500' : 
                    apiStatus?.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                />
                <span className="font-medium">
                  {apiStatus?.status === 'operational' ? 'System Operational' : 
                   apiStatus?.status === 'degraded' ? 'Partially Operational' : 'System Down'}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Recent Analyses</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-12 w-full" />
            ) : (
              <div className="text-3xl font-bold">
                {recentAnalyses.length}
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">High Risk Entities</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-12 w-full" />
            ) : (
              <div className="text-3xl font-bold">
                {highRiskEntities.length}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Analyses</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : recentAnalyses.length === 0 ? (
              <p className="text-muted-foreground text-center py-4">No recent analyses found</p>
            ) : (
              <ul className="space-y-3">
                {recentAnalyses.map((analysis) => (
                  <li key={analysis.id} className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <div className="font-medium">{analysis.target}</div>
                      <div className="text-sm text-muted-foreground">{analysis.analysis_type}</div>
                    </div>
                    <div className="text-sm">
                      {new Date(analysis.timestamp).toLocaleString()}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>High Risk Entities</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : highRiskEntities.length === 0 ? (
              <p className="text-muted-foreground text-center py-4">No high risk entities found</p>
            ) : (
              <ul className="space-y-3">
                {highRiskEntities.map((entity) => (
                  <li key={entity.id} className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <div className="font-medium">{entity.address}</div>
                      <div className="text-sm text-muted-foreground">{entity.category}</div>
                    </div>
                    <div className="text-sm">
                      Risk Score: <span className="font-medium">{entity.risk_score}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
