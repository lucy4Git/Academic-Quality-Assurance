"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api-client";

type ExportFormat = "csv" | "excel" | "pdf";

interface ExportState {
  loading: boolean;
  error: string | null;
}

const FORMAT_CONFIG: Record<ExportFormat, { label: string; mime: string; ext: string }> = {
  csv: { label: "CSV", mime: "text/csv", ext: "csv" },
  excel: {
    label: "Excel (.xlsx)",
    mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ext: "xlsx",
  },
  pdf: { label: "PDF (text)", mime: "text/plain", ext: "txt" },
};

function downloadBlob(data: ArrayBuffer, filename: string, mime: string) {
  const blob = new Blob([data], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function ReportsView() {
  const [state, setState] = useState<Record<ExportFormat, ExportState>>({
    csv: { loading: false, error: null },
    excel: { loading: false, error: null },
    pdf: { loading: false, error: null },
  });

  async function handleExport(format: ExportFormat) {
    setState((prev) => ({
      ...prev,
      [format]: { loading: true, error: null },
    }));

    try {
      const response = await apiClient.get(`/reporting/export/${format}`, {
        responseType: "arraybuffer",
      });
      const cfg = FORMAT_CONFIG[format];
      const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
      downloadBlob(response.data as ArrayBuffer, `aqaa_report_${ts}.${cfg.ext}`, cfg.mime);
      setState((prev) => ({ ...prev, [format]: { loading: false, error: null } }));
    } catch {
      setState((prev) => ({
        ...prev,
        [format]: { loading: false, error: "Export failed. Please try again." },
      }));
    }
  }

  return (
    <div className="space-y-8 p-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Export institutional QA data as structured reports
        </p>
      </div>

      <div className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
          Dashboard export
        </h2>
        <p className="text-sm text-gray-600">
          Download the current dashboard aggregate data (institutions, faculties, programmes,
          modules, audits, evidence files) in your preferred format.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
          {(["csv", "excel", "pdf"] as ExportFormat[]).map((format) => {
            const cfg = FORMAT_CONFIG[format];
            const { loading, error } = state[format];
            return (
              <div
                key={format}
                className="rounded-xl border border-gray-200 bg-white p-5 flex flex-col gap-3"
              >
                <div>
                  <p className="font-semibold text-gray-900">{cfg.label}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {format === "csv" && "UTF-8 with BOM — compatible with Excel"}
                    {format === "excel" && "Multi-sheet workbook with metadata"}
                    {format === "pdf" && "Plain-text placeholder (PDF rendering planned)"}
                  </p>
                </div>
                {error && (
                  <p className="text-xs text-red-600">{error}</p>
                )}
                <button
                  onClick={() => handleExport(format)}
                  disabled={loading}
                  className="mt-auto rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {loading ? "Exporting…" : `Download ${cfg.label}`}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
        <strong className="text-gray-700">Note:</strong> Reports are scoped to institutions
        visible to your role. System administrators see all active pilot institutions; other
        roles see only their own institution.
      </div>
    </div>
  );
}
