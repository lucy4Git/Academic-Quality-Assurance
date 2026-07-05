"use client";

import { lazy, Suspense } from "react";
import { motion } from "framer-motion";
import { ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

// Lazy-load Recharts to avoid SSR / bundle issues
const RadialBarChart = lazy(() =>
  import("recharts").then((m) => ({ default: m.RadialBarChart }))
);
const RadialBar = lazy(() =>
  import("recharts").then((m) => ({ default: m.RadialBar }))
);
const PolarAngleAxis = lazy(() =>
  import("recharts").then((m) => ({ default: m.PolarAngleAxis }))
);

interface HealthMetric {
  label: string;
  value: number;
  fill: string;
}

const METRICS: HealthMetric[] = [
  { label: "Overall",             value: 87, fill: "#6366f1" },
  { label: "Compliance",          value: 91, fill: "#10b981" },
  { label: "Evidence Complete",   value: 78, fill: "#3b82f6" },
  { label: "Assessment Quality",  value: 84, fill: "#8b5cf6" },
  { label: "Moderation Status",   value: 73, fill: "#f59e0b" },
];

function MetricBar({ metric, index }: { metric: HealthMetric; index: number }) {
  const colour =
    metric.value >= 85 ? "text-emerald-600" :
    metric.value >= 70 ? "text-amber-500" :
    "text-red-500";

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">{metric.label}</span>
        <span className={cn("text-xs font-bold tabular-nums", colour)}>{metric.value}%</span>
      </div>
      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: metric.fill }}
          initial={{ width: "0%" }}
          animate={{ width: `${metric.value}%` }}
          transition={{ duration: 1, delay: 0.2 + index * 0.1, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>
    </div>
  );
}

function RadialChart() {
  const data = METRICS.map((m) => ({ name: m.label, value: m.value, fill: m.fill }));

  return (
    <Suspense fallback={<div className="h-48 w-48 mx-auto flex items-center justify-center"><Skeleton className="h-48 w-48 rounded-full" /></div>}>
      <RadialBarChart
        width={200}
        height={200}
        cx={100}
        cy={100}
        innerRadius={30}
        outerRadius={95}
        data={data}
        startAngle={90}
        endAngle={-270}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
        <RadialBar
          dataKey="value"
          cornerRadius={4}
          background={{ fill: "var(--muted)" }}
        />
      </RadialBarChart>
    </Suspense>
  );
}

export function InstitutionHealth() {
  const overall = METRICS[0].value;
  const overallColour =
    overall >= 85 ? "text-emerald-600" :
    overall >= 70 ? "text-amber-500" :
    "text-red-500";

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-xl border border-border bg-card p-5"
    >
      <div className="flex items-center gap-2 mb-5">
        <ShieldCheck className="h-4 w-4 text-indigo-500" />
        <h2 className="text-base font-semibold text-foreground">Institution Health</h2>
      </div>

      <div className="flex flex-col items-center gap-6 sm:flex-row">
        {/* Radial chart */}
        <div className="flex-shrink-0 flex flex-col items-center gap-1">
          <RadialChart />
          <p className={cn("text-2xl font-bold tabular-nums -mt-2", overallColour)}>{overall}%</p>
          <p className="text-xs text-muted-foreground">Overall Score</p>
        </div>

        {/* Metric bars */}
        <div className="flex-1 w-full space-y-3">
          {METRICS.map((m, i) => (
            <MetricBar key={m.label} metric={m} index={i} />
          ))}
        </div>
      </div>
    </motion.section>
  );
}
