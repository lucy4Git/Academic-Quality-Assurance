"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  BookOpen,
  Plus,
  Search,
  MoreHorizontal,
  Pencil,
  Trash2,
  Eye,
  GraduationCap,
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
import { useDepartments, useDeleteDepartment } from "@/hooks/useDepartments";
import { useFaculties } from "@/hooks/useFaculties";
import { useRole } from "@/hooks/useRole";
import { InstitutionSelect } from "@/components/common/InstitutionSelect";
import type { Department } from "@/types";

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
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-7 w-7 rounded" />
        </div>
      ))}
    </div>
  );
}

export function DepartmentsList() {
  const router = useRouter();
  const { isSysAdmin, isQAOfficer, isDean, isHOD } = useRole();
  const { data: departments, isLoading, isError, refetch } = useDepartments();
  const { data: faculties } = useFaculties();
  const deleteMutation = useDeleteDepartment();

  const [search, setSearch] = useState("");
  const [institutionFilter, setInstitutionFilter] = useState<string | undefined>(undefined);
  const [deleteTarget, setDeleteTarget] = useState<Department | null>(null);

  // faculty_id → { label, institution_id }
  const facultyMap = useMemo(() => {
    const m = new Map<string, { label: string; institution_id: string }>();
    faculties?.forEach((f) =>
      m.set(f.id, { label: `${f.name} (${f.code})`, institution_id: f.institution_id })
    );
    return m;
  }, [faculties]);

  const filtered = useMemo(() => {
    if (!departments) return [];
    let list = departments;
    if (institutionFilter) {
      list = list.filter(
        (d) => facultyMap.get(d.faculty_id)?.institution_id === institutionFilter
      );
    }
    const q = search.trim().toLowerCase();
    if (!q) return list;
    return list.filter(
      (d) =>
        d.name.toLowerCase().includes(q) ||
        d.code.toLowerCase().includes(q) ||
        (facultyMap.get(d.faculty_id)?.label ?? "").toLowerCase().includes(q)
    );
  }, [departments, search, institutionFilter, facultyMap]);

  async function handleDelete() {
    if (!deleteTarget) return;
    await deleteMutation.mutateAsync(deleteTarget.id);
    setDeleteTarget(null);
  }

  // Create: DeanRequired (SA, QA, Dean)
  const canCreate = isDean;
  // Delete: HODRequired (SA, QA, Dean, HOD) — same as update
  const canDelete = isHOD;

  return (
    <>
      <PageHeader
        title="Departments"
        subtitle={
          departments
            ? `${departments.length} ${departments.length === 1 ? "department" : "departments"}`
            : undefined
        }
        actions={
          canCreate ? (
            <Link
              href="/departments/new"
              className={cn(buttonVariants({ variant: "default", size: "sm" }))}
            >
              <Plus className="mr-1.5 h-4 w-4" />
              Add Department
            </Link>
          ) : undefined
        }
      />

      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="relative flex-1 min-w-48 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          placeholder="Search by name, code or faculty…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
          aria-label="Search departments"
        />
        </div>
        {isSysAdmin && (
          <InstitutionSelect value={institutionFilter} onChange={setInstitutionFilter} />
        )}
      </div>

      {isLoading && <TableSkeleton />}

      {isError && (
        <ErrorState
          message="Failed to load departments. Check your connection and try again."
          onRetry={refetch}
        />
      )}

      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState
          icon={BookOpen}
          title={search ? "No departments match your search" : "No departments yet"}
          description={
            search
              ? "Try a different name, code, or faculty."
              : "Add your first department to get started."
          }
          action={
            !search && canCreate ? (
              <Link
                href="/departments/new"
                className={cn(buttonVariants({ variant: "default", size: "sm" }))}
              >
                <Plus className="mr-1.5 h-4 w-4" />
                Add Department
              </Link>
            ) : undefined
          }
        />
      )}

      {!isLoading && !isError && filtered.length > 0 && (
        <div className="space-y-2">
          {filtered.map((dept) => (
            <DepartmentRow
              key={dept.id}
              department={dept}
              facultyLabel={facultyMap.get(dept.faculty_id)?.label}
              showFaculty={isDean}
              canEdit={isHOD}
              canDelete={canDelete}
              onView={() => router.push(`/departments/${dept.id}`)}
              onEdit={() => router.push(`/departments/${dept.id}/edit`)}
              onDelete={() => setDeleteTarget(dept)}
            />
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Department"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This will permanently remove all programmes, modules, files, and audit data under this department. This action cannot be undone.`}
        confirmLabel="Delete Department"
        isPending={deleteMutation.isPending}
        onConfirm={handleDelete}
      />
    </>
  );
}

interface DeptRowProps {
  department: Department;
  facultyLabel?: string;
  showFaculty: boolean;
  canEdit: boolean;
  canDelete: boolean;
  onView: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

function DepartmentRow({
  department,
  facultyLabel,
  showFaculty,
  canEdit,
  canDelete,
  onView,
  onEdit,
  onDelete,
}: DeptRowProps) {
  return (
    <div className="flex items-center gap-4 p-4 rounded-lg border border-border bg-card hover:bg-accent/30 transition-colors group">
      <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
        <BookOpen className="h-5 w-5 text-primary" />
      </div>

      <div className="flex-1 min-w-0">
        <button
          onClick={onView}
          className="text-sm font-medium text-foreground hover:text-primary transition-colors text-left truncate block w-full"
        >
          {department.name}
        </button>
        {showFaculty && facultyLabel && (
          <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
            <GraduationCap className="h-3 w-3 inline-block" />
            {facultyLabel}
          </p>
        )}
      </div>

      <Badge variant="secondary" className="font-mono text-xs flex-shrink-0">
        {department.code}
      </Badge>

      <span className="text-xs text-muted-foreground flex-shrink-0 hidden md:block w-24 text-right">
        {formatDate(department.created_at)}
      </span>

      <DropdownMenu>
        <DropdownMenuTrigger
          className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-muted transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
          aria-label={`Actions for ${department.name}`}
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
