import type { Metadata } from "next";
import { InstitutionWorkspaceView } from "./InstitutionWorkspaceView";

export const metadata: Metadata = { title: "Institution Workspace" };

export default function WorkspacePage() {
  return <InstitutionWorkspaceView />;
}
