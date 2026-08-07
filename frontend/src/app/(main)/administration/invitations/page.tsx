"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Copy,
  XCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Clock,
  Users,
  Mail,
  Globe,
  Shield,
  AlertCircle,
  CheckCircle2,
  Ban,
} from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import { RoleGuard } from "@/components/auth/RoleGuard";
import type { UserRole } from "@/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Invitation {
  id: string;
  invitation_type: string;
  role: string | null;
  institution_id: string | null;
  email_restriction: string | null;
  domain_restriction: string | null;
  status: string;
  use_count: number;
  max_uses: number;
  expires_at: string;
  created_at: string;
  notes: string | null;
  requires_email_verification: boolean;
}

interface CreateInvitationForm {
  invitation_type: string;
  role: string;
  institution_id: string;
  email_restriction: string;
  domain_restriction: string;
  expires_in_days: number;
  max_uses: number;
  notes: string;
  requires_email_verification: boolean;
}

const INVITATION_TYPES = [
  { value: "student_onboarding", label: "Student Onboarding" },
  { value: "staff_lecturer", label: "Lecturer" },
  { value: "staff_coordinator", label: "Programme Coordinator" },
  { value: "staff_hod", label: "Head of Department" },
  { value: "staff_dean", label: "Faculty Dean" },
  { value: "qa_officer", label: "QA Officer" },
  { value: "external_moderator", label: "External Moderator" },
  { value: "institution_admin", label: "Institution Administrator" },
];

// Roles that only system_admin may create invitations for
const SYSTEM_ADMIN_ONLY_TYPES = new Set(["institution_admin"]);

const STATUS_CONFIG: Record<string, { label: string; icon: React.ReactElement; className: string }> = {
  pending: { label: "Active", icon: <CheckCircle2 className="h-3.5 w-3.5" />, className: "text-emerald-700 bg-emerald-50 border-emerald-200" },
  consumed: { label: "Used", icon: <Users className="h-3.5 w-3.5" />, className: "text-blue-700 bg-blue-50 border-blue-200" },
  revoked: { label: "Revoked", icon: <Ban className="h-3.5 w-3.5" />, className: "text-red-700 bg-red-50 border-red-200" },
  expired: { label: "Expired", icon: <Clock className="h-3.5 w-3.5" />, className: "text-amber-700 bg-amber-50 border-amber-200" },
};

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
// Create invitation dialog
// ---------------------------------------------------------------------------

