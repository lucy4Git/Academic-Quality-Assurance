"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Layers, Plus, Search, MoreHorizontal, Pencil, Trash2, Eye } from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
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
import { useProgrammes, useDeleteProgramme } from "@/hooks/useProgrammes";
import { useDepartments } from "@/hooks/useDepartments";
import { useFaculties } from "@/hooks/useFaculties";
import { useRole } from "@/hooks/useRole";
import { InstitutionSelect } from "@/components/common/InstitutionSelect";
import { PROGRAMME_LEVEL_LABELS } from "@/types";
import type { Programme } from "@/types";

const LEVEL_BADGE: Record<string, string> = {
  undergraduate: "bg-blue-50 text-blue-700 border-blue-200",
  postgraduate:  "bg-purple-50 text-purple-700 border-purple-200",
  doctoral:      "bg-amber-50 text-amber-700 border-amber-200",
};

function TableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 rounded-lg border border-border">
          <Skeleton className="h-9 w-9 rounded-lg flex-shrink-0" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-52" />
            <Skeleton className="h-3 w-32" />
          </div>
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-5 w-24 rounded-full" />
          <Skeleton className="h-7 w-7 rounded" />
        </div>
      ))}
    </div>
  );
}

export function ProgrammesList() {
  const router = useRouter();
  const { isSysAdmin, isQAOfficer, isHOD } = useRole();
  const { data: programmes, isLoading, isError, refetch } = useProgrammes();
  const { data: departments } = useDepartments();
  const { data: faculties } = useFaculties();
  const deleteMutation = useDeleteProgramme();

  const [search, setSearch] = useState("");
  const [institutionFilter, setInstitutionFilter] = useState<string | undefined>(undefined);
  const [deleteTarget, setDeleteTarget] = useState<Programme | null>(null);

  // dept_id → { name, institution_id } via faculty chain
  const deptMap = useMemo(() => {
    const facMap = new Map<string, string>(); // faculty_id → institution_id
    faculties?.forEach((f) => facMap.set(f.id, f.institution_id));
    const m = new Map<string, { name: string; institution_id: string }>();
    departments?.forEach((d) =>
      m.set(d.id, {
        name: d.name,
        institution_id: facMap.get(d.faculty_id) ?? "",
      })
    );
    return m;
  }, [departments, faculties]);

  const filtered = useMemo(() => {
    if (!programmes) return [];
    let list = programmes;
    if (institutionFilter) {
      list = list.filter(
        (p) => deptMap.get(p.department_id)?.institution_id === institutionFilter
      );
    }
    const q = search.trim().toLowerCase();
    if (!q) return list;
    return list.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.code.toLowerCase().includes(q) ||
        (deptMap.get(p.department_id)?.name ?? "").toLowerCase().includes(q)
    );
  }, [programmes, search, institutionFilter, deptMap]);

  const canCreate = isSysAdmin || isQAOfficer || isHOD;
  const canDelete = isSysAdmin || isQAOfficer;

  async function handleDelete() {
    if (!deleteTarget) return;
    await deleteMutation.mutateAsync(deleteTarget.id);
    setDeleteTarget(null);
  }

  return (
    <>
      <PageHeader
        title="Programmes"
        subtitle={programmes ? `${programmes.length} programme${programmes.length !== 1 ? "s" : ""}` : undefined}
        actions={
          canCreate ? (
            <Link href="/programmes/new" className={cn(buttonVariants({ variant: "default", size: "sm" }))}>
              <Plus className="mr-1.5 h-4 w-4" />
              Add Programme
            </Link>
          ) : undefined
        }
      />

      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Search by name, code or department…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
            aria-label="Search programmes"
          />
        </div>
        {isSysAdmin && (
          <InstitutionSelect value={institutionFilter} onChange={setInstitutionFilter} />
        )}
      </div>

      {isLoading && <TableSkeleton />}
      {isError && (
        <ErrorState message="Failed to load programmes." onRetry={refetch} />
      )}
      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState
          icon={Layers}
          title={search ? "No programmes match your search" : "No programmes yet"}
          description={search ? "Try a different term." : "Add your first programme to get started."}
          action={
            !search && canCreate ? (
              <Link href="/programmes/new" className={cn(buttonVariants({ variant: "default", size: "sm" }))}>
                <Plus className="mr-1.5 h-4 w-4" />
                Add Programme
              </Link>
            ) : undefined
          }
        />
      )}

      {!isLoading && !isError && filtered.length > 0 && (
        <div className="space-y-2">
          {filtered.map((prog) => (
            <div
              key={prog.id}
              className="flex items-center gap-4 p-4 rounded-lg border border-border bg-card hover:bg-accent/30 transition-colors group"
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Layers className="h-5 w-5 text-primary" />
              </div>

              <div className="flex-1 min-w-0">
                <button
                  onClick={() => router.push(`/programmes/${prog.id}`)}
                  className="text-sm font-medium text-foreground hover:text-primary transition-colors text-left truncate block w-full"
                >
                  {prog.name}
                </button>
                <p className="text-xs text-muted-foreground mt-0.5 truncate">
                  {deptMap.get(prog.department_id)?.name ?? "—"}
                </p>
              </div>

              <Badge variant="secondary" className="font-mono text-xs flex-shrink-0">
                {prog.code}
              </Badge>

              <span
                className={cn(
                  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold flex-shrink-0 hidden sm:inline-flex",
                  LEVEL_BADGE[prog.level] ?? "text-slate-600 bg-slate-50 border-slate-200"
                )}
              >
                {PROGRAMME_LEVEL_LABELS[prog.level]}
              </span>

              <span className="text-xs text-muted-foreground flex-shrink-0 hidden md:block w-24 text-right">
                {formatDate(prog.created_at)}
              </span>

              <DropdownMenu>
                <DropdownMenuTrigger
                  className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-muted transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                  aria-label={`Actions for ${prog.name}`}
                >
                  <MoreHorizontal className="h-4 w-4" />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-40">
                  <DropdownMenuItem onClick={() => router.push(`/programmes/${prog.id}`)}>
                    <Eye className="mr-2 h-4 w-4" /> View Details
                  </DropdownMenuItem>
                  {canCreate && (
                    <DropdownMenuItem onClick={() => router.push(`/programmes/${prog.id}/edit`)}>
                      <Pencil className="mr-2 h-4 w-4" /> Edit
                    </DropdownMenuItem>
                  )}
                  {canDelete && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => setDeleteTarget(prog)}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="mr-2 h-4 w-4" /> Delete
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Programme"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This will permanently remove all modules and audit data under this programme. This cannot be undone.`}
        confirmLabel="Delete Programme"
        isPending={deleteMutation.isPending}
        onConfirm={handleDelete}
      />
    </>
  );
}
