"use client";

import { useState, useEffect, useCallback } from 'react';

interface ConnectionStatus {
  isConnected: boolean;
  error: string | null;
  backendVersion?: string;
  latency: number | null;
  baseUrl: string;
  lastChecked: Date | null;
}

/**
 * Custom hook to check connection to the backend API
 */
export function useBackendConnection() {
  const [status, setStatus] = useState<ConnectionStatus>({
    isConnected: false,
    error: null,
    latency: null,
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
    lastChecked: null,
  });
  
  const [isChecking, setIsChecking] = useState(false);

  /**
   * Check connection to the backend using health endpoint
   */
  const checkConnection = useCallback(async () => {
    setIsChecking(true);
    
    try {
      const start = performance.now();
      const response = await fetch(`${status.baseUrl}/api/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(5000), // 5 second timeout
      });
      
      const end = performance.now();
      
      if (response.ok) {
        const data = await response.json();
        
        setStatus({
          isConnected: true,
          error: null,
          backendVersion: data.version || 'Unknown',
          latency: Math.round(end - start),
          baseUrl: status.baseUrl,
          lastChecked: new Date(),
        });
      } else {
        setStatus({
          isConnected: false,
          error: `API returned status: ${response.status} ${response.statusText}`,
          latency: Math.round(end - start),
          baseUrl: status.baseUrl,
          lastChecked: new Date(),
        });
      }
    } catch (error) {
      setStatus({
        isConnected: false,
        error: error instanceof Error ? error.message : 'Unknown connection error',
        latency: null,
        baseUrl: status.baseUrl,
        lastChecked: new Date(),
      });
    } finally {
      setIsChecking(false);
    }
  }, [status.baseUrl]);

  // Initial connection check on component mount
  useEffect(() => {
    checkConnection();
    // Set up automatic reconnection attempts if not connected
    const intervalId = setInterval(() => {
      if (!status.isConnected) {
        checkConnection();
      }
    }, 30000); // Try reconnecting every 30 seconds if disconnected
    
    return () => clearInterval(intervalId);
  }, [checkConnection, status.isConnected]);

  return { status, isChecking, checkConnection };
}
