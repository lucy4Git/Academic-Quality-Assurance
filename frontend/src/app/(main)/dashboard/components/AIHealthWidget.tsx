"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Brain,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Settings,
  RefreshCw,
} from "lucide-react";
import { useProviderStatus, useProviderHealth } from "@/hooks/useProviderHealth";
import type { ProviderHealthEntry } from "@/lib/api/providers";

const STATUS_CONFIG: Record<
  string,
  { label: string; color: string; icon: typeof CheckCircle2 }
> = {
  ok: { label: "Operational", color: "text-emerald-600", icon: CheckCircle2 },
  error: { label: "Error", color: "text-red-500", icon: XCircle },
  not_configured: { label: "Not Configured", color: "text-muted-foreground", icon: AlertTriangle },
  not_implemented: { label: "Scaffolded", color: "text-amber-500", icon: AlertTriangle },
  unavailable: { label: "Unavailable", color: "text-red-500", icon: XCircle },
};

function ProviderRow({
  name,
  entry,
  isActive,
}: {
  name: string;
  entry: ProviderHealthEntry;
  isActive: boolean;
}) {
  const cfg = STATUS_CONFIG[entry.status] ?? STATUS_CONFIG["not_configured"];
  const Icon = cfg.icon;
  const latency = entry.latency_ms > 0 ? `${Math.round(entry.latency_ms)}ms` : "—";

  return (
    <div className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
      <div className="flex items-center gap-2 min-w-0">
        <Icon className={`h-3.5 w-3.5 flex-shrink-0 ${cfg.color}`} />
        <span className="text-sm font-medium capitalize truncate">{name}</span>
        {isActive && (
          <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300 flex-shrink-0">
            ACTIVE
          </span>
        )}
      </div>
      <div className="flex items-center gap-2 flex-shrink-0 ml-2">
        <span className={`text-xs ${cfg.color}`}>{cfg.label}</span>
        <span className="text-xs text-muted-foreground w-10 text-right">{latency}</span>
      </div>
    </div>
  );
}

export function AIHealthWidget() {
  const router = useRouter();
  const { data: status, isLoading: statusLoading } = useProviderStatus();
  const {
    data: health,
    isLoading: healthLoading,
    refetch,
    isFetching,
  } = useProviderHealth();

  const isLoading = statusLoading || healthLoading;
  const overall = health?.overall ?? "degraded";
  const isHealthy = overall === "healthy";

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-xl border border-border bg-card p-5"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div
            className={`h-8 w-8 rounded-full flex items-center justify-center ${
              isHealthy ? "bg-emerald-100 dark:bg-emerald-900/30" : "bg-amber-100 dark:bg-amber-900/30"
            }`}
          >
            <Brain
              className={`h-4 w-4 ${isHealthy ? "text-emerald-600" : "text-amber-600"}`}
            />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">AI Provider Health</p>
            <p className="text-xs text-muted-foreground capitalize">
              {isLoading ? "Checking…" : overall}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-1.5 rounded-lg hover:bg-muted transition-colors disabled:opacity-40"
            aria-label="Refresh health check"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 text-muted-foreground ${isFetching ? "animate-spin" : ""}`}
            />
          </button>
          <button
            type="button"
            onClick={() => router.push("/settings/ai-providers")}
            className="p-1.5 rounded-lg hover:bg-muted transition-colors"
            aria-label="AI provider settings"
          >
            <Settings className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
        </div>
      </div>

      {/* Active provider summary */}
      {status && !statusLoading && (
        <div className="mb-3 px-3 py-2 rounded-lg bg-muted/50 text-xs space-y-0.5">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Active provider</span>
            <span className="font-semibold capitalize">{status.active_provider}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Model</span>
            <span className="font-mono text-[11px]">{status.active_model}</span>
          </div>
          {status.fallback_chain.length > 0 && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Fallback</span>
              <span className="capitalize">{status.fallback_chain.join(" → ")}</span>
            </div>
          )}
        </div>
      )}

      {/* Provider list */}
      <div>
        {isLoading && (
          <div className="py-4 text-center text-sm text-muted-foreground">
            Checking providers…
          </div>
        )}
        {health &&
          Object.entries(health.providers).map(([name, entry]) => (
            <ProviderRow
              key={name}
              name={name}
              entry={entry}
              isActive={name === status?.active_provider}
            />
          ))}
      </div>

      <button
        type="button"
        onClick={() => router.push("/settings/ai-providers")}
        className="mt-4 w-full text-xs text-muted-foreground hover:text-foreground underline underline-offset-2 transition-colors"
      >
        Manage AI providers →
      </button>
    </motion.section>
  );
}
