"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { MessageSquare } from "lucide-react";

type Session = {
  id: string;
  title: string | null;
  created_at: string;
  message_count: number;
};

export default function RecentPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void fetch("/api/proxy/ai-assistant/sessions", { credentials: "include" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Could not load recent conversations.");
        return response.json() as Promise<Session[]>;
      })
      .then((items) => { if (!cancelled) setSessions(items); })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "Could not load recent conversations.");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div><h1 className="text-3xl font-bold">Recent</h1><p className="mt-1 text-muted-foreground">Continue one of your AQAA conversations.</p></div>
      {loading && <p className="text-sm text-muted-foreground">Loading conversations…</p>}
      {error && <p className="text-sm text-destructive" role="alert">{error}</p>}
      {!loading && !error && sessions.length === 0 && <div className="rounded-xl border border-dashed p-8 text-center"><MessageSquare className="mx-auto mb-3 h-8 w-8 text-muted-foreground" /><p className="font-medium">No conversations yet</p><Link href="/workspace" className="mt-2 inline-block text-sm text-primary hover:underline">Start a new conversation</Link></div>}
      <div className="divide-y rounded-xl border bg-card">
        {sessions.map((session) => <Link key={session.id} href={`/workspace?session=${session.id}`} className="flex items-center gap-3 p-4 transition hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"><MessageSquare className="h-5 w-5 shrink-0 text-primary" /><span className="min-w-0 flex-1"><span className="block truncate font-medium">{session.title || "Untitled conversation"}</span><span className="text-xs text-muted-foreground">{session.message_count} messages · {new Date(session.created_at).toLocaleString()}</span></span></Link>)}
      </div>
    </div>
  );
}
