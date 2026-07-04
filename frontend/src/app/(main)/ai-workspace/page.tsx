import type { Metadata } from "next";
import { AiWorkspaceView } from "./AiWorkspaceView";

export const metadata: Metadata = { title: "AI Workspace" };

export default function AiWorkspacePage() {
  return <AiWorkspaceView />;
}
