"use client";

import type { Metadata } from "next";
import { WorkspaceLandingView } from "./WorkspaceLandingView";
import { GenericWorkspaceView } from "./GenericWorkspaceView";
import { useAuth } from "@/hooks/useAuth";

// export const metadata: Metadata = { title: "Workspace — AQAA" };

export default function WorkspacePage() {
  const { user } = useAuth();

  if (user?.role === "generic_user") {
    return <GenericWorkspaceView />;
  }

  return <WorkspaceLandingView />;
}
