'use client';

import { useState } from 'react';
import { useBackendConnection } from '@/hooks/useBackendConnection';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowDownUp, CheckCircle, ServerCrash, RefreshCw } from 'lucide-react';
import Link from 'next/link';

export default function ConnectionStatusWidget() {
  const { status, isChecking, checkConnection } = useBackendConnection();
  
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          Backend Connection
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-6 w-6" 
            onClick={() => checkConnection()}
            disabled={isChecking}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isChecking ? 'animate-spin' : ''}`} />
          </Button>
        </CardTitle>
        <CardDescription className="text-xs">
          Status of Python backend API server
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center">
            {isChecking ? (
              <ArrowDownUp className="h-5 w-5 mr-2 text-blue-500 animate-pulse" />
            ) : status.isConnected ? (
              <CheckCircle className="h-5 w-5 mr-2 text-green-500" />
            ) : (
              <ServerCrash className="h-5 w-5 mr-2 text-red-500" />
            )}
            <div>
              <div className="font-medium text-sm">
                {isChecking ? "Checking connection..." : 
                 status.isConnected ? "Connected" : "Not connected"}
              </div>
              <div className="text-xs text-muted-foreground">
                {status.isConnected 
                  ? `v${status.backendVersion || '1.0'} - ${status.latency}ms latency` 
                  : status.error || "Failed to connect to backend"}
              </div>
            </div>
          </div>
          
          <div className="text-xs text-muted-foreground">
            <span className="inline-block w-20">API URL:</span> 
            {status.baseUrl}
          </div>
          
          <div className="text-xs text-muted-foreground">
            <span className="inline-block w-20">Last checked:</span>
            {status.lastChecked ? status.lastChecked.toLocaleTimeString() : 'Never'}
          </div>
        </div>
      </CardContent>
      <CardFooter className="pt-1">
        <Link 
          href="/settings/api" 
          className="text-xs text-primary hover:underline"
        >
          View API settings
        </Link>
      </CardFooter>
    </Card>
  );
}
