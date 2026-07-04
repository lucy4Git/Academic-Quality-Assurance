import type { Metadata } from "next";
import { ModuleDetailView } from "./ModuleDetailView";

export const metadata: Metadata = { title: "Module" };

export default function ModuleDetailPage({ params }: { params: { id: string } }) {
  return <ModuleDetailView id={params.id} />;
}
