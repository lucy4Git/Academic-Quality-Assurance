"use client";

import Link from "next/link";
import { Brain } from "lucide-react";
import { useRole } from "@/hooks/useRole";

export function FloatingAIButton() {
  const { isLecturer } = useRole();

  // Only show for staff (lecturer and above); hide for students
  if (!isLecturer) return null;

  return (
    <Link
      href="/ai-workspace"
      aria-label="Open AI Workspace"
      title="Open AI Workspace"
      className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full shadow-lg transition-all duration-200 hover:scale-110 hover:shadow-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring bg-gradient-to-br from-indigo-500 to-purple-600 text-white"
    >
      <Brain className="h-6 w-6" />
    </Link>
  );
}
