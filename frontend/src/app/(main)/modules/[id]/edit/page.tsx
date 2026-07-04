import type { Metadata } from "next";
import { EditModuleView } from "./EditModuleView";

export const metadata: Metadata = { title: "Edit Module" };

export default function EditModulePage({ params }: { params: { id: string } }) {
  return <EditModuleView id={params.id} />;
}
