import type { Metadata } from "next";
import { EditInstitutionView } from "./EditInstitutionView";

export const metadata: Metadata = { title: "Edit Institution" };

export default function EditInstitutionPage({
  params,
}: {
  params: { id: string };
}) {
  return <EditInstitutionView id={params.id} />;
}
