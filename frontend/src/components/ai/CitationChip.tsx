"use client";

import { useState, useRef } from "react";
import { ExternalLink, FileText, Building2, BookOpen, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Citation } from "@/lib/api/ai-assistant";

const ENTITY_ICONS: Record<string, React.ElementType> = {
  policy: BookOpen,
  document: FileText,
  module: FileText,
  programme: FileText,
  qualification: FileText,
  institution: Building2,
};

const ENTITY_COLORS: Record<string, string> = {
  policy: "bg-violet-500",
  document: "bg-blue-500",
  module: "bg-emerald-500",
  programme: "bg-indigo-500",
  qualification: "bg-amber-500",
  institution: "bg-rose-500",
};

function CitationTooltip({ citation }: { citation: Citation }) {
  const Icon = ENTITY_ICONS[citation.entity_type?.toLowerCase() ?? ""] ?? FileText;
  const dotColor = ENTITY_COLORS[citation.entity_type?.toLowerCase() ?? ""] ?? "bg-slate-500";
  const confidence = Math.round((citation.relevance_score ?? 0) * 100);

  return (
    <div className="w-72 rounded-xl border border-border bg-card shadow-xl shadow-black/10 p-3 text-left z-50">
      {/* Header */}
      <div className="flex items-start gap-2 mb-2">
        <div className={cn("w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0", dotColor)} />
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold text-foreground leading-tight line-clamp-2">
            {citation.title}
          </p>
          <span className="inline-block mt-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
            {citation.entity_type}
          </span>
        </div>
        <Icon className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0 mt-0.5" />
      </div>

      {/* Snippet */}
      {citation.snippet && (
        <p className="text-[11px] text-muted-foreground leading-relaxed border-l-2 border-border pl-2 mb-2 line-clamp-3">
          {citation.snippet}
        </p>
      )}

      {/* Metadata */}
      <div className="flex items-center justify-between pt-1.5 border-t border-border/60">
        <div className="flex items-center gap-1">
          <div className="h-1.5 w-16 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full bg-blue-500"
              style={{ width: `${confidence}%` }}
            />
          </div>
          <span className="text-[10px] text-muted-foreground">{confidence}% relevant</span>
        </div>
        {citation.source_document && (
          <button
            type="button"
            onClick={() => navigator.clipboard.writeText(citation.source_document)}
            className="text-[10px] text-blue-500 hover:text-blue-700 flex items-center gap-0.5 transition-colors"
          >
            <ExternalLink className="h-2.5 w-2.5" />
            Source
          </button>
        )}
      </div>
    </div>
  );
}

export function CitationChip({
  index,
  citation,
}: {
  index: number;
  citation?: Citation;
}) {
  const [visible, setVisible] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = () => {
    if (timer.current) clearTimeout(timer.current);
    setVisible(true);
  };
  const hide = () => {
    timer.current = setTimeout(() => setVisible(false), 120);
  };

  return (
    <span className="relative inline-block align-middle mx-0.5">
      <button
        type="button"
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        className="inline-flex items-center justify-center h-4 w-4 rounded-full bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 text-[9px] font-bold hover:bg-blue-200 dark:hover:bg-blue-900 transition-colors cursor-default"
        aria-label={`Citation ${index + 1}${citation ? `: ${citation.title}` : ""}`}
      >
        {index + 1}
      </button>
      {visible && citation && (
        <div
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 pointer-events-auto"
          onMouseEnter={show}
          onMouseLeave={hide}
        >
          <CitationTooltip citation={citation} />
        </div>
      )}
    </span>
  );
}

/** Parse [SOURCE:N] markers from assistant text and replace with CitationChip */
export function injectCitationChips(
  text: string,
  citations: Citation[],
): React.ReactNode[] {
  const parts = text.split(/(\[SOURCE:\d+\])/g);
  return parts.map((part, i) => {
    const match = part.match(/\[SOURCE:(\d+)\]/);
    if (match) {
      const idx = parseInt(match[1], 10) - 1;
      return (
        <CitationChip key={i} index={idx} citation={citations[idx]} />
      );
    }
    return part;
  });
}
