"use client";

import { lazy, Suspense, memo } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { GraduationCap, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { useFaculties } from "@/hooks/useFaculties";
import { useAuthStore } from "@/store/auth.store";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const AreaChart = lazy(() => import("recharts").then((m) => ({ default: m.AreaChart })));
const Area     = lazy(() => import("recharts").then((m) => ({ default: m.Area })));

interface FacultyCardData {
  id: string;
  name: string;
  code?: string;
  healthPct: number;
  modules: number;
  missingEvidence: number;
  openRisks: number;
  trend: number[]; // last 6 data points
}

// Generate deterministic mock data per faculty based on its index
function enrich(
  faculties: { id: string; name: string; code?: string; module_count?: number }[]
): FacultyCardData[] {
  const seeds = [87, 73, 91, 65, 82, 78, 69, 94];
  return faculties.slice(0, 8).map((f, i) => {
    const h = seeds[i % seeds.length];
    return {
      id: f.id,
      name: f.name,
      code: f.code,
      healthPct: h,
      modules: (f.module_count ?? 6) + (i * 2),
      missingEvidence: Math.max(0, 5 - i),
      openRisks: i % 3 === 0 ? 2 : i % 4 === 0 ? 3 : 1,
      trend: [
        h - 6, h - 3, h - 5, h - 1, h - 2, h,
      ],
    };
  });
}

const MiniSparkline = memo(function MiniSparkline({ data, colour }: { data: number[]; colour: string }) {
  const points = data.map((v, i) => ({ v }));
  return (
    <Suspense fallback={<div className="h-10 w-24 bg-muted rounded animate-pulse" />}>
      <AreaChart width={96} height={40} data={points}>
        <defs>
          <linearGradient id={`sg-${colour.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={colour} stopOpacity={0.3} />
            <stop offset="100%" stopColor={colour} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="v"
          stroke={colour}
          strokeWidth={2}
          fill={`url(#sg-${colour.replace("#", "")})`}
          dot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    </Suspense>
  );
});

function FacultyCard({ faculty, index }: { faculty: FacultyCardData; index: number }) {
  const pct = faculty.healthPct;
  const colour =
    pct >= 85 ? "#10b981" : pct >= 70 ? "#f59e0b" : "#ef4444";
  const sparkColour =
    pct >= 85 ? "#10b981" : pct >= 70 ? "#f59e0b" : "#ef4444";

  const trendDelta = faculty.trend[faculty.trend.length - 1] - faculty.trend[0];
  const TrendIcon = trendDelta > 2 ? TrendingUp : trendDelta < -2 ? TrendingDown : Minus;
  const trendColour =
    trendDelta > 2 ? "text-emerald-500" :
    trendDelta < -2 ? "text-red-500" :
    "text-muted-foreground";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.07, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -2 }}
    >
      <Link
        href="/faculties"
        className="block rounded-xl border border-border bg-card p-4 transition-shadow hover:shadow-md"
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="min-w-0">
            <p className="text-sm font-semibold text-foreground truncate">{faculty.name}</p>
            {faculty.code && (
              <p className="text-xs text-muted-foreground">{faculty.code}</p>
            )}
          </div>
          <span
            className="flex-shrink-0 text-lg font-bold tabular-nums"
            style={{ color: colour }}
          >
            {pct}%
          </span>
        </div>

        {/* Health bar */}
        <div className="h-1.5 rounded-full bg-muted mb-3 overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: colour }}
            initial={{ width: "0%" }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.9, delay: index * 0.07 + 0.2 }}
          />
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-2 text-center mb-3">
          <div>
            <p className="text-xs font-bold text-foreground">{faculty.modules}</p>
            <p className="text-[10px] text-muted-foreground">Modules</p>
          </div>
          <div>
            <p className={cn("text-xs font-bold", faculty.missingEvidence > 0 ? "text-amber-500" : "text-emerald-500")}>
              {faculty.missingEvidence}
            </p>
            <p className="text-[10px] text-muted-foreground">Missing</p>
          </div>
          <div>
            <p className={cn("text-xs font-bold", faculty.openRisks > 1 ? "text-red-500" : "text-foreground")}>
              {faculty.openRisks}
            </p>
            <p className="text-[10px] text-muted-foreground">Risks</p>
          </div>
        </div>

        {/* Sparkline + trend */}
        <div className="flex items-center justify-between">
          <MiniSparkline data={faculty.trend} colour={sparkColour} />
          <div className={cn("flex items-center gap-1 text-[11px] font-semibold", trendColour)}>
            <TrendIcon className="h-3.5 w-3.5" />
            {trendDelta > 0 ? "+" : ""}{trendDelta}%
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

export function FacultyOverview() {
  const user = useAuthStore((s) => s.user);
  const { data: faculties, isLoading } = useFaculties(
    user?.role === "system_admin" ? undefined : user?.institution_id ?? undefined
  );

  if (isLoading) {
    return (
      <section>
        <h2 className="text-base font-semibold text-foreground mb-4">Faculty Overview</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-52 rounded-xl" />
          ))}
        </div>
      </section>
    );
  }

  if (!faculties || faculties.length === 0) {
    return null;
  }

  const enriched = enrich(faculties);

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
          <GraduationCap className="h-4 w-4 text-muted-foreground" />
          Faculty Overview
        </h2>
        <Link href="/faculties" className="text-xs text-primary hover:underline font-medium">
          Manage →
        </Link>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {enriched.map((f, i) => (
          <FacultyCard key={f.id} faculty={f} index={i} />
        ))}
      </div>
    </section>
  );
}
