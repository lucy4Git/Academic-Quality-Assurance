import { WorkflowDetailView } from "./WorkflowDetailView";

export const metadata = { title: "Audit Workflow — AQAA" };

export default function WorkflowDetailPage({ params }: { params: { id: string } }) {
  return <WorkflowDetailView id={params.id} />;
}
