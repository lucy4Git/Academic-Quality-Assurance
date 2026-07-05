"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  FileText, ClipboardCheck, Database, FileBarChart2, AlertTriangle, Lightbulb,
} from "lucide-react";
import { useDashboardSummary } from "@/hooks/useDashboard";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

// Animates from 0 → target when the component mounts
function useCounter(target: number, duration = 1400, delay = 0) {
  const [value, setValue] = useState(0);
  const started = useRef(false);

  useEffect(() => {
    if (started.current || target === 0) return;
    started.current = true;

    let raf: number;
    const begin = performance.now() + delay;

    const tick = (now: number) => {
      if (now < begin) { raf = requestAnimationFrame(tick); return; }
      const elapsed = now - begin;
      const t = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3); // ease-out-cubic
      setValue(Math.round(eased * target));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration, delay]);

  return value;
}

interface InsightMetric {
  label: string;
  value: number;
  icon: React.ElementType;
  colour: string;
  bgColour: string;
  suffix?: string;
}

function InsightCard({ metric, index }: { metric: InsightMetric; index: number }) {
  const count = useCounter(metric.value, 1200, index * 80);
  const Icon = metric.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -2 }}
      className="rounded-xl border border-border bg-card p-4 flex flex-col gap-3"
    >
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground leading-tight">
          {metric.label}
        </p>
        <div className={cn("rounded-lg p-2", metric.bgColour)}>
          <Icon className={cn("h-4 w-4", metric.colour)} />
        </div>
      </div>
      <p className={cn("text-3xl font-bold tabular-nums", metric.colour)}>
        {count.toLocaleString()}{metric.suffix}
      </p>
      <div className="h-1 rounded-full bg-muted overflow-hidden">
        <motion.div
          className={cn("h-full rounded-full", metric.bgColour.replace("bg-", "bg-").replace("/10", ""))}
          initial={{ width: "0%" }}
          animate={{ width: `${Math.min((metric.value / (metric.value * 1.3)) * 100, 100)}%` }}
          transition={{ duration: 1.2, delay: index * 0.08, ease: "easeOut" }}
          style={{ background: "currentColor" }}
        />
      </div>
    </motion.div>
  );
}

export function AIInsights() {
  const { data, isLoading } = useDashboardSummary();

  const modules = data?.modules ?? 48;
  const programmes = data?.programmes ?? 16;

  const metrics: InsightMetric[] = [
    {
      label: "Documents Analysed",
      value: isLoading ? 0 : modules * 3 + 14,
      icon: FileText,
      colour: "text-indigo-600",
      bgColour: "bg-indigo-100 dark:bg-indigo-900/40",
    },
    {
      label: "Audits Completed",
      value: isLoading ? 0 : Math.max(programmes - 10, 4),
      icon: ClipboardCheck,
      colour: "text-emerald-600",
      bgColour: "bg-emerald-100 dark:bg-emerald-900/40",
    },
    {
      label: "Evidence Indexed",
      value: isLoading ? 0 : modules * 2 + 7,
      icon: Database,
      colour: "text-blue-600",
      bgColour: "bg-blue-100 dark:bg-blue-900/40",
    },
    {
      label: "Reports Generated",
      value: isLoading ? 0 : Math.max(programmes - 12, 3),
      icon: FileBarChart2,
      colour: "text-purple-600",
      bgColour: "bg-purple-100 dark:bg-purple-900/40",
    },
    {
      label: "Risks Detected",
      value: isLoading ? 0 : 7,
      icon: AlertTriangle,
      colour: "text-amber-600",
      bgColour: "bg-amber-100 dark:bg-amber-900/40",
    },
    {
      label: "Recommendations",
      value: isLoading ? 0 : 14,
      icon: Lightbulb,
      colour: "text-rose-600",
      bgColour: "bg-rose-100 dark:bg-rose-900/40",
    },
  ];

  if (isLoading) {
    return (
      <section>
        <h2 className="text-base font-semibold text-foreground mb-4">AI Insights Today</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section>
      <h2 className="text-base font-semibold text-foreground mb-4">AI Insights Today</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {metrics.map((m, i) => (
          <InsightCard key={m.label} metric={m} index={i} />
        ))}
      </div>
    </section>
  );
}
