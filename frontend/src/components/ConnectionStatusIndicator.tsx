"use client";

import { useEffect } from 'react';
import Link from 'next/link';
import { useBackendConnection } from '@/hooks/useBackendConnection';
import { RefreshCw, CheckCircle, XCircle } from 'lucide-react';

export default function ConnectionStatusIndicator({ className = "" }) {
  const { status, isChecking, checkConnection } = useBackendConnection();
  
  // Check connection status when component mounts
  useEffect(() => {
    checkConnection();
  }, [checkConnection]);
  
  return (
    <Link 
      href="/settings/api"
      className={`relative flex items-center space-x-1 rounded p-1 hover:bg-gray-100 dark:hover:bg-gray-800 ${className}`}
      title={status.isConnected ? `Connected (${status.latency}ms)` : 'Backend disconnected'}
    >
      {isChecking ? (
        <RefreshCw className="h-5 w-5 animate-spin text-blue-500" />
      ) : status.isConnected ? (
        <CheckCircle className="h-5 w-5 text-green-500" />
      ) : (
        <XCircle className="h-5 w-5 text-red-500" />
      )}
      <span className="text-xs font-medium">
        {isChecking ? (
          'Checking...'
        ) : status.isConnected ? (
          <span className="text-green-600 dark:text-green-500">Connected</span>
        ) : (
          <span className="text-red-600 dark:text-red-500">Disconnected</span>
        )}
      </span>
    </Link>
  );
}
