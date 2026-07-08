"use client";

import { memo } from "react";
import {
  BookOpen, FileText, Shield, GraduationCap, Building2, CheckSquare,
  AlertTriangle, ClipboardCheck, Layers, ArrowRight, ExternalLink,
  TrendingUp, Hash,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ── Shared card shell ─────────────────────────────────────────────────────────

function CardShell({
  accent,
  icon: Icon,
  badge,
  title,
  subtitle,
  children,
  href,
  className,
}: {
  accent: string;
  icon: React.ElementType;
  badge?: string;
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
  href?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "relative rounded-xl border border-border bg-card shadow-sm overflow-hidden my-2",
        "hover:shadow-md transition-shadow group",
        className,
      )}
    >
      {/* Left accent bar */}
      <div className={cn("absolute left-0 top-0 bottom-0 w-[3px]", accent)} />

      <div className="pl-4 pr-4 py-3">
        <div className="flex items-start gap-2.5">
          {/* Icon */}
          <div className={cn("w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5", accent, "bg-opacity-15")}>
            <Icon className="h-3.5 w-3.5 text-foreground opacity-70" />
          </div>

          <div className="min-w-0 flex-1">
            {badge && (
              <span className="text-[9px] font-semibold uppercase tracking-widest text-muted-foreground">
                {badge}
              </span>
            )}
            <p className="text-sm font-semibold text-foreground leading-tight truncate">{title}</p>
            {subtitle && (
              <p className="text-[11px] text-muted-foreground mt-0.5 leading-snug">{subtitle}</p>
            )}
          </div>

          {href ? (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-auto text-muted-foreground hover:text-foreground transition-colors opacity-0 group-hover:opacity-100"
              aria-label="Open source"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          ) : (
            <ArrowRight className="ml-auto h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-60 transition-opacity" />
          )}
        </div>

        {children && <div className="mt-2.5 pl-9">{children}</div>}
      </div>
    </div>
  );
}

// ── Badge chip ────────────────────────────────────────────────────────────────

function Chip({ label, color }: { label: string; color: string }) {
  return (
    <span className={cn("inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium", color)}>
      {label}
    </span>
  );
}

// ── Domain cards ──────────────────────────────────────────────────────────────

export const PolicyCard = memo(function PolicyCard({
  title,
  version,
  status,
  policyType,
}: {
  title: string;
  version?: string;
  status?: string;
  policyType?: string;
}) {
  const statusColor =
    status === "approved" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
    : status === "draft" ? "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
    : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";

  return (
    <CardShell accent="bg-violet-500" icon={BookOpen} badge="Policy" title={title} subtitle={policyType}>
      <div className="flex gap-1.5 flex-wrap">
        {version && <Chip label={`v${version}`} color="bg-muted text-muted-foreground" />}
        {status && <Chip label={status} color={statusColor} />}
      </div>
    </CardShell>
  );
});

export const ModuleCard = memo(function ModuleCard({
  code,
  title,
  nqfLevel,
  credits,
  status,
}: {
  code: string;
  title: string;
  nqfLevel?: number;
  credits?: number;
  status?: string;
}) {
  return (
    <CardShell accent="bg-blue-500" icon={FileText} badge="Module" title={`${code} — ${title}`}>
      <div className="flex gap-1.5 flex-wrap">
        {nqfLevel && <Chip label={`NQF ${nqfLevel}`} color="bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300" />}
        {credits && <Chip label={`${credits} credits`} color="bg-muted text-muted-foreground" />}
        {status && <Chip label={status} color="bg-muted text-muted-foreground" />}
      </div>
    </CardShell>
  );
});

export const ProgrammeCard = memo(function ProgrammeCard({
  name,
  code,
  nqfLevel,
  qualificationType,
  credits,
}: {
  name: string;
  code?: string;
  nqfLevel?: number;
  qualificationType?: string;
  credits?: number;
}) {
  return (
    <CardShell
      accent="bg-indigo-500"
      icon={GraduationCap}
      badge="Programme"
      title={name}
      subtitle={code}
    >
      <div className="flex gap-1.5 flex-wrap">
        {qualificationType && <Chip label={qualificationType} color="bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300" />}
        {nqfLevel && <Chip label={`NQF ${nqfLevel}`} color="bg-muted text-muted-foreground" />}
        {credits && <Chip label={`${credits} credits`} color="bg-muted text-muted-foreground" />}
      </div>
    </CardShell>
  );
});

