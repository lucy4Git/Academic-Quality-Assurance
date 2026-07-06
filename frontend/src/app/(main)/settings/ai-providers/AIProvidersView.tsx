"use client";

import { motion } from "framer-motion";
import {
  Brain,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Info,
  Zap,
  Shield,
} from "lucide-react";
import { useProviderStatus, useProviderHealth } from "@/hooks/useProviderHealth";
import { useRole } from "@/hooks/useRole";
import type { ProviderHealthEntry } from "@/lib/api/providers";

// Per-provider display metadata
const PROVIDER_META: Record<string, { label: string; description: string; badge?: string }> = {
  openai: {
    label: "OpenAI",
    description: "GPT-4o-mini and GPT-4o family. Production-grade, globally available.",
  },
  anthropic: {
    label: "Anthropic (Claude)",
    description: "Claude Haiku / Sonnet family. Exceptional reasoning and context length.",
    badge: "Scaffolded",
  },
  ollama: {
    label: "Ollama (Local)",
    description: "Self-hosted model via Ollama. Runs on-premise — no data leaves your network.",
  },
  gemini: {
    label: "Google Gemini",
    description: "Gemini 2.5 Flash. Multimodal, cost-effective, available via Google AI Studio.",
    badge: "Scaffolded",
  },
  local_dev: {
    label: "Local Dev",
    description: "Template-based fallback. Used when no external provider is configured.",
  },
};

const STATUS_CONFIG: Record<
  string,
  { label: string; colorBg: string; colorText: string; icon: typeof CheckCircle2 }
> = {
  ok: {
    label: "Operational",
    colorBg: "bg-emerald-50 dark:bg-emerald-900/20",
    colorText: "text-emerald-700 dark:text-emerald-400",
    icon: CheckCircle2,
  },
  error: {
    label: "Error",
    colorBg: "bg-red-50 dark:bg-red-900/20",
    colorText: "text-red-700 dark:text-red-400",
    icon: XCircle,
  },
  not_configured: {
    label: "Not Configured",
    colorBg: "bg-muted",
    colorText: "text-muted-foreground",
    icon: AlertTriangle,
  },
  not_implemented: {
    label: "Scaffolded",
    colorBg: "bg-amber-50 dark:bg-amber-900/20",
    colorText: "text-amber-700 dark:text-amber-400",
    icon: AlertTriangle,
  },
  unavailable: {
    label: "Unavailable",
    colorBg: "bg-red-50 dark:bg-red-900/20",
    colorText: "text-red-700 dark:text-red-400",
    icon: XCircle,
  },
};

