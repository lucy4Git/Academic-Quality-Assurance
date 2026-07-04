import type { Metadata } from "next";
import { ProgrammeDetailView } from "./ProgrammeDetailView";

export const metadata: Metadata = { title: "Programme" };

export default function ProgrammeDetailPage({ params }: { params: { id: string } }) {
  return <ProgrammeDetailView id={params.id} />;
}
