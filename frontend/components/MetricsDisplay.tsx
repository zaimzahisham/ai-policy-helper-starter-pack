'use client';
import React from 'react';
import { FileText, Hash, MessageSquare, Database } from 'lucide-react';
import { cn } from '@/lib/utils';
import { MetricsResponse } from '@/lib/api';

interface MetricsDisplayProps {
  metrics: MetricsResponse;
}

export function MetricsDisplay({ metrics }: MetricsDisplayProps) {
  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  // Use backend field names directly (total_docs, total_chunks)
  // Note: ask_count and fallback_used are not in backend MetricsResponse
  const isFallback = false; // Not tracked by backend, default to Qdrant

  const metricCards = [
    {
      label: 'Indexed Documents',
      value: formatNumber(metrics.total_docs),
      icon: FileText,
      color: 'bg-blue-50 text-blue-700 border-blue-200',
    },
    {
      label: 'Chunks',
      value: formatNumber(metrics.total_chunks),
      icon: Hash,
      color: 'bg-purple-50 text-purple-700 border-purple-200',
    },
    {
      label: 'Questions Asked',
      value: 'N/A', // Not tracked by backend MetricsResponse
      icon: MessageSquare,
      color: 'bg-green-50 text-green-700 border-green-200',
    },
    {
      label: 'Vector Store',
      value: isFallback ? 'In-Memory (Fallback)' : 'Qdrant',
      icon: Database,
      color: isFallback
        ? 'bg-amber-50 text-amber-700 border-amber-200'
        : 'bg-indigo-50 text-indigo-700 border-indigo-200',
    },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {metricCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={cn(
                'flex items-center gap-3 p-4 rounded-lg border',
                card.color
              )}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium opacity-75">{card.label}</div>
                <div className="text-lg font-semibold truncate">{card.value}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Raw JSON in collapsible section for debugging */}
      <details className="mt-4">
        <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground transition-colors">
          View raw metrics (debug)
        </summary>
        <pre className="mt-2 p-4 bg-muted rounded-lg text-xs overflow-auto">
          {JSON.stringify(metrics, null, 2)}
        </pre>
      </details>
    </div>
  );
}

