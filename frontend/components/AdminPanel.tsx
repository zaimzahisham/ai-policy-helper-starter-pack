'use client';
import React from 'react';
import { apiIngest } from '@/lib/api';
import { useToast } from './ToastProvider';
import { useMetrics } from './MetricsProvider';
import { MetricsDisplay } from './MetricsDisplay';
import { Loader2, RefreshCw, Upload } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function AdminPanel() {
  const { metrics, refreshMetrics } = useMetrics();
  const [busy, setBusy] = React.useState(false);
  const [refreshing, setRefreshing] = React.useState(false);
  const { showToast } = useToast();

  const refresh = async () => {
    setRefreshing(true);
    try {
      await refreshMetrics();
    } catch (e: any) {
      showToast(`Failed to fetch metrics: ${e.message}`, 'error');
    } finally {
      setRefreshing(false);
    }
  };

  const ingest = async () => {
    setBusy(true);
    try {
      await apiIngest();
      await refreshMetrics(); // Refresh metrics after ingestion
      showToast('Documents ingested successfully', 'success');
    } catch (e: any) {
      showToast(`Ingestion failed: ${e.message}`, 'error');
    } finally {
      setBusy(false);
    }
  };

  // Metrics are now managed by MetricsProvider, no need to fetch on mount

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
      <h2 className="text-2xl font-semibold mb-4 text-foreground">Admin</h2>
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={ingest}
          disabled={busy}
          className={cn(
            'px-4 py-2 rounded-lg border border-border bg-background text-foreground hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2',
            busy && 'cursor-wait'
          )}
          aria-label="Ingest sample documents"
        >
          {busy ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Indexing...</span>
            </>
          ) : (
            <>
              <Upload className="h-4 w-4" />
              <span>Ingest sample docs</span>
            </>
          )}
        </button>
        <button
          onClick={refresh}
          disabled={refreshing}
          className="px-4 py-2 rounded-lg border border-border bg-background text-foreground hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          aria-label="Refresh metrics"
        >
          <RefreshCw
            className={cn('h-4 w-4', refreshing && 'animate-spin')}
          />
          <span>Refresh metrics</span>
        </button>
      </div>
      {metrics ? (
        <MetricsDisplay metrics={metrics} />
      ) : (
        <div className="text-center text-muted-foreground py-8">
          <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
          <p className="text-sm">Loading metrics...</p>
        </div>
      )}
    </div>
  );
}
