"use client";

import { useInstitutions } from "@/hooks/useInstitutions";

interface Props {
  /** Currently selected institution id, or undefined for "all" */
  value: string | undefined;
  onChange: (id: string | undefined) => void;
}

/**
 * Institution filter dropdown — only renders for System Admin.
 * Shows active pilot institutions only (never archived demo institutions).
 * Callers are responsible for hiding this component for non-admin users.
 */
export function InstitutionSelect({ value, onChange }: Props) {
  const { data: institutions } = useInstitutions();

  return (
    <select
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value || undefined)}
      className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
      aria-label="Filter by institution"
    >
      <option value="">All Institutions</option>
      {institutions?.map((inst) => (
        <option key={inst.id} value={inst.id}>
          {inst.code} — {inst.name}
        </option>
      ))}
    </select>
  );
}
