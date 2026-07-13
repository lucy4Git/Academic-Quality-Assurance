import type { Metadata } from "next";
import { AccreditationWorkspace } from "./AccreditationWorkspace";

export const metadata: Metadata = { title: "Accreditation" };

export default function Page() {
  return <AccreditationWorkspace />;
}