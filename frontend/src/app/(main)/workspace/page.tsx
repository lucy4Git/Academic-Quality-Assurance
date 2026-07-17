import type { Metadata } from "next";
import { WorkspaceLandingView } from "./WorkspaceLandingView";

export const metadata: Metadata = { title: "Workspace — AQAA" };

export default function WorkspacePage() {
  return <WorkspaceLandingView />;
}
