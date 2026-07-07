"use client";
import Link from "next/link";
import { useAuthStore } from "@/store/auth.store";
import { useInstitutionKnowledgeLiveCounts } from "@/hooks/useInstitutionKnowledge";
import { BookText, FileText, Layers, FileSearch, Brain, BookOpen, FileBarChart } from "lucide-react";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const name = user?.full_name?.split(" ")[0] ?? "there";
  const { data: counts, isLoading } = useInstitutionKnowledgeLiveCounts(
    user?.institution_id ?? undefined
  );

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-8">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Good morning, {name}</h1>
        <p className="text-muted-foreground mt-1">Here is your institutional quality overview.</p>
      </div>

      {/* Live institutional knowledge counts */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border bg-card p-5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-muted-foreground">Modules</p>
            <Layers className="h-4 w-4 text-blue-500" />
          </div>
          <p className="text-3xl font-bold text-blue-600">
            {isLoading ? "—" : counts?.modules ?? 0}
          </p>
          <p className="text-xs mt-1">
            {isLoading ? (
              <span className="text-muted-foreground">Demo data</span>
            ) : (
              <span className="text-green-500">Live</span>
            )}
          </p>
        </div>
        <div className="rounded-xl border bg-card p-5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-muted-foreground">Policies</p>
            <BookText className="h-4 w-4 text-green-500" />
          </div>
          <p className="text-3xl font-bold text-green-600">
            {isLoading ? "—" : counts?.policies ?? 0}
          </p>
          <p className="text-xs mt-1">
            {isLoading ? (
              <span className="text-muted-foreground">Demo data</span>
            ) : (
              <span className="text-green-500">Live</span>
            )}
          </p>
        </div>
        <div className="rounded-xl border bg-card p-5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-muted-foreground">Documents</p>
            <FileText className="h-4 w-4 text-purple-500" />
          </div>
          <p className="text-3xl font-bold text-purple-600">
            {isLoading ? "—" : counts?.institution_documents ?? 0}
          </p>
          <p className="text-xs mt-1">
            {isLoading ? (
              <span className="text-muted-foreground">Demo data</span>
            ) : (
              <span className="text-green-500">Live</span>
            )}
          </p>
        </div>
      </div>

      {/* Quick actions */}
      <div>
        <h2 className="text-base font-semibold mb-3">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link href="/audits" className="inline-flex items-center gap-2 rounded-lg border bg-card px-4 py-2 text-sm font-medium hover:bg-accent transition-colors">
            <FileSearch className="h-4 w-4 text-primary" /> Run AI Audit
          </Link>
          <Link href="/knowledge-search" className="inline-flex items-center gap-2 rounded-lg border bg-card px-4 py-2 text-sm font-medium hover:bg-accent transition-colors">
            <BookOpen className="h-4 w-4 text-primary" /> Browse Knowledge
          </Link>
          <Link href="/reports" className="inline-flex items-center gap-2 rounded-lg border bg-card px-4 py-2 text-sm font-medium hover:bg-accent transition-colors">
            <FileBarChart className="h-4 w-4 text-primary" /> View Reports
          </Link>
          <Link href="/ai-workspace" className="inline-flex items-center gap-2 rounded-lg border bg-card px-4 py-2 text-sm font-medium hover:bg-accent transition-colors">
            <Brain className="h-4 w-4 text-primary" /> Ask AI
          </Link>
        </div>
      </div>
    </div>
  );
}
