"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/common/PageHeader";
import { ZipUploadPanel } from "@/components/files/ZipUploadPanel";
import { useModules } from "@/hooks/useModules";

export function ZipUploadPageView() {
  const router = useRouter();
  const { data: modules, isLoading } = useModules();
  const [selectedModuleId, setSelectedModuleId] = useState("");

  return (
    <>
      <PageHeader
        title="Bulk ZIP Import"
        subtitle="Upload a ZIP archive to automatically classify and import multiple evidence files at once."
        actions={
          <Link href="/files" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
            Back to File Library
          </Link>
        }
      />

      <div className="max-w-3xl space-y-6">
        {/* Module selector */}
        <div className="rounded-xl border border-border bg-card p-5 space-y-3">
          <div>
            <p className="text-sm font-semibold text-foreground">Select Module</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              All files from the ZIP will be attached to this module.
            </p>
          </div>
          <select
            value={selectedModuleId}
            onChange={(e) => setSelectedModuleId(e.target.value)}
            disabled={isLoading}
            className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
          >
            <option value="">— Select a module —</option>
            {modules?.map((m) => (
              <option key={m.id} value={m.id}>
                {m.code} — {m.name}
              </option>
            ))}
          </select>
        </div>

        {/* ZIP upload panel */}
        {selectedModuleId ? (
          <div className="rounded-xl border border-border bg-card p-5">
            <ZipUploadPanel
              moduleId={selectedModuleId}
              onSuccess={() => router.push("/files")}
            />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16 text-center">
            <p className="text-sm font-medium text-muted-foreground">
              Select a module above to begin uploading
            </p>
          </div>
        )}

        {/* How it works */}
        <div className="rounded-xl border border-border bg-muted/30 p-5 space-y-2">
          <p className="text-sm font-semibold text-foreground">How bulk import works</p>
          <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground">
            <li>Drop a ZIP file containing your module documents</li>
            <li>AQAA automatically classifies each file by type (assessment plan, moderation report, etc.)</li>
            <li>Review and correct any misclassified files</li>
            <li>Confirm — files are queued for upload and virus scanning</li>
          </ol>
          <p className="text-xs text-muted-foreground/70 pt-1">
            Required categories: Assessment Plan, Internal Moderation, Attendance Register, Study Guide.
            Missing categories are flagged before confirmation.
          </p>
        </div>
      </div>
    </>
  );
}
