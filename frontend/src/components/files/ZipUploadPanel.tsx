"use client";

import { useState, useRef, useCallback } from "react";
import {
  useZipUpload,
  useConfirmZipMapping,
  type ClassifiedFile,
  type ZipManifest,
} from "@/hooks/useZipUpload";

const FILE_CATEGORY_OPTIONS = [
  "assessment_plan",
  "internal_moderation",
  "external_moderation",
  "moderation_evidence",
  "attendance_register",
  "study_guide",
  "sample_scripts",
  "marking_rubric",
  "results_sheet",
  "examiner_report",
  "quality_review_report",
  "programme_specification",
  "module_outline",
  "student_feedback",
  "learning_outcomes",
  "evidence",
];

interface FileCategoryRow {
  file: ClassifiedFile;
  selectedCategory: string;
}

function CategorySelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-md border border-gray-300 bg-white px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="">-- unclassified --</option>
      {FILE_CATEGORY_OPTIONS.map((c) => (
        <option key={c} value={c}>
          {c.replace(/_/g, " ")}
        </option>
      ))}
    </select>
  );
}

function DropZone({
  onFile,
  isDragging,
  setIsDragging,
}: {
  onFile: (f: File) => void;
  isDragging: boolean;
  setIsDragging: (v: boolean) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const f = e.dataTransfer.files[0];
      if (f && f.name.endsWith(".zip")) onFile(f);
    },
    [onFile, setIsDragging]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 transition-colors ${
        isDragging
          ? "border-blue-400 bg-blue-50"
          : "border-gray-300 bg-gray-50 hover:border-blue-300 hover:bg-blue-50/50"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".zip"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
        }}
      />
      <svg
        className={`mb-3 h-10 w-10 ${isDragging ? "text-blue-400" : "text-gray-400"}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
        />
      </svg>
      <p className="text-sm font-medium text-gray-700">
        Drag &amp; drop a ZIP file here, or click to browse
      </p>
      <p className="mt-1 text-xs text-gray-400">ZIP archives only · Max 50 MB</p>
    </div>
  );
}

interface ZipUploadPanelProps {
  moduleId: string;
  onSuccess?: () => void;
}

export function ZipUploadPanel({ moduleId, onSuccess }: ZipUploadPanelProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [manifest, setManifest] = useState<ZipManifest | null>(null);
  const [rows, setRows] = useState<FileCategoryRow[]>([]);
  const [successCount, setSuccessCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const zipUpload = useZipUpload();
  const confirmMapping = useConfirmZipMapping();

  const handleFile = useCallback(
    async (file: File) => {
      setManifest(null);
      setRows([]);
      setSuccessCount(null);
      setError(null);

      try {
        const result = await zipUpload.mutateAsync(file);
        setManifest(result);
        const allFiles = [...result.classified, ...result.unclassified];
        setRows(
          allFiles.map((f) => ({
            file: f,
            selectedCategory: f.category ?? "",
          }))
        );
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Upload failed. Please try again.");
      }
    },
    [zipUpload]
  );

  const handleConfirm = async () => {
    const files = rows
      .filter((r) => r.selectedCategory)
      .map((r) => ({ path_in_zip: r.file.path_in_zip, category: r.selectedCategory }));

    if (files.length === 0) {
      setError("Please assign at least one file to a category before confirming.");
      return;
    }

    setError(null);
    try {
      const result = await confirmMapping.mutateAsync({ module_id: moduleId, files });
      setSuccessCount(result.accepted);
      setManifest(null);
      setRows([]);
      onSuccess?.();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Confirmation failed. Please try again.");
    }
  };

  const handleReset = () => {
    setManifest(null);
    setRows([]);
    setSuccessCount(null);
    setError(null);
  };

  if (successCount !== null) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-green-200 bg-green-50 py-10 text-center">
        <p className="text-2xl font-bold text-green-700">{successCount}</p>
        <p className="mt-1 text-sm text-green-700 font-medium">
          {successCount === 1 ? "file" : "files"} queued for processing
        </p>
        <button
          onClick={handleReset}
          className="mt-4 rounded-lg border border-green-300 px-4 py-2 text-sm font-medium text-green-700 hover:bg-green-100"
        >
          Upload another ZIP
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {!manifest && !zipUpload.isPending && (
        <DropZone
          onFile={handleFile}
          isDragging={isDragging}
          setIsDragging={setIsDragging}
        />
      )}

      {zipUpload.isPending && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-gray-50 py-10">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          <p className="mt-3 text-sm text-gray-600">Analysing ZIP contents…</p>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {manifest && rows.length > 0 && (
        <div className="space-y-4">
          {/* Summary bar */}
          <div className="flex flex-wrap items-center gap-4 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm">
            <span className="font-medium text-blue-900">
              {manifest.total_files} files extracted
            </span>
            <span className="text-blue-700">{manifest.classified.length} auto-classified</span>
            {manifest.unclassified.length > 0 && (
              <span className="text-yellow-700">
                {manifest.unclassified.length} need manual category
              </span>
            )}
            {manifest.missing_required.length > 0 && (
              <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                Missing: {manifest.missing_required.map((c) => c.replace(/_/g, " ")).join(", ")}
              </span>
            )}
          </div>

          {/* File list */}
          <div className="overflow-hidden rounded-xl border border-gray-200">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                  <th className="px-4 py-3">File</th>
                  <th className="px-4 py-3">Size</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rows.map((row, i) => (
                  <tr key={row.file.path_in_zip} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-800 max-w-xs truncate">
                      {row.file.filename}
                    </td>
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                      {(row.file.size_bytes / 1024).toFixed(1)} KB
                    </td>
                    <td className="px-4 py-3">
                      <CategorySelect
                        value={row.selectedCategory}
                        onChange={(v) =>
                          setRows((prev) =>
                            prev.map((r, idx) =>
                              idx === i ? { ...r, selectedCategory: v } : r
                            )
                          )
                        }
                      />
                    </td>
                    <td className="px-4 py-3">
                      {row.file.confidence > 0 ? (
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                            row.file.confidence >= 0.8
                              ? "bg-green-100 text-green-700"
                              : row.file.confidence >= 0.5
                              ? "bg-yellow-100 text-yellow-700"
                              : "bg-gray-100 text-gray-500"
                          }`}
                        >
                          {Math.round(row.file.confidence * 100)}%
                        </span>
                      ) : (
                        <span className="text-gray-400 text-xs">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <button
              onClick={handleReset}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
            >
              Start over
            </button>
            <button
              onClick={handleConfirm}
              disabled={confirmMapping.isPending || rows.every((r) => !r.selectedCategory)}
              className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {confirmMapping.isPending
                ? "Submitting…"
                : `Confirm ${rows.filter((r) => r.selectedCategory).length} files`}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
