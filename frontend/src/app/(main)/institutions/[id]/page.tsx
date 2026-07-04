import type { Metadata } from "next";
import { InstitutionDetailView } from "./InstitutionDetailView";

export const metadata: Metadata = { title: "Institution" };

export default function InstitutionDetailPage({
  params,
}: {
  params: { id: string };
}) {
  return <InstitutionDetailView id={params.id} />;
}
