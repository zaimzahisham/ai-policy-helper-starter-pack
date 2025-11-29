'use client';
import React from 'react';
import { apiAsk, MetricsResponse } from '@/lib/api';
import { useToast } from './ToastProvider';
import { useMetrics } from './MetricsProvider';
import { Loader2, Send, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  citations?: { title: string; section?: string }[];
  chunks?: { title: string; section?: string; text: string }[];
};

export default function Chat() {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [q, setQ] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [expandedChunks, setExpandedChunks] = React.useState<Set<number>>(new Set());
  const { showToast } = useToast();
  const { updateMetrics, refreshMetrics } = useMetrics();
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const send = async () => {
    if (!q.trim() || loading) return;
    const my: Message = { role: 'user', content: q };
    setMessages((m) => [...m, my]);
    setLoading(true);
    try {
      const res = await apiAsk(q);
      const ai: Message = {
        role: 'assistant',
        content: res.answer,
        citations: res.citations,
        chunks: res.chunks,
      };
      setMessages((m) => [...m, ai]);
      
      // Update metrics from the ask response (includes full MetricsResponse fields)
      if (res.metrics && res.metrics.ask_count !== undefined) {
        // res.metrics contains all MetricsResponse fields (from backend)
        updateMetrics(res.metrics as Partial<MetricsResponse>);
      }
      
      showToast('Answer generated successfully', 'success');
    } catch (e: any) {
      const errorMsg = e.message || 'Failed to get answer';
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${errorMsg}`,
      };
      setMessages((m) => [...m, errorMessage]);
      showToast(errorMsg, 'error');
    } finally {
      setLoading(false);
      setQ('');
    }
  };

  const toggleChunks = (index: number) => {
    setExpandedChunks((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
      <h2 className="text-2xl font-semibold mb-4 text-foreground">Chat</h2>
      <div
        className="max-h-96 overflow-y-auto p-4 border border-border rounded-lg mb-4 bg-muted/30 space-y-4"
        style={{ scrollbarWidth: 'thin' }}
      >
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground py-8">
            <p className="text-sm">Start a conversation by asking a question</p>
            <p className="text-xs mt-2 opacity-75">
              Try: "Can a customer return a damaged blender after 20 days?"
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={cn(
              'flex gap-3',
              m.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={cn(
                'max-w-[80%] rounded-lg p-3',
                m.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-background border border-border'
              )}
            >
              <div className="text-xs font-medium mb-1 opacity-75">
                {m.role === 'user' ? 'You' : 'Assistant'}
              </div>
              <div className="text-sm whitespace-pre-wrap">{m.content}</div>
              {m.citations && m.citations.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {m.citations.map((c, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 bg-accent text-accent-foreground px-2.5 py-1 rounded-full text-xs font-medium border border-border"
                      title={c.section || c.title}
                    >
                      <FileText className="h-3 w-3" />
                      {c.title}
                      {c.section && (
                        <span className="opacity-75">— {c.section}</span>
                      )}
                    </span>
                  ))}
                </div>
              )}
              {m.chunks && m.chunks.length > 0 && (
                <div className="mt-3">
                  <button
                    onClick={() => toggleChunks(i)}
                    className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                    aria-expanded={expandedChunks.has(i)}
                  >
                    {expandedChunks.has(i) ? (
                      <>
                        <ChevronUp className="h-3 w-3" />
                        Hide supporting chunks
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-3 w-3" />
                        View supporting chunks ({m.chunks.length})
                      </>
                    )}
                  </button>
                  {expandedChunks.has(i) && (
                    <div className="mt-2 space-y-2">
                      {m.chunks.map((c, idx) => (
                        <div
                          key={idx}
                          className="bg-muted p-3 rounded-lg border border-border"
                        >
                          <div className="font-semibold text-sm mb-1 text-foreground">
                            {c.title}
                            {c.section && (
                              <span className="text-muted-foreground font-normal">
                                {' — '}
                                {c.section}
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground whitespace-pre-wrap">
                            {c.text}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="bg-background border border-border rounded-lg p-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="flex gap-2">
        <input
          placeholder="Ask about policy or products..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          disabled={loading}
          className="flex-1 px-4 py-2 border border-input rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Question input"
        />
        <button
          onClick={send}
          disabled={loading || !q.trim()}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          aria-label="Send message"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="hidden sm:inline">Sending...</span>
            </>
          ) : (
            <>
              <Send className="h-4 w-4" />
              <span className="hidden sm:inline">Send</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
