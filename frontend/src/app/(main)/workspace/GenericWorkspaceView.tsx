"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Brain,
  Sparkles,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

type PromptItem = { category: string; emoji: string; prompt: string };

const QA_OFFICER_PROMPTS: PromptItem[] = [
  { category: "Evidence",    emoji: "📂", prompt: "What evidence needs to be uploaded for this module?" },
  { category: "Audit",       emoji: "✅", prompt: "Summarize the key audit findings for my module" },
  { category: "Compliance",  emoji: "📋", prompt: "What is the compliance status of my modules?" },
  { category: "Findings",    emoji: "🔍", prompt: "Show me the most recent QA findings" },
];

const LECTURER_PROMPTS: PromptItem[] = [
  { category: "Evidence",    emoji: "📂", prompt: "What evidence do I need to upload for my modules?" },
  { category: "Audit",       emoji: "✅", prompt: "Summarize my module's audit findings this semester" },
  { category: "Compliance",  emoji: "📋", prompt: "What is the compliance status of my modules?" },
  { category: "Assessment",  emoji: "📝", prompt: "Explain the assessment policy for my level" },
];

function getPromptsForPersona(persona?: string | null): PromptItem[] {
  if (persona === "quality_assurance_officer") return QA_OFFICER_PROMPTS;
  if (persona === "lecturer") return LECTURER_PROMPTS;
  return QA_OFFICER_PROMPTS;
}

export function GenericWorkspaceView() {
  const router = useRouter();
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const prompts = getPromptsForPersona(user?.persona);

  const handleAsk = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    // Wave 2 will implement actual conversation routing
    // For Wave 1, just acknowledge the intent
  };

  const personaLabel = user?.persona === "quality_assurance_officer"
    ? "Quality Assurance Officer"
    : user?.persona === "lecturer"
    ? "Lecturer"
    : "User";

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div className="text-center space-y-3 pt-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/6 border border-primary/15 text-xs font-semibold text-primary">
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          AQAA Workspace
        </div>
        <h1 className="text-4xl font-bold tracking-tight text-foreground">
          What would you like to review?
        </h1>
        <p className="text-base text-muted-foreground max-w-xl mx-auto leading-relaxed">
          Ask AQAA about academic quality, evidence, compliance, and audits.
        </p>
      </div>

      {/* ── Composer ──────────────────────────────────────────────────────── */}
      <form onSubmit={handleAsk} className="max-w-2xl mx-auto">
        <div className="flex items-center gap-3 rounded-2xl border-2 border-border bg-card px-5 py-4 shadow-sm focus-within:border-primary/40 focus-within:shadow-lg focus-within:shadow-primary/5 transition-all duration-200">
          <Brain className="h-5 w-5 text-primary flex-shrink-0" aria-hidden="true" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask AQAA anything about academic quality…"
            className="flex-1 bg-transparent text-base text-foreground placeholder:text-muted-foreground/40 outline-none"
            aria-label="Ask AQAA"
          />
          <button
            type="submit"
            disabled={!query.trim()}
            aria-label="Submit"
            className={cn(
              "flex-shrink-0 flex items-center justify-center h-9 w-9 rounded-xl transition-all duration-150",
              query.trim()
                ? "bg-primary text-white hover:bg-primary/90 shadow-md shadow-primary/25"
                : "bg-muted text-muted-foreground/30 cursor-not-allowed"
            )}
          >
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </form>

      {/* ── Suggested prompts ──────────────────────────────────────────────── */}
      <div className="max-w-2xl mx-auto">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 text-center">
          Suggested for {personaLabel}
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {prompts.map((p) => (
            <button
              key={p.prompt}
              type="button"
              onClick={() => setQuery(p.prompt)}
              className="flex items-start gap-2.5 p-3 rounded-xl border border-border/60 bg-card/50 hover:bg-card hover:border-border hover:shadow-sm text-left transition-all group cursor-pointer"
            >
              <span className="text-base leading-none mt-0.5 flex-shrink-0" aria-hidden="true">
                {p.emoji}
              </span>
              <div className="min-w-0 flex-1">
                <span className="text-[10.5px] font-semibold text-primary uppercase tracking-wide block mb-0.5">
                  {p.category}
                </span>
                <p className="text-[12.5px] text-foreground/80 leading-snug line-clamp-2">
                  {p.prompt}
                </p>
              </div>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/30 group-hover:text-muted-foreground flex-shrink-0 mt-1 ml-auto transition-colors" aria-hidden="true" />
            </button>
          ))}
        </div>
      </div>

      {/* ── Empty state message ────────────────────────────────────────────── */}
      <div className="max-w-2xl mx-auto text-center">
        <p className="text-sm text-muted-foreground">
          Start a conversation to get personalized guidance on quality assurance, compliance, and evidence management.
        </p>
      </div>
    </div>
  );
}
