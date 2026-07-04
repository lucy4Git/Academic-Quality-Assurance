"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Building2,
  Plus,
  Search,
  MoreHorizontal,
  Pencil,
  Trash2,
  Eye,
} from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { ComplianceBar } from "@/components/common/StatusBadge";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { buttonVariants } from "@/components/ui/button";
import { cn, formatDate } from "@/lib/utils";
import { useInstitutions, useDeleteInstitution } from "@/hooks/useInstitutions";
import { useRole } from "@/hooks/useRole";
import { InstitutionTypeBadge } from "@/components/institution/InstitutionTypeBadge";
import type { Institution } from "@/types";

// ── Skeleton row shown while fetching ─────────────────────────────────────────
function TableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 p-4 rounded-lg border border-border"
        >
          <Skeleton className="h-9 w-9 rounded-lg flex-shrink-0" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-3 w-32" />
          </div>
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-7 w-7 rounded" />
        </div>
      ))}
    </div>
  );
}

export function InstitutionsList() {
  const router = useRouter();
  const { isSysAdmin } = useRole();
  const { data: institutions, isLoading, isError, refetch } = useInstitutions(isSysAdmin);
  const deleteMutation = useDeleteInstitution();

  const [search, setSearch] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Institution | null>(null);

  const filtered = useMemo(() => {
    if (!institutions) return [];
    const q = search.trim().toLowerCase();
    if (!q) return institutions;
    return institutions.filter(
      (i) =>
        i.name.toLowerCase().includes(q) ||
        i.code.toLowerCase().includes(q) ||
        (i.country ?? "").toLowerCase().includes(q)
    );
  }, [institutions, search]);

  const activePilot = useMemo(
    () => filtered.filter((i) => i.is_active),
    [filtered]
  );
  const archivedDemo = useMemo(
    () => filtered.filter((i) => !i.is_active),
    [filtered]
  );

  async function handleDelete() {
    if (!deleteTarget) return;
    await deleteMutation.mutateAsync(deleteTarget.id);
    setDeleteTarget(null);
  }

  return (
    <>
      <PageHeader
        title="Institutions"
        subtitle={
          institutions
            ? `${institutions.length} institution${institutions.length !== 1 ? "s" : ""} registered`
            : undefined
        }
        actions={
          <RoleGuard roles={["system_admin"]}>
            <Link
              href="/institutions/new"
              className={cn(buttonVariants({ variant: "default", size: "sm" }))}
            >
              <Plus className="mr-1.5 h-4 w-4" />
              Add Institution
            </Link>
          </RoleGuard>
        }
      />

      {/* Search toolbar */}
      <div className="relative mb-4 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          placeholder="Search by name or code…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
          aria-label="Search institutions"
        />
      </div>

      {/* Loading */}
      {isLoading && <TableSkeleton />}

      {/* Error */}
      {isError && (
        <ErrorState
          message="Failed to load institutions. Check your connection and try again."
          onRetry={refetch}
        />
      )}

      {/* Empty state */}
      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState
          icon={Building2}
          title={
            search
              ? "No institutions match your search"
              : "No institutions yet"
          }
          description={
            search
              ? "Try a different name or code."
              : "Add your first institution to get started."
          }
          action={
            !search && isSysAdmin ? (
              <Link
                href="/institutions/new"
                className={cn(buttonVariants({ variant: "default", size: "sm" }))}
              >
                <Plus className="mr-1.5 h-4 w-4" />
                Add Institution
              </Link>
            ) : undefined
          }
        />
      )}

      {/* Institution cards */}
      {!isLoading && !isError && filtered.length > 0 && (
        isSysAdmin ? (
          <div className="space-y-6">
            {/* Active pilot institutions */}
            {activePilot.length > 0 && (
              <section>
                <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-2">
                  Active Pilot Institutions
                </h2>
                <div className="space-y-2">
                  {activePilot.map((institution) => (
                    <InstitutionRow
                      key={institution.id}
                      institution={institution}
                      isSysAdmin={isSysAdmin}
                      onView={() => router.push(`/institutions/${institution.id}`)}
                      onEdit={() => router.push(`/institutions/${institution.id}/edit`)}
                      onDelete={() => setDeleteTarget(institution)}
                    />
                  ))}
                </div>
              </section>
            )}

            {/* Archived demo institutions */}
            {archivedDemo.length > 0 && (
              <section>
                <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-2">
                  Archived Demo Institutions
                </h2>
                <div className="space-y-2">
                  {archivedDemo.map((institution) => (
                    <InstitutionRow
                      key={institution.id}
                      institution={institution}
                      isSysAdmin={isSysAdmin}
                      onView={() => router.push(`/institutions/${institution.id}`)}
                      onEdit={() => router.push(`/institutions/${institution.id}/edit`)}
                      onDelete={() => setDeleteTarget(institution)}
                    />
                  ))}
                </div>
              </section>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map((institution) => (
              <InstitutionRow
                key={institution.id}
                institution={institution}
                isSysAdmin={isSysAdmin}
                onView={() => router.push(`/institutions/${institution.id}`)}
                onEdit={() => router.push(`/institutions/${institution.id}/edit`)}
                onDelete={() => setDeleteTarget(institution)}
              />
            ))}
          </div>
        )
      )}

      {/* Delete confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Institution"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This will permanently remove all faculties, departments, programmes, modules, files, and audit data associated with this institution. This action cannot be undone.`}
        confirmLabel="Delete Institution"
        isPending={deleteMutation.isPending}
        onConfirm={handleDelete}
      />
    </>
  );
}

// ── Single institution row ─────────────────────────────────────────────────────
interface InstitutionRowProps {
  institution: Institution;
  isSysAdmin: boolean;
  onView: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

function InstitutionRow({
  institution,
  isSysAdmin,
  onView,
  onEdit,
  onDelete,
}: InstitutionRowProps) {
  return (
    <div className={cn(
      "flex items-center gap-4 p-4 rounded-lg border border-border bg-card hover:bg-accent/30 transition-colors group",
      !institution.is_active && "opacity-60"
    )}>
      {/* Institution avatar */}
      <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
        {institution.logo_url ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={institution.logo_url}
            alt={institution.name}
            className="w-8 h-8 object-contain rounded"
          />
        ) : (
          <Building2 className="h-5 w-5 text-primary" />
        )}
      </div>

      {/* Name + code */}
      <div className="flex-1 min-w-0">
        <button
          onClick={onView}
          className="text-sm font-medium text-foreground hover:text-primary transition-colors text-left truncate block w-full"
        >
          {institution.name}
        </button>
        <p className="text-xs text-muted-foreground mt-0.5">
          {institution.country ?? "—"}
        </p>
      </div>

      {/* Code badge + type badge */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <Badge variant="secondary" className="font-mono text-xs">
          {institution.code}
        </Badge>
        <InstitutionTypeBadge
          institutionType={institution.institution_type}
          isActive={institution.is_active}
          size="xs"
        />
      </div>

      {/* Compliance placeholder (Phase 3 — dashboard endpoint) */}
      <div className="w-32 flex-shrink-0 hidden sm:block">
        <ComplianceBar score={null} showLabel={false} />
      </div>

      {/* Created date */}
      <span className="text-xs text-muted-foreground flex-shrink-0 hidden md:block w-24 text-right">
        {formatDate(institution.created_at)}
      </span>

      {/* Row actions */}
      <DropdownMenu>
        <DropdownMenuTrigger
          className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-muted transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
          aria-label={`Actions for ${institution.name}`}
        >
          <MoreHorizontal className="h-4 w-4" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-40">
          <DropdownMenuItem onClick={onView}>
            <Eye className="mr-2 h-4 w-4" />
            View Details
          </DropdownMenuItem>
          {isSysAdmin && (
            <>
              <DropdownMenuItem onClick={onEdit}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={onDelete}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
