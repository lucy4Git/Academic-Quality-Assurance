import type { Metadata } from "next";
import { FacultyDetailView } from "./FacultyDetailView";

export const metadata: Metadata = { title: "Faculty" };

export default function FacultyDetailPage({
  params,
}: {
  params: { id: string };
}) {
  return <FacultyDetailView id={params.id} />;
}
