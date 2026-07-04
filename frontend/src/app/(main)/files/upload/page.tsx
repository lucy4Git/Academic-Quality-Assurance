import type { Metadata } from "next";
import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { UploadEvidenceView } from "./UploadEvidenceView";

export const metadata: Metadata = { title: "Upload Evidence" };

export default function UploadEvidencePage() {
  return (
    <Suspense fallback={<div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full max-w-lg" />)}</div>}>
      <UploadEvidenceView />
    </Suspense>
  );
}
