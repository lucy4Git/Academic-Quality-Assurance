import type { Metadata } from "next";
import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { CreateModuleView } from "./CreateModuleView";

export const metadata: Metadata = { title: "New Module" };

export default function CreateModulePage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-lg space-y-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      }
    >
      <CreateModuleView />
    </Suspense>
  );
}
