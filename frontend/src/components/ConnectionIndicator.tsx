'use client';

import { useState } from 'react';
import { useBackendConnection } from '@/hooks/useBackendConnection';
import { CheckCircle, ServerCrash, Loader2 } from 'lucide-react';
import Link from 'next/link';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export default function ConnectionIndicator() {
  const { status, isChecking, checkConnection } = useBackendConnection();
  const [showTooltip, setShowTooltip] = useState(false);
  
  return (
    <TooltipProvider>
      <Tooltip open={showTooltip} onOpenChange={setShowTooltip}>
        <TooltipTrigger asChild>
          <button 
            className="flex items-center gap-1 p-1.5 rounded-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700"
            onClick={() => {
              checkConnection();
              setShowTooltip(true);
              setTimeout(() => setShowTooltip(false), 2000);
            }}
          >
            {isChecking ? (
              <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
            ) : status.isConnected ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <ServerCrash className="h-5 w-5 text-red-500" />
            )}
            <span className="text-xs font-medium">
              {isChecking 
                ? 'Checking...' 
                : status.isConnected 
                  ? 'API Connected' 
                  : 'API Disconnected'}
            </span>
          </button>
        </TooltipTrigger>
        <TooltipContent side="top">
          <div className="space-y-2 p-1">
            <p className="text-sm">
              {isChecking 
                ? 'Checking connection...' 
                : status.isConnected 
                  ? `Connected to ${status.baseUrl}` 
                  : `Connection failed: ${status.error || 'Unknown error'}`}
            </p>
            
            {status.isConnected && !isChecking && (
              <p className="text-xs text-gray-500">
                Latency: {status.latency}ms
                {status.backendVersion && ` • Version: ${status.backendVersion}`}
              </p>
            )}
            
            <p className="text-xs text-gray-500">
              Last checked: {status.lastChecked ? status.lastChecked.toLocaleTimeString() : 'Never'}
            </p>
            
            <div className="border-t border-gray-200 dark:border-gray-700 pt-1 mt-1">
              <Link 
                href="/settings/api" 
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                View API settings
              </Link>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
