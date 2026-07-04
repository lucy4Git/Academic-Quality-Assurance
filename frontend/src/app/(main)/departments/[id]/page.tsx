import type { Metadata } from "next";
import { DepartmentDetailView } from "./DepartmentDetailView";

export const metadata: Metadata = { title: "Department" };

export default function DepartmentDetailPage({
  params,
}: {
  params: { id: string };
}) {
  return <DepartmentDetailView id={params.id} />;
}
