import type { Metadata } from "next";
import { EditFacultyView } from "./EditFacultyView";

export const metadata: Metadata = { title: "Edit Faculty" };

export default function EditFacultyPage({
  params,
}: {
  params: { id: string };
}) {
  return <EditFacultyView id={params.id} />;
}
