import type { Metadata } from "next";
import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { CreateAuditView } from "./CreateAuditView";

export const metadata: Metadata = { title: "New Audit" };

export default function CreateAuditPage() {
  return (
    <Suspense fallback={<div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>}>
      <CreateAuditView />
    </Suspense>
  );
}
