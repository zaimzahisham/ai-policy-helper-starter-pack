import React from 'react';
import { ToastProvider } from '@/contexts/ToastProvider';
import { MetricsProvider } from '@/contexts/MetricsProvider';
import './globals.css';

export const metadata = { title: 'AI Policy Helper' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ToastProvider>
          <MetricsProvider>
            <div className="max-w-4xl mx-auto px-6 py-8">
              {children}
            </div>
          </MetricsProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
