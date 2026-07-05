"use client";

import { motion } from "framer-motion";
import {
  FileSearch, ClipboardCheck, AlertTriangle, Database, Brain,
  Upload, FileBarChart2, CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ActivityEvent {
  id: string;
  time: string;
  label: string;
  detail?: string;
  type: "audit" | "risk" | "index" | "report" | "upload" | "analysis" | "success";
}

const TYPE_CONFIG = {
  audit:    { icon: ClipboardCheck, colour: "text-indigo-500",  bg: "bg-indigo-100 dark:bg-indigo-900/50" },
  risk:     { icon: AlertTriangle,  colour: "text-amber-500",   bg: "bg-amber-100 dark:bg-amber-900/50" },
  index:    { icon: Database,       colour: "text-blue-500",    bg: "bg-blue-100 dark:bg-blue-900/50" },
  report:   { icon: FileBarChart2,  colour: "text-purple-500",  bg: "bg-purple-100 dark:bg-purple-900/50" },
  upload:   { icon: Upload,         colour: "text-emerald-500", bg: "bg-emerald-100 dark:bg-emerald-900/50" },
  analysis: { icon: FileSearch,     colour: "text-slate-500",   bg: "bg-slate-100 dark:bg-slate-900/50" },
  success:  { icon: CheckCircle2,   colour: "text-emerald-500", bg: "bg-emerald-100 dark:bg-emerald-900/50" },
};

// Realistic mock activity for today
const ACTIVITY: ActivityEvent[] = [
  { id: "a1", time: "09:05", label: "AQAA analysed 138 module files",         detail: "CSC401, INF302, MEC301",                type: "analysis" },
  { id: "a2", time: "09:14", label: "Moderation report generated",             detail: "CSC401 — ICT Faculty",                  type: "report" },
  { id: "a3", time: "09:27", label: "Policy inconsistency detected",           detail: "Assessment criteria mismatch in EEE401", type: "risk" },
  { id: "a4", time: "09:40", label: "Evidence batch indexed",                  detail: "47 files added to Qdrant",              type: "index" },
  { id: "a5", time: "10:02", label: "Outcome alignment audit completed",       detail: "INF302 — score 91/100",                 type: "audit" },
  { id: "a6", time: "10:18", label: "Evidence upload processed",               detail: "MEC301 — 12 new documents",             type: "upload" },
  { id: "a7", time: "10:33", label: "Accreditation readiness audit triggered", detail: "EBIT Faculty, UP",                      type: "audit" },
  { id: "a8", time: "10:51", label: "Compliance report ready",                 detail: "Q2 2026 — Senate format",               type: "success" },
];

function TimelineEvent({ event, index, isLast }: { event: ActivityEvent; index: number; isLast: boolean }) {
  const cfg = TYPE_CONFIG[event.type];
  const Icon = cfg.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: index * 0.06, ease: [0.16, 1, 0.3, 1] }}
      className="relative flex gap-4 pb-5"
    >
      {/* Vertical connector */}
      {!isLast && (
        <div className="absolute left-[19px] top-9 bottom-0 w-px bg-border" />
      )}

      {/* Time */}
      <span className="flex-shrink-0 w-10 pt-1 text-[11px] font-mono font-medium text-muted-foreground text-right">
        {event.time}
      </span>

      {/* Icon node */}
      <div className={cn(
        "flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center border border-border z-10",
        cfg.bg
      )}>
        <Icon className={cn("h-3.5 w-3.5", cfg.colour)} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pt-0.5">
        <p className="text-sm font-medium text-foreground">{event.label}</p>
        {event.detail && (
          <p className="text-xs text-muted-foreground mt-0.5 truncate">{event.detail}</p>
        )}
      </div>
    </motion.div>
  );
}

export function RecentAIActivity() {
  return (
    <section className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
          <Brain className="h-4 w-4 text-indigo-500" />
          Recent AI Activity
        </h2>
        <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200 font-semibold dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800">
          Live
        </span>
      </div>

      <div>
        {ACTIVITY.map((event, i) => (
          <TimelineEvent
            key={event.id}
            event={event}
            index={i}
            isLast={i === ACTIVITY.length - 1}
          />
        ))}
      </div>
    </section>
  );
}
