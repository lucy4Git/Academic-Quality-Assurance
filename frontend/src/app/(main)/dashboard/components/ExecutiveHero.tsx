"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Brain, Upload, Play, FileBarChart2, Sparkles } from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import { useInstitutions } from "@/hooks/useInstitutions";
import { useRole } from "@/hooks/useRole";
import { ROLE_LABELS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/types";

// ── Animated circular health score ──────────────────────────────────────────

const RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function HealthRing({ score }: { score: number }) {
  const [animated, setAnimated] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 300);
    return () => clearTimeout(t);
  }, []);

  const dashOffset = animated
    ? CIRCUMFERENCE - (score / 100) * CIRCUMFERENCE
    : CIRCUMFERENCE;

  const colour =
    score >= 80 ? "#10b981" : score >= 60 ? "#f59e0b" : "#ef4444";

  return (
    <div className="relative flex items-center justify-center">
      <svg viewBox="0 0 120 120" className="h-36 w-36 -rotate-90">
        {/* Track */}
        <circle
          cx="60" cy="60" r={RADIUS}
          fill="none" stroke="currentColor" strokeWidth="8"
          className="text-muted/30"
        />
        {/* Progress */}
        <circle
          cx="60" cy="60" r={RADIUS}
          fill="none"
          stroke={colour}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={dashOffset}
          style={{ transition: "stroke-dashoffset 1.4s cubic-bezier(0.16,1,0.3,1)" }}
        />
      </svg>
      {/* Score label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center rotate-0">
        <span className="text-2xl font-bold tabular-nums" style={{ color: colour }}>
          {score}
        </span>
        <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider">
          Health
        </span>
      </div>
    </div>
  );
}

// ── Action button ────────────────────────────────────────────────────────────

interface ActionButtonProps {
  label: string;
  icon: React.ElementType;
  href: string;
  primary?: boolean;
}

function ActionButton({ label, icon: Icon, href, primary }: ActionButtonProps) {
  const router = useRouter();
  return (
    <motion.button
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      onClick={() => router.push(href)}
      className={cn(
        "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-colors",
        primary
          ? "bg-indigo-600 text-white hover:bg-indigo-700 shadow-md shadow-indigo-500/20"
          : "bg-card border border-border text-foreground hover:bg-muted"
      )}
    >
      <Icon className="h-4 w-4 flex-shrink-0" />
      {label}
    </motion.button>
  );
}

// ── Main component ───────────────────────────────────────────────────────────

interface ExecutiveHeroProps {
  healthScore: number;
  aiSummary: string;
}

export function ExecutiveHero({ healthScore, aiSummary }: ExecutiveHeroProps) {
  const user = useAuthStore((s) => s.user);
  const { data: institutions } = useInstitutions();
  const { isCoordinator, isLecturer } = useRole();

  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const firstName = user?.full_name?.split(" ")[0] ?? "there";
  const role = user?.role as UserRole | undefined;
  const userInstitution = institutions?.find((i) => i.id === user?.institution_id);
  const isSystemAdmin = role === "system_admin";

  const institutionLabel = isSystemAdmin
    ? "All Institutions"
    : userInstitution?.name ?? "AQAA Platform";

  const institutionCode = isSystemAdmin ? undefined : userInstitution?.code;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="relative overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-background via-background to-indigo-50/30 dark:to-indigo-950/20 p-6"
    >
      {/* Decorative blur blob */}
      <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-indigo-400/5 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-16 -left-8 h-48 w-48 rounded-full bg-purple-400/5 blur-3xl" />

      <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        {/* Left — greeting + meta */}
        <div className="flex-1 space-y-4">
          {/* Greeting */}
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="h-4 w-4 text-indigo-500" />
              <span className="text-xs font-semibold uppercase tracking-widest text-indigo-500">
                AI Executive Dashboard
              </span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              {greeting}, {firstName}
            </h1>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <span className={cn(
                "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border",
                institutionCode === "TUT"
                  ? "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800"
                  : institutionCode === "UP"
                  ? "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800"
                  : "bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950 dark:text-indigo-300 dark:border-indigo-800"
              )}>
                {institutionLabel}
              </span>
              {role && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-muted text-muted-foreground border border-border">
                  {ROLE_LABELS[role]}
                </span>
              )}
            </div>
          </div>

          {/* AI summary */}
          <div className="flex items-start gap-2.5 p-3 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900">
            <Brain className="h-4 w-4 text-indigo-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-foreground/80 leading-relaxed">{aiSummary}</p>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap gap-2">
            <ActionButton label="Ask AQAA" icon={Brain} href="/ai-assistant" primary />
            {isCoordinator && (
              <ActionButton label="Start Audit" icon={Play} href="/audits" />
            )}
            {isLecturer && (
              <ActionButton label="Upload Folder" icon={Upload} href="/files/upload" />
            )}
            {isCoordinator && (
              <ActionButton label="Generate Report" icon={FileBarChart2} href="/reports" />
            )}
          </div>
        </div>

        {/* Right — health ring */}
        <div className="flex flex-col items-center gap-2">
          <HealthRing score={healthScore} />
          <p className="text-xs text-muted-foreground font-medium">
            Institution Health Score
          </p>
        </div>
      </div>
    </motion.div>
  );
}
