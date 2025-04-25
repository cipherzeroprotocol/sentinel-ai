"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, FileText, Search, ExternalLink } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { sentinelApi, RecentAnalysis } from "@/lib/apiClient";

interface Report {
  id: string;
  target: string;
  target_type: 'address' | 'token';
  analysis_type: string;
  risk_score?: number;
  timestamp: string;
  report_path?: string;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadReports() {
      setIsLoading(true);
      setError("");
      try {
        const response = await sentinelApi.getReports();
        setReports(response.reports || []);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load reports";
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    }

    loadReports();
  }, []);

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Reports</h1>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4">
        {isLoading ? (
          // Loading skeletons
          [...Array(3)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-6 w-1/3" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-2/3" />
              </CardContent>
            </Card>
          ))
        ) : reports.length === 0 ? (
          // No reports found
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <FileText className="h-16 w-16 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium mb-2">No Reports Found</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Start analyzing addresses or tokens to generate reports
              </p>
              <Button asChild>
                <a href="/analyze">Start Analysis</a>
              </Button>
            </CardContent>
          </Card>
        ) : (
          // Display reports
          reports.map((report) => (
            <Card key={report.id}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>{report.target_type === 'address' ? 'Address Analysis' : 'Token Analysis'}</span>
                  <span className="text-sm text-muted-foreground">
                    {new Date(report.timestamp).toLocaleDateString()}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <p className="font-medium mb-1">
                    {report.target_type === 'address' ? 'Address:' : 'Token:'}
                  </p>
                  <p className="text-sm font-mono bg-gray-100 dark:bg-gray-800 p-2 rounded">
                    {report.target}
                  </p>
                </div>
                
                <div className="mb-4">
                  <p className="font-medium mb-1">Analysis Type:</p>
                  <p className="text-sm">{report.analysis_type}</p>
                </div>
                
                {report.risk_score !== undefined && (
                  <div className="mb-4">
                    <p className="font-medium mb-1">Risk Score:</p>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                      <div 
                        className={`h-2.5 rounded-full ${
                          report.risk_score >= 80 ? 'bg-red-500' : 
                          report.risk_score >= 60 ? 'bg-orange-500' : 
                          report.risk_score >= 40 ? 'bg-yellow-500' : 
                          'bg-green-500'
                        }`}
                        style={{ width: `${report.risk_score}%` }}
                      ></div>
                    </div>
                    <p className="text-right text-sm mt-1">{report.risk_score}/100</p>
                  </div>
                )}
                
                <div className="flex space-x-3 mt-4">
                  {report.report_path && (
                    <Button variant="outline" asChild>
                      <a href={`/reports/${report.report_path}`} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        View Report
                      </a>
                    </Button>
                  )}
                  <Button variant="outline" asChild>
                    <a href={`/search?q=${report.target}`}>
                      <Search className="h-4 w-4 mr-2" />
                      Search Related
                    </a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
