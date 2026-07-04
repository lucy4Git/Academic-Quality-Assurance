import type { Metadata } from "next";
import { Suspense } from "react";
import { CreateDepartmentView } from "./CreateDepartmentView";
import { Skeleton } from "@/components/ui/skeleton";

export const metadata: Metadata = { title: "New Department" };

export default function CreateDepartmentPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-lg space-y-4">
          <Skeleton className="h-8 w-48" />
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      }
    >
      <CreateDepartmentView />
    </Suspense>
  );
}
