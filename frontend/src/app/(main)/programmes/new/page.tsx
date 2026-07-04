import type { Metadata } from "next";
import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { CreateProgrammeView } from "./CreateProgrammeView";

export const metadata: Metadata = { title: "New Programme" };

export default function CreateProgrammePage() {
  return (
    <Suspense fallback={<div className="max-w-lg space-y-4">{Array.from({length:5}).map((_,i)=><Skeleton key={i} className="h-10 w-full"/>)}</div>}>
      <CreateProgrammeView />
    </Suspense>
  );
}
