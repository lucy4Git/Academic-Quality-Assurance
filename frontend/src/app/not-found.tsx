import Link from "next/link";
import { MapPinOff } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="text-center">
        <div className="inline-flex items-center justify-center rounded-full bg-muted p-6 mb-6">
          <MapPinOff className="h-12 w-12 text-muted-foreground" aria-hidden="true" />
        </div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Page Not Found</h1>
        <p className="text-muted-foreground mb-8 max-w-md">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <Link href="/dashboard" className={cn(buttonVariants({ variant: "default" }))}>
          Go to Dashboard
        </Link>
      </div>
    </div>
  );
}
