"use client";

import { useEffect } from 'react';
import { RefreshCw, Check, XCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useBackendConnection } from '@/hooks/useBackendConnection';

export default function ApiStatusWidget() {
  const { status, isChecking, checkConnection } = useBackendConnection();

  // Set up periodic status checks
  useEffect(() => {
    const interval = setInterval(() => {
      checkConnection();
    }, 60000); // Check every minute
    
    return () => clearInterval(interval);
  }, [checkConnection]);

  return (
    <Card className="bg-white dark:bg-gray-800">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">API Status</CardTitle>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => checkConnection()}
            disabled={isChecking}
            className="h-8 w-8 p-0"
          >
            <RefreshCw className={`h-4 w-4 ${isChecking ? 'animate-spin' : ''}`} />
            <span className="sr-only">Refresh</span>
          </Button>
        </div>
        <CardDescription className="text-sm text-gray-500 dark:text-gray-400">
          Python backend connection
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Connection:</span>
            <div className="flex items-center">
              {status.isConnected ? (
                <>
                  <Check className="mr-1 h-4 w-4 text-green-500" />
                  <span className="text-sm text-green-600 dark:text-green-400">Connected</span>
                </>
              ) : (
                <>
                  <XCircle className="mr-1 h-4 w-4 text-red-500" />
                  <span className="text-sm text-red-600 dark:text-red-400">Disconnected</span>
                </>
              )}
            </div>
          </div>
          
          {status.latency !== null && (
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Latency:</span>
              <span className="text-sm">
                {status.latency} ms
              </span>
            </div>
          )}
          
          {status.isConnected && status.backendVersion && (
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">API Version:</span>
              <span className="text-sm font-mono">
                {status.backendVersion}
              </span>
            </div>
          )}
          
          {status.lastChecked && (
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Last Check:</span>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {new Date(status.lastChecked).toLocaleTimeString()}
              </span>
            </div>
          )}
          
          {status.error && (
            <div className="mt-2 p-2 rounded-md bg-red-50 dark:bg-red-900/20 text-xs text-red-600 dark:text-red-400">
              {status.error}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
