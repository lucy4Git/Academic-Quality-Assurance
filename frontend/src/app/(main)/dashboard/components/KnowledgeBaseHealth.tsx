"use client";

import { motion } from "framer-motion";
import { Database, Cpu, HardDrive, Cloud, Server } from "lucide-react";
import { cn } from "@/lib/utils";

type ServiceStatus = "healthy" | "warning" | "offline";

interface Service {
  name: string;
  description: string;
  status: ServiceStatus;
  icon: React.ElementType;
  latency?: string;
}

const STATUS_CONFIG: Record<ServiceStatus, { label: string; dot: string; badge: string }> = {
  healthy: {
    label: "Healthy",
    dot: "bg-emerald-500",
    badge: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
  },
  warning: {
    label: "Warning",
    dot: "bg-amber-500",
    badge: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
  },
  offline: {
    label: "Offline",
    dot: "bg-red-500",
    badge: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800",
  },
};

const SERVICES: Service[] = [
  { name: "Qdrant",    description: "Vector store",     status: "healthy", icon: Database, latency: "12ms" },
  { name: "Redis",     description: "Cache layer",      status: "healthy", icon: Server,   latency: "2ms"  },
  { name: "Postgres",  description: "Primary database", status: "healthy", icon: HardDrive,latency: "8ms"  },
  { name: "OpenAI",    description: "GPT-4o provider",  status: "healthy", icon: Cloud,    latency: "320ms"},
  { name: "Ollama",    description: "Local LLM",        status: "healthy", icon: Cpu,      latency: "45ms" },
  { name: "MinIO",     description: "Object storage",   status: "warning", icon: HardDrive,latency: "—"    },
];

function PulseDot({ status }: { status: ServiceStatus }) {
  const colour = STATUS_CONFIG[status].dot;
  return (
    <span className="relative flex h-2.5 w-2.5">
      {status === "healthy" && (
        <span className={cn("animate-ping absolute inline-flex h-full w-full rounded-full opacity-60", colour)} />
      )}
      <span className={cn("relative inline-flex rounded-full h-2.5 w-2.5", colour)} />
    </span>
  );
}

function ServiceCard({ service, index }: { service: Service; index: number }) {
  const cfg = STATUS_CONFIG[service.status];
  const Icon = service.icon;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, delay: index * 0.05, ease: [0.16, 1, 0.3, 1] }}
      className="flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3"
    >
      <div className="flex-shrink-0 h-9 w-9 rounded-lg bg-muted flex items-center justify-center">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-foreground">{service.name}</p>
        <p className="text-xs text-muted-foreground">{service.description}</p>
      </div>
      <div className="flex-shrink-0 flex flex-col items-end gap-1">
        <div className="flex items-center gap-1.5">
          <PulseDot status={service.status} />
          <span className={cn("text-[11px] font-semibold px-2 py-0.5 rounded-full border", cfg.badge)}>
            {cfg.label}
          </span>
        </div>
        {service.latency && (
          <span className="text-[10px] text-muted-foreground font-mono">{service.latency}</span>
        )}
      </div>
    </motion.div>
  );
}

export function KnowledgeBaseHealth() {
  const healthyCount = SERVICES.filter((s) => s.status === "healthy").length;

  return (
    <section className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
          <Database className="h-4 w-4 text-indigo-500" />
          Knowledge Base &amp; Services
        </h2>
        <span className="text-xs text-muted-foreground font-medium">
          {healthyCount}/{SERVICES.length} operational
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {SERVICES.map((s, i) => (
          <ServiceCard key={s.name} service={s} index={i} />
        ))}
      </div>
    </section>
  );
}
