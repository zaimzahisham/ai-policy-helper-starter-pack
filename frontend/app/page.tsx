import Chat from '@/components/Chat';
import AdminPanel from '@/components/AdminPanel';

export default function Page() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold text-foreground">AI Policy & Product Helper</h1>
        <p className="text-muted-foreground">
          Local-first RAG starter. Ingest sample docs, ask questions, and see citations.
        </p>
      </div>
      <AdminPanel />
      <Chat />
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
        <h3 className="text-xl font-semibold mb-3 text-foreground">How to test</h3>
        <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
          <li>
            Click <strong className="text-foreground">Ingest sample docs</strong>.
          </li>
          <li>
            Ask: <em className="text-foreground">Can a customer return a damaged blender after 20 days?</em>
          </li>
          <li>
            Ask: <em className="text-foreground">What's the shipping SLA to East Malaysia for bulky items?</em>
          </li>
        </ol>
      </div>
    </div>
  );
}
