"use client";

import { useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Upload, Loader2, FileText, X } from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useUploadEvidence } from "@/hooks/useEvidence";
import { useAudits } from "@/hooks/useModuleAudits";
import { useRole } from "@/hooks/useRole";
import { EVIDENCE_CATEGORIES } from "@/types";

const ACCEPTED = ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.zip";

export function UploadEvidenceView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isSysAdmin } = useRole();
  const { data: audits } = useAudits();
  const uploadMutation = useUploadEvidence();

  const [auditId, setAuditId] = useState(searchParams.get("audit_id") ?? "");
  const [checklistItemId] = useState(searchParams.get("checklist_item_id") ?? "");
  const [category, setCategory] = useState(searchParams.get("category") ?? "general");
  const [description, setDescription] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const fileRef = useRef<HTMLInputElement>(null);

  function handleFile(f: File) {
    if (f.size > 50 * 1024 * 1024) {
      setErrors((p) => ({ ...p, file: "File must be smaller than 50 MB." }));
      return;
    }
    setErrors((p) => { const n = { ...p }; delete n.file; return n; });
    setSelectedFile(f);
  }

  function validate() {
    const e: Record<string, string> = {};
    if (!auditId) e.audit_id = "Audit is required.";
    if (!selectedFile) e.file = "Please select a file to upload.";
    return e;
  }

  async function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    if (!selectedFile) return;
    setErrors({});
    await uploadMutation.mutateAsync({
      file: selectedFile,
      auditId,
      checklistItemId: checklistItemId || null,
      evidenceCategory: category,
      description: description || null,
    });
    router.push("/files");
  }

  const cls = (err: boolean) =>
    `flex h-9 w-full rounded-md border bg-background px-3 py-1 text-sm ${err ? "border-destructive" : "border-input"}`;

  return (
    <RoleGuard
      roles={["system_admin","quality_assurance_officer","faculty_dean","head_of_department","programme_coordinator","lecturer"]}
      fallback={<div className="py-16 text-center"><p className="text-muted-foreground">You don&apos;t have permission to upload evidence.</p></div>}
    >
      <PageHeader
        title="Upload Evidence"
        subtitle="Attach a document to an audit as evidence for a QA checklist item."
        actions={<Link href="/files" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>Cancel</Link>}
      />

      <div className="max-w-lg">
        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} noValidate className="space-y-5">
              {/* Audit selector */}
              <div className="space-y-1.5">
                <Label htmlFor="ev-audit">Audit <span className="text-destructive">*</span></Label>
                <select
                  id="ev-audit"
                  value={auditId}
                  onChange={(e) => setAuditId(e.target.value)}
                  className={cls(!!errors.audit_id)}
                >
                  <option value="">Select an audit…</option>
                  {audits?.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.academic_year} — {a.status}
                    </option>
                  ))}
                </select>
                {errors.audit_id && <p role="alert" className="text-xs text-destructive">{errors.audit_id}</p>}
              </div>

              {/* Category */}
              <div className="space-y-1.5">
                <Label htmlFor="ev-cat">Evidence Category</Label>
                <select id="ev-cat" value={category} onChange={(e) => setCategory(e.target.value)} className={cls(false)}>
                  {EVIDENCE_CATEGORIES.map((c) => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>

              {/* Drop zone */}
              <div className="space-y-1.5">
                <Label>File <span className="text-destructive">*</span></Label>
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={(e) => {
                    e.preventDefault(); setDragOver(false);
                    const f = e.dataTransfer.files[0];
                    if (f) handleFile(f);
                  }}
                  onClick={() => fileRef.current?.click()}
                  className={cn(
                    "flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 cursor-pointer transition-colors",
                    dragOver ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-muted/30"
                  )}
                >
                  {selectedFile ? (
                    <div className="flex items-center gap-3 w-full">
                      <FileText className="h-8 w-8 text-primary flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-foreground truncate">{selectedFile.name}</p>
                        <p className="text-xs text-muted-foreground">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <>
                      <Upload className="h-8 w-8 text-muted-foreground mb-2" />
                      <p className="text-sm text-muted-foreground">Drop a file here or <span className="text-primary underline">browse</span></p>
                      <p className="text-xs text-muted-foreground/60 mt-1">PDF, Word, Excel, PowerPoint, images · max 50 MB</p>
                    </>
                  )}
                </div>
                <input
                  ref={fileRef}
                  type="file"
                  accept={ACCEPTED}
                  className="hidden"
                  onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
                />
                {errors.file && <p role="alert" className="text-xs text-destructive">{errors.file}</p>}
              </div>

              {/* Description */}
              <div className="space-y-1.5">
                <Label htmlFor="ev-desc">Description (optional)</Label>
                <textarea
                  id="ev-desc"
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Brief note about this evidence…"
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2 border-t">
                <Button type="button" variant="outline" onClick={() => router.push("/files")} disabled={uploadMutation.isPending}>
                  Cancel
                </Button>
                <Button type="submit" disabled={uploadMutation.isPending}>
                  {uploadMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  <Upload className="mr-2 h-4 w-4" />
                  Upload
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  );
}
