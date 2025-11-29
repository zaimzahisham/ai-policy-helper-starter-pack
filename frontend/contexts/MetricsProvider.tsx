'use client';
import React, { createContext, useContext, useState, useCallback } from 'react';
import { apiMetrics } from '@/lib/api/client';
import type { MetricsResponse } from '@/lib/types/api';

interface MetricsContextType {
  metrics: MetricsResponse | null;
  refreshMetrics: () => Promise<void>;
  updateMetrics: (newMetrics: Partial<MetricsResponse>) => void;
}

const MetricsContext = createContext<MetricsContextType | undefined>(undefined);

export function MetricsProvider({ children }: { children: React.ReactNode }) {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);

  const refreshMetrics = useCallback(async () => {
    try {
      const m = await apiMetrics();
      setMetrics(m);
    } catch (error) {
      // Silently fail - metrics refresh shouldn't break the app
      console.error('Failed to refresh metrics:', error);
    }
  }, []);

  const updateMetrics = useCallback((newMetrics: Partial<MetricsResponse>) => {
    setMetrics((prev) => {
      if (!prev) {
        // If metrics haven't been loaded yet, use the new metrics as initial state
        // (assuming newMetrics contains all required fields from AskResponse)
        if (newMetrics.ask_count !== undefined && newMetrics.total_docs !== undefined) {
          return newMetrics as MetricsResponse;
        }
        // Otherwise trigger a full refresh
        refreshMetrics();
        return null;
      }
      return { ...prev, ...newMetrics } as MetricsResponse;
    });
  }, [refreshMetrics]);

  // Initial fetch on mount
  React.useEffect(() => {
    refreshMetrics();
  }, [refreshMetrics]);

  return (
    <MetricsContext.Provider value={{ metrics, refreshMetrics, updateMetrics }}>
      {children}
    </MetricsContext.Provider>
  );
}

export function useMetrics() {
  const context = useContext(MetricsContext);
  if (context === undefined) {
    throw new Error('useMetrics must be used within a MetricsProvider');
  }
  return context;
}

