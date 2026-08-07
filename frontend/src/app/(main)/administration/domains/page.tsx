"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Globe,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Trash2,
  AlertCircle,
  ShieldCheck,
  Users,
  ChevronDown,
  ChevronUp,
  Building2,
  ToggleLeft,
  ToggleRight,
} from "lucide-react";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { useAuthStore } from "@/store/auth.store";
import type { UserRole } from "@/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface InstitutionDomain {
  id: string;
  institution_id: string;
  domain: string;
  is_active: boolean;
  is_verified: boolean;
  auto_assign_student: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

interface DomainCreateForm {
  domain: string;
  institution_id: string;
  is_active: boolean;
  is_verified: boolean;
  auto_assign_student: boolean;
}

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function apiFetch(path: string, options?: RequestInit) {
  const res = await fetch(`/api/proxy/${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  if (res.status === 204) return null;
  return res.json();
}

// ---------------------------------------------------------------------------
// Add domain dialog
// ---------------------------------------------------------------------------

function AddDomainDialog({
  onClose,
  institutionId,
}: {
  onClose: () => void;
  institutionId: string | null;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<DomainCreateForm>({
    domain: "",
    institution_id: institutionId ?? "",
    is_active: true,
    is_verified: false,
    auto_assign_student: false,
  });

  const mutation = useMutation({
    mutationFn: async (data: DomainCreateForm) => {
      const body: Record<string, unknown> = {
        domain: data.domain.toLowerCase().replace(/^@/, "").trim(),
        is_active: data.is_active,
        is_verified: data.is_verified,
        auto_assign_student: data.auto_assign_student,
      };
      if (data.institution_id) body.institution_id = data.institution_id;
      return apiFetch("institution-domains", { method: "POST", body: JSON.stringify(body) });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["institution-domains"] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-white dark:bg-zinc-900 p-6 shadow-2xl">
        <h2 className="text-lg font-semibold mb-1">Add Domain</h2>
        <p className="text-sm text-muted-foreground mb-5">
          Map an institutional email domain. Public providers (Gmail, Outlook, Yahoo, etc.) are
          blocked.
        </p>

        {mutation.error && (
          <div className="mb-4 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 p-3 text-sm text-red-700 dark:text-red-300 flex gap-2">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            {(mutation.error as Error).message}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Domain</label>
            <input
              type="text"
              value={form.domain}
              onChange={(e) => setForm((f) => ({ ...f, domain: e.target.value }))}
              placeholder="institution.ac.za"
              className="w-full rounded-lg border px-3 py-2 text-sm bg-background font-mono"
              autoFocus
            />
            <p className="text-xs text-muted-foreground mt-1">
              Enter without @ prefix. Will be normalised to lowercase.
            </p>
          </div>

          {!institutionId && (
            <div>
              <label className="block text-sm font-medium mb-1">Institution ID</label>
              <input
                type="text"
                value={form.institution_id}
                onChange={(e) => setForm((f) => ({ ...f, institution_id: e.target.value }))}
                placeholder="UUID of the institution"
                className="w-full rounded-lg border px-3 py-2 text-sm bg-background font-mono"
              />
            </div>
          )}

          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
                className="rounded"
              />
              Active — enforce domain matching immediately
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={form.is_verified}
                onChange={(e) => setForm((f) => ({ ...f, is_verified: e.target.checked }))}
                className="rounded"
              />
              Mark as verified (domain ownership confirmed)
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={form.auto_assign_student}
                onChange={(e) =>
                  setForm((f) => ({ ...f, auto_assign_student: e.target.checked }))
                }
                className="rounded"
              />
              Auto-assign students registering with this domain
            </label>
          </div>
        </div>

        <div className="flex gap-2 mt-6">
          <button
            onClick={onClose}
            className="flex-1 rounded-lg border px-4 py-2 text-sm font-medium hover:bg-muted/50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate(form)}
            disabled={mutation.isPending || !form.domain.trim()}
            className="flex-1 rounded-lg bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
          >
            {mutation.isPending ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Add Domain
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Domain row
// ---------------------------------------------------------------------------

function DomainRow({ domain }: { domain: InstitutionDomain }) {
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState(false);

  const patch = useMutation({
    mutationFn: (data: Partial<Pick<InstitutionDomain, "is_active" | "auto_assign_student" | "is_verified">>) =>
      apiFetch(`institution-domains/${domain.id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["institution-domains"] }),
  });

  const remove = useMutation({
    mutationFn: () => apiFetch(`institution-domains/${domain.id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["institution-domains"] }),
  });

  return (
    <div className="rounded-lg border bg-card">
      <div
        className="flex items-center gap-3 p-4 cursor-pointer"
        onClick={() => setExpanded((v) => !v)}
      >
        {/* Domain icon */}
        <div
          className={`p-2 rounded-lg ${domain.is_active ? "bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600" : "bg-muted text-muted-foreground"}`}
        >
          <Globe className="h-4 w-4" />
        </div>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono font-medium text-sm">{domain.domain}</span>
            {domain.is_active ? (
              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border text-emerald-700 bg-emerald-50 border-emerald-200 dark:text-emerald-400 dark:bg-emerald-950/30 dark:border-emerald-800">
                <CheckCircle2 className="h-3 w-3" />
                Active
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border text-muted-foreground bg-muted border-border">
                <XCircle className="h-3 w-3" />
                Inactive
              </span>
            )}
            {domain.is_verified && (
              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border text-blue-700 bg-blue-50 border-blue-200 dark:text-blue-400 dark:bg-blue-950/30 dark:border-blue-800">
                <ShieldCheck className="h-3 w-3" />
                Verified
              </span>
            )}
            {domain.auto_assign_student && (
              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border text-violet-700 bg-violet-50 border-violet-200 dark:text-violet-400 dark:bg-violet-950/30 dark:border-violet-800">
                <Users className="h-3 w-3" />
                Auto-assign
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Added {new Date(domain.created_at).toLocaleDateString()}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => patch.mutate({ is_active: !domain.is_active })}
            disabled={patch.isPending}
            className="p-1.5 rounded-md hover:bg-muted/80 transition-colors text-muted-foreground"
            title={domain.is_active ? "Deactivate domain" : "Activate domain"}
          >
            {domain.is_active ? (
              <ToggleRight className="h-4 w-4 text-emerald-600" />
            ) : (
              <ToggleLeft className="h-4 w-4" />
            )}
          </button>
          <button
            onClick={() => {
              if (confirm(`Remove domain "${domain.domain}"? This cannot be undone.`)) {
                remove.mutate();
              }
            }}
            disabled={remove.isPending}
            className="p-1.5 rounded-md text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
            title="Remove domain"
          >
            <Trash2 className="h-4 w-4" />
          </button>
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="border-t px-4 py-3 space-y-3 bg-muted/20">
          <div className="text-xs text-muted-foreground space-y-1">
            <div>
              <span className="font-medium text-foreground">ID:</span>{" "}
              <span className="font-mono">{domain.id}</span>
            </div>
            <div>
              <span className="font-medium text-foreground">Institution:</span>{" "}
              <span className="font-mono">{domain.institution_id}</span>
            </div>
            <div>
              <span className="font-medium text-foreground">Last updated:</span>{" "}
              {new Date(domain.updated_at).toLocaleString()}
            </div>
          </div>

          {/* Toggles */}
          <div className="flex flex-wrap gap-3 text-sm">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={domain.is_verified}
                onChange={(e) => patch.mutate({ is_verified: e.target.checked })}
                className="rounded"
              />
              Verified
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={domain.auto_assign_student}
                onChange={(e) => patch.mutate({ auto_assign_student: e.target.checked })}
                className="rounded"
              />
              Auto-assign students
            </label>
          </div>

          {(patch.error || remove.error) && (
            <p className="text-xs text-red-600">
              {((patch.error ?? remove.error) as Error).message}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

const ALLOWED_ROLES: UserRole[] = ["system_admin", "institution_admin"];

export default function DomainsPage() {
  const user = useAuthStore((s) => s.user);
  const [showAdd, setShowAdd] = useState(false);
  const [activeFilter, setActiveFilter] = useState<boolean | null>(null);

  const { data: domains = [], isLoading, error } = useQuery<InstitutionDomain[]>({
    queryKey: ["institution-domains", activeFilter],
    queryFn: () => {
      const params = new URLSearchParams();
      if (activeFilter !== null) params.set("is_active", String(activeFilter));
      const qs = params.toString();
      return apiFetch(`institution-domains${qs ? `?${qs}` : ""}`);
    },
  });

  const activeDomains = domains.filter((d) => d.is_active);
  const verifiedDomains = domains.filter((d) => d.is_verified);
  const autoAssignDomains = domains.filter((d) => d.auto_assign_student);

  return (
    <RoleGuard roles={ALLOWED_ROLES}>
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Institution Domains</h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Manage email domain mappings for automatic institutional assignment
            </p>
          </div>
          <button
            onClick={() => setShowAdd(true)}
            className="flex items-center gap-2 rounded-lg bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add Domain
          </button>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          {[
            { label: "Total", value: domains.length, icon: <Globe className="h-4 w-4" />, color: "text-foreground" },
            { label: "Active", value: activeDomains.length, icon: <CheckCircle2 className="h-4 w-4" />, color: "text-emerald-600" },
            { label: "Auto-assign", value: autoAssignDomains.length, icon: <Users className="h-4 w-4" />, color: "text-violet-600" },
          ].map((stat) => (
            <div key={stat.label} className="rounded-lg border bg-card p-4 text-center">
              <div className={`flex justify-center mb-1 ${stat.color}`}>{stat.icon}</div>
              <div className="text-2xl font-bold">{stat.value}</div>
              <div className="text-xs text-muted-foreground">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Filter bar */}
        <div className="flex gap-2 mb-4">
          {[
            { value: null, label: "All" },
            { value: true, label: "Active" },
            { value: false, label: "Inactive" },
          ].map((f) => (
            <button
              key={String(f.value)}
              onClick={() => setActiveFilter(f.value)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                activeFilter === f.value
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Security notice */}
        <div className="mb-5 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 p-3 text-sm text-blue-800 dark:text-blue-300 flex gap-2">
          <Building2 className="h-4 w-4 mt-0.5 shrink-0" />
          <div>
            <span className="font-medium">Domain security: </span>
            Public providers (Gmail, Outlook, Yahoo, iCloud, etc.) cannot be registered.
            Auto-assign automatically links students whose email matches the domain to this institution.
          </div>
        </div>

        {/* List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12 text-muted-foreground">
            <RefreshCw className="h-5 w-5 animate-spin mr-2" />
            Loading domains…
          </div>
        ) : error ? (
          <div className="rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-200 p-4 text-sm text-red-700">
            {(error as Error).message}
          </div>
        ) : domains.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <Globe className="h-10 w-10 mx-auto mb-3 opacity-30" />
            <p className="font-medium">No domains configured</p>
            <p className="text-sm mt-1">
              Add your first institutional domain to enable automatic student assignment
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {domains.map((d) => (
              <DomainRow key={d.id} domain={d} />
            ))}
          </div>
        )}
      </div>

      {showAdd && (
        <AddDomainDialog
          onClose={() => setShowAdd(false)}
          institutionId={user?.institution_id ?? null}
        />
      )}
    </RoleGuard>
  );
}
