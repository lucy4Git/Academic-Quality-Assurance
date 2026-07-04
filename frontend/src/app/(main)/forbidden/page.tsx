import type { Metadata } from "next";
import Link from "next/link";
import { ShieldX } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const metadata: Metadata = { title: "Access Denied" };

export default function ForbiddenPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="rounded-full bg-destructive/10 p-6 mb-6">
        <ShieldX className="h-12 w-12 text-destructive" aria-hidden="true" />
      </div>
      <h1 className="text-2xl font-bold text-foreground mb-2">Access Denied</h1>
      <p className="text-muted-foreground max-w-md mb-8">
        You don&apos;t have permission to view this page. If you believe this is
        an error, contact your system administrator.
      </p>
      <div className="flex gap-3">
        <Link href="/dashboard" className={cn(buttonVariants({ variant: "default" }))}>
          Go to Dashboard
        </Link>
        <Link href="javascript:history.back()" className={cn(buttonVariants({ variant: "outline" }))}>
          Go Back
        </Link>
      </div>
    </div>
  );
}