function ProviderCard({
  name,
  entry,
  isActive,
}: {
  name: string;
  entry: ProviderHealthEntry;
  isActive: boolean;
}) {
  const meta = PROVIDER_META[name] ?? { label: name, description: "" };
  const cfg = STATUS_CONFIG[entry.status] ?? STATUS_CONFIG["not_configured"];
  const Icon = cfg.icon;
  const latency =
    entry.latency_ms > 0 ? `${Math.round(entry.latency_ms)} ms` : null;

  return (
    <div
      className={`relative rounded-xl border p-5 transition-colors ${
        isActive
          ? "border-indigo-300 dark:border-indigo-700 bg-indigo-50/40 dark:bg-indigo-950/20"
          : "border-border bg-card"
      }`}
    >
      {isActive && (
        <span className="absolute top-3 right-3 text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-600 text-white">
          ACTIVE
        </span>
      )}

      <div className="flex items-start gap-3">
        <div
          className={`mt-0.5 h-8 w-8 rounded-lg flex items-center justify-center flex-shrink-0 ${cfg.colorBg}`}
        >
          <Icon className={`h-4 w-4 ${cfg.colorText}`} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-sm font-semibold text-foreground">{meta.label}</h3>
            {meta.badge && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full border border-amber-300 text-amber-700 dark:border-amber-700 dark:text-amber-400">
                {meta.badge}
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
            {meta.description}
          </p>

          <div className="mt-3 flex items-center gap-3 flex-wrap">
            <span
              className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${cfg.colorBg} ${cfg.colorText}`}
            >
              <Icon className="h-3 w-3" />
              {cfg.label}
            </span>
            {latency && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Zap className="h-3 w-3" />
                {latency}
              </span>
            )}
          </div>

          {entry.error && (
            <p className="mt-2 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">
              {entry.error}
            </p>
          )}

          {entry.note && (
            <p className="mt-2 text-xs text-muted-foreground flex items-center gap-1">
              <Info className="h-3 w-3 flex-shrink-0" />
              {entry.note}
            </p>
          )}

          {name === "ollama" && entry.available_models && entry.available_models.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-muted-foreground mb-1">Available models:</p>
              <div className="flex flex-wrap gap-1">
                {entry.available_models.slice(0, 5).map((m) => (
                  <span
                    key={m}
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-muted text-muted-foreground"
                  >
                    {m}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function AIProvidersView() {
  const { isSysAdmin, isQAOfficer } = useRole();
  const { data: status, isLoading: statusLoading } = useProviderStatus();
  const {
    data: health,
    isLoading: healthLoading,
    refetch,
    isFetching,
    error: healthError,
  } = useProviderHealth();

  const canViewHealth = isSysAdmin || isQAOfficer;
  const isLoading = statusLoading || healthLoading;

  return (
    <div className="max-w-3xl mx-auto space-y-8 py-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI Provider Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">
          View the active AI provider configuration and run health checks across all
          configured providers.
        </p>
      </div>

      {/* Configuration snapshot */}
      <section>
        <h2 className="text-base font-semibold mb-3">Active Configuration</h2>
        {statusLoading && (
          <div className="rounded-xl border border-border bg-card p-5 text-sm text-muted-foreground">
            Loading configuration…
          </div>
        )}
        {status && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl border border-border bg-card p-5 grid grid-cols-2 sm:grid-cols-3 gap-4"
          >
            {[
              { label: "Active provider", value: status.active_provider },
              { label: "Model", value: status.active_model },
              { label: "Temperature", value: String(status.temperature) },
              { label: "Max tokens", value: String(status.max_tokens) },
              {
                label: "Fallback chain",
                value:
                  status.fallback_chain.length > 0
                    ? status.fallback_chain.join(" → ")
                    : "None",
              },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="text-sm font-medium capitalize mt-0.5 font-mono">{value}</p>
              </div>
            ))}
          </motion.div>
        )}
      </section>

      {/* Provider health */}
      {canViewHealth && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-semibold">Provider Health</h2>
            <button
              type="button"
              onClick={() => refetch()}
              disabled={isFetching}
              className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors disabled:opacity-40"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
              {isFetching ? "Checking…" : "Refresh"}
            </button>
          </div>

          {/* Overall status banner */}
          {health && (
            <div
              className={`mb-4 flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium ${
                health.overall === "healthy"
                  ? "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800"
                  : "bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800"
              }`}
            >
              {health.overall === "healthy" ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <AlertTriangle className="h-4 w-4" />
              )}
              {health.overall === "healthy"
                ? "All operational providers are healthy"
                : "One or more providers are degraded — fallback is active"}
            </div>
          )}

          {healthError && (
            <div className="mb-4 px-4 py-3 rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 text-sm text-red-700 dark:text-red-400">
              Could not load health data — you may not have permission, or the backend
              is unreachable.
            </div>
          )}

          {isLoading && (
            <div className="rounded-xl border border-border bg-card p-8 text-center text-sm text-muted-foreground">
              Running health checks…
            </div>
          )}

          {health && (
            <div className="space-y-3">
              {Object.entries(health.providers).map(([name, entry]) => (
                <motion.div
                  key={name}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <ProviderCard
                    name={name}
                    entry={entry}
                    isActive={name === status?.active_provider}
                  />
                </motion.div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Config help */}
      <section className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-start gap-3">
          <Shield className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold">Changing providers</h3>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
              Provider configuration is managed via environment variables in{" "}
              <code className="font-mono bg-muted px-1 py-0.5 rounded text-xs">
                backend/.env
              </code>
              . Set <code className="font-mono bg-muted px-1 py-0.5 rounded text-xs">AI_PROVIDER</code> to{" "}
              <code className="font-mono bg-muted px-1 py-0.5 rounded text-xs">OPENAI</code>,{" "}
              <code className="font-mono bg-muted px-1 py-0.5 rounded text-xs">ANTHROPIC</code>,{" "}
              <code className="font-mono bg-muted px-1 py-0.5 rounded text-xs">OLLAMA</code>, or{" "}
              <code className="font-mono bg-muted px-1 py-0.5 rounded text-xs">LOCAL_DEV</code>{" "}
              and restart the backend. API keys are never logged or returned by any endpoint.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