export const FindingCard = memo(function FindingCard({
  title,
  severity,
  area,
  status,
}: {
  title: string;
  severity?: "critical" | "major" | "minor" | "observation";
  area?: string;
  status?: string;
}) {
  const severityColor =
    severity === "critical" ? "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300"
    : severity === "major" ? "bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-300"
    : severity === "minor" ? "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
    : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";

  return (
    <CardShell accent="bg-rose-500" icon={AlertTriangle} badge="Finding" title={title} subtitle={area}>
      <div className="flex gap-1.5 flex-wrap">
        {severity && <Chip label={severity} color={severityColor} />}
        {status && <Chip label={status} color="bg-muted text-muted-foreground" />}
      </div>
    </CardShell>
  );
});

export const AccreditationCard = memo(function AccreditationCard({
  body,
  status,
  expiryDate,
  programme,
}: {
  body: string;
  status?: string;
  expiryDate?: string;
  programme?: string;
}) {
  const statusColor =
    status === "accredited" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
    : status === "pending" ? "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
    : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";

  return (
    <CardShell accent="bg-amber-500" icon={Shield} badge="Accreditation" title={body} subtitle={programme}>
      <div className="flex gap-1.5 flex-wrap">
        {status && <Chip label={status} color={statusColor} />}
        {expiryDate && <Chip label={`Expires ${expiryDate}`} color="bg-muted text-muted-foreground" />}
      </div>
    </CardShell>
  );
});

export const AuditCard = memo(function AuditCard({
  agentType,
  scope,
  status,
  findings,
}: {
  agentType: string;
  scope?: string;
  status?: string;
  findings?: number;
}) {
  const statusColor =
    status === "completed" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
    : status === "running" ? "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300"
    : status === "failed" ? "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300"
    : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";

  return (
    <CardShell accent="bg-emerald-500" icon={ClipboardCheck} badge="Audit" title={agentType} subtitle={scope}>
      <div className="flex gap-1.5 flex-wrap">
        {status && <Chip label={status} color={statusColor} />}
        {findings !== undefined && <Chip label={`${findings} findings`} color="bg-muted text-muted-foreground" />}
      </div>
    </CardShell>
  );
});

export const InstitutionCard = memo(function InstitutionCard({
  name,
  code,
  type,
  province,
}: {
  name: string;
  code?: string;
  type?: string;
  province?: string;
}) {
  return (
    <CardShell accent="bg-slate-500" icon={Building2} badge="Institution" title={name} subtitle={code}>
      <div className="flex gap-1.5 flex-wrap">
        {type && <Chip label={type} color="bg-muted text-muted-foreground" />}
        {province && <Chip label={province} color="bg-muted text-muted-foreground" />}
      </div>
    </CardShell>
  );
});

export const QualificationCard = memo(function QualificationCard({
  title,
  saqa,
  nqfLevel,
  credits,
  field,
}: {
  title: string;
  saqa?: string;
  nqfLevel?: number;
  credits?: number;
  field?: string;
}) {
  return (
    <CardShell
      accent="bg-teal-500"
      icon={Hash}
      badge="Qualification"
      title={title}
      subtitle={field}
    >
      <div className="flex gap-1.5 flex-wrap">
        {saqa && <Chip label={`SAQA ${saqa}`} color="bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-300" />}
        {nqfLevel && <Chip label={`NQF ${nqfLevel}`} color="bg-muted text-muted-foreground" />}
        {credits && <Chip label={`${credits} credits`} color="bg-muted text-muted-foreground" />}
      </div>
    </CardShell>
  );
});

export const EvidenceCard = memo(function EvidenceCard({
  title,
  category,
  module,
  uploadState,
}: {
  title: string;
  category?: string;
  module?: string;
  uploadState?: string;
}) {
  const stateColor =
    uploadState === "ready" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
    : uploadState === "scanning" ? "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300"
    : uploadState === "quarantined" ? "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300"
    : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";

  return (
    <CardShell accent="bg-cyan-500" icon={Layers} badge="Evidence" title={title} subtitle={module}>
      <div className="flex gap-1.5 flex-wrap">
        {category && <Chip label={category} color="bg-muted text-muted-foreground" />}
        {uploadState && <Chip label={uploadState} color={stateColor} />}
      </div>
    </CardShell>
  );
});
