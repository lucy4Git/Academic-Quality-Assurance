"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Boxes,
  Plus,
  Search,
  MoreHorizontal,
  Pencil,
  Trash2,
  Eye,
  Filter,
} from "lucide-react";

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
import { useModules, useDeleteModule } from "@/hooks/useModules";
import { useProgrammes } from "@/hooks/useProgrammes";
import { useDepartments } from "@/hooks/useDepartments";
import { useFaculties } from "@/hooks/useFaculties";
import { useRole } from "@/hooks/useRole";
import { InstitutionSelect } from "@/components/common/InstitutionSelect";
import type { Module } from "@/types";
import { SEMESTER_OPTIONS } from "@/types";

function TableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 rounded-lg border border-border">
          <Skeleton className="h-9 w-9 rounded-lg flex-shrink-0" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-56" />
            <Skeleton className="h-3 w-36" />
          </div>
          <Skeleton className="h-5 w-14 rounded-full" />
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-7 w-7 rounded" />
        </div>
      ))}
    </div>
  );
}

export function ModulesList() {
  const router = useRouter();
  const { isCoordinator, isSysAdmin, isQAOfficer } = useRole();
  const { data: modules, isLoading, isError, refetch } = useModules();
  const { data: programmes } = useProgrammes();
  const { data: departments } = useDepartments();
  const { data: faculties } = useFaculties();
  const deleteMutation = useDeleteModule();

  const [search, setSearch] = useState("");
  const [filterProg, setFilterProg] = useState("");
  const [filterYear, setFilterYear] = useState("");
  const [filterSem, setFilterSem] = useState("");
  const [institutionFilter, setInstitutionFilter] = useState<string | undefined>(undefined);
  const [deleteTarget, setDeleteTarget] = useState<Module | null>(null);

  // programme_id → { label, institution_id } via dept→faculty chain
  const progMap = useMemo(() => {
    const facMap = new Map<string, string>(); // faculty_id → institution_id
    faculties?.forEach((f) => facMap.set(f.id, f.institution_id));
    const deptInstMap = new Map<string, string>(); // dept_id → institution_id
    departments?.forEach((d) => deptInstMap.set(d.id, facMap.get(d.faculty_id) ?? ""));
    const m = new Map<string, { label: string; institution_id: string }>();
    programmes?.forEach((p) =>
      m.set(p.id, {
        label: `${p.name} (${p.code})`,
        institution_id: deptInstMap.get(p.department_id) ?? "",
      })
    );
    return m;
  }, [programmes, departments, faculties]);

  // Derive academic years from loaded modules
  const academicYears = useMemo(() => {
    const years = modules?.map((m) => m.academic_year) ?? [];
    return Array.from(new Set(years)).sort().reverse();
  }, [modules]);

  const filtered = useMemo(() => {
    if (!modules) return [];
    let list = modules;
    if (institutionFilter) {
      list = list.filter(
        (m) => progMap.get(m.programme_id)?.institution_id === institutionFilter
      );
    }
    if (filterProg) list = list.filter((m) => m.programme_id === filterProg);
    if (filterYear) list = list.filter((m) => m.academic_year === filterYear);
    if (filterSem) list = list.filter((m) => m.semester === filterSem);
    const q = search.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (m) =>
          m.name.toLowerCase().includes(q) ||
          m.code.toLowerCase().includes(q) ||
          (progMap.get(m.programme_id)?.label ?? "").toLowerCase().includes(q)
      );
    }
    return list;
  }, [modules, search, filterProg, filterYear, filterSem, institutionFilter, progMap]);

  const canCreate = isCoordinator;
  const canDelete = isSysAdmin || isQAOfficer || isCoordinator;

  async function handleDelete() {
    if (!deleteTarget) return;
    await deleteMutation.mutateAsync(deleteTarget.id);
    setDeleteTarget(null);
  }

  const cls = "flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm";

  return (
    <>
      <PageHeader
        title="Modules"
        subtitle={
          modules
            ? `${modules.length} module${modules.length !== 1 ? "s" : ""}`
            : undefined
        }
        actions={
          canCreate ? (
            <Link
              href="/modules/new"
              className={cn(buttonVariants({ variant: "default", size: "sm" }))}
            >
              <Plus className="mr-1.5 h-4 w-4" />
              Add Module
            </Link>
          ) : undefined
        }
      />

      {/* Toolbar: search + filters */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Search by name, code or programme…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
            aria-label="Search modules"
          />
        </div>

        <div className="flex items-center gap-1 text-muted-foreground flex-shrink-0">
          <Filter className="h-4 w-4" />
        </div>

        {isSysAdmin && (
          <InstitutionSelect value={institutionFilter} onChange={setInstitutionFilter} />
        )}

        {/* Programme filter */}
        <select
          value={filterProg}
          onChange={(e) => setFilterProg(e.target.value)}
          className={cls}
          aria-label="Filter by programme"
        >
          <option value="">All programmes</option>
          {programmes?.map((p) => (
            <option key={p.id} value={p.id}>{p.code} — {p.name}</option>
          ))}
        </select>

        {/* Academic year filter */}
        <select
          value={filterYear}
          onChange={(e) => setFilterYear(e.target.value)}
          className={cls}
          aria-label="Filter by academic year"
        >
          <option value="">All years</option>
          {academicYears.map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>

        {/* Semester filter */}
        <select
          value={filterSem}
          onChange={(e) => setFilterSem(e.target.value)}
          className={cls}
          aria-label="Filter by semester"
        >
          <option value="">All semesters</option>
          {SEMESTER_OPTIONS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {isLoading && <TableSkeleton />}
      {isError && (
        <ErrorState message="Failed to load modules." onRetry={refetch} />
      )}
      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState
          icon={Boxes}
          title={search || filterProg || filterYear || filterSem ? "No modules match your filters" : "No modules yet"}
          description={
            search || filterProg || filterYear || filterSem
              ? "Try adjusting your search or filters."
              : "Add your first module to get started."
          }
          action={
            !search && !filterProg && canCreate ? (
              <Link href="/modules/new" className={cn(buttonVariants({ variant: "default", size: "sm" }))}>
                <Plus className="mr-1.5 h-4 w-4" />
                Add Module
              </Link>
            ) : undefined
          }
        />
      )}

      {!isLoading && !isError && filtered.length > 0 && (
        <div className="space-y-2">
          {filtered.map((mod) => (
            <div
              key={mod.id}
              className="flex items-center gap-4 p-4 rounded-lg border border-border bg-card hover:bg-accent/30 transition-colors group"
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Boxes className="h-5 w-5 text-primary" />
              </div>

              <div className="flex-1 min-w-0">
                <button
                  onClick={() => router.push(`/modules/${mod.id}`)}
                  className="text-sm font-medium text-foreground hover:text-primary transition-colors text-left truncate block w-full"
                >
                  {mod.name}
                </button>
                <p className="text-xs text-muted-foreground mt-0.5 truncate">
                  {progMap.get(mod.programme_id)?.label ?? "—"}
                </p>
              </div>

              <Badge variant="secondary" className="font-mono text-xs flex-shrink-0">
                {mod.code}
              </Badge>

              <span className="text-xs text-muted-foreground flex-shrink-0 hidden sm:block">
                {mod.semester}
              </span>

              <Badge
                variant="outline"
                className="text-xs flex-shrink-0 hidden md:inline-flex font-mono"
              >
                {mod.academic_year}
              </Badge>

              <span className="text-xs text-muted-foreground flex-shrink-0 hidden lg:block w-8 text-right">
                {mod.credits}cr
              </span>

              <DropdownMenu>
                <DropdownMenuTrigger
                  className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-muted transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                  aria-label={`Actions for ${mod.name}`}
                >
                  <MoreHorizontal className="h-4 w-4" />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-40">
                  <DropdownMenuItem onClick={() => router.push(`/modules/${mod.id}`)}>
                    <Eye className="mr-2 h-4 w-4" /> View Details
                  </DropdownMenuItem>
                  {canCreate && (
                    <DropdownMenuItem onClick={() => router.push(`/modules/${mod.id}/edit`)}>
                      <Pencil className="mr-2 h-4 w-4" /> Edit
                    </DropdownMenuItem>
                  )}
                  {canDelete && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => setDeleteTarget(mod)}
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
        title="Delete Module"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This will permanently remove all evidence files and audit data. This cannot be undone.`}
        confirmLabel="Delete Module"
        isPending={deleteMutation.isPending}
        onConfirm={handleDelete}
      />
    </>
  );
}
