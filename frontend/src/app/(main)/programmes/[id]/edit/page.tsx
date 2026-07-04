import type { Metadata } from "next";
import { EditProgrammeView } from "./EditProgrammeView";

export const metadata: Metadata = { title: "Edit Programme" };

export default function EditProgrammePage({ params }: { params: { id: string } }) {
  return <EditProgrammeView id={params.id} />;
}
