"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Brain, Send, ArrowRight } from "lucide-react";

const SUGGESTED_PROMPTS = [
  "What are the top compliance risks this semester?",
  "Summarise CSC401 evidence status",
  "Which modules have missing moderation reports?",
  "How many audits were completed this quarter?",
];

export function MiniAIWidget() {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    router.push(`/ai-assistant?q=${encodeURIComponent(q)}`);
  };

  const handleSuggestedPrompt = (prompt: string) => {
    router.push(`/ai-assistant?q=${encodeURIComponent(prompt)}`);
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-xl border border-indigo-200 dark:border-indigo-800 bg-gradient-to-br from-indigo-50/60 to-purple-50/40 dark:from-indigo-950/30 dark:to-purple-950/20 p-5"
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center">
          <Brain className="h-4 w-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-semibold text-foreground">Ask AQAA AI</p>
          <p className="text-xs text-muted-foreground">Powered by your institution&apos;s knowledge base</p>
        </div>
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="mb-3">
        <div className="flex items-center gap-2 rounded-xl border border-border bg-background p-2 focus-within:ring-2 focus-within:ring-indigo-400/50 focus-within:border-indigo-400 transition-all">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a quality assurance question…"
            className="flex-1 min-w-0 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none px-1"
            aria-label="AI query input"
          />
          <motion.button
            whileTap={{ scale: 0.92 }}
            type="submit"
            disabled={!query.trim()}
            className="flex-shrink-0 h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
            aria-label="Submit query"
          >
            <Send className="h-3.5 w-3.5" />
          </motion.button>
        </div>
      </form>

      {/* Suggested prompts */}
      <div className="space-y-1.5">
        {SUGGESTED_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => handleSuggestedPrompt(prompt)}
            className="w-full text-left flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-muted-foreground hover:text-foreground hover:bg-white/60 dark:hover:bg-white/5 transition-colors"
          >
            <ArrowRight className="h-3 w-3 flex-shrink-0 text-indigo-400" />
            {prompt}
          </button>
        ))}
      </div>

      {/* CTA */}
      <button
        type="button"
        onClick={() => router.push("/ai-workspace")}
        className="mt-4 w-full flex items-center justify-center gap-2 py-2 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 transition-colors"
      >
        Open Full AI Workspace
        <ArrowRight className="h-4 w-4" />
      </button>
    </motion.section>
  );
}
