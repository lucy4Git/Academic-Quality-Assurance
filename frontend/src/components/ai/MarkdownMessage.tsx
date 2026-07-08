"use client";

/**
 * MarkdownMessage
 * Renders AI response text as rich markdown with:
 *  - react-markdown + remark-gfm (GFM tables, strikethrough, task lists)
 *  - [SOURCE:N] → CitationChip inline replacement
 *  - Code blocks with copy button
 *  - Premium typography matching Quantum Precision design system
 */

import { memo, useState, useMemo, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { CitationChip } from "@/components/ai/CitationChip";
import type { Citation } from "@/lib/api/ai-assistant";

// ── Code block with copy ──────────────────────────────────────────────────────

function CodeBlock({ children, language }: { children: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [children]);

  return (
    <div className="relative group rounded-xl border border-border bg-[#0f1117] my-3 overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/10">
        <span className="text-[10px] font-mono text-white/40 uppercase tracking-widest">
          {language || "code"}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1 text-white/40 hover:text-white/80 transition-colors text-[10px]"
          aria-label="Copy code"
        >
          {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="px-4 py-3 overflow-x-auto text-[12.5px] leading-relaxed text-white/90 font-mono">
        <code>{children}</code>
      </pre>
    </div>
  );
}

// ── Inline text with citation chip injection ───────────────────────────────────

function InlineWithCitations({
  text,
  citations,
}: {
  text: string;
  citations: Citation[];
}) {
  const parts = useMemo(() => {
    const segments = text.split(/(\[SOURCE:\d+\])/g);
    return segments.map((seg, i) => {
      const match = seg.match(/\[SOURCE:(\d+)\]/);
      if (match) {
        const idx = parseInt(match[1], 10) - 1;
        return <CitationChip key={i} index={idx} citation={citations[idx]} />;
      }
      return seg;
    });
  }, [text, citations]);

  return <>{parts}</>;
}

// ── Main component ────────────────────────────────────────────────────────────

interface MarkdownMessageProps {
  content: string;
  citations?: Citation[];
  isStreaming?: boolean;
  className?: string;
}

export const MarkdownMessage = memo(function MarkdownMessage({
  content,
  citations = [],
  isStreaming = false,
  className,
}: MarkdownMessageProps) {
  const hasCitations = citations.length > 0;

  return (
    <div
      className={cn(
        "prose prose-sm dark:prose-invert max-w-none",
        "prose-headings:font-semibold prose-headings:tracking-tight",
        "prose-h1:text-base prose-h2:text-sm prose-h3:text-sm",
        "prose-p:leading-relaxed prose-p:text-[13.5px]",
        "prose-li:text-[13.5px] prose-li:leading-relaxed",
        "prose-strong:font-semibold prose-strong:text-foreground",
        "prose-code:text-[12px] prose-code:font-mono",
        "prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md",
        "prose-code:before:content-none prose-code:after:content-none",
        "prose-blockquote:border-l-blue-500 prose-blockquote:text-muted-foreground",
        "prose-table:text-[12px]",
        "prose-th:bg-muted prose-th:font-semibold",
        "prose-td:py-1.5",
        "[&_table]:rounded-lg [&_table]:overflow-hidden [&_table]:border [&_table]:border-border",
        "[&_th]:px-3 [&_th]:py-2 [&_td]:px-3 [&_td]:border-t [&_td]:border-border",
        className,
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Code block — custom renderer
          code({ className: cls, children, ...props }) {
            const isBlock = cls?.startsWith("language-");
            if (isBlock) {
              const lang = cls?.replace("language-", "");
              return (
                <CodeBlock language={lang}>{String(children).replace(/\n$/, "")}</CodeBlock>
              );
            }
            return (
              <code className={cls} {...props}>
                {children}
              </code>
            );
          },

          // Inline text — inject citation chips
          p({ children }) {
            if (!hasCitations) return <p>{children}</p>;
            return (
              <p>
                {(Array.isArray(children) ? children : [children]).map((child, i) =>
                  typeof child === "string" ? (
                    <InlineWithCitations key={i} text={child} citations={citations} />
                  ) : (
                    child
                  ),
                )}
              </p>
            );
          },

          // Table — add scroll wrapper
          table({ children }) {
            return (
              <div className="overflow-x-auto my-3">
                <table>{children}</table>
              </div>
            );
          },

          // Links — open in new tab
          a({ href, children }) {
            return (
              <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">
                {children}
              </a>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>

      {/* Streaming cursor */}
      {isStreaming && (
        <span className="inline-block w-0.5 h-4 bg-blue-500 rounded-full ml-0.5 animate-pulse align-middle" />
      )}
    </div>
  );
});
