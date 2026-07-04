import type { Metadata } from "next";
import { EditDepartmentView } from "./EditDepartmentView";

export const metadata: Metadata = { title: "Edit Department" };

export default function EditDepartmentPage({
  params,
}: {
  params: { id: string };
}) {
  return <EditDepartmentView id={params.id} />;
}
