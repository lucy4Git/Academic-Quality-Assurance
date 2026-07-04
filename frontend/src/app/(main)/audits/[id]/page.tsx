import type { Metadata } from "next";
import { AuditDetailView } from "./AuditDetailView";

export const metadata: Metadata = { title: "Audit" };

export default function AuditDetailPage({ params }: { params: { id: string } }) {
  return <AuditDetailView id={params.id} />;
}