function CreateInvitationDialog({
  onClose,
  userRole,
  institutionId,
}: {
  onClose: () => void;
  userRole: UserRole;
  institutionId: string | null;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<CreateInvitationForm>({
    invitation_type: "staff_lecturer",
    role: "lecturer",
    institution_id: institutionId ?? "",
    email_restriction: "",
    domain_restriction: "",
    expires_in_days: 7,
    max_uses: 1,
    notes: "",
    requires_email_verification: true,
  });
  const [createdToken, setCreatedToken] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const mutation = useMutation({
    mutationFn: async (data: CreateInvitationForm) => {
      const body: Record<string, unknown> = {
        invitation_type: data.invitation_type,
        role: data.role,
        expires_in_days: data.expires_in_days,
        max_uses: data.max_uses,
        requires_email_verification: data.requires_email_verification,
      };
      if (data.institution_id) body.institution_id = data.institution_id;
      if (data.email_restriction) body.email_restriction = data.email_restriction;
      if (data.domain_restriction) body.domain_restriction = data.domain_restriction;
      if (data.notes) body.notes = data.notes;
      return apiFetch("invitations", { method: "POST", body: JSON.stringify(body) });
    },
    onSuccess: (data) => {
      setCreatedToken(data.token);
      queryClient.invalidateQueries({ queryKey: ["invitations"] });
    },
  });

  const allowedTypes = INVITATION_TYPES.filter(
    (t) => userRole === "system_admin" || !SYSTEM_ADMIN_ONLY_TYPES.has(t.value)
  );

  function setType(value: string) {
    const roleMap: Record<string, string> = {
      student_onboarding: "student",
      staff_lecturer: "lecturer",
      staff_coordinator: "programme_coordinator",
      staff_hod: "head_of_department",
      staff_dean: "faculty_dean",
      qa_officer: "quality_assurance_officer",
      external_moderator: "lecturer",
      institution_admin: "institution_admin",
    };
    setForm((f) => ({ ...f, invitation_type: value, role: roleMap[value] ?? f.role }));
  }

  async function copyToken() {
    if (!createdToken) return;
    await navigator.clipboard.writeText(createdToken);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (createdToken) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <div className="w-full max-w-md rounded-xl bg-white dark:bg-zinc-900 p-6 shadow-2xl">
          <h2 className="text-lg font-semibold mb-2">Invitation Created</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Copy this token now — it will not be shown again. Share it securely with the invitee.
          </p>
          <div className="rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 p-3 mb-4">
            <p className="text-xs font-mono break-all text-amber-900 dark:text-amber-200 select-all">{createdToken}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={copyToken}
              className="flex-1 flex items-center justify-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium hover:bg-muted/50 transition-colors"
            >
              <Copy className="h-4 w-4" />
              {copied ? "Copied!" : "Copy Token"}
            </button>
            <button
              onClick={onClose}
              className="flex-1 rounded-lg bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white dark:bg-zinc-900 p-6 shadow-2xl overflow-y-auto max-h-[90vh]">
        <h2 className="text-lg font-semibold mb-1">Create Invitation</h2>
        <p className="text-sm text-muted-foreground mb-5">
          The one-time token is shown once after creation. Store it securely.
        </p>

        {mutation.error && (
          <div className="mb-4 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 p-3 text-sm text-red-700 dark:text-red-300 flex gap-2">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            {(mutation.error as Error).message}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Invitation Type</label>
            <select
              value={form.invitation_type}
              onChange={(e) => setType(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-sm bg-background"
            >
              {allowedTypes.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          {!institutionId && (
            <div>
              <label className="block text-sm font-medium mb-1">Institution ID</label>
              <input
                type="text"
                value={form.institution_id}
                onChange={(e) => setForm((f) => ({ ...f, institution_id: e.target.value }))}
                placeholder="UUID of the target institution"
                className="w-full rounded-lg border px-3 py-2 text-sm bg-background font-mono"
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Expires (days)</label>
              <input
                type="number"
                min={1}
                max={90}
                value={form.expires_in_days}
                onChange={(e) => setForm((f) => ({ ...f, expires_in_days: +e.target.value }))}
                className="w-full rounded-lg border px-3 py-2 text-sm bg-background"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Max Uses</label>
              <input
                type="number"
                min={1}
                max={100}
                value={form.max_uses}
                onChange={(e) => setForm((f) => ({ ...f, max_uses: +e.target.value }))}
                className="w-full rounded-lg border px-3 py-2 text-sm bg-background"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Bind to Email <span className="text-muted-foreground font-normal">(optional)</span>
            </label>
            <input
              type="email"
              value={form.email_restriction}
              onChange={(e) => setForm((f) => ({ ...f, email_restriction: e.target.value }))}
              placeholder="user@institution.ac.za"
              className="w-full rounded-lg border px-3 py-2 text-sm bg-background"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Bind to Domain <span className="text-muted-foreground font-normal">(optional)</span>
            </label>
            <input
              type="text"
              value={form.domain_restriction}
              onChange={(e) => setForm((f) => ({ ...f, domain_restriction: e.target.value }))}
              placeholder="institution.ac.za"
              className="w-full rounded-lg border px-3 py-2 text-sm bg-background"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Notes <span className="text-muted-foreground font-normal">(optional)</span>
            </label>
            <textarea
              rows={2}
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              placeholder="Internal note for this invitation"
              className="w-full rounded-lg border px-3 py-2 text-sm bg-background resize-none"
            />
          </div>

          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={form.requires_email_verification}
              onChange={(e) => setForm((f) => ({ ...f, requires_email_verification: e.target.checked }))}
              className="rounded"
            />
            Require email verification after registration
          </label>
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
            disabled={mutation.isPending}
            className="flex-1 rounded-lg bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
          >
            {mutation.isPending ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Create
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Invitation row
// ---------------------------------------------------------------------------

function InvitationRow({ inv, canRevoke }: { inv: Invitation; canRevoke: boolean }) {
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState(false);

  const expires = new Date(inv.expires_at);
  const isExpired = expires < new Date() && inv.status === "pending";
  const effectiveStatus = isExpired ? "expired" : inv.status;
  const statusCfg = STATUS_CONFIG[effectiveStatus] ?? STATUS_CONFIG.pending;

  const revoke = useMutation({
    mutationFn: () => apiFetch(`invitations/${inv.id}/revoke`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["invitations"] }),
  });

  const typeLabel = INVITATION_TYPES.find((t) => t.value === inv.invitation_type)?.label ?? inv.invitation_type;

  return (
    <div className="rounded-lg border bg-card">
      <div
        className="flex items-start gap-3 p-4 cursor-pointer"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm">{typeLabel}</span>
            <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border ${statusCfg.className}`}>
              {statusCfg.icon}
              {statusCfg.label}
            </span>
            {inv.role && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                {inv.role.replace(/_/g, " ")}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground flex-wrap">
            <span className="flex items-center gap-1">
              <Users className="h-3 w-3" />
              {inv.use_count}/{inv.max_uses} uses
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {isExpired ? "Expired" : `Expires ${expires.toLocaleDateString()}`}
            </span>
            {inv.email_restriction && (
              <span className="flex items-center gap-1">
                <Mail className="h-3 w-3" />
                {inv.email_restriction}
              </span>
            )}
            {inv.domain_restriction && (
              <span className="flex items-center gap-1">
                <Globe className="h-3 w-3" />
                @{inv.domain_restriction}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {canRevoke && inv.status === "pending" && !isExpired && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (confirm("Revoke this invitation? This cannot be undone.")) revoke.mutate();
              }}
              disabled={revoke.isPending}
              className="p-1.5 rounded-md text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
              title="Revoke invitation"
            >
              <XCircle className="h-4 w-4" />
            </button>
          )}
          {expanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </div>
      </div>
      {expanded && (
        <div className="border-t px-4 py-3 text-xs text-muted-foreground space-y-1 bg-muted/20">
          <div><span className="font-medium text-foreground">ID:</span> <span className="font-mono">{inv.id}</span></div>
          {inv.institution_id && <div><span className="font-medium text-foreground">Institution:</span> <span className="font-mono">{inv.institution_id}</span></div>}
          <div><span className="font-medium text-foreground">Created:</span> {new Date(inv.created_at).toLocaleString()}</div>
          <div><span className="font-medium text-foreground">Email verification:</span> {inv.requires_email_verification ? "Required" : "Not required"}</div>
          {inv.notes && <div><span className="font-medium text-foreground">Notes:</span> {inv.notes}</div>}
          {revoke.error && (
            <p className="text-red-600">{(revoke.error as Error).message}</p>
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

export default function InvitationsPage() {
  const user = useAuthStore((s) => s.user);
  const [showCreate, setShowCreate] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("");

  const { data: invitations = [], isLoading, error } = useQuery<Invitation[]>({
    queryKey: ["invitations", statusFilter],
    queryFn: () => {
      const qs = statusFilter ? `?status=${statusFilter}` : "";
      return apiFetch(`invitations${qs}`);
    },
  });

  const canCreate = user?.role === "system_admin" || user?.role === "institution_admin";
  const canRevoke = canCreate;

  return (
    <RoleGuard roles={ALLOWED_ROLES}>
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Invitations</h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Create and manage secure one-time registration tokens
            </p>
          </div>
          {canCreate && (
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 rounded-lg bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              <Plus className="h-4 w-4" />
              Create Invitation
            </button>
          )}
        </div>

        {/* Filter bar */}
        <div className="flex gap-2 mb-4 flex-wrap">
          {[
            { value: "", label: "All" },
            { value: "pending", label: "Active" },
            { value: "consumed", label: "Used" },
            { value: "revoked", label: "Revoked" },
          ].map((f) => (
            <button
              key={f.value}
              onClick={() => setStatusFilter(f.value)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                statusFilter === f.value
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Security notice */}
        <div className="mb-5 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 p-3 text-sm text-amber-800 dark:text-amber-300 flex gap-2">
          <Shield className="h-4 w-4 mt-0.5 shrink-0" />
          <div>
            <span className="font-medium">Token security: </span>
            Invitation tokens are shown only once at creation and are never retrievable afterward. Share tokens securely.
          </div>
        </div>

        {/* List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12 text-muted-foreground">
            <RefreshCw className="h-5 w-5 animate-spin mr-2" />
            Loading invitations…
          </div>
        ) : error ? (
          <div className="rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-200 p-4 text-sm text-red-700">
            {(error as Error).message}
          </div>
        ) : invitations.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <Shield className="h-10 w-10 mx-auto mb-3 opacity-30" />
            <p className="font-medium">No invitations found</p>
            <p className="text-sm mt-1">
              {statusFilter ? `No ${statusFilter} invitations` : "Create your first invitation to onboard users"}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {invitations.map((inv) => (
              <InvitationRow key={inv.id} inv={inv} canRevoke={canRevoke} />
            ))}
          </div>
        )}
      </div>

      {showCreate && (
        <CreateInvitationDialog
          onClose={() => setShowCreate(false)}
          userRole={(user?.role as UserRole) ?? "institution_admin"}
          institutionId={user?.institution_id ?? null}
        />
      )}
    </RoleGuard>
  );
}
