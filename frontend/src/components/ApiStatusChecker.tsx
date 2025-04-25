import React from 'react';
import { useBackendConnection } from '@/hooks/useBackendConnection';
import { Button } from '@/components/ui/button';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

interface ApiStatusCheckerProps {
  className?: string;
}

/**
 * Component to check and display backend API connection status
 */
export function ApiStatusChecker({ className = '' }: ApiStatusCheckerProps) {
  const { status, isChecking, checkConnection } = useBackendConnection();
  
  return (
    <div className={`rounded-md border p-4 ${className}`}>
      <div className="flex flex-col space-y-3">
        <div className="flex justify-between items-center">
          <h3 className="font-medium">API Connection Status</h3>
          <Button
            size="sm"
            variant="outline"
            onClick={() => checkConnection()}
            disabled={isChecking}
          >
            {isChecking ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Checking...
              </>
            ) : (
              'Check Connection'
            )}
          </Button>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="font-semibold min-w-24">Status:</div>
          {status.isConnected ? (
            <div className="flex items-center text-green-600 dark:text-green-500">
              <CheckCircle className="mr-1 h-4 w-4" /> Connected
            </div>
          ) : (
            <div className="flex items-center text-red-600 dark:text-red-500">
              <AlertCircle className="mr-1 h-4 w-4" /> Not Connected
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="font-semibold min-w-24">API URL:</div>
          <div className="text-gray-700 dark:text-gray-300">{status.baseUrl}</div>
        </div>
        
        {status.latency !== null && (
          <div className="flex items-center space-x-2">
            <div className="font-semibold min-w-24">Latency:</div>
            <div className="text-gray-700 dark:text-gray-300">{status.latency}ms</div>
          </div>
        )}
        
        {status.error && (
          <div className="flex items-center space-x-2">
            <div className="font-semibold min-w-24">Error:</div>
            <div className="text-red-600 dark:text-red-500">{status.error}</div>
          </div>
        )}
        
        {status.lastChecked && (
          <div className="flex items-center space-x-2">
            <div className="font-semibold min-w-24">Last Checked:</div>
            <div className="text-gray-700 dark:text-gray-300">
              {status.lastChecked.toLocaleTimeString()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ApiStatusChecker;
