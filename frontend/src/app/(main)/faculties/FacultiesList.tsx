"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  GraduationCap,
  Plus,
  Search,
  MoreHorizontal,
  Pencil,
  Trash2,
  Eye,
  Building2,
  MapPin,
} from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { buttonVariants } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn, formatDate } from "@/lib/utils";
import { useFaculties, useDeleteFaculty } from "@/hooks/useFaculties";
import { useInstitutions } from "@/hooks/useInstitutions";
import { useRole } from "@/hooks/useRole";
import { useAuthStore } from "@/store/auth.store";
import { InstitutionSelect } from "@/components/common/InstitutionSelect";
import type { Faculty } from "@/types";

function TableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 p-4 rounded-lg border border-border"
        >
          <Skeleton className="h-9 w-9 rounded-lg flex-shrink-0" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-52" />
            <Skeleton className="h-3 w-32" />
          </div>
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-7 w-7 rounded" />
        </div>
      ))}
    </div>
  );
}

export function FacultiesList() {
  const router = useRouter();
  const { isSysAdmin, isQAOfficer } = useRole();
  const user = useAuthStore((s) => s.user);

  const [institutionFilter, setInstitutionFilter] = useState<string | undefined>(undefined);

  const { data: faculties, isLoading, isError, refetch } = useFaculties(institutionFilter);
  const { data: institutions } = useInstitutions();
  const deleteMutation = useDeleteFaculty();

  const [search, setSearch] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Faculty | null>(null);

  // Build institution lookup map
  const institutionMap = useMemo(() => {
    const m = new Map<string, string>();
    institutions?.forEach((i) => m.set(i.id, i.name));
    return m;
  }, [institutions]);

  const filtered = useMemo(() => {
    if (!faculties) return [];
    const q = search.trim().toLowerCase();
    if (!q) return faculties;
    return faculties.filter(
      (f) =>
        f.name.toLowerCase().includes(q) ||
        f.code.toLowerCase().includes(q) ||
        (f.campus ?? "").toLowerCase().includes(q) ||
        (institutionMap.get(f.institution_id) ?? "")
          .toLowerCase()
          .includes(q)
    );
  }, [faculties, search, institutionMap]);

  async function handleDelete() {
    if (!deleteTarget) return;
    await deleteMutation.mutateAsync(deleteTarget.id);
    setDeleteTarget(null);
  }

  // Determine who can create (SA or QA Officer per backend)
  const canCreate = isSysAdmin || isQAOfficer;
  // Delete is Dean+ on backend — SA and QA Officer can delete
  const canDelete = isSysAdmin || isQAOfficer;

  return (
    <>
      <PageHeader
        title="Faculties"
        subtitle={
          faculties
            ? `${faculties.length} ${faculties.length === 1 ? "faculty" : "faculties"}`
            : undefined
        }
        actions={
          canCreate ? (
            <Link
              href="/faculties/new"
              className={cn(buttonVariants({ variant: "default", size: "sm" }))}
            >
              <Plus className="mr-1.5 h-4 w-4" />
              Add Faculty
            </Link>
          ) : undefined
        }
      />

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Search by name, code or campus…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
            aria-label="Search faculties"
          />
        </div>
        {isSysAdmin && (
          <InstitutionSelect value={institutionFilter} onChange={setInstitutionFilter} />
        )}
      </div>

      {isLoading && <TableSkeleton />}

      {isError && (
        <ErrorState
          message="Failed to load faculties. Check your connection and try again."
          onRetry={refetch}
        />
      )}

      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState
          icon={GraduationCap}
          title={search ? "No faculties match your search" : "No faculties yet"}
          description={
            search
              ? "Try a different name, code, or campus."
              : "Add your first faculty to get started."
          }
          action={
            !search && canCreate ? (
              <Link
                href="/faculties/new"
                className={cn(
                  buttonVariants({ variant: "default", size: "sm" })
                )}
              >
                <Plus className="mr-1.5 h-4 w-4" />
                Add Faculty
              </Link>
            ) : undefined
          }
        />
      )}

      {!isLoading && !isError && filtered.length > 0 && (
        <div className="space-y-2">
          {filtered.map((faculty) => (
            <FacultyRow
              key={faculty.id}
              faculty={faculty}
              institutionName={institutionMap.get(faculty.institution_id)}
              showInstitution={isSysAdmin}
              canEdit={canCreate}
              canDelete={canDelete}
              onView={() => router.push(`/faculties/${faculty.id}`)}
              onEdit={() => router.push(`/faculties/${faculty.id}/edit`)}
              onDelete={() => setDeleteTarget(faculty)}
            />
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Faculty"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This will permanently remove all departments, programmes, modules, files, and audit data under this faculty. This action cannot be undone.`}
        confirmLabel="Delete Faculty"
        isPending={deleteMutation.isPending}
        onConfirm={handleDelete}
      />
    </>
  );
}

interface FacultyRowProps {
  faculty: Faculty;
  institutionName?: string;
  showInstitution: boolean;
  canEdit: boolean;
  canDelete: boolean;
  onView: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

function FacultyRow({
  faculty,
  institutionName,
  showInstitution,
  canEdit,
  canDelete,
  onView,
  onEdit,
  onDelete,
}: FacultyRowProps) {
  return (
    <div className="flex items-center gap-4 p-4 rounded-lg border border-border bg-card hover:bg-accent/30 transition-colors group">
      {/* Icon */}
      <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
        <GraduationCap className="h-5 w-5 text-primary" />
      </div>

      {/* Name + institution */}
      <div className="flex-1 min-w-0">
        <button
          onClick={onView}
          className="text-sm font-medium text-foreground hover:text-primary transition-colors text-left truncate block w-full"
        >
          {faculty.name}
        </button>
        {showInstitution && institutionName && (
          <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
            <Building2 className="h-3 w-3 inline-block" />
            {institutionName}
          </p>
        )}
      </div>

      {/* Code badge */}
      <Badge variant="secondary" className="font-mono text-xs flex-shrink-0">
        {faculty.code}
      </Badge>

      {/* Campus badge */}
      {faculty.campus ? (
        <Badge
          variant="outline"
          className="text-xs flex-shrink-0 hidden sm:inline-flex gap-1"
        >
          <MapPin className="h-3 w-3" />
          {faculty.campus}
        </Badge>
      ) : (
        <span className="text-xs text-muted-foreground/50 hidden sm:block w-24">
          No campus
        </span>
      )}

      {/* Created date */}
      <span className="text-xs text-muted-foreground flex-shrink-0 hidden md:block w-24 text-right">
        {formatDate(faculty.created_at)}
      </span>

      {/* Row actions */}
      <DropdownMenu>
        <DropdownMenuTrigger
          className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-muted transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
          aria-label={`Actions for ${faculty.name}`}
        >
          <MoreHorizontal className="h-4 w-4" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-40">
          <DropdownMenuItem onClick={onView}>
            <Eye className="mr-2 h-4 w-4" />
            View Details
          </DropdownMenuItem>
          {canEdit && (
            <DropdownMenuItem onClick={onEdit}>
              <Pencil className="mr-2 h-4 w-4" />
              Edit
            </DropdownMenuItem>
          )}
          {canDelete && (
            <>
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
